"""Operações em arquivos regulares com confirmação e Lixeira nativa do macOS."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import tempfile
import uuid

ACTIONS = {'rename', 'move', 'trash', 'trash_list', 'restore'}


def fingerprint(p):
    if p.is_symlink() or not p.is_file() or p.stat().st_nlink != 1:
        raise ValueError('Somente arquivos regulares, sem links, são aceitos.')
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def native_trash(path):
    if platform.system() != 'Darwin':
        raise ValueError('Lixeira nativa disponível somente no macOS; nada foi excluído.')
    script = '''ObjC.import('Foundation');
function run(argv) {
    var destination = Ref(); var error = Ref();
    var url = $.NSURL.fileURLWithPath(argv[0]);
    var ok = $.NSFileManager.defaultManager.trashItemAtURLResultingItemURLError(url, destination, error);
    if (!ok) throw new Error(error[0] ? ObjC.unwrap(error[0].localizedDescription) : 'Falha na Lixeira');
    return ObjC.unwrap(destination[0].path);
}'''
    # Caminho transmitido como argumento, jamais interpolado no script.
    result = subprocess.run(['/usr/bin/osascript','-l','JavaScript','-e',script,str(path)],
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError('Falha na Lixeira do macOS: ' + result.stderr[:1000])
    dest = Path(result.stdout.rstrip('\n'))
    if not dest.is_absolute():
        raise ValueError('O macOS não retornou o caminho da Lixeira. Confira no Finder.')
    return dest


def move_no_replace(src, dst, digest):
    """Publica sem sobrescrever; verifica cópia antes de remover a origem."""
    if dst.exists() or dst.is_symlink():
        raise ValueError('Destino já existe; escolha outro nome.')
    if not dst.parent.is_dir():
        raise ValueError('A pasta de destino deve existir.')
    fd, name = tempfile.mkstemp(dir=dst.parent, prefix='.cambuca-move-')
    os.close(fd)
    temp = Path(name)
    try:
        shutil.copy2(src, temp)
        if fingerprint(temp) != digest or fingerprint(src) != digest:
            raise ValueError('Arquivo mudou durante a operação; origem preservada.')
        os.link(temp, dst)  # Falha se o destino existir, inclusive em corrida.
        temp.unlink()
        if fingerprint(src) != digest:
            raise ValueError('Origem mudou após a cópia; ambos os arquivos foram preservados.')
        src.unlink()
    finally:
        temp.unlink(missing_ok=True)


class FileTools:
    def __init__(self, ws, state=None, trash_backend=native_trash):
        self.ws = ws
        self.state = Path(state) if state else Path.home()/'.local/share/cambuca/trash.sqlite3'
        self.trash_backend = trash_backend

    def db(self):
        self.state.parent.mkdir(parents=True, exist_ok=True)
        if not self.state.exists():
            fd = os.open(self.state, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        db = sqlite3.connect(self.state)
        db.execute('CREATE TABLE IF NOT EXISTS items (id TEXT PRIMARY KEY, root TEXT, original TEXT, trashed TEXT, digest TEXT, status TEXT)')
        return db

    def file(self, name):
        # Rejeita links mesmo quando apontam para dentro do workspace.
        raw = self.ws.root / name
        if raw.is_symlink():
            raise ValueError('Links simbólicos não são aceitos.')
        p = self.ws.path(name)
        if p == self.ws.root or not p.is_file():
            raise ValueError('Esta operação aceita apenas arquivos, não pastas.')
        return p

    def execute(self, a):
        from campos import display
        action = a['action']
        if action == 'trash_list':
            with self.db() as db:
                rows = db.execute('SELECT id,original,status FROM items WHERE root=? AND status != ? ORDER BY rowid DESC LIMIT 100',
                                  (str(self.ws.root),'restored')).fetchall()
            return json.dumps([{'id':r[0],'path':r[1],'status':r[2]} for r in rows],ensure_ascii=False)
        if self.ws.readonly:
            return 'Recusado: modo somente leitura.'
        if action in {'rename','move'}:
            src = self.file(a['path'])
            if action == 'rename':
                name = a['name']
                if not isinstance(name,str) or not name or name in {'.','..'} or '/' in name:
                    raise ValueError('Informe apenas o novo nome, sem pasta.')
                dst = self.ws.path(str(src.parent/name))
            else:
                dst = self.ws.path(a['destination'])
            if dst.exists() or dst.is_symlink():
                raise ValueError('Destino já existe. Nenhum arquivo será sobrescrito.')
            digest = fingerprint(src)
            display(f'{action}: {src}\nDestino: {dst}')
            if not self.ws.approve('Confirmar operação?'):
                return 'Operação recusada.'
            if self.file(a['path']) != src or fingerprint(src) != digest or self.ws.path(str(dst)) != dst:
                raise ValueError('Origem ou destino mudou; operação cancelada.')
            move_no_replace(src,dst,digest)
            return f'Concluído: {dst.relative_to(self.ws.root)}'
        if action == 'trash':
            src = self.file(a['path']); digest = fingerprint(src)
            display(f'Enviar à Lixeira do macOS: {src}')
            if not self.ws.approve('Confirmar envio à Lixeira?'):
                return 'Operação recusada.'
            if self.file(a['path']) != src or fingerprint(src) != digest:
                raise ValueError('Arquivo mudou; operação cancelada.')
            item = uuid.uuid4().hex
            with self.db() as db:
                db.execute('INSERT INTO items VALUES (?,?,?,?,?,?)',
                           (item,str(self.ws.root),str(src),'',digest,'pending'))
            try:
                trashed = self.trash_backend(src)
                with self.db() as db:
                    db.execute('UPDATE items SET trashed=?,status=? WHERE id=?',(str(trashed),'trashed',item))
                if src.exists() or fingerprint(trashed) != digest:
                    raise ValueError('Resultado da Lixeira precisa de revisão manual.')
            except Exception as exc:
                # Nunca há fallback para exclusão permanente nem repetição automática.
                raise ValueError(f'Operação precisa de revisão no Finder. ID {item}. {exc}') from exc
            return f'Enviado à Lixeira. ID de recuperação: {item}. Use /restore {item}.'
        if action == 'restore':
            item = a['id']
            with self.db() as db:
                row = db.execute('SELECT original,trashed,digest,status FROM items WHERE id=? AND root=?',
                                 (item,str(self.ws.root))).fetchone()
            if not row or row[3] != 'trashed':
                raise ValueError('ID não recuperável neste workspace. Consulte /trash e o Finder.')
            dst = self.ws.path(row[0]); src = Path(row[1])
            if not src.exists():
                raise ValueError('Arquivo não está mais na Lixeira; pode ter sido restaurado ou removido no Finder.')
            if dst.exists() or dst.is_symlink():
                raise ValueError('Já existe arquivo no local original. Renomeie-o antes de restaurar.')
            if fingerprint(src) != row[2]:
                raise ValueError('Conteúdo na Lixeira mudou. Restauração automática recusada.')
            display(f'Restaurar da Lixeira: {src}\nDestino original: {dst}')
            if not self.ws.approve('Confirmar restauração?'):
                return 'Restauração recusada.'
            if self.ws.path(row[0]) != dst:
                raise ValueError('Destino mudou; operação cancelada.')
            move_no_replace(src,dst,row[2])
            with self.db() as db:
                db.execute('UPDATE items SET status=? WHERE id=?',('restored',item))
            return f'Restaurado: {dst.relative_to(self.ws.root)}'
        raise ValueError('Operação desconhecida.')
