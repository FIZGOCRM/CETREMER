# Handoff de design — GoMut e Emergensimples

Versão de 16/11/2026. Este pacote entrega o design **fechado** de três interfaces para quem vai implementá-las no código real (pessoa ou agente). O objetivo é que nada de estilo seja decidido na implementação: cores, fontes, tamanhos, espaçamentos, ícones, textos e comportamentos estão definidos aqui.

## 1. O que está sendo entregue

| Interface | De quem é a identidade | Aparência | Entrada no protótipo |
|---|---|---|---|
| **Tela de login** | GoMut (dona da plataforma) | Fundo verde profundo, cartão escuro translúcido, botão âmbar | `coprodutor.html` (sem sessão) e `index.html#/entrar` |
| **Área de membros** | Emergensimples (cliente da GoMut), mentoria **Plantão sem GPT** | Fundo escuro `#141414`, vermelho `#e50914`, texto branco | `index.html` |
| **Painel do produtor** (também chamado área do coprodutor) | GoMut | Fundo branco, Verde GO `#04736b`, texto grafite `#202221` | `coprodutor.html` |

A GoMut é a plataforma, no modelo de Eduzz e Hotmart: ela oferece a estrutura e o produtor (o cliente) publica os cursos. A área de membros leva a identidade do cliente. O painel e o login levam a identidade da GoMut.

As duas áreas usam **os mesmos componentes** (mesmos formatos, tamanhos, tipografia e acabamento). O painel muda **só as cores** e acrescenta poucas peças próprias (painel lateral, tabela, aba Básico).

## 2. Ordem de leitura

1. `01-regras-inviolaveis.md` — o que não pode ser mudado nem suposto.
2. `PROMPT-1-reconhecimento-da-stack.md` — rodar **antes de escrever código**, para levantar a stack do projeto real.
3. `02-tokens/tokens.md` e `02-tokens/tokens.json` — cores, tipografia, medidas, sombras, movimento e pontos de quebra.
4. `03-componentes/componentes.md` — cada componente com medidas e estados. Os três arquivos `css-por-componente-*.md` trazem o CSS completo, regra por regra.
5. `04-icones/icones.md` — os ícones (SVG) e as capas geradas.
6. `05-telas/` — tela por tela: login, área de membros e painel do produtor.
7. `06-comportamentos-e-regras.md` — permissões, publicação, liberação de aulas, avisos e o que é automático.
8. `07-mapa-de-configuracoes.md` — o que o painel configura e onde isso aparece para o aluno.
9. `08-pendencias-e-perguntas.md` — o que ainda **não** foi definido e não deve ser implementado por conta própria.
10. `PROMPT-2-implementacao.md` — instruções de trabalho para a implementação.

## 3. Ordem de autoridade

Quando duas fontes deste pacote parecerem dizer coisas diferentes, vale a de cima:

1. **`01-regras-inviolaveis.md`** e `08-pendencias-e-perguntas.md`.
2. **O CSS do protótipo** (`prototipo/assets/css/*.css`). É a fonte normativa de estilo. Os arquivos `css-por-componente-*.md` são cópia exata dele, reorganizada.
3. **Os documentos** `02` a `07`. Eles explicam o CSS e as decisões. Se um número de um documento divergir do CSS, vale o CSS — e a divergência deve ser avisada.
4. **As imagens** em `telas/`. Foram tiradas do próprio protótipo e servem para conferência visual.
5. **O JavaScript do protótipo** (`prototipo/assets/js/*.js`). Serve como referência de estrutura HTML, nomes de classe, textos e fluxos. **Não** é referência de arquitetura nem de qualidade de código.

Se algo necessário não estiver em nenhuma dessas fontes, **não invente**: pare e pergunte (ver `01-regras-inviolaveis.md`, regra 1).

## 4. O que é só demonstração no protótipo

O protótipo é HTML, CSS e JavaScript puros, sem build, com dados salvos no navegador. Estas partes existem só para o design poder ser navegado e **não devem ser copiadas como comportamento**:

- **Login simulado**: qualquer preenchimento entra. A regra real de autenticação e de permissão é da programação.
- **Dados fictícios**: nomes de cursos, pessoas, números, datas e textos de exemplo (`assets/js/data.js`). Os **rótulos da interface** (títulos de tela, botões, mensagens, dicas) são definitivos.
- **Armazenamento**: `localStorage` e `sessionStorage`. No produto real os dados vêm do servidor.
- **Reprodutor de vídeo simulado** na tela da aula (slides, capítulos e legenda de exemplo). No produto real o vídeo é incorporado do **Vimeo**.
- **Envio de arquivos** (capa, e-book): ilustrativo. A capa do curso é reduzida e guardada no navegador só para aparecer em "Meus cursos".
- **Ligação entre as áreas**: o que se altera no painel ainda não muda a área de membros, com duas exceções (responder chamado e responder na comunidade).
- **Resposta automática da mentora** na comunidade, alguns segundos depois de publicar: é simulação.
- **"Excluir curso"** no curso de exemplo mostra a confirmação e não apaga.
- **Avisos de reserva** dentro de `<main id="view">` nos dois HTML ("não abre por este arquivo"): são do protótipo.
- **Rodapé da área de membros** com "protótipo de interface com conteúdo fictício" e "Restaurar dados de exemplo", e o texto de rodapé do painel ("protótipo: as alterações ficam salvas só neste navegador"): são do protótipo.

## 5. Conteúdo do pacote

```
handoff-design/
├── LEIA-PRIMEIRO.md
├── PROMPT-1-reconhecimento-da-stack.md
├── PROMPT-2-implementacao.md
├── 01-regras-inviolaveis.md
├── 02-tokens/
│   ├── tokens.md                 cores, tipografia, medidas, movimento, pontos de quebra
│   └── tokens.json               os mesmos valores, para leitura por programa
├── 03-componentes/
│   ├── componentes.md            cada componente: estrutura, medidas e estados
│   ├── medidas-de-conferencia.md valores medidos no navegador, para conferir a implementação
│   ├── css-por-componente-area-de-membros.md
│   ├── css-por-componente-painel-do-produtor.md
│   └── css-por-componente-login.md
├── 04-icones/
│   ├── icones.md
│   ├── icones/                   51 ícones em SVG
│   └── motivos-das-capas/        14 desenhos usados nas capas geradas
├── 05-telas/
│   ├── login.md
│   ├── area-de-membros.md
│   └── painel-do-produtor.md
├── 06-comportamentos-e-regras.md
├── 07-mapa-de-configuracoes.md
├── 08-pendencias-e-perguntas.md
├── telas/                        imagens de todas as telas
│   ├── painel/computador-1440/   e  painel/celular-390/
│   └── membros/computador-1440/  e  membros/celular-390/
└── prototipo/                    o protótipo completo (fonte normativa do estilo)
    ├── index.html                área de membros
    ├── coprodutor.html           painel do produtor
    └── assets/                   css, js e marca (logotipo e arte do login)
```

## 6. Como abrir o protótipo

1. Mantenha a pasta `prototipo/` inteira, com `assets/` ao lado dos dois HTML.
2. Sirva a pasta por um servidor local simples (por exemplo `python3 -m http.server 4173` dentro de `prototipo/`) e abra `http://localhost:4173/coprodutor.html` (painel) ou `http://localhost:4173/` (área de membros). Abrir os arquivos direto no navegador também funciona.
3. Na tela de login, clique em **Entrar** (e-mail e senha podem ficar em branco).
4. As fontes são carregadas do Google Fonts: é preciso internet.

## 7. Vocabulário

- **Produtor / coprodutor**: quem gerencia o curso no painel. No protótipo a etiqueta é "Coprodutor".
- **Membro / aluno**: quem assiste, na área de membros.
- **Curso**: o produto do produtor. O curso do cliente é a mentoria "Plantão sem GPT".
- **Tema**: cada assunto do catálogo da área de membros (ex.: "Dor Torácica"). Na área de membros os temas aparecem na página "Cursos".
- **Módulo** e **aula**: partes de um tema. Na jornada da mentoria o módulo se chama **Semana**.
- **Trilha**: sequência de temas em ordem.
- **Curso à venda**: curso fora do plano do aluno, com página própria e checkout.
- **Fileira**: linha horizontal de cartões na página inicial do aluno.
