# Cambuca 0.4.1 — Word e arquivos com recuperação

Digite `cambuca` na pasta de trabalho para conversar com seu modelo GGUF local. Esta versão acrescenta suporte a Word (.docx) e operações próprias de renomear, mover, enviar à Lixeira e restaurar arquivos.

## Instalar pelo GitHub

```bash
brew install python llama.cpp git
git clone https://github.com/ricardojacamposDev/cambuca.git
cd cambuca
python3 instalar.py
```

Depois, abra uma nova aba do Terminal, entre na pasta desejada e digite `cambuca`.

## Instalar ou atualizar por ZIP

Feche o Cambuca antes de atualizar. Extraia este ZIP em uma pasta nova para não misturar versões. Se a pasta extraída estiver em Downloads:

```bash
brew install python llama.cpp
cd ~/Downloads/cambuca
python3 instalar.py
```

O instalador cria um ambiente virtual privado, instala `python-docx==1.2.0` e suas dependências, copia os módulos e atualiza o comando. Essa etapa requer internet. Não usa sudo. Preserva a escolha do modelo e os registros de Lixeira existentes. Se a instalação de dependências falhar (por exemplo, sem internet), a atualização é interrompida e a instalação anterior, se houver, continua funcionando.

Abra uma nova aba do Terminal e entre na pasta desejada:

```bash
cd ~/Documents/MeuProjeto
cambuca
```

Na primeira abertura, arraste o GGUF para o terminal quando solicitado. O modelo não acompanha o pacote. Use um modelo Instruct/Chat compatível com llama.cpp. Se houver partes, mantenha todas juntas e selecione a primeira. Para escolher outro: `cambuca --configure`.

A inferência e as ferramentas Word funcionam localmente após instalar dependências. O cliente não tem telemetria; comandos de terminal aprovados podem acessar a rede.

## Pedidos em linguagem natural

- “Leia o documento minuta.docx e resuma seu conteúdo.”
- “Crie relatorio.docx com título, dois parágrafos e uma tabela de pendências.”
- “No documento minuta.docx, substitua o trecho João Silva por João Souza.”
- “Acrescente um parágrafo de encerramento ao documento relatorio.docx.”
- “Renomeie minuta.docx para minuta-revisada.docx.”
- “Mova minuta-revisada.docx para a pasta Revisados.”
- “Envie rascunho.docx para a Lixeira.”
- “Liste os arquivos que posso recuperar da Lixeira.”

O agente deverá ler documentos antes de editar. Toda modificação mostra uma descrição e exige `sim`. Enter ou qualquer outra resposta recusa. A aderência a essas ferramentas depende do modelo; os comandos diretos abaixo funcionam sem interpretação da IA.

## Comandos diretos dentro do chat

```text
/rename "minuta.docx" "minuta-revisada.docx"
/move "minuta-revisada.docx" "Revisados/minuta-revisada.docx"
/delete "rascunho.docx"
/trash
/restore ID
```

Substitua `ID` pelo identificador exibido em `/trash`. A pasta de destino precisa existir. As operações aceitam arquivos regulares, não diretórios ou links. Não sobrescrevem arquivos existentes. Os caminhos devem permanecer dentro da pasta de trabalho.

`/delete` envia o arquivo à **Lixeira do macOS**, sem exclusão permanente. Não há fallback para `rm`. A Lixeira precisa estar acessível e a operação pode ser recusada pelo sistema, especialmente em volumes externos.

## Prompt pessoal e pasta de conhecimento

O instalador cria `~/Documents/Cambuca`. O que estiver nela vale para qualquer projeto:

- `prompt.md`: suas instruções, somadas às instruções internas do Cambuca. As internas definem as ferramentas e não podem ser substituídas. Exemplo: “Responda de forma breve e cite a fonte.” O limite é um quarto do histórico: 4.500 caracteres com o contexto padrão.
- `conhecimento/`: arquivos `.md` e `.txt`, inclusive em subpastas. A cada pergunta, o Cambuca busca os trechos mais relevantes e os anexa só àquela pergunta, sem acumular no histórico. O chat mostra os arquivos usados, por exemplo `Conhecimento: contratos/modelo.md`.

Na primeira instalação, a pasta já vem com um `prompt.md` de exemplo e um guia do Cambuca em `conhecimento/guia-cambuca.md`; as mesmas cópias estão em `exemplos/` no repositório. Edite ou apague à vontade: atualizações não os recriam.

A busca é por palavras (BM25 no SQLite), ignora acentos e aproxima flexões: “restaurar” encontra “restauração”. Ela não entende sinônimos, então use na pergunta as palavras que aparecem nos documentos. Arquivos novos ou alterados entram na pergunta seguinte, sem reiniciar. Arquivos e pastas ocultos são ignorados, e links simbólicos são seguidos. Limites: 5 MB por arquivo, 5.000 arquivos e 50 MB no total, em UTF-8 ou Windows-1252. Os trechos usam até um quarto do histórico por pergunta. `cambuca --doctor` mostra se o prompt está ativo e quantos arquivos foram encontrados.

## Recuperar sem carregar o modelo

Na mesma pasta de trabalho usada para a exclusão:

```bash
cambuca --trash-list
cambuca --restore ID
```

Ou indique a pasta explicitamente:

```bash
cambuca --workspace ~/Documents/MeuProjeto --trash-list
cambuca --workspace ~/Documents/MeuProjeto --restore ID
```

A restauração também pede confirmação e devolve o arquivo ao caminho original. Se já houver arquivo com esse nome, ele não será sobrescrito: renomeie ou mova o arquivo atual antes de restaurar. A pasta original deve continuar existindo.

O app só lista/restaura itens enviados à Lixeira por suas ferramentas próprias. Exclusões feitas por comandos livres, por outros aplicativos ou por versões anteriores não entram nesse registro. Você também pode abrir a Lixeira no Finder e mover o arquivo de volta manualmente. Se a Lixeira for esvaziada, o Cambuca não recupera o conteúdo. Não promete a opção “Colocar de Volta” do Finder: a restauração ao local original é oferecida pelo próprio Cambuca.

Se uma operação falhar depois de enviar o arquivo à Lixeira, o registro pode ficar `pending`. Confira o Finder; não repita automaticamente. Registros ficam vinculados ao caminho completo do workspace; se mover ou renomear a pasta inteira, use o Finder para recuperar itens antigos.

## Suporte Word e limites

| Recurso | Suporte |
| --- | --- |
| Ler texto de parágrafos, tabelas, cabeçalhos e rodapés | Sim, por blocos paginados |
| Criar títulos, seções, parágrafos e tabelas | Sim |
| Acrescentar texto/tabelas ao final | Sim |
| Substituir texto exato em parágrafos e células | Sim, com contagem de ocorrências |
| Preservar estilos básicos de trechos editados | Sim; texto novo herda o formato do início do trecho |
| Backup antes de editar | Sim, cópia exata da versão anterior |
| Editar campos, hyperlinks, imagens, caixas de texto ou revisões | Não; trechos complexos são recusados |
| DOC antigo, DOCM, arquivos protegidos por senha, macros | Não |
| Renderizar páginas ou editar como no Word visual | Não |

O suporte de leitura não inclui caixas de texto, notas de rodapé, comentários e conteúdo dentro de alterações controladas. Não considere o resumo uma leitura completa desses elementos. A leitura é limitada a 100 blocos por chamada e 4000 caracteres por bloco; documentos com parágrafos muito extensos precisam ser examinados no Word.

As substituições mantêm propriedades dos runs simples e não removem tabelas ou seções. Isso não garante fidelidade perfeita em todos os recursos avançados do Word; confira o resultado em documentos importantes. O app não executa macros.

Antes de cada edição, uma cópia binária é salva em `.campos/word-backups/` dentro do workspace. O caminho aparece após a gravação. Para desfazer, feche o documento no Word e copie esse backup sobre o arquivo editado pelo Finder. No Finder, `⌘⇧.` mostra pastas ocultas. Não apague esses backups enquanto precisar deles.

Arquivos Word: máximo 20 MB compactados e 80 MB expandidos. Criação/acréscimo: até 100 blocos e 50 mil caracteres por ação, sujeitos ao limite de saída do modelo. Peça mudanças pequenas se a resposta for truncada. A ferramenta de gravação de texto comum recusa extensões Word para não produzir um DOCX inválido.

## Outras opções

```bash
cambuca --read-only
cambuca --context 4096
cambuca --gpu-layers 0
cambuca --doctor
```

Somente leitura bloqueia todas as mutações, inclusive restauração e comandos livres. O padrão é contexto 8192. O histórico da conversa acompanha o contexto: cerca de 6.000 caracteres com 4096, 18.000 com 8192 e 90.000 com 32768. Contextos maiores usam mais memória. `/clear` limpa o histórico e `/exit` fecha o chat e o servidor. Fechar a aba do Terminal também encerra o servidor.

## Segurança e dados locais

As ferramentas próprias são limitadas ao workspace; exigem confirmação e verificam mudanças concorrentes comuns. Isso não constitui sandbox contra processos maliciosos ou condições de corrida deliberadas. Comandos livres aprovados continuam com as permissões do usuário, inclusive fora do workspace e na rede. Prefira as ferramentas próprias para exclusões recuperáveis.

O instalador usa `~/.local/share/cambuca` e `~/.local/bin/cambuca`, e acrescenta PATH em `.zshrc` e `.bash_profile`. A configuração do modelo está em `~/.config/cambuca/config.json`. O registro de Lixeira está em `~/.local/share/cambuca/trash.sqlite3`; ele contém caminhos e hashes, não cópias dos arquivos. Logs do motor ficam em `~/.local/state/cambuca`. Conversas não são persistidas. O índice da pasta de conhecimento fica só na memória durante a sessão.

As operações de mover e restaurar fazem cópia verificada antes de remover a origem, podendo exigir espaço adicional. Se o volume não permitir publicação segura sem sobrescrita, a operação falha preservando a origem. Não oferecemos garantia de preservação de todos os metadados específicos de provedores de nuvem/volumes.

## Validação

55 testes automatizados passaram (Linux e macOS com Python 3.10+): núcleo do agente, inicializador, instalador simulado, Word, movimentação, recusa, conflitos, Lixeira simulada, restauração e pasta de conhecimento. Um DOCX de teste criado e editado pelo módulo foi renderizado e inspecionado visualmente.

**Ainda não validado em Mac real:** API nativa de Lixeira, permissões de discos externos, execução GGUF e Metal. Os testes do adaptador macOS verificam o comando e seus argumentos com resposta simulada, não substituem a validação nativa. O instalador de dependências foi testado com instalação simulada; não foi executado no seu Mac.

Teste de aceitação recomendado no Mac, com arquivos descartáveis:

1. Crie um DOCX simples, abra no Word e peça uma substituição. Verifique conteúdo e backup.
2. Renomeie e mova um arquivo; tente mover sobre outro existente e confirme a recusa.
3. Use `/delete`, confira o arquivo na Lixeira do Finder e copie seu ID.
4. Encerre o chat e execute `cambuca --restore ID`; verifique o conteúdo original.
5. Recuse uma exclusão e confira que o arquivo permanece no lugar.

Para rodar os testes após instalação:

```bash
~/.local/share/cambuca/venv/bin/python -m unittest discover -s tests -v
```

Use sempre o Python 3.10+ do ambiente virtual; o Python do sistema no macOS (3.9) não tem as dependências do projeto.

## Referências

- https://python-docx.readthedocs.io/en/latest/
- https://developer.apple.com/documentation/foundation/filemanager/trashitem(at:resultingitemurl:)
- https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
