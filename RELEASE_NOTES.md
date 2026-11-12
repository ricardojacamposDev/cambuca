# Cambuca 0.4.0 — Notas de release

## Novidades
- **Prompt pessoal:** `~/Documents/Cambuca/prompt.md` complementa as instruções internas do Cambuca e vale para qualquer projeto. As instruções internas, que definem as ferramentas, continuam valendo. O limite é um quarto do histórico (4.500 caracteres com o contexto padrão); acima disso, o arquivo é ignorado e o chat avisa.
- **Pasta de conhecimento:** arquivos `.md` e `.txt` em `~/Documents/Cambuca/conhecimento/`, inclusive em subpastas. A cada pergunta, o Cambuca busca os trechos mais relevantes e os anexa só àquela pergunta, sem acumular no histórico. O chat mostra os arquivos usados.
- A busca é por palavras (BM25 no SQLite FTS5, em memória), ignora acentos e aproxima flexões. Arquivos novos ou alterados entram na pergunta seguinte, sem reiniciar.
- A abertura do chat e o `cambuca --doctor` mostram o estado do prompt pessoal e quantos arquivos de conhecimento foram encontrados.
- O instalador cria `~/Documents/Cambuca/conhecimento`.

## Testes
- 53 testes automatizados passando.
- Novos testes: divisão em blocos, busca sem acentos e com flexões, atualização de arquivos novos, alterados e removidos, filtros e limites, links em ciclo, orçamento de trechos, leitura do prompt e trechos válidos só no turno atual.

## Limitações conhecidas
- A busca não entende sinônimos: a pergunta precisa usar palavras que aparecem nos documentos.
- Limites da pasta de conhecimento: 5 MB por arquivo, 5.000 arquivos e 50 MB no total, em UTF-8 ou Windows-1252.
- Se o launcher for morto com `kill -9` (`SIGKILL`), o motor ainda fica órfão.
- Testes da Lixeira nativa do macOS ainda dependem de validação em máquina real.
- Possível, não verificado: sem Acesso Total ao Disco para o Terminal, o macOS pode bloquear a leitura de `~/.Trash`.
- Comandos livres (`run`) não são sandboxados (por design, com aprovação explícita).
- Sem verificação de hash da dependência `python-docx` no instalador.

## Verificação
- `python -m unittest discover -s tests` → 53/53 OK (Python 3.12, macOS).
- Com o modelo GGUF real e uma pasta pessoal temporária: o `prompt.md` pedia para terminar as respostas com uma palavra de controle, e a pasta de conhecimento tinha um documento com o código de um cofre e outro sem relação. À pergunta sobre o código, o Cambuca usou só o documento certo, citou o arquivo, respondeu o código correto e terminou com a palavra de controle.

---

# Cambuca 0.3.4 — Notas de release

## Correções
- Fechar a aba do Terminal, ou encerrar o Cambuca com `kill`, agora também encerra o motor `llama-server`. Antes, o launcher morria com o `SIGHUP` ou `SIGTERM` sem executar a limpeza, e o motor continuava rodando sozinho com o modelo na memória (cerca de 5 GB com o modelo de teste). Um comando aprovado no chat que estiver em execução também é encerrado.

## Testes
- 45 testes automatizados passando.
- Novo teste: `test_hangup_stops_server`. Com o launcher da 0.3.3, o próprio processo de teste morre pelo `SIGHUP`.

## Limitações conhecidas
- Se o launcher for morto com `kill -9` (`SIGKILL`), o motor ainda fica órfão: esse sinal não pode ser tratado.
- Contextos maiores usam mais memória no llama-server. O máximo prático depende do modelo e da memória do Mac.
- Testes da Lixeira nativa do macOS ainda dependem de validação em máquina real.
- Possível, não verificado: sem Acesso Total ao Disco para o Terminal, o macOS pode bloquear a leitura de `~/.Trash`, o que afetaria a conferência após enviar à Lixeira e a restauração.
- Comandos livres (`run`) não são sandboxados (por design, com aprovação explícita).
- Sem verificação de hash da dependência `python-docx` no instalador.

## Verificação
- `python -m unittest discover -s tests` → 45/45 OK (Python 3.12, macOS).
- Com o modelo GGUF real, chat aberto e `SIGHUP` enviado ao launcher: na 0.3.3, o `llama-server` ficou órfão; na 0.3.4, ele registrou `cleaning up before exit...` e encerrou, e o launcher saiu com código 129.

---

# Cambuca 0.3.3 — Notas de release

## Novidades
- O histórico da conversa acompanha o tamanho do contexto (`--context`). Antes, ficava fixo em 18.000 caracteres a partir de 8192 tokens. Agora cresce na mesma proporção: 90.000 caracteres com 32768, por exemplo. Com 4096 e 8192 os valores não mudam (6.000 e 18.000).
- Quando o histórico enche, o aviso sugere abrir o `cambuca` com `--context` maior, a opção disponível no comando, em vez de `--history-chars`.

## Testes
- 44 testes automatizados passando.
- Novo teste: `test_history_follows_context`.

## Limitações conhecidas
- Contextos maiores usam mais memória no llama-server. O máximo prático depende do modelo e da memória do Mac.
- Testes com modelo GGUF real e Lixeira nativa do macOS ainda dependem de validação em máquina real.
- Possível, não verificado: sem Acesso Total ao Disco para o Terminal, o macOS pode bloquear a leitura de `~/.Trash`, o que afetaria a conferência após enviar à Lixeira e a restauração.
- Comandos livres (`run`) não são sandboxados (por design, com aprovação explícita).
- Sem verificação de hash da dependência `python-docx` no instalador.

## Verificação
- `python -m unittest discover -s tests` → 44/44 OK (Python 3.12, macOS).

---

# Cambuca 0.3.2 — Notas de release

## Correções
- Modelo: o caminho é gravado como absoluto em `config.json`. Um modelo escolhido com caminho relativo (`cambuca --model m.gguf` ou na primeira configuração) volta a funcionar a partir de qualquer pasta. O caminho também não é mais reduzido como texto em `..`, então abre o mesmo arquivo que o sistema abriria. Regressão introduzida na 0.3.1.
- Instalador: a reinstalação guarda o ambiente virtual existente até o novo estar completo. Se a criação do ambiente ou a instalação do `python-docx` falhar (por exemplo, sem internet), o ambiente anterior é restaurado e o Cambuca continua funcionando. Na 0.3.1, uma falha apagava o ambiente que funcionava.
- Lixeira: erros do registro SQLite (bloqueado por outra sessão ou corrompido) aparecem como mensagem de erro, com o caminho do registro, em vez de encerrar o chat. A conexão é sempre fechada. Se uma restauração mover o arquivo mas não conseguir atualizar o registro, a mensagem informa que o arquivo foi restaurado.

## Testes
- 43 testes automatizados passando.
- Novos testes: caminho relativo usado a partir de outra pasta; reinstalação com sucesso, com falha e após execução interrompida; registro corrompido; fechamento da conexão; falha ao atualizar o registro após restaurar. Os 6 testes de regressão falham com o código da 0.3.1.

## Limitações conhecidas
- Testes com modelo GGUF real e Lixeira nativa do macOS ainda dependem de validação em máquina real.
- Possível, não verificado: sem Acesso Total ao Disco para o Terminal, o macOS pode bloquear a leitura de `~/.Trash`, o que afetaria a conferência após enviar à Lixeira e a restauração.
- Comandos livres (`run`) não são sandboxados (por design, com aprovação explícita).
- Sem verificação de hash da dependência `python-docx` no instalador.

## Verificação
- `python -m unittest discover -s tests` → 43/43 OK (Python 3.12, macOS).
- Instalador executado de verdade com uma pasta pessoal temporária: instalação, reinstalação e reinstalação sem acesso ao PyPI. Na última, a atualização foi interrompida e o ambiente anterior continuou com `python-docx`.

---

# Cambuca 0.3.1 — Notas de release

> **Atualize para a [0.3.2](https://github.com/ricardojacamposDev/cambuca/releases/tag/v0.3.2).** Problemas desta versão corrigidos na 0.3.2:
> - Um modelo escolhido com caminho relativo deixa de funcionar quando o `cambuca` é aberto em outra pasta.
> - Uma reinstalação que falha (por exemplo, sem internet) apaga o ambiente virtual que funcionava, e o instalador não é idempotente como descrito abaixo.
> - Erros do registro SQLite da Lixeira (bloqueado ou corrompido) podem encerrar o chat.

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
