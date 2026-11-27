# CLAUDE.md

## Respostas longas vão para `respostas/`

Quando uma resposta for longa (explicações com várias seções, tabelas, fórmulas ou revisões), escreva-a num arquivo Markdown em `respostas/` em vez de colocá-la inteira no chat.

- Use um nome curto e descritivo, em português e minúsculas (ex.: `respostas/escalonamento.md`).
- Comece o arquivo com um título `#` que diga a pergunta respondida e, se houver, o trecho de código em questão.
- Links para o código são relativos ao arquivo, por exemplo: `[main.py:112](../src/main.py#L112)`. Links entre respostas usam o nome do arquivo irmão, por exemplo: `[kkt.md](kkt.md)`.
- Se o assunto já tiver um arquivo em `respostas/`, atualize esse arquivo em vez de criar outro.
- No chat, responda só com um resumo de 1 a 3 linhas e o link para o arquivo.

Respostas curtas continuam direto no chat.

`docs/` guarda apenas o material da disciplina (enunciado, artigo de referência e relatório).
