# Cambuca 0.3.1 — Notas de release

## Novidades e correções

### Correções
- Portabilidade no macOS: caminho do modelo normalizado sem resolver links simbólicos (`/var` vs `/private/var`), corrigindo falha de teste no sistema-alvo.
- Robustez de DOCX: rejeita arquivos com caminhos internos inseguros ou excesso de partes (>1000).
- SQLite: fechamento explícito de conexões em operações de Lixeira.
- Lixeira nativa do macOS: tratamento claro de timeout do `osascript`.
- Instalador: ambiente virtual recriado com segurança em reinstalações (idempotente) e verificação de versão do pip desativada.

### Documentação
- README atualizado para 36 testes e instrução explícita de usar Python 3.10+ do venv.
- Versão exibida no `--doctor` atualizada para 0.3.1.

### Testes
- 36 testes automatizados passando (Linux e macOS com Python 3.10+).
- Novo teste de regressão: `test_unsafe_docx_rejected`.

## Limitações conhecidas
- Testes com modelo GGUF real e Lixeira nativa do macOS ainda dependem de validação em máquina real.
- Comandos livres (`run`) não são sandboxados (por design, com aprovação explícita).
- Sem verificação de hash da dependência `python-docx` no instalador.

## Verificação
- `python -m unittest discover -s tests` → 36/36 OK.
- Compilação de todos os módulos: OK.
- Varredura estática de vulnerabilidades: 0 achados.
