# Componentes

Cada componente abaixo existe uma vez e é usado nas duas áreas. A coluna "Área de membros" mostra as cores do cliente; a coluna "Painel do produtor" mostra as mesmas peças com as cores da GoMut. **Formato, tamanho, tipografia e espaçamento são iguais nas duas áreas.**

Este documento resume o essencial. O CSS completo de cada componente, regra por regra e com as variáveis já resolvidas, está em:

- `css-por-componente-area-de-membros.md`
- `css-por-componente-painel-do-produtor.md` (só o que muda de cor e as peças próprias do painel)
- `css-por-componente-login.md`

Os nomes entre crases são as classes do protótipo. Use-os para achar a regra no CSS. Na implementação os nomes podem seguir o padrão do projeto, mas os valores não mudam.

Valores de conferência medidos no navegador: `medidas-de-conferencia.md`.

## 1. Botão — `.btn`

Estrutura: `<button class="btn btn--VARIANTE [btn--sm|btn--lg|btn--block]">[ícone] Texto</button>`. O ícone, quando existe, vem **antes** do texto, salvo nos botões "Próxima" e de compra, em que a seta vem depois.

| Propriedade | Valor |
|---|---|
| Disposição | `inline-flex`, alinhado ao centro, `gap: 10px`, `white-space: nowrap` |
| Altura | `42px` |
| Espaço interno | `0 22px` |
| Raio | `4px` |
| Texto | Inter, `16px`, peso `600` |
| Ícone | `1.3em` de lado |
| Transição | `background`, `color`, `border-color` em `150ms` |
| Desligado (`[disabled]`) | `opacity: 0.45` (no painel: `0.4`), cursor "não permitido" |
| Pequeno (`.btn--sm`) | altura `34px`, espaço interno `0 14px`, texto `14px` |
| Grande (`.btn--lg`) | altura `clamp(42px, 3.6vw, 54px)`, espaço interno `0 clamp(20px, 2.2vw, 32px)`, texto `clamp(15px, 1.25vw, 19px)`. Só no destaque da área de membros |
| Largura total (`.btn--block`) | `width: 100%` |

Variantes e cores:

| Variante | Área de membros | Painel do produtor |
|---|---|---|
| Principal | `.btn--red`: fundo `#e50914`, texto `#fff`; mouse `#f6121d`; pressionado `#b20710` | `.btn--go`: fundo `#04736b`, texto `#fff`; mouse `#058278`; pressionado `#035a54` |
| Claro / invertido | `.btn--light`: fundo `#fff`, texto `#000`; mouse `rgba(255,255,255,0.75)` | `.btn--light`: fundo `#202221`, texto `#fff`; mouse `#3b3f3d` |
| Contorno | `.btn--outline`: borda `1px rgba(255,255,255,0.32)`, texto `#fff`; mouse borda `#fff` e fundo `rgba(255,255,255,0.08)`; ligado (`.is-on`) borda `#fff` e fundo `rgba(255,255,255,0.12)` | `.btn--outline`: fundo `#fff`, borda `1px rgba(32,34,33,0.34)`, texto `#202221`; mouse borda `#202221` e fundo `#e5f0ea` |
| Suave | `.btn--dim`: fundo `rgba(109,109,110,0.7)`, texto `#fff`; mouse `rgba(109,109,110,0.4)` | `.btn--dim`: fundo `#d6e6dd`, texto `#202221`; mouse `#b4c7be` |
| Perigo | não existe | `.btn--perigo`: fundo `#b93a2b`, texto `#fff`; mouse `#c9463a`. **Só** no botão de confirmar das janelas de ações que tiram algo do ar (excluir, despublicar, cancelar plano, restaurar) |

Regra de uso no painel: uma ação principal por tela em `.btn--go`; as demais em `.btn--outline`. Ações do cabeçalho do curso usam `.btn--sm`.

Outros botões:

- **Botão de ícone** `.ibtn` (painel): `34 × 34px`, raio `4px`, borda `1px rgba(32,34,33,0.34)`, fundo `#fff`, ícone de `16px`; mouse: borda `#202221`, fundo `#e5f0ea`; desligado: `opacity: 0.3`. Usado nas setas de ordem, editar e excluir de linhas. A seta "para cima" é o ícone `down` girado 180°.
- **Botão redondo** `.rbtn` (área de membros): `40 × 40px`, círculo, borda `2px rgba(255,255,255,0.5)`, fundo `rgba(42,42,42,0.6)`; pequeno `34 × 34px`. Usado em "adicionar à lista" e "curtir".
- **Botão de texto** `.linkbtn`: `14px`, peso `500`, cor `--c-text-3`; mouse: cor `--c-text` e sublinhado.

## 2. Etiqueta — `.tag`

| Propriedade | Valor |
|---|---|
| Disposição | `inline-flex`, `gap: 6px` |
| Espaço interno | `3px 8px` |
| Raio | `2px` |
| Texto | Inter `11px`, peso `700`, `letter-spacing: 0.08em`, MAIÚSCULAS, `line-height: 1.4` |

| Variante | Área de membros | Painel do produtor |
|---|---|---|
| Padrão | fundo `#2f2f2f`, texto `#e5e5e5` | fundo `#ecebe6`, texto `#363a38` |
| Destaque | `.tag--red`: fundo `#e50914`, texto `#fff` | `.tag--go`: fundo `#04736b`, texto `#fff` |
| Contorno | `.tag--line`: sem fundo, borda `1px rgba(255,255,255,0.32)`, texto `#e5e5e5` | `.tag--line`: sem fundo, borda `1px rgba(32,34,33,0.34)`, texto `#363a38` |
| Positivo | `.tag--ok`: fundo `rgba(70,211,105,0.16)`, texto `#46d369` | `.tag--ok`: fundo `#e5f0ea`, texto `#035a54` |
| Pendência | não existe | `.tag--alerta`: fundo `#fcddbb`, texto `#202221` |
| Ao vivo | `.tag--live`: fundo `#e50914`, com ponto branco de 6 px pulsando | não usada |

Uso fixo no painel: "Publicado", "Publicada", "Ativo", "Resolvido", "Liberado" → `.tag--ok`. "Despublicado", "Rascunho", "Aberto", "Sem resposta", "Sem link de checkout" → `.tag--alerta`. "Coprodutor", "Novo", etiqueta de quem responde pela mentoria → `.tag--go`. Datas e informações neutras → `.tag--line` ou padrão.

## 3. Campos de formulário

Estrutura de um campo: `.field` (grade, `gap: 6px`) com rótulo, controle e, embaixo, dica `.hint`. Formulário: `.form` (grade, `gap: 18px`); `.form--2` e `.form--3` dividem em 2 e 3 colunas iguais (uma coluna até 599 px e 899 px, respectivamente).

| Peça | Medidas | Área de membros | Painel do produtor |
|---|---|---|---|
| Rótulo (`.field label`) | Inter `14px`, peso `500` | cor `#b3b3b3` | cor `#565d5a` |
| Campo (`.input`) | largura total, altura `48px`, espaço interno `0 14px`, raio `4px`, borda `1px`, texto `16px` | fundo `rgba(22,22,22,0.7)`, borda `#5e5e5e`; mouse `#8c8c8c`; foco: contorno `2px #fff` afastado `2px` e borda `#fff` | fundo `#fff`, borda `#b3bfb9`; mouse `#6f7c77`; foco: contorno `2px #04736b` e borda `#04736b`; texto de exemplo `#6e7672` |
| Área de texto (`textarea.input`) | altura automática, mínimo `96px`, espaço interno `12px 14px`, `line-height: 1.5`, redimensiona só na vertical | igual ao campo | igual ao campo |
| Campo pequeno (`.input--sm`) | altura `38px`, texto `14px` | — | usado em busca e dentro de opções |
| Seleção (`.select select`) | espaço interno `10px 40px 10px 14px`, raio `4px`, texto `16px` peso `600`, seta: triângulo de `5px` a `14px` da direita | fundo `#242424`, borda `#4d4d4d`, seta `#fff` | fundo `#fff`, borda `#b3bfb9`, seta `#202221` |
| Chave (`.switch`) | `46 × 26px`, raio `13px`; ponto de `20px` a `3px` da borda, desliza `20px` em `260ms` | desligada: trilho `#414141`; ligada: trilho `#e50914`; ponto `#fff` | desligada: trilho `#b4c7be`, ponto `#fff`; ligada: trilho `#04736b`, **ponto `#faad31`** |
| Dica (`.hint`) | `12px`, `line-height: 1.45` | — | cor `#565d5a` |
| Caixa de marcar e opção | `18 × 18px`, `accent-color` | — | `#04736b` |
| Escolha de arquivo (`.cop-arquivo`, painel) | campo com espaço interno `9px 10px`, texto `14px`; botão do navegador com borda `1px rgba(32,34,33,0.34)`, raio `4px`, peso `600` | — | — |
| Contador de caracteres (`.cop-conta`, painel) | `12px`, cor `#6e7672`, números tabulares, à direita, na mesma linha da dica | — | — |

Busca do painel (`.cop-busca`): campo pequeno com lupa de `18px` a `12px` da esquerda e texto começando a `38px`; largura máxima `340px`.

## 4. Abas — `.tabs` e `.tab`

Faixa horizontal com linha de `1px` (`--c-line`) embaixo; `gap: clamp(16px, 2.4vw, 32px)`; rola na horizontal sem barra de rolagem quando não cabe.

Aba: espaço interno `14px 0`, Inter `16px` peso `600`, cor `--c-text-3`. Mouse e ativa: cor `--c-text`. Ativa (`.is-on`): traço de `3px` na cor de destaque (`#e50914` nos membros, `#04736b` no painel), colado na linha de baixo.

No painel, a faixa de abas fica a `clamp(18px, 2.4vw, 30px)` do conteúdo (`.cop-tabs`).

## 5. Filtro em pílula — `.chip`

Espaço interno `7px 14px`, raio `999px`, borda `1px --c-line-strong`, Inter `14px` peso `500`, cor `--c-text-2`. Mouse: borda e texto `--c-text`. Ligado: área de membros fundo `#fff`, texto `#000`, peso `600`; painel fundo `#202221`, texto `#fff`.

É a única peça em formato de pílula. Não use esse formato em botões.

## 6. Painel — `.panel`

Caixa de conteúdo: espaço interno `clamp(18px, 2vw, 26px)`, raio `10px`, fundo `--c-surface-1`, borda `1px --c-line`. **Sem sombra.**

Cabeçalho (`.panel__head`): título à esquerda (Inter `18px` peso `700`) com frase opcional embaixo (`14px`, `--c-text-3`) e ação opcional à direita; `margin-bottom: 16px`.

## 7. Linha de configuração — `.setrow`

Linha com texto à esquerda e controle à direita: `display: flex`, espaço entre as pontas, `gap: 20px`, espaço interno `16px 0`, linha de `1px --c-line` embaixo (a última não tem). Título em peso `600`; frase em `14px` `--c-text-3`.

À direita pode haver chave, etiqueta, botão pequeno ou um grupo de botões de ícone. Até 599 px, quando o grupo de botões não cabe ao lado do texto, ele desce para a linha de baixo, alinhado à direita.

## 8. Linha de arquivo e de ferramenta — `.file`

`display: flex`, `gap: 14px`, espaço interno `12px 14px`, raio `4px`, fundo `--c-surface-2`. Ícone à esquerda, título (`14px` peso `600`) com frase (`12px` `--c-text-3`), e à direita um botão ou, na versão de link (`.file--link`), uma seta.

No painel, a lista "Ferramentas de gestão" usa `.file--link` com ícone em Verde GO; título e frase em uma linha só, cortados com reticências.

## 9. Cartão de número — `.stat`

Espaço interno `18px 20px`, raio `10px`, fundo `--c-surface-1`, borda `1px --c-line`. Rótulo `14px` `--c-text-3` com ícone na cor de destaque; valor `clamp(30px, 3.2vw, 44px)` peso `600`, `line-height: 1.05`, `letter-spacing: -0.02em`; apoio `12px` `--c-text-3`. No painel o cartão é um link: ao passar o mouse a borda vira `--c-line-strong`. Sem sombra e sem elevação.

## 10. Barra do topo — `.nav`

Fixa no alto, altura `68px` (até 899 px: `56px`), `z-index: 50`.

- **Área de membros**: fundo em degradê transparente que vira `#141414` sólido ao rolar (`.is-solid`). Marca em texto ("Emergensimples", `clamp(18px, 1.6vw, 22px)` peso `700`), links (Início, Mentoria, Cursos, Trilhas, Ao vivo, Minha lista), busca, sininho e perfil. Até 899 px os links somem e aparece a barra inferior com 5 itens.
- **Painel**: fundo `#fff`, linha de `1px` embaixo. Logotipo da GoMut com `40px` de altura (36 px até 1199 px; 32 px até 899 px), etiqueta "Coprodutor", e à direita "Visualizar como membro" (botão pequeno de contorno) e o menu da conta. Margem esquerda de `26px` (alinha o logotipo com os ícones do painel lateral); margem direita `clamp(20px, 3vw, 44px)`.

## 11. Painel lateral do painel do produtor — `.cop-lado`

Fixo à esquerda, do fim da barra do topo até o fim da tela. Largura `248px` (até 1199 px: `228px`), espaço interno `18px 12px 24px`, fundo `#fff`, linha de `1px` à direita, rola na vertical se precisar.

Opção (`.cop-lado__menu a`): `display: flex`, `gap: 12px`, espaço interno `11px 14px`, raio `4px`, Inter `16px` peso `500`, cor `#565d5a`, `white-space: nowrap`; ícone de `20px`. Entre as opções: `2px`.

- Mouse: texto `#202221`, fundo `rgba(4,115,107,0.06)`.
- Ativa (`.is-on`): texto `#202221`, peso `600`, fundo `#e5f0ea`, traço interno de `3px` em `#04736b` à esquerda (`box-shadow: inset 3px 0 0`), ícone em `#04736b`.

Opções, nesta ordem, com o ícone de cada uma: Criar curso (`plus`), Meus cursos (`grid`), Relatórios (`painel-grafico`), Comunidade (`message`), Alunos (`users`), Certificados (`award`), Controle de acesso (`painel-escudo`), Chamados (`help`), Configurações (`sliders`).

Até 899 px o painel fica recolhido fora da tela. Um botão de menu (`painel-menu`, `40 × 40px`) na barra do topo o abre: largura `min(300px, 84vw)`, desliza em `260ms`, com sombra `--shadow-pop` e véu `rgba(20,39,36,0.55)` sobre o conteúdo. Fecha ao tocar no véu, ao escolher uma opção ou com a tecla Esc.

## 12. Menu suspenso — `.dd`

Painel de `250px` (`.dd__panel--menu`) a `14px` abaixo do botão, alinhado à direita, com `--shadow-pop`. Área de membros: fundo `rgba(0,0,0,0.94)`, borda `1px --c-line`, borda de cima `2px #e5e5e5`. Painel: fundo `#fff`, borda de cima `2px #202221`. Item: `gap: 12px`, espaço interno `11px 16px`, `14px`; mouse com fundo de realce. Cabeçalho do menu com avatar, nome e linha de apoio.

## 13. Janelas — `.modal` e `.sheet`

Véu fixo cobrindo a tela (`rgba(0,0,0,0.72)` nos membros; `rgba(20,39,36,0.55)` no painel). Janela centralizada: largura `min(940px, calc(100% - 32px))`, margem `32px auto 48px`, raio `10px`, fundo `--c-surface-1`, sombra `--shadow-pop`; botão de fechar redondo de `36px` no canto superior direito. Até 599 px ocupa a tela inteira, sem raio.

Janelas de edição e de confirmação do painel (`.cop-dialog`): título em Archivo (ver tokens), formulário e rodapé com os botões à direita: "Cancelar" (`.btn--outline`) e a ação (`.btn--go`, ou `.btn--perigo` nas confirmações de ações que tiram algo do ar).

## 14. Aviso rápido — `.toast`

Embaixo, no centro da tela (`bottom: 28px`; `78px` até 899 px na área de membros). `gap: 10px`, espaço interno `12px 18px`, raio `4px`, `14px` peso `600`, sombra `--shadow-pop`. Área de membros: fundo `#fff`, texto `#141414`, ícone `#e50914`. Painel: fundo `#142724`, texto `#fefcf5`, ícone `#faad31`.

## 15. Avatar — `.avatar`

Quadrado de `32px` com raio `4px` (redondo com `.avatar--round`; grande `56px`), iniciais em `12px` peso `700`. Fundo: degradê de 135° do tom de destaque ao tom pressionado (`#e50914 → #b20710` nos membros; `#058278 → #035a54` no painel). Versão cinza (`.avatar--gray`) para alunos.

## 16. Barra de progresso — `.progressbar`

Altura `4px`, raio `2px`. Trilho `rgba(255,255,255,0.22)` nos membros e `rgba(32,34,33,0.13)` no painel; preenchimento na cor de destaque.

## 17. Capa — `.cover`

Proporção `16 / 9`, raio `4px`. Quando não há imagem enviada, a capa é **gerada**: fundo em degradês calculados a partir de um matiz (`--h`, de 0 a 360), um desenho de linha (ver `04-icones/motivos-das-capas/`), um sobretítulo e o título em Archivo condensada, em maiúsculas. Definição completa em `css-por-componente-area-de-membros.md`, seção "Capas". Formas: padrão (16:9), pôster (`2 / 3`) e miniatura (sem textos).

No painel, a capa enviada pelo produtor aparece no cartão de "Meus cursos" ocupando a mesma área, com `object-fit: cover`.

## 18. Cartão de curso e de tema — `.card` e `.gcard`

`.card`: a capa como link, com raio `4px`. Ao passar o mouse: `filter: brightness(1.08)`. Selos sobre a capa (`.card__badge`): "Novo", "Concluído", "Mentoria".

`.gcard`: cartão em grade, com a capa e, embaixo, o texto (`.gcard__meta`: `13px`, `--c-text-4`, com o nome em peso `600` numa linha só). Grade: `repeat(var(--cols), 1fr)`, vão vertical `clamp(24px, 3vw, 44px)` e horizontal `--gap`.

Em "Meus cursos" (painel), entre a capa e o nome aparece a etiqueta de situação, e o nome usa `16px`.

## 19. Cabeçalho de página

- Caminho (`.crumbs`): `14px`, `--c-text-3`, itens separados por "·", com seta para a esquerda no primeiro; `margin-bottom: 12px`.
- Cabeçalho (`.page__head`): título à esquerda e ações à direita, alinhados pela base, quebrando linha quando não cabem; `margin-bottom: clamp(20px, 2.6vw, 36px)`.
- Página (`.page`): espaço interno `calc(var(--nav-h) + clamp(20px, 3vw, 40px)) var(--gutter) 72px`. No painel, a página começa depois do painel lateral (`margin-left: var(--lado-w)`).

## 20. Tabela do painel — `.cop-tabela`

Caixa com borda `1px --c-line`, raio `10px`, rolagem horizontal própria. Cabeçalho: `12px` peso `600`, `letter-spacing: 0.06em`, MAIÚSCULAS, fundo `#e5f0ea`, espaço interno `12px 16px`. Célula: `14px 16px`, linha de `1px` embaixo; mouse na linha: fundo de realce. Largura mínima da tabela `900px` (`760px` até 1439 px).

## 21. Módulo que abre e fecha — `.week`

Caixa com raio `10px`, fundo `--c-surface-1`, borda `1px --c-line`. Cabeçalho clicável: número em círculo de `52px` com borda de `2px`, sobretítulo, título (`18px` peso `700`), linha de apoio e seta. Dentro, a lista de aulas (`.eps`).

## 22. Estado vazio — `.empty`

Centralizado: ícone de `48px` (`--c-surface-4`), título `--fs-xl` e frase de até `44ch`; espaço interno `clamp(40px, 8vw, 96px) 16px`.

## 23. Peças da aba Básico do curso (painel)

- Grade (`.cop-basico__grade`): duas colunas, `minmax(240px, 36%)` e o restante, vão `clamp(20px, 3vw, 40px)`. Até 1099 px, uma coluna com a capa por último.
- Caixa da capa (`.cop-capa`): espaço interno `12px`, borda `1px` **tracejada** `rgba(32,34,33,0.34)`, raio `10px`; dentro, a capa em `16 / 9` com raio `4px`. Mouse: borda `#04736b` e fundo de realce. Clicar abre a escolha do arquivo.
- Ações da capa (`.cop-capa__acoes`): "Enviar imagem" ou "Trocar imagem", e "Remover imagem" quando há imagem; botões de texto com ícone de `16px`, centralizados.
- Rodapé do formulário (`.cop-basico__pe`): linha de `1px` em cima, botões à direita, `gap: 10px`: "Cancelar" (`.btn--outline`) e "Salvar alterações" (`.btn--go`, desligado até haver alteração).

## 24. Foco e seleção de texto

- Foco por teclado (`:focus-visible`): contorno de `2px`, afastado `2px`. Cor: `#fff` na área de membros, `#04736b` no painel, `#faad31` no login (`#04736b` dentro da barra clara do login).
- Seleção de texto: área de membros fundo `#e50914` e texto `#fff`; painel fundo `#04736b` e texto `#fff`; login fundo `#faad31` e texto `#202221`.
