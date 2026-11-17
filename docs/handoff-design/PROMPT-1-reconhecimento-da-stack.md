# Prompt 1 — reconhecimento da stack

Cole o texto abaixo no agente de código, **dentro do repositório do projeto real**, antes de qualquer implementação. O relatório que ele devolver serve para adaptar o mapeamento dos tokens e dos componentes à stack, sem suposições de nenhum dos dois lados.

---

```text
Você vai implementar um design que já está fechado. Antes de escrever qualquer código, preciso
de um relatório do que este repositório usa. Não altere nenhum arquivo nesta etapa. Não instale
nada. Só leia o repositório e responda.

Responda em português, com base apenas no que encontrar nos arquivos. Para cada item, cite o
arquivo (e a linha, quando fizer sentido) de onde tirou a informação. Se não encontrar, escreva
"não encontrado" em vez de deduzir.

1. VISÃO GERAL
   - Linguagem, framework e versão (ex.: Next.js, Nuxt, Laravel, Rails, Django).
   - Como o projeto é organizado em pastas (árvore resumida, 2 níveis).
   - Como se roda, se testa e se publica (comandos).
   - É um repositório só ou há front-end e back-end separados?

2. ESTILO
   - Como o estilo é escrito: Tailwind (qual versão e onde está a configuração), CSS Modules,
     Sass, styled-components, CSS puro, outro.
   - Existem tokens ou tema hoje? Onde? Liste as cores, fontes, espaçamentos, raios e pontos de
     quebra que já estão definidos.
   - Há variáveis CSS globais? Há suporte a mais de um tema na mesma aplicação (o design tem três
     contextos de cor: área de membros escura, painel claro e tela de login)?
   - Há reset ou estilos globais que afetem botões, campos, títulos e links?
   - Existe modo escuro configurado? Como é ativado?

3. COMPONENTES E BIBLIOTECAS DE INTERFACE
   - Biblioteca de componentes em uso (ex.: shadcn/ui, Radix, MUI, Chakra, Ant, Bootstrap,
     Headless UI) e versão.
   - Lista dos componentes que já existem no projeto (botão, campo, seleção, chave, abas, janela,
     menu suspenso, aviso rápido, tabela, cartão, barra lateral), com o caminho de cada um.
   - Biblioteca de ícones em uso.
   - Como as fontes são carregadas hoje. O projeto aceita fonte variável com eixo de largura
     (Archivo com o eixo wdth) e Inter?

4. PÁGINAS, ROTAS E ACESSO
   - Sistema de rotas e lista das rotas que já existem.
   - Como funciona a autenticação e como os papéis são distinguidos (produtor, coprodutor,
     aluno). Onde isso é verificado.
   - O que já existe hoje da área de membros, do painel do produtor e da tela de login.

5. DADOS
   - Banco de dados, ORM e onde ficam os modelos.
   - Modelos que já existem para: curso, módulo, aula, aluno, plano ou matrícula, encontro ao
     vivo, publicação e resposta da comunidade, chamado de suporte, certificado, aviso.
   - Como o front-end busca e grava dados (API REST, GraphQL, server actions, outro).
   - Gerenciamento de estado no cliente.
   - Formulários e validação (biblioteca e padrão usado).

6. ARQUIVOS E INTEGRAÇÕES
   - Como é feito envio de arquivos (imagens e PDF) e onde ficam guardados.
   - Integração de vídeo: há Vimeo hoje? Como o vídeo é incorporado?
   - Envio de e-mail e avisos dentro do sistema.
   - Pagamento ou checkout externo.

7. QUALIDADE
   - Testes existentes (tipo e ferramenta), lint e formatação.
   - Navegadores e tamanhos de tela que o projeto se compromete a atender.
   - Regras de acessibilidade já adotadas.

8. RISCOS PARA APLICAR UM DESIGN FECHADO
   - O que, na stack atual, pode impedir que valores exatos sejam usados (ex.: escala fixa de
     espaçamento, tema de biblioteca difícil de zerar, pontos de quebra fixos, fontes).
   - Estilos ou componentes existentes que entram em conflito com um design novo.
   - O que você precisaria que eu decidisse antes de começar.

9. PERGUNTAS
   - Liste tudo o que ficou sem resposta ou ambíguo.

Formato da resposta: um documento em Markdown com os nove títulos acima, objetivo, sem código
novo e sem propostas de implementação. No fim, uma tabela de três colunas: "O que o design
exige", "O que a stack oferece hoje", "Lacuna".

Para preencher essa tabela, considere que o design exige: três conjuntos de tokens de cor na
mesma aplicação; Archivo variável (eixo de largura) e Inter; 51 ícones próprios em SVG; pontos de
quebra próprios (599, 899, 1023, 1099, 1199, 1279, 1439 e 1499 px); componentes com medidas
exatas em pixels; barra lateral fixa de 248 px no painel; janelas de edição; avisos rápidos;
envio de imagem de capa e de PDF; vídeo do Vimeo incorporado.
```

---

## O que fazer com a resposta

1. Guarde o relatório junto deste pacote.
2. Envie o relatório à responsável pelo design. Com ele é possível entregar o mapeamento pronto para a stack (por exemplo, a configuração de tema da ferramenta de estilo com os valores exatos).
3. Só depois siga para o `PROMPT-2-implementacao.md`.
