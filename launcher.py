"""Inicialização integrada do Cambuca, sem dependências Python externas."""
import argparse
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import campos

CONFIG = Path.home() / '.config' / 'cambuca' / 'config.json'

def validate_model(value):
    p = Path(value).expanduser().resolve(strict=True)
    with p.open('rb') as f:
        if f.read(4) != b'GGUF':
            raise ValueError('O arquivo não possui assinatura GGUF.')
    return p

def get_model(selected=None, configure=False, config=CONFIG):
    if selected:
        model = validate_model(selected)
    elif config.exists() and not configure:
        model = validate_model(json.loads(config.read_text())['model'])
        return model
    else:
        campos.display('Primeira configuração: arraste o arquivo GGUF para este terminal e pressione Enter.')
        value = input('Modelo GGUF > ').strip()
        # Aceita caminho cru com espaços ou caminho escapado pelo Finder.
        if Path(value).expanduser().is_file():
            model = validate_model(value)
        else:
            values = shlex.split(value)
            if len(values) != 1:
                raise ValueError('Informe somente um arquivo GGUF.')
            model = validate_model(values[0])
    config.parent.mkdir(parents=True, exist_ok=True)
    temp = config.with_suffix('.tmp-' + str(os.getpid()))
    try:
        temp.write_text(json.dumps({'model':str(model)}, ensure_ascii=False, indent=2))
        temp.chmod(0o600)
        temp.replace(config)
    finally:
        temp.unlink(missing_ok=True)
    return model

def stop(proc):
    if proc.poll() is None:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()

def ready(port):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), campos.NoRedirect())
    try:
        with opener.open(f'http://127.0.0.1:{port}/health', timeout=1) as r:
            return r.status == 200
    except (OSError, ValueError):
        return False

def main():
    parser = argparse.ArgumentParser(description='Cambuca — seu assistente local. Basta digitar cambuca na pasta do projeto.')
    parser.add_argument('--model', help='Seleciona e salva outro arquivo GGUF')
    parser.add_argument('--configure', action='store_true', help='Pergunta novamente o caminho do modelo')
    parser.add_argument('--workspace', default='.', help='Pasta do projeto; padrão: pasta atual')
    parser.add_argument('--read-only', action='store_true')
    parser.add_argument('--context', type=int, default=8192)
    parser.add_argument('--gpu-layers', type=int, default=99 if platform.machine() == 'arm64' else 0)
    parser.add_argument('--doctor', action='store_true')
    parser.add_argument('--trash-list', action='store_true', help='Lista a Lixeira do workspace sem carregar modelo')
    parser.add_argument('--restore', metavar='ID', help='Restaura arquivo sem carregar modelo')
    args = parser.parse_args()
    proc = None
    try:
        if args.trash_list or args.restore:
            ws = campos.Workspace(args.workspace,args.read_only)
            action = {'action':'restore','id':args.restore} if args.restore else {'action':'trash_list'}
            campos.display(ws.execute(action))
            return 0
        binary = shutil.which('llama-server')
        if args.doctor:
            campos.display(f'Cambuca 0.3.0\nPython {platform.python_version()}\nllama-server: {binary or "não encontrado"}\nConfiguração: {CONFIG}')
            return 0
        if not binary:
            raise ValueError('Instale primeiro: brew install python llama.cpp')
        if args.context < 4096:
            raise ValueError('Use --context 4096 ou maior neste inicializador.')
        root = campos.Workspace(args.workspace, args.read_only).root
        model = get_model(args.model, args.configure)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        logs = Path.home() / '.local' / 'state' / 'cambuca'
        logs.mkdir(parents=True, exist_ok=True)
        log = logs / f'server-{os.getpid()}.log'
        # Arquivo privado; os logs podem conter metadados do modelo.
        fd = os.open(log, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as output:
            proc = subprocess.Popen([binary,'-m',str(model),'--host','127.0.0.1','--port',str(port),
                '--ctx-size',str(args.context),'--n-gpu-layers',str(args.gpu_layers),'--alias','local'],
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            campos.display(f'Cambuca | {root}\nCarregando {model.name}… (Ctrl+C cancela)')
            deadline = time.monotonic() + 300
            while True:
                if proc.poll() is not None:
                    raise ValueError(f'O motor encerrou. Veja o log: {log}')
                if ready(port):
                    break
                if time.monotonic() > deadline:
                    raise ValueError(f'Carregamento excedeu 5 minutos. Veja o log: {log}')
                time.sleep(.4)
            # Cliente e motor usam a mesma aba; o processo é encerrado no finally.
            original = sys.argv
            try:
                sys.argv = ['cambuca','chat','--workspace',str(root),'--port',str(port),
                            '--history-chars',str(6000 if args.context < 8192 else 18000)]
                if args.read_only:
                    sys.argv.append('--read-only')
                return campos.main()
            finally:
                sys.argv = original
    except (OSError, ValueError, KeyError, EOFError) as exc:
        campos.display(f'Erro: {exc}\nPara selecionar novamente o modelo: cambuca --configure')
        return 1
    except KeyboardInterrupt:
        campos.display('\nInterrompido.')
        return 130
    finally:
        if proc:
            stop(proc)

if __name__ == '__main__':
    sys.exit(main())
