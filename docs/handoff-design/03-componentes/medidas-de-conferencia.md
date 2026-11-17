# Medidas de conferência

Valores **medidos no navegador** (estilo calculado), no protótipo. Servem para conferir a implementação com as ferramentas do navegador: selecione o mesmo elemento, na mesma tela e na mesma largura, e compare.

- Largura da janela: **1440 px** (altura 900 px). Para o celular, confira pelas imagens de `telas/…/celular-390/` e pelos pontos de quebra de `02-tokens/tokens.md`.
- As cores aparecem como o navegador as calcula (`rgb` / `rgba`). `rgba(0, 0, 0, 0)` significa sem fundo.
- Largura e altura dependem do conteúdo e da largura da tela; os demais valores não.
- Gerado automaticamente. Em caso de diferença com o CSS do protótipo, vale o CSS.

## Painel do produtor (1440 px)

### Meus cursos

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Barra do topo<br>`.cop-nav` | 1440 × 68 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | bottom 1px solid rgba(32, 34, 33, 0.13) | `0px` | `0px 43.2px 0px 26px` |
| Logotipo da GoMut<br>`.cop-brand img` | 145 × 40 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Etiqueta "Coprodutor"<br>`.cop-nav__tag` | 103 × 21 | Inter 700 11px/15.4px espaç. 0.88px uppercase | `rgb(255, 255, 255)` | `rgb(4, 115, 107)` | sem | `2px` | `3px 8px` |
| Botão "Visualizar como membro" (pequeno, contorno)<br>`.cop-nav__aluno` | 226 × 34 | Inter 600 14px/21px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgba(32, 34, 33, 0.34) | `4px` | `0px 14px` |
| Avatar da conta<br>`.nav__profile .avatar` | 0 × 0 | Inter 700 12px/18px espaç. 0.24px | `rgb(255, 255, 255)` | `degradê` | sem | `4px` | `0px` |
| Painel lateral<br>`.cop-lado` | 248 × 745 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | right 1px solid rgba(32, 34, 33, 0.13) | `0px` | `18px 12px 24px` |
| Opção do painel lateral<br>`.cop-lado__menu a:not(.is-on)` | 223 × 46 | Inter 500 16px/24px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `4px` | `11px 14px` |
| Opção ativa do painel lateral<br>`.cop-lado__menu a.is-on` | 223 × 46 | Inter 600 16px/24px | `rgb(32, 34, 33)` | `rgb(229, 240, 234)` · sombra rgb(4, 115, 107) 3px 0px 0px 0px inset | sem | `4px` | `11px 14px` |
| Ícone da opção<br>`.cop-lado__menu a .ico` | 20 × 20 | Inter 500 16px/24px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Área da página (espaço interno)<br>`.page` | 1192 × 699 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `108px 43.2px 72px` |
| Título da página<br>`.page__title` | 372 × 49 | Archivo 800 48px/48.96px largura 82% espaç. -0.576px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Frase abaixo do título<br>`.page__sub` | 372 × 24 | Inter 400 16px/24px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Botão principal "Criar curso"<br>`.page__head .btn--go` | 161 × 42 | Inter 600 16px/24px | `rgb(255, 255, 255)` | `rgb(4, 115, 107)` | sem | `4px` | `0px 22px` |
| Campo de busca<br>`.cop-busca .input` | 340 × 38 | Inter 400 14px/21px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgb(179, 191, 185) | `4px` | `0px 14px 0px 38px` |
| Contagem "1 curso"<br>`.toolbar__count` | 47 × 21 | Inter 400 14px/21px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Capa do cartão do curso<br>`.cop-cursos .cover` | 270 × 152 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `degradê` | sem | `4px` | `0px` |
| Etiqueta "Publicado"<br>`.cop-cursos .tag` | 88 × 21 | Inter 700 11px/15.4px espaç. 0.88px uppercase | `rgb(3, 90, 84)` | `rgb(229, 240, 234)` | sem | `2px` | `3px 8px` |
| Nome do curso no cartão<br>`.cop-cursos .gcard__meta strong` | 266 × 22 | Inter 600 16px/22.4px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Texto "N aulas · N alunos"<br>`.cop-cursos .gcard__meta` | 270 × 78 | Inter 400 13px/18.2px | `rgb(110, 118, 114)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `8px 2px 0px` |

### Página do curso, aba Básico

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Caminho "‹ Meus cursos"<br>`.crumbs a` | 110 × 21 | Inter 500 14px/21px | `rgb(54, 58, 56)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Linha "Por autor"<br>`.page__sub` | 338 × 24 | Inter 400 16px/24px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Botão pequeno de contorno ("Visualizar curso")<br>`.page__head .btn--outline` | 167 × 34 | Inter 600 14px/21px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgba(32, 34, 33, 0.34) | `4px` | `0px 14px` |
| Faixa de abas<br>`.cop-tabs` | 1106 × 53 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | bottom 1px solid rgba(32, 34, 33, 0.13) | `0px` | `0px` |
| Aba ativa<br>`.tab.is-on` | 52 × 52 | Inter 600 16px/24px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `14px 0px` |
| Aba<br>`.tab:not(.is-on)` | 87 × 52 | Inter 600 16px/24px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `14px 0px` |
| Painel<br>`.panel` | 1106 × 573 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgba(32, 34, 33, 0.13) | `10px` | `26px` |
| Caixa da capa (tracejada)<br>`.cop-capa` | 379 × 224 | Inter 500 14px/21px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | 1px dashed rgba(32, 34, 33, 0.34) | `10px` | `12px` |
| Capa dentro da caixa<br>`.cop-capa .cover` | 353 × 198 | Inter 500 14px/21px | `rgb(255, 255, 255)` | `degradê` | sem | `4px` | `0px` |
| Ação "Enviar imagem"<br>`.cop-capa__acoes .linkbtn` | 122 × 29 | Inter 500 14px/21px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `4px 0px` |
| Rótulo de campo<br>`.field > label[for="f-nome"]` | 633 × 21 | Inter 500 14px/21px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Campo de texto<br>`#f-nome` | 633 × 48 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgb(179, 191, 185) | `4px` | `0px 14px` |
| Área de texto<br>`#f-desc` | 633 × 146 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgb(179, 191, 185) | `4px` | `12px 14px` |
| Seleção<br>`#f-tutor` | 633 × 46 | Inter 500 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgb(179, 191, 185) | `4px` | `10px 40px 10px 14px` |
| Dica de campo<br>`.cop-campo-pe .hint` | 230 × 17 | Inter 400 12px/17.4px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Contador de caracteres<br>`.cop-conta` | 42 × 18 | Inter 400 12px/18px | `rgb(110, 118, 114)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Rodapé do formulário<br>`.cop-basico__pe` | 1052 × 61 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | top 1px solid rgba(32, 34, 33, 0.13) | `0px` | `18px 0px 0px` |
| Botão "Cancelar"<br>`.cop-basico__pe .btn--outline` | 115 × 42 | Inter 600 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgba(32, 34, 33, 0.34) | `4px` | `0px 22px` |
| Botão "Salvar alterações" (desligado)<br>`.cop-basico__pe .btn--go` | 178 × 42 | Inter 600 16px/24px | `rgb(255, 255, 255)` | `rgb(4, 115, 107)` · opacidade 0.4 | sem | `4px` | `0px 22px` |

### Página do curso, aba Visão geral

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Cartão de número<br>`.stat` | 266 × 137 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgba(32, 34, 33, 0.13) | `10px` | `18px 20px` |
| Rótulo do número<br>`.stat__label` | 224 × 21 | Inter 400 14px/21px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Número<br>`.stat__value` | 224 × 46 | Inter 600 44px/46.2px espaç. -0.88px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Apoio do número<br>`.stat__delta` | 224 × 18 | Inter 400 12px/18px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Título de seção<br>`.section-title` | 259 × 35 | Inter 700 23.04px/34.56px | `rgb(54, 58, 56)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Sobretítulo de grupo<br>`.cop-grupo` | 359 × 18 | Inter 600 12px/18px espaç. 1.44px uppercase | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Linha de ferramenta<br>`.file--link` | 359 × 65 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(229, 240, 234)` | sem | `4px` | `12px 14px` |
| Quadro do ícone da linha<br>`.file__ico` | 40 × 40 | Inter 400 16px/24px | `rgb(54, 58, 56)` | `rgb(214, 230, 221)` | sem | `4px` | `0px` |
| Nome da ferramenta<br>`.file--link strong` | 245 × 21 | Inter 600 14px/21px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Frase da ferramenta<br>`.file--link strong + span` | 245 × 18 | Inter 400 12px/18px | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Etiqueta de pendência<br>`.tag--alerta` | 87 × 21 | Inter 700 11px/15.4px espaç. 0.88px uppercase | `rgb(32, 34, 33)` | `rgb(252, 221, 187)` | sem | `2px` | `3px 8px` |
| Título de painel<br>`.panel__head h2` | 235 × 27 | Inter 700 18px/27px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Linha de lista<br>`.setrow` | 618 × 81 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | bottom 1px solid rgba(32, 34, 33, 0.13) | `0px` | `16px 0px` |

### Alunos

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Filtro em pílula ligado<br>`.chip.is-on` | 72 × 37 | Inter 600 14px/21px | `rgb(255, 255, 255)` | `rgb(32, 34, 33)` | 1px solid rgb(32, 34, 33) | `999px` | `7px 14px` |
| Filtro em pílula<br>`.chip:not(.is-on)` | 72 × 37 | Inter 500 14px/21px | `rgb(54, 58, 56)` | `rgba(0, 0, 0, 0)` | 1px solid rgba(32, 34, 33, 0.34) | `999px` | `7px 14px` |
| Caixa da tabela<br>`.cop-tabela` | 1106 × 781 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgba(32, 34, 33, 0.13) | `10px` | `0px` |
| Cabeçalho da tabela<br>`.cop-tabela th` | 249 × 43 | Inter 600 12px/18px espaç. 0.72px uppercase | `rgb(86, 93, 90)` | `rgb(229, 240, 234)` | bottom 1px solid rgba(32, 34, 33, 0.13) | `0px` | `12px 16px` |
| Célula da tabela<br>`.cop-tabela td` | 249 × 92 | Inter 400 14px/21px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | bottom 1px solid rgba(32, 34, 33, 0.13) | `0px` | `14px 16px` |
| Avatar do aluno<br>`.avatar--gray` | 32 × 32 | Inter 700 12px/18px espaç. 0.24px | `rgb(32, 34, 33)` | `rgb(180, 199, 190)` | sem | `50%` | `0px` |
| Etiqueta "Ativo"<br>`.tag--ok` | 54 × 21 | Inter 700 11px/15.4px espaç. 0.88px uppercase | `rgb(3, 90, 84)` | `rgb(229, 240, 234)` | sem | `2px` | `3px 8px` |
| Barra de progresso (trilho)<br>`.progressbar` | 90 × 4 | Inter 400 14px/21px | `rgb(32, 34, 33)` | `rgba(32, 34, 33, 0.13)` | sem | `2px` | `0px` |
| Barra de progresso (preenchimento)<br>`.progressbar > i` | 25 × 4 | Inter 400 14px/21px | `rgb(32, 34, 33)` | `rgb(4, 115, 107)` | sem | `2px` | `0px` |
| Botão "Cancelar plano"<br>`.cop-tabela [data-cop="cancelar"]` | 132 × 34 | Inter 600 14px/21px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgba(32, 34, 33, 0.34) | `4px` | `0px 14px` |

### Conteúdo, tela do tema

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Botão invertido "Editar tema"<br>`.btn--light` | 163 × 42 | Inter 600 16px/24px | `rgb(255, 255, 255)` | `rgb(32, 34, 33)` | sem | `4px` | `0px 22px` |
| Módulo<br>`.week` | 1106 × 582 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgba(32, 34, 33, 0.34) | `10px` | `0px` |
| Número do módulo<br>`.week__n` | 52 × 52 | Archivo 800 22px/33px largura 80% | `rgb(86, 93, 90)` | `rgba(0, 0, 0, 0)` | 2px solid rgb(180, 199, 190) | `50%` | `0px` |
| Título do módulo<br>`.week h3` | 964 × 27 | Inter 700 18px/27px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Botão de ícone (seta de ordem)<br>`.ibtn:not([disabled])` | 34 × 34 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` | 1px solid rgba(32, 34, 33, 0.34) | `4px` | `0px` |
| Etiqueta de contorno<br>`.tag--line` | 174 × 23 | Inter 700 11px/15.4px espaç. 0.88px uppercase | `rgb(54, 58, 56)` | `rgba(0, 0, 0, 0)` | 1px solid rgba(32, 34, 33, 0.34) | `2px` | `3px 8px` |
| Etiqueta padrão<br>`.cop-resumo .tag:not(.tag--line):not(.tag--go)` | 152 × 23 | Inter 700 11px/15.4px espaç. 0.88px uppercase | `rgb(54, 58, 56)` | `rgb(236, 235, 230)` | sem | `2px` | `3px 8px` |

### Configurações, aba Avisos

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Chave ligada<br>`.switch[aria-checked="true"]` | 46 × 26 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(4, 115, 107)` | sem | `13px` | `0px` |

### Janela de confirmação

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Véu atrás da janela<br>`.modal__backdrop` | 1440 × 813 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgba(20, 39, 36, 0.55)` | sem | `0px` | `0px` |
| Janela<br>`.sheet` | 760 × 235 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(255, 255, 255)` · sombra rgba(20, 39, 36, 0.2) 0px 14px 44px 0px | sem | `10px` | `0px` |
| Título da janela<br>`.cop-dialog h2` | 640 × 33 | Archivo 800 30px/33px largura 82% | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Texto da janela<br>`.cop-dialog__txt` | 684 × 50 | Inter 400 16px/24.8px | `rgb(54, 58, 56)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Botão de perigo<br>`.btn--perigo` | 144 × 42 | Inter 600 16px/24px | `rgb(255, 255, 255)` | `rgb(185, 58, 43)` | sem | `4px` | `0px 22px` |
| Botão de fechar<br>`.sheet__close` | 36 × 36 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgb(229, 240, 234)` | sem | `50%` | `0px` |

## Área de membros (1440 px)

### Início

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Barra do topo<br>`.nav` | 1440 × 68 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `degradê` | sem | `0px` | `0px 57.6px` |
| Marca em texto<br>`.nav__brand` | 173 × 33 | Inter 700 22px/33px espaç. -0.44px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Link da barra<br>`.nav__links a:not(.is-active)` | 59 × 21 | Inter 400 14px/21px | `rgb(229, 229, 229)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Link ativo da barra<br>`.nav__links a.is-active` | 37 × 21 | Inter 700 14px/21px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Avatar<br>`.nav__profile .avatar` | 32 × 32 | Inter 700 12px/18px espaç. 0.24px | `rgb(255, 255, 255)` | `degradê` | sem | `4px` | `0px` |
| Etiqueta "Mentoria"<br>`.hero__kicker .tag` | 82 × 21 | Inter 700 11px/15.4px espaç. 0.88px uppercase | `rgb(255, 255, 255)` | `rgb(229, 9, 20)` | sem | `2px` | `3px 8px` |
| Título do destaque<br>`.hero__title` | 645 × 227 | Archivo 900 135.36px/113.702px largura 64% espaç. -1.62432px uppercase | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Descrição do destaque<br>`.hero__desc` | 645 × 82 | Inter 400 19.44px/27.216px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Botão claro grande<br>`.hero__actions .btn--light` | 183 × 52 | Inter 600 18px/27px | `rgb(0, 0, 0)` | `rgb(255, 255, 255)` | sem | `4px` | `0px 31.68px` |
| Botão suave grande<br>`.hero__actions .btn--dim` | 252 × 52 | Inter 600 18px/27px | `rgb(255, 255, 255)` | `rgba(109, 109, 110, 0.7)` | sem | `4px` | `0px 31.68px` |
| Capa de cartão<br>`.rail .cover` | 259 × 145 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `degradê` | sem | `4px` | `0px` |

### Cursos

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Área da página (espaço interno)<br>`.page` | 1440 × 1559 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `108px 57.6px 72px` |
| Título da página<br>`.page__title` | 626 × 49 | Archivo 800 48px/48.96px largura 82% espaç. -0.576px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Frase abaixo do título<br>`.page__sub` | 626 × 48 | Inter 400 16px/24px | `rgb(179, 179, 179)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Filtro em pílula ligado<br>`.chip.is-on` | 131 × 37 | Inter 600 14px/21px | `rgb(0, 0, 0)` | `rgb(255, 255, 255)` | 1px solid rgb(255, 255, 255) | `999px` | `7px 14px` |
| Filtro em pílula<br>`.chip:not(.is-on)` | 109 × 37 | Inter 500 14px/21px | `rgb(229, 229, 229)` | `rgba(0, 0, 0, 0)` | 1px solid rgba(255, 255, 255, 0.32) | `999px` | `7px 14px` |
| Botão "Filtro"<br>`.fbtn` | 101 × 37 | Inter 500 14px/21px | `rgb(255, 255, 255)` | `rgb(36, 36, 36)` | 1px solid rgb(77, 77, 77) | `4px` | `7px 12px` |
| Nome do tema no cartão<br>`.gcard__meta strong` | 255 × 18 | Inter 600 13px/18.2px | `rgb(229, 229, 229)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Texto do cartão<br>`.gcard__meta` | 259 × 44 | Inter 400 13px/18.2px | `rgb(128, 128, 128)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `8px 2px 0px` |

### Mentoria

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Faixa de abas<br>`.tabs` | 1325 × 53 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | bottom 1px solid rgba(255, 255, 255, 0.12) | `0px` | `0px` |
| Aba ativa<br>`.tab.is-on` | 64 × 52 | Inter 600 16px/24px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `14px 0px` |
| Aba<br>`.tab:not(.is-on)` | 138 × 52 | Inter 600 16px/24px | `rgb(179, 179, 179)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `14px 0px` |
| Título de seção<br>`.section-title` | 942 × 35 | Inter 700 23.04px/34.56px | `rgb(229, 229, 229)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Semana (módulo)<br>`.week` | 942 × 104 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgb(24, 24, 24)` | 1px solid rgba(255, 255, 255, 0.12) | `10px` | `0px` |
| Número da semana<br>`.week__n` | 52 × 52 | Archivo 800 22px/33px largura 80% | `rgb(6, 33, 15)` | `rgb(70, 211, 105)` | 2px solid rgb(70, 211, 105) | `50%` | `0px` |
| Título da semana<br>`.week h3` | 744 × 27 | Inter 700 18px/27px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Painel<br>`.panel` | 340 × 198 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgb(24, 24, 24)` | 1px solid rgba(255, 255, 255, 0.12) | `10px` | `26px` |
| Título de painel<br>`.panel__head h3` | 156 × 27 | Inter 700 18px/27px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Botão principal vermelho<br>`.btn--red` | 286 × 42 | Inter 600 16px/24px | `rgb(255, 255, 255)` | `rgb(229, 9, 20)` | sem | `4px` | `0px 22px` |
| Botão pequeno de contorno<br>`.btn--outline.btn--sm` | 159 × 34 | Inter 600 14px/21px | `rgb(255, 255, 255)` | `rgba(255, 255, 255, 0.12)` | 1px solid rgb(255, 255, 255) | `4px` | `0px 14px` |
| Etiqueta padrão<br>`.panel__head .tag` | 110 × 21 | Inter 700 11px/15.4px espaç. 0.88px uppercase | `rgb(229, 229, 229)` | `rgb(47, 47, 47)` | sem | `2px` | `3px 8px` |

### Central de ajuda

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Rótulo de campo<br>`.field label` | 753 × 21 | Inter 500 14px/21px | `rgb(179, 179, 179)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Seleção<br>`.select select` | 753 × 46 | Inter 500 16px/24px | `rgb(179, 179, 179)` | `rgb(36, 36, 36)` | 1px solid rgb(77, 77, 77) | `4px` | `10px 40px 10px 14px` |
| Área de texto<br>`textarea.input` | 753 × 170 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgba(22, 22, 22, 0.7)` | 1px solid rgb(94, 94, 94) | `4px` | `12px 14px` |
| Chamado<br>`.ticket` | 450 × 63 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgb(35, 35, 35)` | sem | `6px` | `0px` |
| Etiqueta "Resolvido"<br>`.tag--ok` | 104 × 21 | Inter 700 11px/15.4px espaç. 0.88px uppercase | `rgb(70, 211, 105)` | `rgba(70, 211, 105, 0.16)` | sem | `2px` | `3px 8px` |

### Conta e preferências

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Item ativo do menu lateral<br>`.settings__nav button.is-on` | 220 × 46 | Inter 500 16px/24px | `rgb(255, 255, 255)` | `rgb(35, 35, 35)` · sombra rgb(229, 9, 20) 3px 0px 0px 0px inset | sem | `4px` | `11px 14px` |
| Item do menu lateral<br>`.settings__nav button:not(.is-on)` | 220 × 46 | Inter 500 16px/24px | `rgb(179, 179, 179)` | `rgba(0, 0, 0, 0)` | sem | `4px` | `11px 14px` |
| Campo de texto<br>`.input` | 366 × 48 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgba(22, 22, 22, 0.7)` | 1px solid rgb(94, 94, 94) | `4px` | `0px 14px` |
| Avatar grande<br>`.avatar--lg` | 56 × 56 | Inter 700 18px/27px espaç. 0.36px | `rgb(255, 255, 255)` | `degradê` | sem | `4px` | `0px` |

### Meu progresso

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Cartão de número<br>`.stat` | 432 × 137 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgb(24, 24, 24)` | 1px solid rgba(255, 255, 255, 0.12) | `10px` | `18px 20px` |
| Número<br>`.stat__value` | 390 × 46 | Inter 600 44px/46.2px espaç. -0.88px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Rótulo do número<br>`.stat__label` | 390 × 21 | Inter 400 14px/21px | `rgb(179, 179, 179)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |

## Tela de login (1440 px)

### Tela de login

| Elemento | Largura × altura | Fonte (família, peso, tamanho/altura de linha) | Cor do texto | Fundo | Borda | Raio | Espaço interno |
|---|---|---|---|---|---|---|---|
| Barra do topo (vidro claro)<br>`.gm-login__barra` | 1342 × 62 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgba(255, 255, 255, 0.84)` | 1px solid rgba(255, 255, 255, 0.7) | `10px` | `10px 28px` |
| Logotipo<br>`.gm-login__logo img` | 145 × 40 | Inter 400 16px/24px | `rgb(32, 34, 33)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Link "Entrar"<br>`.gm-login__link` | 75 × 40 | Inter 600 16px/24px | `rgb(3, 90, 84)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `8px 2px` |
| Título de destaque<br>`.gm-login__texto h1` | 488 × 142 | Archivo 800 68.4px/71.136px largura 84% espaç. -0.8208px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Frase de apoio<br>`.gm-login__texto p` | 431 × 48 | Inter 300 16.56px/24.012px | `rgba(255, 255, 255, 0.92)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Arte "GO + mamute"<br>`.gm-login__arte` | 547 × 280 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Imagem da arte (opacidade)<br>`.gm-login__arte img` | 547 × 280 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` · opacidade 0.74 | sem | `0px` | `0px` |
| Cartão de acesso<br>`.gm-login__cartao` | 372 × 342 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgba(9, 22, 20, 0.74)` | 1px solid rgba(255, 255, 255, 0.16) | `10px` | `34px` |
| Título do cartão<br>`.gm-login__cartao h2` | 302 × 35 | Inter 600 23.04px/34.56px | `rgb(255, 255, 255)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Frase do cartão<br>`.gm-login__cartao > div > p` | 302 × 21 | Inter 400 14px/21px | `rgba(255, 255, 255, 0.78)` | `rgba(0, 0, 0, 0)` | sem | `0px` | `0px` |
| Campo<br>`.gm-login__cartao .input` | 302 × 52 | Inter 400 16px/24px | `rgb(255, 255, 255)` | `rgba(8, 20, 18, 0.55)` | 1px solid rgba(255, 255, 255, 0.26) | `4px` | `0px 14px` |
| Botão "Entrar"<br>`.gm-login__entrar` | 302 × 52 | Inter 600 18px/27px | `rgb(32, 34, 33)` | `rgb(250, 173, 49)` | sem | `4px` | `0px 22px` |
