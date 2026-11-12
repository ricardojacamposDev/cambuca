# Guia rápido do Cambuca

Arquivo de exemplo da pasta de conhecimento. A busca é por palavras, por isso cada seção tem uma linha de palavras-chave com os termos que alguém usaria na pergunta, inclusive sinônimos.

## Abrir, encerrar e configurar o modelo

Palavras-chave: iniciar, abrir, começar, sair, fechar, encerrar, modelo, GGUF, configurar, trocar modelo.

- Abra o Terminal na pasta do projeto e digite cambuca.
- Para sair, use /exit. Fechar a aba do Terminal também encerra o chat e o servidor.
- Os comandos que começam com barra (/exit, /clear, /delete, /trash, /restore, /rename, /move) são digitados por você no chat. O assistente não consegue executá-los.
- Para escolher outro arquivo GGUF: cambuca --configure pergunta de novo o caminho do modelo; arraste o arquivo .gguf para o Terminal e pressione Enter. Também dá para indicar direto: cambuca --model caminho/do/modelo.gguf.
- cambuca --doctor mostra a versão, o llama-server, onde fica a configuração do modelo, o prompt pessoal e a pasta de conhecimento.

## Contexto e histórico da conversa

Palavras-chave: contexto, memória, histórico, tokens, limite, esqueceu, conversa longa, limpar, /clear.

- O contexto padrão é de 8192 tokens. Para aumentar: cambuca --context 32768. O mínimo é 4096.
- O histórico acompanha o contexto: cerca de 6.000 caracteres com 4096, 18.000 com 8192 e 90.000 com 32768.
- Quando aparecer "Limite preventivo de histórico atingido", digite /clear no chat para limpar a conversa, ou saia e abra o cambuca com um contexto maior.
- Contextos maiores usam mais memória do Mac.

## Lixeira: apagar e recuperar arquivos

Palavras-chave: apagar, excluir, deletar, remover, lixeira, recuperar, restaurar, desfazer exclusão.

- /delete "arquivo.txt" envia o arquivo à Lixeira do macOS, a mesma do Finder. Nunca há exclusão permanente.
- /trash lista os arquivos que o Cambuca enviou à Lixeira a partir deste projeto, com o ID de cada um.
- /restore ID devolve o arquivo ao local original. Se já existir um arquivo com o mesmo nome, renomeie-o antes.
- Sem abrir o modelo: cambuca --trash-list e cambuca --restore ID.
- Depois que a Lixeira é esvaziada, o Cambuca não recupera mais o arquivo.

## Renomear e mover arquivos

Palavras-chave: renomear, trocar nome, mover, transferir, pasta.

- /rename "minuta.docx" "minuta-revisada.docx" troca o nome.
- /move "minuta.docx" "Revisados/minuta.docx" move para outra pasta, que precisa existir.
- Nenhuma operação sobrescreve um arquivo existente.

## Documentos Word

Palavras-chave: Word, docx, documento, editar, substituir, backup, cópia de segurança, desfazer edição.

- Peça em linguagem natural: ler, criar, acrescentar texto ou substituir um trecho em arquivos .docx.
- Antes de cada edição, uma cópia é salva em .campos/word-backups/ dentro do projeto. O caminho exato aparece logo depois da edição.
- O nome do backup tem um código antes do nome original, por exemplo 3f2a9c…-relatorio.docx. Não é igual ao nome do arquivo editado.
- A pasta .campos fica oculta. No Finder, Command+Shift+Ponto mostra pastas ocultas.
- Para desfazer: feche o documento no Word. Renomeie o arquivo editado (por exemplo, para relatorio-editado.docx), copie o backup para a mesma pasta e renomeie a cópia com o nome original (relatorio.docx).
- Limites: 20 MB compactado e 80 MB expandido. Arquivos .doc antigos não são suportados.

## Prompt pessoal e pasta de conhecimento

Palavras-chave: prompt, instruções, personalizar, conhecimento, RAG, documentos de referência.

- ~/Documents/Cambuca/prompt.md complementa as instruções do Cambuca. As mudanças valem a partir da próxima abertura.
- ~/Documents/Cambuca/conhecimento/ aceita arquivos .md e .txt, inclusive em subpastas. Arquivos novos ou alterados entram na pergunta seguinte.
- A busca não entende sinônimos. Por isso, escreva nos documentos as palavras que você usaria para perguntar.
