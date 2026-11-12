#!/usr/bin/env python3
"""Instala apenas para o usuário atual; não usa sudo; instala python-docx em ambiente virtual privado."""
import os
from pathlib import Path
import shlex
import shutil
import sys
import subprocess
import venv

if sys.version_info < (3, 10):
    sys.exit('Requer Python 3.10+: brew install python')
source = Path(__file__).resolve().parent
destination = Path.home()/'.local'/'share'/'cambuca'
bin_dir = Path.home()/'.local'/'bin'
destination.mkdir(parents=True, exist_ok=True)
bin_dir.mkdir(parents=True, exist_ok=True)
environment = destination/'venv'
previous = destination/'venv.anterior'
discard = destination/'venv.descartar'
# Reinstalação segura: o ambiente que já funciona fica guardado até o novo
# estar completo. Uma falha, ou uma execução anterior interrompida, o restaura.
if previous.exists():
    shutil.rmtree(environment, ignore_errors=True)
    previous.rename(environment)
shutil.rmtree(discard, ignore_errors=True)
if environment.exists():
    environment.rename(previous)
python = environment/'bin'/'python'
try:
    venv.EnvBuilder(with_pip=True).create(environment)
    subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', 'python-docx==1.2.0'], check=True)
except BaseException:
    shutil.rmtree(environment, ignore_errors=True)
    if previous.exists():
        previous.rename(environment)
    raise
if previous.exists():
    previous.rename(discard)
    shutil.rmtree(discard, ignore_errors=True)
for name in ['campos.py', 'launcher.py', 'filetools.py', 'wordtools.py']:
    if (source/name).resolve() != (destination/name).resolve():
        shutil.copy2(source/name, destination/name)
launcher = bin_dir/'cambuca'
launcher.write_text('#!/bin/sh\nexec ' + shlex.quote(str(python)) + ' ' + shlex.quote(str(destination/'launcher.py')) + ' "$@"\n')
launcher.chmod(0o755)
line = 'export PATH="$HOME/.local/bin:$PATH"'
for filename in ['.zshrc', '.bash_profile']:
    profile = Path.home()/filename
    text = profile.read_text() if profile.exists() else ''
    if line not in text:
        with profile.open('a') as f:
            f.write('\n# Cambuca: aplicativos locais do usuário\n' + line + '\n')
print('Cambuca instalado. Abra uma nova aba do Terminal e digite: cambuca')
if not shutil.which('llama-server'):
    print('Antes do primeiro uso, instale o motor: brew install python llama.cpp')
