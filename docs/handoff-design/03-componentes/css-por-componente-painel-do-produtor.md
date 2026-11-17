# CSS por componente — painel do produtor

Gerado automaticamente a partir do CSS do protótipo (pasta `prototipo/assets/css/`). Cada regra aparece **inteira e sem alteração**, agrupada por componente. O comentário `/* valores: … */` depois de cada regra mostra o valor final de cada variável usada nela. Regras dentro de `@media` valem só na largura de tela indicada. Contexto das variáveis: painel do produtor (fundo branco, cores da GoMut). O painel usa **todos** os componentes da área de membros (arquivo anterior) e este arquivo traz só o que muda neles (cores) e as peças próprias do painel.

## Índice

- Base, foco e seleção de texto (11 regras)
- Utilitários e textos de apoio (1 regras)
- Botões (18 regras)
- Etiquetas (tags) e nota (6 regras)
- Barra do topo, busca e avisos do sininho (1 regras)
- Menus suspensos (2 regras)
- Avatar (2 regras)
- Avisos rápidos (toast) e aviso de confirmação (2 regras)
- Capas (2 regras)
- Janela do curso e janelas de diálogo (2 regras)
- Página, caminho, filtros e grade (4 regras)
- Painéis, linhas de configuração, listas e números (19 regras)
- Abas (1 regras)
- Formulários: campos, seleção e chave (6 regras)
- Jornada, semanas e lista de aulas (11 regras)
- Ao vivo: agenda, data e contagem (2 regras)
- Comunidade (3 regras)
- Certificado (1 regras)
- Conta, preferências e plano (2 regras)
- Painel: barra do topo e painel lateral (28 regras)
- Painel: Meus cursos e página do curso (aba Básico) (27 regras)
- Painel: Visão geral (11 regras)
- Painel: tabela, busca e listas (35 regras)
- Painel: módulos, aulas, e-book, vídeo e quiz (42 regras)
- Painel: janelas de edição e confirmação (4 regras)
- Outras peças (11 regras)

## Base, foco e seleção de texto

Arquivo de origem: `assets/css/admin.css`

```css
/* GoMut — área do coprodutor.

   A referência de design é a área de membros: mesmos componentes (barra no topo, abas, painéis,
   botões, etiquetas, listas), mesmos formatos, mesma tipografia e mesmo acabamento.
   A navegação fica num painel lateral, à esquerda (ver "painel lateral", mais abaixo).
   Aqui mudam só as CORES, que são as da GoMut (manual da marca v1.0, em assets/marca/),
   sobre fundo branco. Nenhuma peça nova de impacto: o painel é limpo, como a área de membros.

   Um tema só: fundo branco, textos em grafite e Verde GO nas ações.

   Este arquivo só é carregado em coprodutor.html: a área de membros não o usa. */
/* ================================================================== paleta */
html[data-area="coprodutor"] body, body[data-page="coprodutor"] {
  /* cores do manual da GoMut (página "Cores que sustentam a marca") */ --go: #04736b;
  /* Verde GO: ação e interfaces */ --go-hover: #058278;
  --go-press: #035a54;
  --grafite: #202221;
  /* base e títulos */ --ambar: #faad31;
  /* acentos e foco */ --creme: #fefcf5;
  /* área de respiro */ --verde-profundo: #142724;
  /* ambientes escuros */ --verde-palido: #e5f0ea;
  /* superfícies */ /* apoio: o pêssego das notas do manual (pendências) e o vermelho do "evitar" (excluir, erro) */ --pessego: #fcddbb;
  --perigo: #b93a2b;
  --perigo-hover: #c9463a;
  /* ---- cores da interface, sobre fundo branco ---- */ --c-bg: #ffffff;
  --c-surface-1: #ffffff;
  --c-surface-2: var(--verde-palido);
  --c-surface-3: #d6e6dd;
  --c-surface-4: #b4c7be;
  --c-text: var(--grafite);
  --c-text-2: #363a38;
  --c-text-3: #565d5a;
  --c-text-4: #6e7672;
  --c-line: rgba(32, 34, 33, 0.13);
  --c-line-strong: rgba(32, 34, 33, 0.34);
  --acento: var(--go);
  /* indicadores, ícones e links */ --nav-bg: #ffffff;
  --inv-bg: var(--grafite);
  /* botão e filtro "invertidos" */ --inv-fg: #ffffff;
  --inv-hover: #3b3f3d;
  --campo-bg: #ffffff;
  --campo-borda: #b3bfb9;
  --campo-borda-hover: #6f7c77;
  --contorno-bg: #ffffff;
  --contorno-hover: var(--verde-palido);
  --tag-bg: #ecebe6;
  --ok-bg: var(--verde-palido);
  --ok-fg: var(--go-press);
  --alerta-bg: var(--pessego);
  --alerta-fg: var(--grafite);
  --realce: rgba(4, 115, 107, 0.06);
  --toast-bg: var(--verde-profundo);
  --toast-fg: var(--creme);
  --toast-ico: var(--ambar);
  --veu: rgba(20, 39, 36, 0.55);
  --shadow-pop: 0 14px 44px rgba(20, 39, 36, 0.2);
  /* os componentes da área de membros leem estes nomes */ --c-red: var(--acento);
  --c-red-hover: var(--go-hover);
  --c-red-press: var(--go-press);
  --c-green: var(--acento);
  color-scheme: light;
}
/* valores: --acento = #04736b · --ambar = #faad31 · --creme = #fefcf5 · --go = #04736b · --go-hover = #058278 · --go-press = #035a54 · --grafite = #202221 · --pessego = #fcddbb · --verde-palido = #e5f0ea · --verde-profundo = #142724 */

html[data-area="coprodutor"] body {
  background: var(--c-bg);
  color: var(--c-text);
}
/* valores: --c-bg = #ffffff · --c-text = #202221 */

body[data-page="coprodutor"] :focus-visible {
  outline-color: var(--acento);
}
/* valores: --acento = #04736b */

body[data-page="coprodutor"] ::selection {
  background: var(--go);
  color: #fff;
}
/* valores: --go = #04736b */

/* A tela de login fica em assets/css/login.css: é a mesma nas duas áreas. */
/* ============================================================ painel lateral */
/* Menu do produtor, à esquerda, em todas as telas do painel. As opções usam o mesmo desenho do menu
   lateral de "Configurações" da área de membros (ícone e nome; fundo suave e traço na opção aberta),
   com as cores da GoMut. */
html[data-area="coprodutor"] body {
  --lado-w: 248px;
}

body[data-page="coprodutor"] .input {
  background: var(--campo-bg);
  border-color: var(--campo-borda);
  color: var(--c-text);
}
/* valores: --c-text = #202221 · --campo-bg = #ffffff · --campo-borda = #b3bfb9 */

body[data-page="coprodutor"] .input:hover {
  border-color: var(--campo-borda-hover);
}
/* valores: --campo-borda-hover = #6f7c77 */

body[data-page="coprodutor"] .input:focus {
  outline: 2px solid var(--acento);
  border-color: var(--acento);
}
/* valores: --acento = #04736b */

body[data-page="coprodutor"] .input::placeholder {
  color: var(--c-text-4);
}
/* valores: --c-text-4 = #6e7672 */

.input--sm {
  width: auto;
  height: 38px;
  font-size: var(--fs-s);
}
/* valores: --fs-s = 14px */

@media (max-width: 1199px) {
  html[data-area="coprodutor"] body {
    --lado-w: 228px;
  }
}

```

## Utilitários e textos de apoio

Arquivo de origem: `assets/css/admin.css`

```css
.hint {
  font-size: var(--fs-xs);
  line-height: 1.45;
  color: var(--c-text-3);
}
/* valores: --c-text-3 = #565d5a · --fs-xs = 12px */

```

## Botões

Arquivo de origem: `assets/css/admin.css`

```css
.btn--go {
  background: var(--go);
  color: #fff;
}
/* valores: --go = #04736b */

.btn--go:hover {
  background: var(--go-hover);
}
/* valores: --go-hover = #058278 */

.btn--go:active {
  background: var(--go-press);
}
/* valores: --go-press = #035a54 */

.btn--perigo {
  background: var(--perigo);
  color: #fff;
}
/* valores: --perigo = #b93a2b */

.btn--perigo:hover {
  background: var(--perigo-hover);
}
/* valores: --perigo-hover = #c9463a */

body[data-page="coprodutor"] .btn--light {
  background: var(--inv-bg);
  color: var(--inv-fg);
}
/* valores: --inv-bg = #202221 · --inv-fg = #ffffff */

body[data-page="coprodutor"] .btn--light:hover {
  background: var(--inv-hover);
}
/* valores: --inv-hover = #3b3f3d */

body[data-page="coprodutor"] .btn--dim {
  background: var(--c-surface-3);
  color: var(--c-text);
}
/* valores: --c-surface-3 = #d6e6dd · --c-text = #202221 */

body[data-page="coprodutor"] .btn--dim:hover {
  background: var(--c-surface-4);
}
/* valores: --c-surface-4 = #b4c7be */

body[data-page="coprodutor"] .btn--outline {
  color: var(--c-text);
  background: var(--contorno-bg);
}
/* valores: --c-text = #202221 · --contorno-bg = #ffffff */

body[data-page="coprodutor"] .btn--outline:hover {
  border-color: var(--c-text);
  background: var(--contorno-hover);
}
/* valores: --c-text = #202221 · --contorno-hover = #e5f0ea */

body[data-page="coprodutor"] .linkbtn:hover {
  color: var(--c-text);
}
/* valores: --c-text = #202221 */

.ibtn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-s);
  border: 1px solid var(--c-line-strong);
  background: var(--contorno-bg);
  color: var(--c-text);
}
/* valores: --c-line-strong = rgba(32, 34, 33, 0.34) · --c-text = #202221 · --contorno-bg = #ffffff · --radius-s = 4px */

.ibtn:hover:not([disabled]) {
  border-color: var(--c-text);
  background: var(--contorno-hover);
}
/* valores: --c-text = #202221 · --contorno-hover = #e5f0ea */

.ibtn[disabled] {
  opacity: 0.3;
  cursor: default;
}

.ibtn .ico {
  width: 16px;
  height: 16px;
}

.ibtn--up .ico {
  transform: rotate(180deg);
}

.cop .btn[disabled], .cop-dialog .btn[disabled] {
  opacity: 0.4;
  cursor: default;
}

```

## Etiquetas (tags) e nota

Arquivo de origem: `assets/css/admin.css`

```css
/* etiquetas: mesmo formato da área de membros; mudam só as cores */
body[data-page="coprodutor"] .tag {
  background: var(--tag-bg);
  color: var(--c-text-2);
}
/* valores: --c-text-2 = #363a38 · --tag-bg = #ecebe6 */

body[data-page="coprodutor"] .tag--go {
  background: var(--go);
  color: #fff;
}
/* valores: --go = #04736b */

body[data-page="coprodutor"] .tag--alerta {
  background: var(--alerta-bg);
  color: var(--alerta-fg);
}
/* valores: --alerta-bg = #fcddbb · --alerta-fg = #202221 */

body[data-page="coprodutor"] .tag--ok {
  background: var(--ok-bg);
  color: var(--ok-fg);
}
/* valores: --ok-bg = #e5f0ea · --ok-fg = #035a54 */

body[data-page="coprodutor"] .tag--line {
  background: none;
  color: var(--c-text-2);
}
/* valores: --c-text-2 = #363a38 */

.cop .tag .ico {
  width: 1em;
  height: 1em;
}

```

## Barra do topo, busca e avisos do sininho

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .caret {
  border-top-color: var(--c-text);
}
/* valores: --c-text = #202221 */

```

## Menus suspensos

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .dd__panel {
  background: var(--c-surface-1);
  border-color: var(--c-line);
  border-top: 2px solid var(--c-text);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) · --c-surface-1 = #ffffff · --c-text = #202221 */

body[data-page="coprodutor"] .dd__item:hover {
  background: var(--realce);
  color: var(--c-text);
}
/* valores: --c-text = #202221 · --realce = rgba(4, 115, 107, 0.06) */

```

## Avatar

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .avatar {
  background: linear-gradient(135deg, var(--go-hover), var(--go-press));
  color: #fff;
}
/* valores: --go-hover = #058278 · --go-press = #035a54 */

body[data-page="coprodutor"] .avatar--gray {
  background: var(--c-surface-4);
  color: var(--c-text);
}
/* valores: --c-surface-4 = #b4c7be · --c-text = #202221 */

```

## Avisos rápidos (toast) e aviso de confirmação

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .toast {
  background: var(--toast-bg);
  color: var(--toast-fg);
}
/* valores: --toast-bg = #142724 · --toast-fg = #fefcf5 */

body[data-page="coprodutor"] .toast .ico {
  color: var(--toast-ico);
}
/* valores: --toast-ico = #faad31 */

```

## Capas

Arquivo de origem: `assets/css/admin.css`

```css
/* Capas e certificado são prévias do que o aluno vê: mantêm as cores da área de membros. */
body[data-page="coprodutor"] .cover, body[data-page="coprodutor"] .cert {
  --c-red: #e50914;
}

body[data-page="coprodutor"] .cover {
  color: #fff;
}

```

## Janela do curso e janelas de diálogo

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .modal__backdrop {
  background: var(--veu);
}
/* valores: --veu = rgba(20, 39, 36, 0.55) */

body[data-page="coprodutor"] .sheet__close {
  background: var(--c-surface-2);
  color: var(--c-text);
}
/* valores: --c-surface-2 = #e5f0ea · --c-text = #202221 */

```

## Página, caminho, filtros e grade

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .chip:hover {
  border-color: var(--c-text);
  color: var(--c-text);
}
/* valores: --c-text = #202221 */

body[data-page="coprodutor"] .chip.is-on {
  background: var(--inv-bg);
  border-color: var(--inv-bg);
  color: var(--inv-fg);
}
/* valores: --inv-bg = #202221 · --inv-fg = #ffffff */

body[data-page="coprodutor"] .crumbs a:hover {
  color: var(--c-text);
}
/* valores: --c-text = #202221 */

body[data-page="coprodutor"] .empty h2 {
  color: var(--c-text);
}
/* valores: --c-text = #202221 */

```

## Painéis, linhas de configuração, listas e números

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .progressbar {
  background: var(--c-line);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) */

body[data-page="coprodutor"] .row:hover {
  background: var(--realce);
}
/* valores: --realce = rgba(4, 115, 107, 0.06) */

body[data-page="coprodutor"] .setrow .tag {
  font-size: 11px;
}

body[data-page="coprodutor"] a.setrow:hover strong {
  text-decoration: underline;
}

body[data-page="coprodutor"] .setrow > .ico {
  color: var(--c-text-4);
}
/* valores: --c-text-4 = #6e7672 */

/* ============================================================== visão geral */
/* Tudo aqui usa peças que já existem na área de membros: os números são os cartões de
   "Meu progresso" e as ferramentas são as linhas das listas de materiais (ícone, nome e frase). */
.cop .stats {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.cop a.stat {
  transition: border-color var(--t-fast);
}
/* valores: --t-fast = 150ms */

.cop a.stat:hover {
  border-color: var(--c-line-strong);
}
/* valores: --c-line-strong = rgba(32, 34, 33, 0.34) */

body[data-page="coprodutor"] .file--link:hover .file__chev {
  color: var(--c-text);
}
/* valores: --c-text = #202221 */

/* linhas de lista com ações (ordem, editar, excluir) */
.setrow .cop-item__acoes {
  flex: none;
}

.setrow .btn span {
  font-size: inherit;
  color: inherit;
}

.cop .file strong {
  overflow-wrap: anywhere;
}

.cop .file .btn + .btn {
  margin-left: 0;
}

.setrow .cop-exemplo {
  display: block;
  margin-top: 2px;
  font-size: var(--fs-xs);
  color: var(--c-text-4);
}
/* valores: --c-text-4 = #6e7672 · --fs-xs = 12px */

@media (max-width: 1279px) {
  .cop .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1279px) {
  .cop .split, .cop.page .mgrid {
    grid-template-columns: minmax(0, 1fr);
  }
}

/* linhas com vários botões de ação: se não couberem ao lado do texto, os botões descem para a linha de baixo */
@media (max-width: 599px) {
  .cop .setrow:has(> .cop-item__acoes) {
    flex-wrap: wrap;
    gap: 10px 16px;
  }
}

@media (max-width: 599px) {
  .cop .setrow:has(> .cop-item__acoes) > div:first-child {
    flex: 1 1 150px;
  }
}

@media (max-width: 599px) {
  .cop .setrow > .cop-item__acoes {
    margin-left: auto;
  }
}

```

## Abas

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .tab:hover, body[data-page="coprodutor"] .tab.is-on {
  color: var(--c-text);
}
/* valores: --c-text = #202221 */

```

## Formulários: campos, seleção e chave

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .select select {
  background: var(--campo-bg);
  border-color: var(--campo-borda);
  color: var(--c-text);
}
/* valores: --c-text = #202221 · --campo-bg = #ffffff · --campo-borda = #b3bfb9 */

body[data-page="coprodutor"] .select::after {
  border-top-color: var(--c-text);
}
/* valores: --c-text = #202221 */

/* chave ligada: trilho em Verde GO e ponto âmbar, como no manual da marca */
body[data-page="coprodutor"] .switch[aria-checked="true"] {
  background: var(--go);
}
/* valores: --go = #04736b */

body[data-page="coprodutor"] .switch[aria-checked="true"]::after {
  background: var(--ambar);
}
/* valores: --ambar = #faad31 */

.field .opt {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  font-size: var(--fs-s);
  font-weight: 400;
  color: var(--c-text);
  cursor: pointer;
}
/* valores: --c-text = #202221 · --fs-s = 14px */

@media (max-width: 599px) {
  .form--2 {
    grid-template-columns: minmax(0, 1fr);
  }
}

```

## Jornada, semanas e lista de aulas

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .week summary:hover, body[data-page="coprodutor"] .ticket summary:hover {
  background: var(--realce);
}
/* valores: --realce = rgba(4, 115, 107, 0.06) */

body[data-page="coprodutor"] .eps {
  border-top-color: var(--c-line);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) */

body[data-page="coprodutor"] .ep {
  border-bottom-color: var(--c-line);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) */

body[data-page="coprodutor"] .ep:hover {
  background: var(--realce);
}
/* valores: --realce = rgba(4, 115, 107, 0.06) */

body[data-page="coprodutor"] .ep__n {
  color: var(--c-text-3);
}
/* valores: --c-text-3 = #565d5a */

/* módulos e aulas */
.cop .week summary {
  grid-template-columns: 52px minmax(0, 1fr) auto;
}

.eps--compact .cop-aula {
  grid-template-columns: 30px minmax(0, 1fr) auto;
}

@media (max-width: 1279px) {
  .cop .aside-stack {
    position: static;
  }
}

@media (max-width: 599px) {
  .cop .week summary {
    grid-template-columns: 40px minmax(0, 1fr) auto;
    gap: 12px;
  }
}

@media (max-width: 599px) {
  .cop .week__n {
    width: 40px;
    height: 40px;
    font-size: 18px;
  }
}

@media (max-width: 599px) {
  .eps--compact .cop-aula {
    grid-template-columns: 24px minmax(0, 1fr);
  }
}

```

## Ao vivo: agenda, data e contagem

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .datebox.is-today {
  background: var(--go);
  color: #fff;
}
/* valores: --go = #04736b */

.agenda__item .cop-item__meta {
  margin-top: 6px;
  font-size: var(--fs-xs);
  color: var(--c-text-4);
}
/* valores: --c-text-4 = #6e7672 · --fs-xs = 12px */

```

## Comunidade

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .post__foot button:hover, body[data-page="coprodutor"] .post__foot button.is-on, body[data-page="coprodutor"] .post__foot button[aria-expanded="true"] {
  color: var(--c-text);
}
/* valores: --c-text = #202221 */

.thread .cop-mod__bar {
  margin-bottom: 0;
}

.post.is-oculta {
  opacity: 0.55;
}

```

## Certificado

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .cert {
  border: 1px solid var(--c-line);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) */

```

## Conta, preferências e plano

Arquivo de origem: `assets/css/admin.css`

```css
body[data-page="coprodutor"] .settings__nav button:hover {
  color: var(--c-text);
  background: var(--realce);
}
/* valores: --c-text = #202221 · --realce = rgba(4, 115, 107, 0.06) */

body[data-page="coprodutor"] .settings__nav button.is-on {
  color: var(--c-text);
}
/* valores: --c-text = #202221 */

```

## Painel: barra do topo e painel lateral

Arquivo de origem: `assets/css/admin.css`

```css
/* ================================================================== logotipo */
/* Arte original da GoMut, sem sombra e sem inversão, sempre sobre fundo claro (manual da marca). */
.cop-brand {
  display: flex;
  flex: none;
  align-items: center;
}

.cop-brand img {
  display: block;
  width: auto;
  height: 40px;
}

.cop-lado {
  position: fixed;
  top: var(--nav-h);
  bottom: 0;
  left: 0;
  z-index: calc(var(--z-nav) - 1);
  width: var(--lado-w);
  padding: 18px 12px 24px;
  overflow-y: auto;
  background: var(--c-bg);
  border-right: 1px solid var(--c-line);
  scrollbar-width: thin;
}
/* valores: --c-bg = #ffffff · --c-line = rgba(32, 34, 33, 0.13) · --lado-w = 248px · --nav-h = 68px · --z-nav = 50 */

.cop-lado__menu {
  display: grid;
  gap: 2px;
}

.cop-lado__menu a {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: var(--radius-s);
  font-size: var(--fs-m);
  font-weight: 500;
  white-space: nowrap;
  color: var(--c-text-3);
  transition: color var(--t-fast), background-color var(--t-fast);
}
/* valores: --c-text-3 = #565d5a · --fs-m = 16px · --radius-s = 4px · --t-fast = 150ms */

.cop-lado__menu a:hover {
  color: var(--c-text);
  background: var(--realce);
}
/* valores: --c-text = #202221 · --realce = rgba(4, 115, 107, 0.06) */

.cop-lado__menu a.is-on {
  color: var(--c-text);
  font-weight: 600;
  background: var(--c-surface-2);
  box-shadow: inset 3px 0 0 var(--acento);
}
/* valores: --acento = #04736b · --c-surface-2 = #e5f0ea · --c-text = #202221 */

.cop-lado__menu .ico {
  width: 20px;
  height: 20px;
}

.cop-lado__menu a.is-on .ico {
  color: var(--acento);
}
/* valores: --acento = #04736b */

/* o botão de menu e o véu só existem no celular (ver "responsivo") */
.cop-nav__menu, .cop-lado__veu {
  display: none;
}

/* o conteúdo começa depois do painel, com margens um pouco menores e um cartão a menos por linha */
@media (min-width: 900px) {
  .cop-lado ~ .page {
    margin-left: var(--lado-w);
    --gutter: clamp(20px, 3vw, 44px);
    --cols: 5;
  }
}
/* valores: --lado-w = 248px */

/* na barra do topo, o logotipo alinha com as opções do menu e a conta alinha com o conteúdo */
@media (min-width: 900px) {
  body[data-page="coprodutor"] .cop-nav {
    padding-left: 26px;
    padding-right: clamp(20px, 3vw, 44px);
  }
}

@media (min-width: 900px) and (max-width: 1499px) {
  .cop-lado ~ .page {
    --cols: 4;
  }
}

@media (min-width: 900px) and (max-width: 1199px) {
  .cop-lado ~ .page {
    --cols: 3;
  }
}

/* ============================ componentes da área de membros, nas cores da GoMut */
body[data-page="coprodutor"] .cop-nav {
  background: var(--nav-bg);
  border-bottom: 1px solid var(--c-line);
  gap: clamp(12px, 2vw, 28px);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) · --nav-bg = #ffffff */

body[data-page="coprodutor"] .cop-nav__tag {
  margin-left: calc(clamp(12px, 2vw, 28px) * -1 + 10px);
}

@media (max-width: 1199px) {
  .cop-brand img {
    height: 36px;
  }
}

/* celular e tablet em pé: o painel lateral fica recolhido e abre pelo botão de menu da barra do topo */
@media (max-width: 899px) {
  body[data-page="coprodutor"] .cop-nav {
    gap: 10px;
  }
}

@media (max-width: 899px) {
  .cop-nav__menu {
    display: grid;
    place-items: center;
    flex: none;
    width: 40px;
    height: 40px;
    margin-left: -8px;
    border-radius: var(--radius-s);
    color: var(--c-text);
  }
}
/* valores: --c-text = #202221 · --radius-s = 4px */

@media (max-width: 899px) {
  .cop-nav__menu:hover {
    background: var(--realce);
  }
}
/* valores: --realce = rgba(4, 115, 107, 0.06) */

@media (max-width: 899px) {
  .cop-nav__menu .ico {
    width: 24px;
    height: 24px;
  }
}

@media (max-width: 899px) {
  .cop-lado {
    width: min(300px, 84vw);
    transform: translateX(-100%);
    visibility: hidden;
    transition: transform var(--t-med) var(--ease), visibility 0s linear var(--t-med);
  }
}
/* valores: --ease = cubic-bezier(0.2, 0.7, 0.2, 1) · --t-med = 260ms */

@media (max-width: 899px) {
  .cop-lado.is-aberto {
    transform: none;
    visibility: visible;
    box-shadow: var(--shadow-pop);
    transition: transform var(--t-med) var(--ease);
  }
}
/* valores: --ease = cubic-bezier(0.2, 0.7, 0.2, 1) · --shadow-pop = 0 14px 44px rgba(20, 39, 36, 0.2) · --t-med = 260ms */

@media (max-width: 899px) {
  .cop-lado.is-aberto + .cop-lado__veu {
    display: block;
    position: fixed;
    inset: var(--nav-h) 0 0 0;
    z-index: calc(var(--z-nav) - 2);
    background: var(--veu);
  }
}
/* valores: --nav-h = 68px · --veu = rgba(20, 39, 36, 0.55) · --z-nav = 50 */

@media (max-width: 899px) {
  .cop-nav__aluno span {
    display: none;
  }
}

@media (max-width: 899px) {
  .cop-nav__aluno {
    padding: 0 10px;
  }
}

@media (max-width: 899px) {
  .cop-brand img {
    height: 32px;
  }
}

/* na barra do celular ficam o menu, a marca e a conta; "Visualizar como membro" está no menu da conta */
@media (max-width: 599px) {
  .cop-nav__aluno, .cop-nav .cop-nav__tag {
    display: none;
  }
}

```

## Painel: Meus cursos e página do curso (aba Básico)

Arquivo de origem: `assets/css/admin.css`

```css
/* ============================================================== meus cursos */
/* Primeira tela do painel: os cursos em cartões, com a capa que o aluno vê (mesmo cartão da lista de
   temas, em tamanho maior: quatro por linha). */
.cop-cursos {
  --cols: 4;
}

.cop-curso__tags {
  display: flex;
  margin: 2px 0 6px;
}

.cop-cursos .gcard__meta strong {
  font-size: var(--fs-m);
  color: var(--c-text);
}
/* valores: --c-text = #202221 · --fs-m = 16px */

/* ========================================================== página do curso */
/* Aba "Básico": a capa à esquerda e, à direita, o título, a descrição e o autor do curso.
   Embaixo, "Cancelar" e "Salvar alterações". */
.cop-basico__grade {
  display: grid;
  grid-template-columns: minmax(240px, 36%) minmax(0, 1fr);
  gap: clamp(20px, 3vw, 40px);
  align-items: start;
}

/* caixa da capa: clicar nela abre a escolha do arquivo */
.cop-capa {
  display: block;
  padding: 12px;
  border: 1px dashed var(--c-line-strong);
  border-radius: var(--radius-l);
  cursor: pointer;
  transition: border-color var(--t-fast), background-color var(--t-fast);
}
/* valores: --c-line-strong = rgba(32, 34, 33, 0.34) · --radius-l = 10px · --t-fast = 150ms */

.cop-capa:hover {
  border-color: var(--acento);
  background: var(--realce);
}
/* valores: --acento = #04736b · --realce = rgba(4, 115, 107, 0.06) */

.cop-basico input[type="file"]:focus-visible + .cop-capa {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}
/* valores: --acento = #04736b */

.cop-capa img {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: var(--radius-s);
}
/* valores: --radius-s = 4px */

.cop-capa__vazia {
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 8px;
  aspect-ratio: 16 / 9;
  border-radius: var(--radius-s);
  background: var(--c-surface-2);
  font-size: var(--fs-s);
  font-weight: 600;
  color: var(--c-text-2);
}
/* valores: --c-surface-2 = #e5f0ea · --c-text-2 = #363a38 · --fs-s = 14px · --radius-s = 4px */

.cop-capa__vazia .ico {
  width: 26px;
  height: 26px;
  color: var(--acento);
}
/* valores: --acento = #04736b */

.cop-capa__acoes {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px 22px;
}

.cop-capa__acoes .linkbtn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 4px 0;
  cursor: pointer;
}

.cop-capa__acoes .ico {
  width: 16px;
  height: 16px;
}

/* capa enviada, nos cartões de "Meus cursos" */
.cop-capa-img {
  background: var(--c-surface-2);
}
/* valores: --c-surface-2 = #e5f0ea */

.cop-capa-img img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* embaixo do campo: a explicação à esquerda e o contador de caracteres à direita */
.cop-campo-pe {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 14px;
}

.cop-conta {
  flex: none;
  font-size: var(--fs-xs);
  color: var(--c-text-4);
  font-variant-numeric: tabular-nums;
}
/* valores: --c-text-4 = #6e7672 · --fs-xs = 12px */

.cop-basico__pe {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  margin-top: clamp(20px, 2.6vw, 30px);
  padding-top: 18px;
  border-top: 1px solid var(--c-line);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) */

.cop-resumo-topo {
  margin-top: 0;
}

.cop-resumo-topo .toolbar__count {
  max-width: 62ch;
  font-size: var(--fs-m);
}
/* valores: --fs-m = 16px */

/* --------------------------------------------------------------- responsivo */
/* O painel lateral ocupa parte da largura da tela: os pontos de quebra abaixo consideram o espaço
   que sobra para o conteúdo, e não a largura inteira. */
@media (max-width: 1439px) {
  .cop-cursos {
    --cols: 3;
  }
}

@media (max-width: 1099px) {
  .cop-cursos {
    --cols: 2;
  }
}

/* aba Básico em uma coluna só, na ordem: título, descrição, autor e, por último, a capa */
@media (max-width: 1099px) {
  .cop-basico__grade {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 1099px) {
  .cop-basico__grade > .field:first-child {
    order: 2;
  }
}

@media (max-width: 1099px) {
  .cop-capa {
    max-width: 440px;
  }
}

@media (max-width: 1099px) {
  .cop-capa__acoes {
    justify-content: flex-start;
  }
}

@media (max-width: 599px) {
  .cop-cursos {
    --cols: 1;
  }
}

```

## Painel: Visão geral

Arquivo de origem: `assets/css/admin.css`

```css
/* título de seção com frase de apoio */
.cop-sec {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 6px 16px;
  margin: clamp(32px, 4vw, 52px) 0 14px;
}

.cop-sec .section-title {
  margin: 0;
}

.cop-sec p {
  font-size: var(--fs-s);
  color: var(--c-text-3);
}
/* valores: --c-text-3 = #565d5a · --fs-s = 14px */

/* ferramentas de gestão: três grupos lado a lado, cada um com a sua lista */
.cop-grupos {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px 14px;
}

.cop-grupo {
  margin-bottom: 10px;
}

.cop-grupos .file .tag {
  flex: none;
}

.cop-grupos .file strong, .cop-grupos .file strong + span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cop-grupos .file__ico .ico {
  color: var(--acento);
}
/* valores: --acento = #04736b */

/* os grupos passam a ficar um embaixo do outro, com as ferramentas em duas colunas */
@media (max-width: 1439px) {
  .cop-grupos {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 1439px) {
  .cop-grupos .files {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 899px) {
  .cop-grupos .files {
    grid-template-columns: minmax(0, 1fr);
  }
}

```

## Painel: tabela, busca e listas

Arquivo de origem: `assets/css/admin.css`

```css
.cop-ordem {
  padding: 8px 0;
}

.cop-ordem + .select, #tr-temas > .select {
  margin-top: 10px;
}

.cop-checks {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
  max-height: 250px;
  overflow: auto;
  padding: 14px;
  border: 1px solid var(--c-line);
  border-radius: var(--radius-s);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) · --radius-s = 4px */

/* listas e tabela */
.cop-item {
  grid-template-columns: auto minmax(0, 1fr) auto;
}

.cop-num {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid var(--c-surface-4);
  font-family: var(--font-display);
  font-weight: 800;
  color: var(--c-text-3);
}
/* valores: --c-surface-4 = #b4c7be · --c-text-3 = #565d5a · --font-display = "Archivo", "Arial Narrow", "Helvetica Neue", Arial, sans-serif */

.cop-row .cover {
  border-radius: var(--radius-s);
}
/* valores: --radius-s = 4px */

.cop-row strong {
  white-space: normal;
}

.cop-sw {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-right: 6px;
  font-size: var(--fs-s);
  color: var(--c-text-3);
}
/* valores: --c-text-3 = #565d5a · --fs-s = 14px */

.cop-busca {
  position: relative;
  flex: 1;
  max-width: 340px;
}

.cop-busca .ico {
  position: absolute;
  left: 12px;
  top: 50%;
  width: 18px;
  height: 18px;
  margin-top: -9px;
  color: var(--c-text-4);
  pointer-events: none;
}
/* valores: --c-text-4 = #6e7672 */

.cop-busca .input {
  width: 100%;
  padding-left: 38px;
}

.cop-tabela {
  position: relative;
  overflow-x: auto;
  border: 1px solid var(--c-line);
  border-radius: var(--radius-l);
  background: var(--c-surface-1);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) · --c-surface-1 = #ffffff · --radius-l = 10px */

.cop-tabela table {
  width: 100%;
  min-width: 900px;
  border-collapse: collapse;
  font-size: var(--fs-s);
}
/* valores: --fs-s = 14px */

.cop-tabela th {
  padding: 12px 16px;
  text-align: left;
  font-size: var(--fs-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
  color: var(--c-text-3);
  background: var(--c-surface-2);
  border-bottom: 1px solid var(--c-line);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) · --c-surface-2 = #e5f0ea · --c-text-3 = #565d5a · --fs-xs = 12px */

.cop-tabela td {
  padding: 14px 16px;
  vertical-align: middle;
  border-bottom: 1px solid var(--c-line);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) */

.cop-tabela tr:last-child td {
  border-bottom: 0;
}

.cop-tabela tbody tr:hover td {
  background: var(--realce);
}
/* valores: --realce = rgba(4, 115, 107, 0.06) */

.cop-tabela .cop-item__acoes {
  flex-wrap: nowrap;
  justify-content: flex-end;
}

.cop-tabela .btn {
  white-space: nowrap;
}

.cop-tabela td strong {
  display: block;
  font-weight: 600;
}

.cop-tabela td strong + span {
  font-size: var(--fs-xs);
  color: var(--c-text-3);
}
/* valores: --c-text-3 = #565d5a · --fs-xs = 12px */

.cop-quem {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cop-quem .avatar {
  flex: none;
}

.cop-vazia {
  padding: 28px 16px;
  text-align: center;
  color: var(--c-text-3);
}
/* valores: --c-text-3 = #565d5a */

.cop-prog {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-variant-numeric: tabular-nums;
}

.cop-prog .progressbar {
  width: 90px;
}

/* tabela de alunos: colunas mais justas e "Configurar plano" só com o ícone, para as ações caberem sem rolar */
@media (max-width: 1439px) {
  .cop-tabela table {
    min-width: 760px;
  }
}

@media (max-width: 1439px) {
  .cop-tabela th, .cop-tabela td {
    padding-left: 12px;
    padding-right: 12px;
  }
}

@media (max-width: 1439px) {
  .cop-tabela [data-cop="plano"] span {
    display: none;
  }
}

@media (max-width: 1439px) {
  .cop-tabela [data-cop="plano"] {
    padding: 0 10px;
  }
}

@media (max-width: 1439px) {
  .cop-prog .progressbar {
    width: 72px;
  }
}

@media (max-width: 599px) {
  .cop-item, .cop-row {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 599px) {
  .cop-item .cop-num, .cop-row .cover {
    display: none;
  }
}

@media (max-width: 599px) {
  .cop-checks {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 599px) {
  .cop-busca {
    max-width: none;
    flex-basis: 100%;
  }
}

```

## Painel: módulos, aulas, e-book, vídeo e quiz

Arquivo de origem: `assets/css/admin.css`

```css
.cop-lib {
  margin-top: 8px;
}

.cop-mod {
  padding: 0 18px 16px;
}

.cop-mod .eps {
  margin: 0 0 12px;
}

.cop-mod__bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.cop-aula .ep__title:hover {
  text-decoration: underline;
}

.cop-aula__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.cop-aula__acoes, .cop-item__acoes {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.cop-novo {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.cop-novo--mod {
  margin-top: 14px;
  max-width: 720px;
}

.cop-vazio {
  margin-bottom: 12px;
}

/* formulários */
/* escolha de arquivo (imagem de capa): mesmo campo dos outros, com o botão do navegador em contorno */
.cop-arquivo {
  height: auto;
  padding: 9px 10px;
  font-size: var(--fs-s);
  color: var(--c-text-3);
}
/* valores: --c-text-3 = #565d5a · --fs-s = 14px */

.cop-arquivo::file-selector-button {
  margin-right: 12px;
  padding: 7px 12px;
  border: 1px solid var(--c-line-strong);
  border-radius: var(--radius-s);
  background: var(--contorno-bg);
  color: var(--c-text);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
/* valores: --c-line-strong = rgba(32, 34, 33, 0.34) · --c-text = #202221 · --contorno-bg = #ffffff · --radius-s = 4px */

.cop-arquivo::file-selector-button:hover {
  border-color: var(--c-text);
  background: var(--contorno-hover);
}
/* valores: --c-text = #202221 · --contorno-hover = #e5f0ea */

.cop-q__e {
  width: 100%;
}

.cop-resumo {
  margin: 0 0 22px;
}

.cop-nota {
  margin: -6px 0 16px;
}

.form--3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.opts {
  display: grid;
  gap: 10px;
}

.opt input[type="radio"], .opt input[type="checkbox"], .cop-q__op input[type="radio"] {
  flex: none;
  width: 18px;
  height: 18px;
  margin: 0;
  accent-color: var(--acento);
}
/* valores: --acento = #04736b */

.opt .input--sm {
  max-width: 170px;
}

.cop-msg {
  font-size: var(--fs-xs);
  font-weight: 600;
}
/* valores: --fs-xs = 12px */

.cop-msg:empty {
  display: none;
}

.cop-msg.is-ok {
  color: var(--acento);
}
/* valores: --acento = #04736b */

.cop-msg.is-erro {
  color: var(--perigo);
}
/* valores: --perigo = #b93a2b */

.cop-col {
  display: grid;
  gap: 14px;
  min-width: 0;
}

/* os painéis encolhem com a tela, e um nome de arquivo comprido quebra de linha em vez de alargar a página */
.cop-col > * {
  min-width: 0;
}

.cop-aulaform .aside-stack {
  top: calc(var(--nav-h) + 20px);
}
/* valores: --nav-h = 68px */

.cop-aulaform .btn--block + .btn--block {
  margin-top: -8px;
}

.cop-video {
  position: relative;
  aspect-ratio: 16 / 9;
  border-radius: var(--radius-s);
  overflow: hidden;
  background: #0d1a18;
}
/* valores: --radius-s = 4px */

.cop-video iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}

.cop-video__vazio {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 8px;
  padding: 16px;
  text-align: center;
  font-size: var(--fs-s);
  color: rgba(254, 252, 245, 0.8);
}
/* valores: --fs-s = 14px */

.cop-video__vazio .ico {
  width: 34px;
  height: 34px;
}

.cop-envio {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  border: 1px dashed var(--c-line-strong);
  border-radius: var(--radius-s);
  font-size: var(--fs-s);
  color: var(--c-text-3);
}
/* valores: --c-line-strong = rgba(32, 34, 33, 0.34) · --c-text-3 = #565d5a · --fs-s = 14px · --radius-s = 4px */

.cop-up {
  transform: rotate(180deg);
}

.cop-q {
  display: grid;
  gap: 8px;
  padding: 14px;
  margin-bottom: 10px;
  border: 1px solid var(--c-line);
  border-radius: var(--radius-m);
  background: var(--c-surface-2);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) · --c-surface-2 = #e5f0ea · --radius-m = 6px */

.cop-q__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: var(--fs-s);
}
/* valores: --fs-s = 14px */

.cop-q__op {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
}

.cop-q__op .input--sm {
  width: 100%;
}

@media (max-width: 1279px) {
  .cop-aulaform .aside-stack {
    order: 2;
  }
}

@media (max-width: 899px) {
  .form--3 {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 599px) {
  .cop-aula__acoes {
    grid-column: 2;
  }
}

@media (max-width: 599px) {
  .cop-novo {
    grid-template-columns: minmax(0, 1fr);
  }
}

```

## Painel: janelas de edição e confirmação

Arquivo de origem: `assets/css/admin.css`

```css
/* janelas de edição e de confirmação */
.cop-dialog {
  padding-top: 28px;
}

.cop-dialog h2 {
  margin: 0 44px 18px 0;
  font-family: var(--font-display);
  font-weight: 800;
  font-stretch: 82%;
  font-size: clamp(22px, 2.4vw, 30px);
  line-height: 1.1;
}
/* valores: --font-display = "Archivo", "Arial Narrow", "Helvetica Neue", Arial, sans-serif */

.cop-dialog__txt {
  line-height: 1.55;
  color: var(--c-text-2);
}
/* valores: --c-text-2 = #363a38 */

.cop-dialog__foot {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 6px;
}

```

## Outras peças

Arquivo de origem: `assets/css/admin.css`

```css
/* a barra, o rodapé e a barra inferior do aluno não aparecem aqui */
html[data-area="coprodutor"] #nav, html[data-area="coprodutor"] #footer, html[data-area="coprodutor"] #tabbar {
  display: none;
}

/* ------------------------------------------------ peças próprias desta área */
.cop-acoes {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.cop-tabs {
  margin-bottom: clamp(18px, 2.4vw, 30px);
}

.cop-foot {
  margin-top: 56px;
  padding-top: 18px;
  border-top: 1px solid var(--c-line);
  font-size: 13px;
  color: var(--c-text-4);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) · --c-text-4 = #6e7672 */

.cop-estreito {
  display: grid;
  gap: 14px;
  max-width: 860px;
}

.cop-coluna {
  max-width: 860px;
}

.cop-mt {
  margin-top: 14px;
}

.cop-perigo {
  margin-top: 28px;
  padding-top: 18px;
  border-top: 1px solid var(--c-line);
}
/* valores: --c-line = rgba(32, 34, 33, 0.13) */

.cop-cert {
  max-width: 640px;
  box-shadow: var(--shadow-pop);
}
/* valores: --shadow-pop = 0 14px 44px rgba(20, 39, 36, 0.2) */

.cop-resposta {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.cop-resposta__foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

```
