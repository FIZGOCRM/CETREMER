# Tokens de design

Valores exatos. O arquivo `tokens.json` (mesma pasta) traz os mesmos valores para leitura por programa. Origem: `prototipo/assets/css/tokens.css` (área de membros), bloco "paleta" de `prototipo/assets/css/admin.css` (painel) e início de `prototipo/assets/css/login.css` (login).

**Como funciona a troca de identidade:** os componentes leem sempre os mesmos nomes de variável (`--c-bg`, `--c-text`, `--c-red`, etc.). A área de membros define esses nomes com as cores do cliente. O painel do produtor **redefine os mesmos nomes** com as cores da GoMut. Por isso o nome `--c-red` continua existindo no painel, onde vale Verde GO. Na implementação, mantenha esse mecanismo (um conjunto de tokens por contexto), com os valores abaixo.

## 1. Cores — área de membros (identidade do cliente)

| Token | Valor | Uso |
|---|---|---|
| `--c-black` | `#000000` | Preto puro |
| `--c-bg` | `#141414` | Fundo da página |
| `--c-surface-1` | `#181818` | Painéis, cartões, janela do curso |
| `--c-surface-2` | `#232323` | Superfície elevada, linha de arquivo, item ativo de menu lateral |
| `--c-surface-3` | `#2f2f2f` | Fundo de etiqueta padrão, passar o mouse em superfícies |
| `--c-surface-4` | `#414141` | Trilho de chave desligada, avatar cinza, ícone de estado vazio |
| `--c-red` | `#e50914` | Cor da marca: botão principal, indicadores, aba ativa, barra de progresso |
| `--c-red-hover` | `#f6121d` | Botão principal ao passar o mouse |
| `--c-red-press` | `#b20710` | Botão principal pressionado |
| `--c-text` | `#ffffff` | Texto principal |
| `--c-text-2` | `#e5e5e5` | Texto secundário |
| `--c-text-3` | `#b3b3b3` | Texto de apoio, rótulos de campo |
| `--c-text-4` | `#808080` | Texto discreto, metadados |
| `--c-line` | `rgba(255, 255, 255, 0.12)` | Bordas e divisórias |
| `--c-line-strong` | `rgba(255, 255, 255, 0.32)` | Borda de botão de contorno e de filtro |
| `--c-green` | `#46d369` | Concluído, positivo |
| `--c-amber` | `#e8b339` | Aviso, destaque secundário |
| Cor do navegador (`theme-color`) | `#141414` | |

Cores fixas usadas em componentes (não são tokens): campo de texto com borda `#5e5e5e` (ao passar o mouse `#8c8c8c`) e fundo `rgba(22, 22, 22, 0.7)`; seleção com borda `#4d4d4d` e fundo `#242424`; aviso rápido com fundo `#ffffff` e texto `#141414`; véu das janelas `rgba(0, 0, 0, 0.72)`; certificado com fundo `#ffffff` e texto `#141414`.

## 2. Cores — painel do produtor (identidade da GoMut)

Paleta da marca:

| Token | Valor | Nome | Uso |
|---|---|---|---|
| `--go` | `#04736b` | Verde GO | Ação principal, indicadores, ícones de destaque, links |
| `--go-hover` | `#058278` | | Botão principal ao passar o mouse |
| `--go-press` | `#035a54` | | Botão principal pressionado; texto da etiqueta "ok" |
| `--grafite` | `#202221` | Grafite | Texto principal, títulos, botão invertido |
| `--ambar` | `#faad31` | Âmbar | Ponto da chave ligada, ícone do aviso rápido. Só em pontos importantes; nunca em texto pequeno |
| `--creme` | `#fefcf5` | Creme | Texto do aviso rápido |
| `--verde-profundo` | `#142724` | Verde profundo | Fundo do aviso rápido; base do véu das janelas |
| `--verde-palido` | `#e5f0ea` | Verde pálido | Superfícies suaves, item ativo do menu lateral, etiqueta "ok" |
| `--pessego` | `#fcddbb` | Pêssego | Etiqueta de pendência ("Despublicado", "Rascunho", "Aberto") |
| `--perigo` | `#b93a2b` | Vermelho de perigo | Botão de confirmação de ações que tiram algo do ar; mensagem de erro |
| `--perigo-hover` | `#c9463a` | | |

Tokens de interface (mesmos nomes da área de membros, redefinidos):

| Token | Valor no painel |
|---|---|
| `--c-bg` | `#ffffff` |
| `--c-surface-1` | `#ffffff` |
| `--c-surface-2` | `#e5f0ea` |
| `--c-surface-3` | `#d6e6dd` |
| `--c-surface-4` | `#b4c7be` |
| `--c-text` | `#202221` |
| `--c-text-2` | `#363a38` |
| `--c-text-3` | `#565d5a` |
| `--c-text-4` | `#6e7672` |
| `--c-line` | `rgba(32, 34, 33, 0.13)` |
| `--c-line-strong` | `rgba(32, 34, 33, 0.34)` |
| `--c-red`, `--c-green`, `--acento` | `#04736b` |
| `--c-red-hover` | `#058278` |
| `--c-red-press` | `#035a54` |
| `--nav-bg` | `#ffffff` |
| `--inv-bg` / `--inv-fg` / `--inv-hover` | `#202221` / `#ffffff` / `#3b3f3d` (botão e filtro "invertidos") |
| `--campo-bg` / `--campo-borda` / `--campo-borda-hover` | `#ffffff` / `#b3bfb9` / `#6f7c77` |
| `--contorno-bg` / `--contorno-hover` | `#ffffff` / `#e5f0ea` (botão de contorno) |
| `--tag-bg` | `#ecebe6` |
| `--ok-bg` / `--ok-fg` | `#e5f0ea` / `#035a54` |
| `--alerta-bg` / `--alerta-fg` | `#fcddbb` / `#202221` |
| `--realce` | `rgba(4, 115, 107, 0.06)` (fundo ao passar o mouse em linhas e itens) |
| `--toast-bg` / `--toast-fg` / `--toast-ico` | `#142724` / `#fefcf5` / `#faad31` |
| `--veu` | `rgba(20, 39, 36, 0.55)` (fundo atrás das janelas e do menu lateral no celular) |
| `--shadow-pop` | `0 14px 44px rgba(20, 39, 36, 0.2)` |
| `--lado-w` | `248px` (largura do painel lateral; `228px` até 1199 px de tela) |
| Cor do navegador (`theme-color`) | `#ffffff` |
| `color-scheme` | `light` |

Dentro do painel, `.cover` e `.cert` voltam a `--c-red: #e50914` (são prévias do que o aluno vê).

Foco no painel: contorno de 2 px em `#04736b`. Seleção de texto no painel: fundo `#04736b`, texto `#ffffff`.

## 3. Cores — tela de login (GoMut)

A tela de login traz a própria paleta e não depende das outras duas.

| Token | Valor | Uso |
|---|---|---|
| `--gm-profundo` | `#142724` | Fundo da tela e da página em volta dela |
| `--gm-go` | `#04736b` | Brilho radial do fundo; foco dentro da barra |
| `--gm-go-escuro` | `#035a54` | Link "Entrar" da barra |
| `--gm-grafite` | `#202221` | Texto da barra e do botão "Entrar" |
| `--gm-ambar` | `#faad31` | Botão "Entrar", contorno de foco, seleção de texto |
| `--c-text` | `#ffffff` | |
| `--c-text-2` | `rgba(255, 255, 255, 0.92)` | Frase de apoio do destaque |
| `--c-text-3` | `rgba(255, 255, 255, 0.78)` | Frase do cartão, rótulos |
| `--c-text-4` | `rgba(255, 255, 255, 0.6)` | |
| `--c-line` | `rgba(255, 255, 255, 0.16)` | Borda do cartão |
| `--c-line-strong` | `rgba(255, 255, 255, 0.34)` | |
| Cor do navegador (`theme-color`) | `#142724` | Só enquanto o login está aberto |

Fundo da tela: `radial-gradient(46% 70% at 56% 52%, rgba(4, 115, 107, 0.9), rgba(4, 115, 107, 0) 74%), #142724`. Até 1199 px: `radial-gradient(64% 62% at 30% 60%, …)`. Até 699 px: `radial-gradient(90% 44% at 50% 38%, …)`.

Outros valores fixos do login: barra do topo `rgba(255, 255, 255, 0.84)` com borda `rgba(255, 255, 255, 0.7)` e `backdrop-filter: blur(16px) saturate(1.3)`; cartão `rgba(9, 22, 20, 0.74)` com `backdrop-filter: blur(8px)`; campo com fundo `rgba(8, 20, 18, 0.55)` e borda `rgba(255, 255, 255, 0.26)` (ao passar o mouse `rgba(255, 255, 255, 0.52)`); botão "Entrar" `#faad31` (ao passar o mouse `#ffbd52`, pressionado `#eb9d1f`); arte "GO + mamute" na cor `rgb(9, 22, 20)` com opacidade `0.74`.

## 4. Tipografia

### Famílias e carregamento

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

| Token | Valor | Uso |
|---|---|---|
| `--font-display` | `"Archivo", "Arial Narrow", "Helvetica Neue", Arial, sans-serif` | Títulos. É a Archivo **variável**, com o eixo de largura (`wdth` 62 a 125) e peso de 100 a 900 |
| `--font-ui` | `"Inter", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` | Todo o resto. Pesos usados: 300, 400, 500, 600, 700 |

A largura condensada dos títulos vem de `font-stretch` (por exemplo `82%`). Sem a Archivo variável com o eixo `wdth`, os títulos ficam errados: não troque por uma Archivo estática.

Texto base (`body`): `400 16px/1.5` Inter, com `-webkit-font-smoothing: antialiased`.

### Escala

| Token | Valor |
|---|---|
| `--fs-xs` | `12px` |
| `--fs-s` | `14px` |
| `--fs-m` | `16px` |
| `--fs-l` | `18px` |
| `--fs-xl` | `clamp(20px, 1.6vw, 26px)` |
| `--fs-page` | `clamp(30px, 3.6vw, 48px)` |
| `--fs-hero` | `clamp(56px, 9.4vw, 156px)` |

### Estilos de texto

| Estilo | Família | Peso | Largura (`font-stretch`) | Tamanho | Altura de linha | Espaçamento | Caixa |
|---|---|---|---|---|---|---|---|
| Título do destaque da área de membros (`.hero__title`) | Archivo | 900 | 64% | `--fs-hero` | 0.84 | -0.012em | MAIÚSCULAS |
| Título de página (`.page__title`) | Archivo | 800 | 82% | `--fs-page` | 1.02 | -0.012em | normal |
| Título de janela de edição do painel (`.cop-dialog h2`) | Archivo | 800 | 82% | `clamp(22px, 2.4vw, 30px)` | 1.1 | — | normal |
| Título da capa gerada (`.cover__title`) | Archivo | 800 | 66% | `9.6cqw` | 0.92 | -0.004em | MAIÚSCULAS |
| Número do módulo (`.week__n`) | Archivo | 800 | 80% | 22px | — | — | — |
| Nome no certificado (`.cert__name`) | Archivo | 800 | 78% | `6.6cqw` | 1 | — | normal |
| Título do login (`.gm-login__texto h1`) | Archivo | 800 | 84% | `clamp(42px, 4.75vw, 82px)` | 1.04 | -0.012em | normal |
| Título de seção (`.section-title`) | Inter | 700 | — | `--fs-xl` | 1.5 | — | normal |
| Título de painel (`.panel__head h2`) | Inter | 700 | — | `--fs-l` | 1.5 | — | normal |
| Subtítulo de página (`.page__sub`) | Inter | 400 | — | `--fs-m` | 1.5 | — | normal |
| Texto base | Inter | 400 | — | `--fs-m` | 1.5 | — | normal |
| Rótulo de campo (`.field label`) | Inter | 500 | — | `--fs-s` | 1.5 | — | normal |
| Dica de campo (`.hint`) | Inter | 400 | — | `--fs-xs` | 1.45 | — | normal |
| Botão (`.btn`) | Inter | 600 | — | `--fs-m` (pequeno: `--fs-s`) | — | — | normal |
| Aba (`.tab`) | Inter | 600 | — | `--fs-m` | — | — | normal |
| Opção do painel lateral (`.cop-lado__menu a`) | Inter | 500 (ativa: 600) | — | `--fs-m` | — | — | normal |
| Etiqueta (`.tag`) | Inter | 700 | — | 11px | 1.4 | 0.08em | MAIÚSCULAS |
| Sobretítulo (`.eyebrow`) | Inter | 600 | — | `--fs-xs` | — | 0.12em | MAIÚSCULAS |
| Número de destaque (`.stat__value`) | Inter | 600 | — | `clamp(30px, 3.2vw, 44px)` | 1.05 | -0.02em | — |
| Frase de apoio do login (`.gm-login__texto p`) | Inter | 300 | — | `clamp(14px, 1.15vw, 17px)` | 1.45 | — | normal |

Regra de escrita: frases com inicial maiúscula só na primeira palavra e em nomes próprios. Maiúsculas totais só onde a tabela indica.

## 5. Forma, espaço e camadas

| Token | Valor | Uso |
|---|---|---|
| `--radius-s` | `4px` | Botões, campos, capas, linhas de arquivo |
| `--radius-m` | `6px` | Chamados, avisos |
| `--radius-l` | `10px` | Painéis, cartões de número, janelas, tabela |
| `--radius-pill` | `999px` | Só nos filtros em pílula (`.chip`) |
| Raio da etiqueta | `2px` | Valor fixo |
| `--gutter` | `clamp(16px, 4vw, 60px)` | Margem lateral da página. No painel, com o painel lateral visível: `clamp(20px, 3vw, 44px)` |
| `--gap` | `8px` (até 599 px: `6px`) | Vão horizontal entre cartões |
| `--nav-h` | `68px` (até 899 px: `56px`) | Altura da barra do topo |
| `--lado-w` | `248px` (até 1199 px: `228px`) | Largura do painel lateral do painel do produtor |
| `--shadow-pop` | membros: `0 14px 44px rgba(0, 0, 0, 0.78)` · painel: `0 14px 44px rgba(20, 39, 36, 0.2)` | Menus suspensos, janelas, avisos rápidos |
| `--shadow-card` | `0 6px 20px rgba(0, 0, 0, 0.5)` | Prévia ampliada de cartão na área de membros |
| `--z-peek` | `40` | Prévia de cartão |
| `--z-nav` | `50` | Barra do topo (painel lateral: 49; véu do painel lateral: 48) |
| `--z-tabbar` | `55` | Barra inferior do celular (área de membros) |
| `--z-modal` | `100` | Janelas |
| `--z-toast` | `200` | Avisos rápidos |

## 6. Movimento

| Token | Valor | Uso |
|---|---|---|
| `--t-fast` | `150ms` | Cor, borda e fundo ao passar o mouse |
| `--t-med` | `260ms` | Cartões, chave, painel lateral do celular, aviso rápido |
| `--ease` | `cubic-bezier(0.2, 0.7, 0.2, 1)` | Curva padrão |
| Entrada de página | `fade-in 0.25s` | |
| Entrada de janela | `sheet-in 0.32s` com `--ease` (de `opacity: 0; transform: scale(0.94) translateY(16px)`) | |

Com `prefers-reduced-motion: reduce`, animações e transições são desligadas (ver o fim de `prototipo/assets/css/app.css`).

## 7. Pontos de quebra

Todos são `max-width`, salvo indicação. Use exatamente estes valores.

### Área de membros (`app.css`, `tokens.css`)

| Largura da tela | O que muda |
|---|---|
| até 1499 px | Cartões por linha (`--cols`): 5 (acima disso: 6) |
| até 1199 px | `--cols`: 4. Tela da aula: coluna lateral de 320 px |
| até 1023 px | Tela da aula e painéis lado a lado passam a uma coluna |
| até 899 px | `--cols`: 3. `--nav-h`: 56 px. Somem os links da barra do topo e aparece a barra inferior; o corpo ganha 62 px de respiro embaixo |
| até 599 px | `--cols`: 2. `--gap`: 6 px. Janela do curso ocupa a tela inteira |

### Painel do produtor (`admin.css`)

O painel lateral ocupa parte da largura; por isso os pontos de quebra do painel são diferentes.

| Largura da tela | O que muda |
|---|---|
| 1500 px ou mais | Cartões de tema por linha: 5. Cartões de "Meus cursos": 4 |
| até 1499 px | Cartões de tema por linha: 4 |
| até 1439 px | "Meus cursos": 3 por linha. Grupos de "Ferramentas de gestão" um embaixo do outro, com 2 colunas. Tabela de alunos mais justa e "Configurar plano" só com o ícone |
| até 1279 px | Cartões de número: 2 por linha. Painéis lado a lado e formulário da aula passam a uma coluna |
| até 1199 px | Painel lateral com 228 px. Cartões de tema por linha: 3. Logotipo com 36 px de altura |
| até 1099 px | "Meus cursos": 2 por linha. Aba Básico em uma coluna (título, descrição, autor e, por último, capa) |
| até 899 px | O painel lateral fica recolhido e abre pelo botão de menu. Conteúdo ocupa a largura toda. Logotipo com 32 px |
| até 599 px | "Meus cursos": 1 por linha. Somem "Visualizar como membro" e a etiqueta "Coprodutor" da barra. Linhas com vários botões quebram em duas |

### Tela de login (`login.css`)

| Largura da tela | Disposição |
|---|---|
| 1900 px ou mais | Três colunas; a arte para de crescer (798 px) |
| de 1200 a 1899 px | Três colunas: frase, arte, cartão |
| de 700 a 1199 px | Duas colunas: frase e arte à esquerda, cartão à direita |
| até 699 px | Uma coluna, centralizada: frase, arte, cartão |

Larguras de conferência usadas nas imagens deste pacote: **1440 px** (computador) e **390 px** (celular). Confira também 1280, 1024, 900 e 768 px.
