# Área do aluno GoMut — plano de adaptação do design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Não delegar sem autorização específica.

**Goal:** Demonstrar o acesso real do aluno a dois cursos fictícios, módulos e aulas com Vimeo, priorizando a visita do médico em 16/11/2026.

**Architecture:** Manter Django, sessões, templates e JavaScript próprio. Aplicar o CSS normativo em bases de layout separadas, preservando dados, permissões e serviços existentes. Funcionalidades do redesign sem backend serão apresentadas com indicação explícita e sem simular gravação.

**Tech Stack:** Python, Django 4.2.30, SQLite, HTML, CSS e JavaScript; sem React, Vue, DRF ou nova infraestrutura de front-end.

**Spec:** `docs/handoff-design/LEIA-PRIMEIRO.md`, `01-regras-inviolaveis.md`, `02-tokens/`, `03-componentes/`, `05-telas/`; complementadas pelas decisões do usuário de 16/11/2026 registradas abaixo, que prevalecem sobre exemplos e regras divergentes do pacote.

**Status:** Aprovado pelo usuário e executado para a entrega prioritária de login, área do aluno e períodos manuais. Diferenças e limites em `docs/area-aluno-demonstracao.md`.

## Decisões confirmadas pelo usuário

- Dois acessos: administrador/produtor com gestão completa e aluno com seus cursos. Sem coprodutor separado nem isolamento entre vários produtores.
- Dois cursos no MVP, mantendo cadastro de novos cursos, módulos e aulas. Estrutura do conteúdo: Curso → Módulo → Aula. Tema/matéria é o assunto; não criar entidades extras pela nomenclatura do protótipo.
- Dados fictícios enquanto a estrutura e os fluxos são testados. Autor é o próprio médico; não desenvolver catálogo de autores.
- Excluir Top 10. Não preencher fileiras artificialmente para aparentar catálogo grande.
- Administrador cadastra alunos e entrega instruções pelo WhatsApp. Importação em lote de alunos reais será realizada posteriormente, quando os dados forem fornecidos. Não enviar mensagens automaticamente.
- Períodos de acesso por aluno/curso serão definidos manualmente pelo administrador: início e último dia quitado. Gateway e cobranças automáticas ficam para etapa futura.
- Ajustar períodos não significa confirmar pagamento no Asaas ou agendar débito. O banco já diferencia período quitado, matrícula e assinatura.
- Aulas incorporadas do Vimeo, sem upload de vídeo. Upload de capa e PDF são funcionalidades distintas; preservar o suporte existente, sem presumir que o Vimeo armazena esses materiais.
- Foco imediato: login, início do aluno, lista de cursos, entrada no curso, módulos, aulas, vídeo e informações das telas.
- Funcionalidade nova sem backend: indicação visível “Necessita de backend”; nada de sucesso fictício nem persistência da aplicação em localStorage.
- Relatórios e controle de acesso fora da entrega imediata.
- Navegadores alvo: Chrome, Edge, Firefox e Opera atuais. Compatibilidade real só será declarada para os navegadores efetivamente verificados.
- Filtro por curso no painel para consultar alunos e gestão, com visão geral quando nenhum curso estiver selecionado.

## Proposta técnica e limites

A abordagem proposta usa os templates Django existentes e as regras visuais do handoff. Uma cópia navegável do protótipo não comprovaria autenticação, matrícula, bloqueio e progresso; uma API/front-end separados ampliariam o trabalho e contrariariam a stack acordada.

A ordem do pacote será ajustada à prioridade expressa pelo usuário: fundamentos → login → área do aluno → controle manual de períodos → demais telas do painel. A indicação de backend pendente e a remoção de Top 10 são divergências autorizadas em relação às imagens.

O controle manual de datas é uma entrega funcional posterior ao fluxo visual principal. Não apresentar uma interface de edição de datas como implementada antes de existir validação, persistência e testes. Na demonstração, períodos fictícios podem ser carregados por preparação explícita da base de demonstração.

Manter o fluxo seguro já existente de código de primeiro acesso e criação de senha. Não criar senha compartilhada ou transportar senha em URL. Cadastro público não será promovido na nova entrada; o endpoint atual não será removido nesta fase. A redefinição de senha e a ativação continuam funcionais em seus endereços; inclusão de novos links na composição fechada do login permanece pendente.

## Global Constraints

- Não aplicar migrations, seed destrutivo ou dados fictícios numa base operacional. Não alterar alunos reais.
- Não recriar dados com `seed.py`: o script atual apaga dados.
- Não ativar Asaas nem criar cobranças, webhooks externos ou assinaturas.
- Preservar controle de matrícula e acesso em todos os endpoints, inclusive JSON. Ocultar botão não é permissão.
- Não abrir acesso ao curso inteiro por o aluno ter um outro curso ativo.
- Não trocar CSS de telas antigas antes de migrar a respectiva base; evitar colisões de `.btn`, `.card`, `.field` e tokens.
- Valores visuais vêm do CSS do protótipo; não arredondar, redesenhar logo ou substituir ícones/fontes.
- Nenhum vídeo falso com interface que pareça reprodução real. Sem vídeo válido: estado vazio existente.
- Recursos sem backend não executam POST nem mostram confirmação de cadastro/salvamento.
- Não expor gestão ao aluno. Nenhum link ao painel na sessão do aluno.
- Datas inclusivas na interface; fim exclusivo internamente em `AccessPeriod`. Manter a tolerância existente de três dias, identificando-a separadamente do período quitado.

## Review Focus

1. Aluno sem matrícula, com curso vencido ou URL de outro curso não deve acessar vídeo/progresso.
2. Troca de identidade e CSS não pode alterar a aparência ou funcionamento de páginas ainda não migradas.
3. Apenas dois cursos: layout sem ranking, contagens e progresso reais da base fictícia, sem filler de catálogo.
4. Falha de Vimeo ou Google Fonts deve ser registrada como limitação; não afirmar validação visual com fonte alternativa.
5. Controles pendentes, inclusive quiz e notificações, precisam de indicação perceptível por teclado e não podem aparentar gravação real.

## Mapeamento dos tokens para Django/CSS

Arquivo de destino: `static/css/gomut/tokens.css`. Sem conversão para escala de biblioteca. Cada token abaixo mantém nome e valor; o escopo é a única adaptação.

| Contexto | Escopo de destino | Herança e carregamento |
|---|---|---|
| Área do aluno | `html[data-area="membros"]` | Todos os tokens base; CSS de membros, sem CSS legado |
| Painel migrado | `html[data-area="admin"]` | Tokens base + sobrescritas do painel; isolado do aluno |
| Login | `html[data-area="login"]` e `.auth.gm-login` | Tokens base para tipografia/medidas + sobrescritas próprias do login |

As bases definirão o contexto no HTML antes da renderização. Painel ainda não migrado continua na base atual. Não criar alternador de tema.

### Tokens base — aluno; herdados pelos outros contextos

| Token | Valor de referência |
|---|---|
| `--c-black` | `#000000` |
| `--c-bg` | `#141414` |
| `--c-surface-1` | `#181818` |
| `--c-surface-2` | `#232323` |
| `--c-surface-3` | `#2f2f2f` |
| `--c-surface-4` | `#414141` |
| `--c-red` | `#e50914` |
| `--c-red-hover` | `#f6121d` |
| `--c-red-press` | `#b20710` |
| `--c-text` | `#ffffff` |
| `--c-text-2` | `#e5e5e5` |
| `--c-text-3` | `#b3b3b3` |
| `--c-text-4` | `#808080` |
| `--c-line` | `rgba(255, 255, 255, 0.12)` |
| `--c-line-strong` | `rgba(255, 255, 255, 0.32)` |
| `--c-green` | `#46d369` |
| `--c-amber` | `#e8b339` |
| `--font-ui` | `"Inter", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` |
| `--font-display` | `"Archivo", "Arial Narrow", "Helvetica Neue", Arial, sans-serif` |
| `--fs-xs` | `12px` |
| `--fs-s` | `14px` |
| `--fs-m` | `16px` |
| `--fs-l` | `18px` |
| `--fs-xl` | `clamp(20px, 1.6vw, 26px)` |
| `--fs-page` | `clamp(30px, 3.6vw, 48px)` |
| `--fs-hero` | `clamp(56px, 9.4vw, 156px)` |
| `--radius-s` | `4px` |
| `--radius-m` | `6px` |
| `--radius-l` | `10px` |
| `--radius-pill` | `999px` |
| `--gutter` | `clamp(16px, 4vw, 60px)` |
| `--gap` | `8px` |
| `--nav-h` | `68px` |
| `--cols` | `6` |
| `--ease` | `cubic-bezier(0.2, 0.7, 0.2, 1)` |
| `--t-fast` | `150ms` |
| `--t-med` | `260ms` |
| `--shadow-pop` | `0 14px 44px rgba(0, 0, 0, 0.78)` |
| `--shadow-card` | `0 6px 20px rgba(0, 0, 0, 0.5)` |
| `--z-peek` | `40` |
| `--z-nav` | `50` |
| `--z-tabbar` | `55` |
| `--z-modal` | `100` |
| `--z-toast` | `200` |

### Sobrescritas — painel

| Token | Valor de referência |
|---|---|
| `--c-bg` | `#ffffff` |
| `--c-surface-1` | `#ffffff` |
| `--c-surface-2` | `#e5f0ea` |
| `--c-surface-3` | `#d6e6dd` |
| `--c-surface-4` | `#b4c7be` |
| `--c-red` | `#04736b` |
| `--c-red-hover` | `#058278` |
| `--c-red-press` | `#035a54` |
| `--c-text` | `#202221` |
| `--c-text-2` | `#363a38` |
| `--c-text-3` | `#565d5a` |
| `--c-text-4` | `#6e7672` |
| `--c-line` | `rgba(32, 34, 33, 0.13)` |
| `--c-line-strong` | `rgba(32, 34, 33, 0.34)` |
| `--c-green` | `#04736b` |
| `--shadow-pop` | `0 14px 44px rgba(20, 39, 36, 0.2)` |
| `--go` | `#04736b` |
| `--go-hover` | `#058278` |
| `--go-press` | `#035a54` |
| `--grafite` | `#202221` |
| `--ambar` | `#faad31` |
| `--creme` | `#fefcf5` |
| `--verde-profundo` | `#142724` |
| `--verde-palido` | `#e5f0ea` |
| `--pessego` | `#fcddbb` |
| `--perigo` | `#b93a2b` |
| `--perigo-hover` | `#c9463a` |
| `--acento` | `#04736b` |
| `--nav-bg` | `#ffffff` |
| `--inv-bg` | `#202221` |
| `--inv-fg` | `#ffffff` |
| `--inv-hover` | `#3b3f3d` |
| `--campo-bg` | `#ffffff` |
| `--campo-borda` | `#b3bfb9` |
| `--campo-borda-hover` | `#6f7c77` |
| `--contorno-bg` | `#ffffff` |
| `--contorno-hover` | `#e5f0ea` |
| `--tag-bg` | `#ecebe6` |
| `--ok-bg` | `#e5f0ea` |
| `--ok-fg` | `#035a54` |
| `--alerta-bg` | `#fcddbb` |
| `--alerta-fg` | `#202221` |
| `--realce` | `rgba(4, 115, 107, 0.06)` |
| `--toast-bg` | `#142724` |
| `--toast-fg` | `#fefcf5` |
| `--toast-ico` | `#faad31` |
| `--veu` | `rgba(20, 39, 36, 0.55)` |
| `--lado-w` | `248px` |

### Sobrescritas — login

| Token | Valor de referência |
|---|---|
| `--c-text-2` | `rgba(255, 255, 255, 0.92)` |
| `--c-text-3` | `rgba(255, 255, 255, 0.78)` |
| `--c-text-4` | `rgba(255, 255, 255, 0.6)` |
| `--c-line` | `rgba(255, 255, 255, 0.16)` |
| `--c-line-strong` | `rgba(255, 255, 255, 0.34)` |
| `--gm-go` | `#04736b` |
| `--gm-go-escuro` | `#035a54` |
| `--gm-grafite` | `#202221` |
| `--gm-ambar` | `#faad31` |
| `--gm-profundo` | `#142724` |

Os valores acima reproduzem `tokens.json`; quando o CSS normativo utiliza `var(...)` para um alias, preservar a referência equivalente no mesmo contexto. O CSS normativo de login também define `--c-text: #ffffff`, embora esse item não conste do grupo login no JSON. Herdar o valor base e registrar essa diferença.

### Pontos de quebra e medidas

Reproduzir o CSS, incluindo `599`, `899`, `1023`, `1099`, `1199`, `1279`, `1439` e `1499px`. Login também possui regras em `699`, `1199` e `1899px`; não descartá-las por não aparecerem na lista resumida. Valores responsivos de tokens são os de `area_de_membros_por_largura_de_tela` de `tokens.json`; demais alterações vêm dos CSS de tela.

Painel: lateral de 248px, 228px até 1199px e recolhida até 899px. Membros: não herdar a navegação lateral antiga. Aula: coluna lateral de 380px, 320px até 1199px e uma coluna até 1023px.

### Fontes e marcas

- Carregar `https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=Inter:wght@300;400;500;600;700&display=swap` na nova base. Preservar `font-stretch` e pesos de cada regra normativa.
- Copiar sem transformação os arquivos existentes `prototipo/assets/marca/gomut-logo.png` e `gomut-go-mamute-vidro-4k.png` para `static/gomut/marca/`. Arte do mamute com opacidade 0,74 conforme o CSS.
- Existe também `gomut-logo-original.webp`. SVG vetorial da marca não foi encontrado; PNG existente atende à demonstração. Não é necessário solicitar novas artes para iniciar.
- Marca do aluno permanece o texto de demonstração entregue no handoff; não introduzir logo GoMut no cabeçalho do aluno. Identidade definitiva do cliente pode ser configurada posteriormente.

### Ícones

Copiar os 51 SVG de `04-icones/icones/` para `static/gomut/icones/`. Criar `templates/partials/gomut/icon.html`, com seleção por nome permitido, para renderizar os SVG inline preservando `currentColor`. Nenhum nome vindo do usuário pode determinar livremente um caminho de include. Manter o fragmento de ícones legado para as telas não migradas.

## Arquivos e responsabilidades

| Arquivo de destino | Responsabilidade |
|---|---|
| `static/css/gomut/tokens.css` | Tokens e escopos; mapeamento integral acima |
| `static/css/gomut/base.css` | Reset normativo, tipografia, foco, seleção e movimento reduzido |
| `static/css/gomut/components.css` | Peças compartilhadas do handoff, sem lógica de negócio |
| `static/css/gomut/members.css` | Composição das telas de aluno e pontos de quebra |
| `static/css/gomut/login.css` | Estilo normativo do login |
| `static/css/gomut/admin.css` | Composição do painel quando migrado, após a demonstração principal |
| `templates/base_gomut.html` | HTML, contexto, fontes, assets e blocos de expansão |
| `templates/base_aluno.html` | Estrutura de membros; adaptação quando todas as telas dependentes estiverem compatíveis |
| `templates/partials/gomut/` | Componentes de template listados abaixo |
| `templates/login.html` | Formulário de autenticação real no desenho entregue |
| `templates/courses/dashboard.html` | Início e os dois cursos do aluno |
| `templates/courses/course_detail.html` | Curso matriculado, módulos, aulas, materiais e progresso |
| `templates/courses/lesson_detail.html` | Vimeo, navegação, conclusão e materiais existentes |
| `templates/courses/access_pending.html` | Acesso pendente/vencido no novo contexto |
| `static/js/gomut/navigation.js` | Menus, pesquisa visual, navegação móvel, rolagem do topo e foco |
| `static/js/gomut/course-dialog.js` | Janela de curso: abrir/fechar, teclado e devolução de foco |
| `static/js/aluno.js` | Adaptar seletores mantendo endpoints reais e conclusão idempotente |
| `courses/selectors.py` | Dados de cursos/módulos/aulas e progresso para templates; sem gravação |
| `courses/student_views.py`, `core/urls.py` | Adaptadores HTTP e eventual rota de detalhe, mantendo verificações de acesso |
| `courses/ui_capabilities.py` | Registro explícito de recursos disponíveis/pendentes, sem fingir implementação |
| `courses/management/commands/prepare_demo.py` | Preparação explícita e não destrutiva de dois cursos fictícios e conta de demonstração |
| `courses/test_member_redesign.py`, `users/test_login_redesign.py` | Fluxos reais e permissões da demonstração |

### Componentes na ordem do documento

| Ordem e componente | Destino principal |
|---|---|
| 1 Botões; 2 etiquetas; 3 campos; 4 abas; 5 filtros | `components.css`; marcação nas telas e fragmentos próprios quando repetida |
| 6 painéis; 7 linhas de configuração; 8 arquivos/ferramentas; 9 números | `components.css`; `partials/gomut/panel.html`, `file.html` |
| 10 barra superior | `partials/gomut/member_header.html`, `navigation.js` |
| 11 lateral do administrador | `partials/gomut/admin_sidebar.html`, `admin.css`, etapa posterior |
| 12 menu suspenso | `partials/gomut/profile_menu.html`, `navigation.js` |
| 13 janelas | `partials/gomut/course_dialog.html`, `course-dialog.js` |
| 14 avisos rápidos | `partials/gomut/messages.html`, `navigation.js`; somente resultados reais |
| 15 avatar | `partials/gomut/avatar.html` |
| 16 progresso | `partials/gomut/progress.html` |
| 17 capa; 18 cartões | `partials/gomut/cover.html`, `course_card.html` |
| 19 cabeçalho; 20 tabela | `components.css`; tabela aplicada na migração do painel |
| 21 módulos expansíveis | `partials/gomut/module_list.html`, `aluno.js` |
| 22 estado vazio | `partials/gomut/empty.html` |
| 23 aba Básico | `admin.css`, `templates/painel/course_edit.html`, etapa posterior |
| 24 foco/seleção | `base.css`; validação de todos os componentes usados |
| Indicação adicional autorizada | `partials/gomut/backend_pending.html` reutilizando etiqueta/alerta existente e texto “Necessita de backend” |

Não criar todos os fragmentos antecipadamente se uma peça só for usada em uma tela. Os destinos nomeiam a responsabilidade, sem exigir abstração de toda tag HTML.

## Telas, rotas e comportamento

| Tela | Rota | Demonstração |
|---|---|---|
| Login | `/login/` | Autenticação real e redirecionamento conforme papel |
| Ativação | `/primeiro-acesso/` | Fluxo existente por código, preservado; fora da reformulação visual imediata |
| Início | `/dashboard/` | Dois cursos e continuação com dados do banco |
| Curso matriculado | `/dashboard/cursos/<slug>/` (nova) | Módulos/aulas e materiais do curso, sem confundir com página pública de venda |
| Janela do curso | Dentro do início, com link para a rota acima | Mesmo conteúdo autorizado; teclado e foco |
| Aula | `/courses/<slug>/lessons/<id>/` | Vimeo real, progresso e anterior/próxima |
| Conta | `/settings/` | Dados já existentes; campos novos marcados como pendentes |
| Certificados | `/certificados/` | Preservar regras por curso existentes; não impor certificado único de mentoria |
| Comunidade | `/community/` | Publicações/respostas existentes; curtir e recursos novos pendentes |
| Ao vivo | `/ao-vivo/` | Links existentes; agenda individual/lembretes pendentes |
| Trilhas, favoritos, ajuda, avisos e quiz | Áreas visuais correspondentes, se incluídas na demonstração | Indicação explícita; sem criar cadastro simulado de chamados, respostas de quiz ou leitura de avisos |
| Área administrativa | `/painel/` e rotas existentes | Continua funcional, migração visual posterior |

Início adaptado ao catálogo pequeno: mostrar cursos e continuação; não criar dezenas de temas fictícios para preencher fileiras. Manter acesso independente: aluno do curso A não ganha curso B.

### Recursos pendentes identificados

Quiz; curtidas; favoritos; trilhas como entidade; avisos persistentes; preferências de notificações sem persistência; central de chamados; minutos/seqüência de estudo; agenda de encontros individualizados; lembretes; liberação programada por aula. Indicadores só serão mostrados como reais se houver dado correspondente no backend. Não rotular como pendente o que já funciona: matrícula, progresso, download existente, comunidades e reprodução Vimeo.

## Execução em entregas verificáveis

### Task 1: Fundamentos visuais sem afetar telas antigas

- [ ] Criar tokens, fontes, ícones e nova base com os destinos indicados.
- [ ] Separar o CSS normativo compartilhado das composições; manter valores e registrar mudanças de seletores necessárias ao Django.
- [ ] Conferir todos os tokens de cada contexto contra o JSON e os aliases contra o CSS.
- [ ] Verificar no navegador fontes carregadas, foco, contraste dos contextos e ausência de CSS legado na nova base.

### Task 2: Login real e preparação da demonstração

- [ ] Cobrir login válido/inválido, aluno/admin, ativação e ausência de promoção do cadastro público. Confirmar falha dos testes novos antes de alterar o fluxo.
- [ ] Adaptar login ao handoff sem login simulado e validar destino de `next` antes do redirecionamento.
- [ ] Preparar dois cursos fictícios, módulos e aulas, conta de demonstração e períodos de acesso sem apagar dados existentes; execução explícita e idempotente.
- [ ] Verificar `python manage.py test users.test_login_redesign users.test_handoff_phase2 users.test_first_access`.
- [ ] Conferir login em 1440/390px e funcionamento por teclado.

### Task 3: Início, cursos e entrada no curso

- [ ] Cobrir duas matrículas, uma matrícula, nenhuma matrícula, curso vencido, tentativa de outro curso e papel administrador. Ver os testes novos falharem.
- [ ] Adaptar seletores, views e templates; criar detalhe autenticado; apresentar janela do curso com alternativa de navegação sem JavaScript.
- [ ] Preservar rótulos aplicáveis do protótipo. Textos que pressupõem assinatura única/mentoria não devem afirmar acesso a todos os cursos; registrar ajuste textual necessário ao modelo de dois cursos.
- [ ] Excluir Top 10 e evitar fileiras vazias; incluir indicação dos controles pendentes.
- [ ] Verificar testes de acesso, rotas e progresso com `python manage.py test courses.test_member_redesign courses.test_access_periods`.
- [ ] Conferir início e detalhe em 1440/390px, depois 1280/1024/900/768px.

### Task 4: Aula com Vimeo e estados pendentes

- [ ] Cobrir preservação de acesso, material do curso correto e conclusão idempotente. Ver falha dos testes novos antes da mudança.
- [ ] Adaptar a aula mantendo iframe/SDK e o backend de progresso; anterior/próxima limitadas ao curso autorizado.
- [ ] Exibir PDF real quando existente; aba Quiz marcada como pendente, sem questões que aparentem resultado salvo.
- [ ] Testar falha de rede do progresso e indisponibilidade do vídeo; não inventar reprodução.
- [ ] Verificar `python manage.py test courses.tests courses.test_architecture courses.test_member_redesign` e assistir a um trecho do Vimeo no navegador quando houver URL válida disponível.

### Task 5: Controle manual dos períodos — próxima entrega funcional

- [ ] Criar `painel/forms.py:AccessPeriodForm`, serviço em `courses/services.py` e seção em `templates/painel/students.html`, usando a rota atual de alunos.
- [ ] Formulário: aluno, curso, início e último dia quitado inclusivos; sem invocar gateway. Registrar concessão com origem manual, referência única e administrador responsável.
- [ ] Novos períodos vencidos não devem reabrir o curso; alterações conflitantes/sobrepostas precisam de revisão e não devem sobrescrever histórico silenciosamente.
- [ ] Validar data final >= inicial; converter último dia inclusivo para fim exclusivo; impedir alterações por aluno. Mostrar tolerância separadamente.
- [ ] Cobrir limites de datas, dois cursos com datas diferentes, duplo envio e ausência de chamadas Asaas em `painel/test_access_period_management.py` antes da implementação.
- [ ] Preservar importação em lote e códigos de primeiro acesso existentes. Alunos reais só serão importados quando os dados chegarem.

### Task 6: Conferência e roteiro para o médico

- [ ] Executar `python manage.py check` e a suíte Django após as mudanças de comportamento; não afirmar resultados antes de ler a saída.
- [ ] Comparar com screenshots do handoff em 1440/390px; conferir as demais larguras e medidas computadas, sem overflow horizontal.
- [ ] Verificar Chrome/Edge/Firefox/Opera onde disponíveis e declarar quais faltaram; não instalar navegadores silenciosamente.
- [ ] Roteiro: abrir login → entrar como aluno → ver dois cursos → abrir curso → navegar módulos → assistir aula → marcar conclusão → confirmar progresso → sair.
- [ ] Registrar no relatório os ajustes autorizados (Top 10 removido, catálogo de dois cursos, recursos pendentes e prioridade do aluno), outras divergências e limitações externas.

## Pontos que não impedem iniciar

- Logo vetorial original: não encontrado, mas o arquivo PNG existe e pode ser usado.
- Novas capas e PDFs: limites de imagem ainda pendentes; manter suporte existente sem novos comportamentos de recorte.
- Identidade final e conteúdo do médico: dados fictícios autorizados nesta etapa.
- Hospedagem: decisão separada da demonstração local.

## Decisões ainda necessárias apenas nos pontos afetados

- Nome da marca do cliente e dos dois cursos quando sairmos dos dados fictícios.
- Conteúdo visual dos links de recuperação/ativação no novo login, se forem incluídos no cartão fechado.
- URL Vimeo disponível e permitida no domínio de demonstração, se a base atual não oferecer vídeo reproduzível.
- Certificação: regras reais futuras; preservar a regra atual por curso até confirmação, sem adotar a duração fictícia da mentoria.
- Semântica de correção retroativa de período manual já concedido; não editar/apagar histórico até esse fluxo ser definido.

## Hospedagem — recomendação separada, sem publicação nesta etapa

Para manter a stack atual, executar Django e o arquivo SQLite no mesmo servidor da equipe, com disco persistente e estratégia de backup/restauração. Usar domínio próprio na Cloudflare com DNS/proxy ou Tunnel apontando à aplicação. Não tratar SQLite como serviço remoto nem compartilhar o arquivo de banco pela rede.

A Cloudflare já documenta suporte a Django em Python Workers, mas isso não comprova compatibilidade de toda esta instalação com SQLite local, uploads e bibliotecas. Adaptação ao Workers não faz parte da demonstração.

Fontes oficiais consultadas em 16/11/2026:
- https://developers.cloudflare.com/workers/languages/python/packages/django/
- https://developers.cloudflare.com/tunnel/concepts/routing/

## Aprovação exigida pelo pacote

`docs/handoff-design/01-regras-inviolaveis.md`, regra 32: “A implementação só começa depois que o mapeamento dos tokens para a stack estiver aprovado.”

O plano acima reúne o mapeamento e as exceções autorizadas pelo usuário. A aprovação pendente é deste plano concreto, sem necessidade de nova decisão sobre framework ou arquitetura.

## Fechamento da execução

- Fundamentos, login real, demonstração separada, cursos, aula e controle manual de períodos implementados.
- Página de progresso usa conclusões reais; métricas sem backend permanecem identificadas.
- Base de layout `base_membros.html` nova: as telas secundárias legadas foram preservadas para evitar migração parcial de CSS.
- Intervalos manuais só acrescentam histórico sem sobreposição; edição retroativa permanece pendente.
- Vimeo: iframe e controles carregam, mas reprodução de mídia externa não foi confirmada automaticamente; homologação de streaming pendente.
- Verificação final e roteiro em `docs/area-aluno-demonstracao.md`.
