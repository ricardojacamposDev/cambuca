# Arquitetura Cambuca 0.3

`launcher.py` inicia o modelo via llama-server e abre o chat na mesma aba. As opções `--trash-list` e `--restore` dispensam o motor de IA. `campos.py` mantém o ciclo JSON e o executor de ferramentas; `wordtools.py` manipula documentos via python-docx e `filetools.py` faz operações de arquivos e recuperação.

## Protocolo

Cada resposta do modelo é um único objeto JSON. Ações disponíveis: `final`, `list`, `read`, `search`, `write`, `run`, `rename`, `move`, `trash`, `trash_list`, `restore`, `word_read`, `word_create`, `word_append`, `word_replace`. O prompt em `campos.py` contém os esquemas e exemplos. Respostas truncadas não são executadas; há limite de 12 etapas e orçamento preventivo por caracteres. Não há streaming nem tool calling nativo por família de modelo.

## Lixeira

O adaptador macOS usa `/usr/bin/osascript -l JavaScript` com o bridge Objective-C do Foundation para chamar `NSFileManager.trashItemAtURL:resultingItemURL:error:`. O caminho é um argumento separado, sem interpolação no script. Nenhum comando de exclusão permanente é usado como fallback.

O journal SQLite registra um UUID, workspace, caminho original, caminho retornado da Lixeira, SHA-256 e status. Primeiro grava `pending`, depois chama a API e atualiza para `trashed`. Uma falha entre etapas exige inspeção no Finder. O app valida conteúdo e destino antes de restaurar e marca `restored` depois de concluir. Esvaziar a Lixeira elimina o conteúdo; o journal não é backup.

Mutações aceitam somente arquivos regulares, sem symlinks ou hard links. Rename/move/restore publicam uma cópia temporária verificada com hard link exclusivo no destino antes de remover a origem. Isso evita sobrescrever destinos existentes, inclusive quando surgem durante a operação. Requer suporte a hard links no destino; falhas de permissão/filesystem podem impedir a operação. Essas verificações não substituem isolamento de processo.

## Word

Leitura percorre parágrafos, tabelas aninhadas, cabeçalhos e rodapés. Cada bloco tem ID e indicação `editable`. Edições de texto em parágrafos complexos são recusadas. Substituição opera em runs simples, de trás para frente, mantendo a formatação do início do trecho para o novo conteúdo. A ação exige `expected_count`, prevenindo alterações silenciosas em número inesperado de ocorrências.

Criação aceita blocos `title`, `heading` (níveis 1–3), `paragraph` e `table`. Acrescentar insere os blocos no final do corpo. Edições gravam backup antes de salvar em arquivo temporário e revalidam o original. Ações de criação não sobrescrevem arquivo existente. O README documenta os limites do formato e o que não é extraído.

## Instalação e manutenção

O instalador cria um venv sob `~/.local/share/cambuca/venv`, instala python-docx 1.2.0 e atualiza os quatro módulos. A seleção de GGUF e o journal são preservados. A instalação necessita internet; inferência e documentos não. Requisitos: Python >=3.10, llama-server para chat, macOS para Lixeira real. Testes usam backend de Lixeira injetável para rodar em Linux.

Os testes de instalação simulam venv/pip. Os testes do adaptador macOS simulam a chamada a osascript. Testes de Word usam python-docx real. Não há teste de inferência com GGUF real nesta entrega.
