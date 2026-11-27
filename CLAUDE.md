# CLAUDE.md

## Antes de responder, consulte `respostas/`

Para poupar tokens: a cada pergunta, verifique primeiro se algum arquivo em `respostas/` já a responde. Basta olhar os títulos (`grep -m1 '^# ' respostas/*.md`) e, se preciso, buscar termos da pergunta com `grep`.

- Se houver resposta: apenas indique o arquivo (e a seção, se for o caso) com o link, em 1 a 2 linhas. Não repita o conteúdo e não refaça a análise.
- Se a resposta existente estiver incompleta ou desatualizada em relação ao código, diga isso e atualize esse arquivo.
- Se não houver: responda normalmente, seguindo a regra abaixo.

## Respostas longas vão para `respostas/`

Quando uma resposta for longa (explicações com várias seções, tabelas, fórmulas ou revisões), escreva-a num arquivo Markdown em `respostas/` em vez de colocá-la inteira no chat.

- Use um nome curto e descritivo, em português e minúsculas (ex.: `respostas/escalonamento.md`).
- Comece o arquivo com um título `#` que diga a pergunta respondida e, se houver, o trecho de código em questão.
- Links para o código são relativos ao arquivo, por exemplo: `[main.py:112](../src/main.py#L112)`. Links entre respostas usam o nome do arquivo irmão, por exemplo: `[kkt.md](kkt.md)`.
- Se o assunto já tiver um arquivo em `respostas/`, atualize esse arquivo em vez de criar outro.
- No chat, responda só com um resumo de 1 a 3 linhas e o link para o arquivo.

Respostas curtas continuam direto no chat.

`docs/` guarda apenas o material da disciplina (enunciado, artigo de referência e relatório).
