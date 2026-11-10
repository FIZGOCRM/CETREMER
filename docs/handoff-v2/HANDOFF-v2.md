# Handoff v2 · Painel administrativo v2 e Área do aluno v2

Para o agente que vai implementar. Este documento é a continuação do `HANDOFF.md` (v1), que você já implementou. Leia este inteiro antes de escrever código. Nada aqui precisa ser adivinhado: cada classe, rota, texto, aviso e destino de redirecionamento está escrito. Quando algo não estiver aqui, pare e pergunte em vez de inventar.

Stack (não muda): Django 4.2, Django Templates, CSS puro, JS vanilla, SQLite em dev, sem build de assets e sem framework JS. Única dependência de front nova: nenhuma. O SDK do Vimeo já era usado no v1.

---

## 0. Como usar este pacote

### 0.1 Três fontes, uma ordem de autoridade

1. **Este texto manda.** Rotas, modelos, regras, textos e comportamento.
2. **`referencia-v2/*.dc.html`** dão os valores visuais exatos e todos os textos das telas. São protótipos interativos do canvas: o HTML de dentro de `<x-dc>` mostra a estrutura e os `style=""` mostram os valores; o `<script type="text/x-dc">` no fim de cada arquivo mostra **quais estados existem e quais textos mudam em cada estado** (leia para entender o comportamento; não copie o código).
3. **`capturas/*.png`** servem para conferir o resultado lado a lado. Cada tela tem a captura padrão e, quando há interação, capturas dos estados (`*-estado-*.png`).

Se uma fonte contradisser a outra, vale a de número menor. As poucas diferenças conhecidas entre o protótipo e o que deve ser construído estão listadas na seção 11 ("Onde o protótipo simplifica").

### 0.2 O que vem no pacote

| Caminho no pacote | O que é | Para onde vai |
| --- | --- | --- |
| `static/css/cetremer-v2.css` | Componentes novos (seções 30 a 50). Não altera nada do v1. | **Colar no fim** de `static/css/cetremer.css` |
| `static/js/ui.js` | Padrões de interação: toast, painel lateral, menus, abas, barra de alterações, Ctrl K, seleção em massa, autosave, criação rápida, switch, mostrar senha, dispensar com Desfazer. | `static/js/ui.js` (novo) |
| `static/js/player.js` | Página da aula: concluir com Desfazer, retomar vídeo, concluir em 90%, próxima aula, modo foco, atalhos. **Substitui `aluno.js`.** | `static/js/player.js` (novo); apagar `aluno.js` na fase A3 |
| `templates/base_core.html` | v1 + `ui.js`, `{% csrf_token %}` global e toasts. | substitui |
| `templates/base_aluno.html` | Novo topo (caminho, busca, sino, menu da conta), menu v2, barra inferior no celular, Ctrl K, diálogo "Sair sem salvar?". | substitui |
| `templates/base_admin.html` | Novo topo (caminho, busca, Criar), menu agrupado, diálogos globais. | substitui |
| `templates/partials/*.html` | `icon.html` (v1 + 17 ícones), `toasts.html`, `leave_dialog.html`, `cmdk.html`, `cmdk_results.html`, `sidebar_aluno_v2.html`, `sidebar_admin_v2.html`, `bottom_nav.html` | `templates/partials/` |
| `templates/painel/_dialog_*.html` | Diálogos "Novo curso" e "Matricular aluno" | `templates/painel/` |
| `python/core/ajax.py` | `wants_json`, `json_ok`, `json_errors`, `json_error` | `core/ajax.py` |
| `python/core/toasts.py` | `toast(request, texto, undo_url=, action=)` | `core/toasts.py` |
| `python/core/templatetags/ui.py` | `toast_meta`, filtros `plural_pt` e `falta_pt` | `core/templatetags/ui.py` |
| `python/core/context_processors_v2.py` | `user_shell`, `student_shell`, `painel_shell` | juntar em `core/context_processors.py` |
| `referencia-v2/` | 21 protótipos: `AlunoV2*.dc.html` (9) e `AdminV2*.dc.html` (12) | não copiar para o repositório |
| `capturas/` | 54 PNG: cada tela e cada estado importante (lista em `capturas/INDICE.md`) | não copiar |
| `demo/componentes.html` | Página estática que usa só `cetremer.css` + `cetremer-v2.css` + `ui.js` com todos os componentes novos funcionando. Abra com `python -m http.server` na pasta do pacote (ver `LEIA-ME.md`). | não copiar |

### 0.3 Antes de começar

1. Leia `docs/redesign-relatorio.md` (o relatório que você escreveu no v1) e confirme que as fases 0 a 7 do v1 estão no `main` e os testes passam.
2. Crie a branch `redesign-v2` a partir do `main`.
3. Rode `python manage.py test` e anote o total de testes. Ele só pode subir.
4. Implemente por fases (seção 12). Um commit por fase, com a lista do que mudou. Não junte fases.

---

## 1. Regras inegociáveis (somam às do v1)

Todas as regras da seção 1 do `HANDOFF.md` continuam valendo (um único CSS, sem `style=""`, cores só por token, ícones pelo partial, pt-BR, acessibilidade, testes). Novas:

1. **Toda ação tem aviso e destino.** A tabela da seção 4 é obrigatória. Nenhuma ação pode terminar em página recarregada sem aviso, nem em tela diferente da tabela.
2. **Funciona sem JS, melhora com JS.** Todo formulário é um `<form method="post">` normal que a view responde com `redirect` + `toast(...)`. O `ui.js` intercepta os que têm `data-async` e a mesma view responde JSON quando `wants_json(request)`. Nunca crie uma ação que só existe em JS.
3. **Nunca `alert()`, `confirm()` ou `prompt()` do navegador.** Confirmação é sempre `<dialog>` nativo, no nível de risco da seção 4.3.
4. **Mensagens do Django viram toast.** Use `core.toasts.toast()` em vez de `messages.success()`. O `partials/messages.html` sai dos layouts logados (continua nas páginas públicas e de login).
5. **Dinheiro nunca em `<input type="number">`.** Campo de texto com prefixo R$ e vírgula, convertido no form (`DecimalField` com `localize=True` ou `clean_price` que troca `.`/`,`). É a causa do bug que zera o preço do curso ao salvar (seção 10, item 1).
6. **Plural sempre certo.** Use `{{ n|plural_pt:"aula,aulas" }}` e `{{ n|falta_pt }}`. Proibido `aula{{ n|pluralize }}` concatenado com número em texto novo, e proibido "1 aulas".
7. **Saudação e nome:** nunca o `username` (ex.: "jane_student"). Use `user_first_name` do context processor.
8. **Horário:** sempre `America/Campo_Grande` no servidor; nas telas de aula ao vivo escreva "(horário de Brasília)" junto do horário convertido para `America/Sao_Paulo` (`{% timezone "America/Sao_Paulo" %}`).
9. **Acessibilidade dos componentes novos:** abas com `role=tablist/tab/tabpanel` e `aria-selected`; switch com `role=switch` e `aria-checked`; menus com `aria-expanded`; painel lateral e diálogos são `<dialog>` com título ligado por `aria-labelledby`; toast tem `role=status` (erro: `role=alert`). Tudo já está nos contratos do `ui.js`; não troque por `div`.
10. **Sem dado inventado.** Os protótipos usam nomes de exemplo (Jane Student, Dr. Rafael Souza, pedidos #1042). Na implementação tudo vem do banco; vazio mostra o estado vazio da tela.

---

## 2. Instalação dos arquivos do pacote (fase A0)

1. Colar `static/css/cetremer-v2.css` no fim de `static/css/cetremer.css` (depois da seção 28 e da 29 "Extras", se você criou). Não renomear classes.
2. Copiar `static/js/ui.js` e `static/js/player.js`.
3. Substituir `templates/base_core.html`, `base_aluno.html`, `base_admin.html` pelos do pacote. Conferir com `git diff` que nenhum bloco usado pelas páginas sumiu: os blocos do aluno são `crumbs`, `page_title`, `page_class`, `content`, `footer`; os do admin são `admin_title`, `crumbs`, `topbar_actions`, `page_class`, `content`. O bloco `topbar_eyebrow`/`topbar_class` do admin v1 deixa de existir: troque nas páginas por `crumbs`.
4. Copiar os partials e os dois diálogos do painel.
5. Copiar `core/ajax.py`, `core/toasts.py`, `core/templatetags/ui.py`; juntar as funções de `context_processors_v2.py` em `core/context_processors.py` e registrar as três.
6. Criar já as rotas citadas pelos layouts, mesmo com view provisória (lição do v1): `search`, `notifications_read_all`, `notification_open`, `course_home`, `painel:search`, `painel:course_create`, `painel:student_enroll`, `painel:course_content`, `painel:course_sales`, `painel:course_settings`, `painel:student_detail`.
7. Rodar o servidor e abrir cada página logada: nada pode quebrar. Commit "v2 fase A0: base e componentes".

---

## 3. Layouts e contexto global

### 3.1 O que muda nos layouts

- **Topo do aluno** (todas as telas com `base_aluno.html`): à esquerda o caminho (`nav.crumbs`) e o título (`h1.topbar__title`); à direita, nesta ordem: botão de busca (`button.topbar-search` com "Buscar aula, curso ou dúvida" e `Ctrl K`), sino (`.popover` com até 8 avisos) e o botão da conta (`button.user-btn`: avatar, primeiro nome e seta) que abre o menu com Minha conta, Pedidos e acessos, Ajuda pelo WhatsApp e Sair. É o mesmo topo em todas as telas. Isso corrige a inconsistência do v1 (e-mail e Sair no Início, só avatar nas outras, só Sair em Minha conta).
- **Menu lateral do aluno** (`sidebar_aluno_v2.html`): Início, Aulas ao vivo (com selo do próximo encontro: "Qui", "Hoje" ou "Ao vivo"), Comunidade (número de respostas não lidas), Certificados (número de certificados prontos para emitir), Minha conta. Embaixo: card "Seu progresso" (aulas concluídas de todas as matrículas) e o botão "Ajuda pelo WhatsApp". O item "Meus cursos" do v1 vira "Início" (a lista de cursos está no Início).
- **Celular (até 720 px):** o menu lateral some e aparece a barra inferior (`bottom_nav.html`) com Início, Ao vivo, Comunidade, Certificados e Conta. O botão de busca vira só o ícone. Toasts ficam centralizados acima da barra.
- **Topo do admin:** só o caminho à esquerda; à direita busca ("Buscar aluno, curso ou pedido"), ações da página (`topbar_actions`, ex.: "Ver como aluno") e o botão "Criar" com o menu Novo curso, Matricular aluno, Importar alunos. O `<h1>` do admin passa para dentro do conteúdo.
- **Menu lateral do admin** (`sidebar_admin_v2.html`): grupos "Visão geral" (Início), "Conteúdo" (Cursos), "Pessoas" (Alunos, Comunidade com número de dúvidas sem resposta), "Vendas" (Pedidos, só para quem pode ver pedidos); no rodapé Configurações e o cartão do usuário com menu (Ver como aluno, Sair).
- **Toasts:** `base_core.html` inclui `partials/toasts.html`, que cria a pilha e converte as mensagens do Django.

### 3.2 Context processors (arquivo do pacote)

| Função | Quando roda | Entrega |
| --- | --- | --- |
| `user_shell` | usuário logado | `user_full_name`, `user_first_name` (nome que o aluno escolheu ou primeiro nome), `user_initials`, `user_avatar_url` |
| `student_shell` | logado e fora do namespace `painel` | `notifications` (8 mais recentes), `unread_count`, `live_badge` (`{label, is_live}` ou `None`), `community_unread`, `certificates_ready`, `lessons_done`, `lessons_total`, `lessons_pct` |
| `painel_shell` | namespace `painel` | `pending_questions`, `painel_categories`, `painel_courses`, `perms_painel` (`orders`, `settings`, `content`, `community`) |

Os trechos marcados `# AJUSTAR` dependem dos nomes reais dos seus modelos. Ajuste e mantenha as consultas agregadas (no máximo 8 queries por página no layout do aluno; conferir com `django-debug-toolbar` ou `assertNumQueries` no teste do Início).

---

## 4. Avisos, confirmações e destino de cada ação

### 4.1 Regras gerais

- **Salvar** mantém você onde está (mesma aba e mesma rolagem). **Criar** leva para dentro do que foi criado. **Excluir ou arquivar** volta para a lista.
- **Toast:** canto inferior direito, empilhados, somem em 5 s; 8 s quando têm Desfazer; **erro não some sozinho**. Passar o mouse pausa o tempo.
- Abrir um item em painel lateral **nunca recarrega a página** (usa `?param=id` na URL para poder compartilhar o link e voltar).
- Ação que demora mostra o botão ocupado (`.is-busy`) e linhas fantasma (`.sk`) no lugar do conteúdo. Nunca tela em branco.

### 4.2 Tabela da área do aluno

| Ação | O que o aluno vê | Para onde vai | Se der erro |
| --- | --- | --- | --- |
| Marcar aula concluída (botão) | Toast "Aula concluída. Progresso salvo" com Desfazer. Faixa verde "Aula concluída · Próxima: {título}" com "Ficar nesta aula" e "Ir para a próxima aula". Topo, lista lateral, contagem do módulo e card do certificado atualizam na hora. | Fica na aula. | Toast de erro "Não foi possível salvar seu progresso. Confira a conexão e tente de novo." e nada muda. |
| Desmarcar aula (clicar em "Concluída") | Toast "Aula desmarcada. Seu progresso voltou para N%" com Desfazer. | Fica na aula. | Igual acima. |
| Vídeo passa de 90% | Mesmo toast de aula concluída (uma vez só por aula). | Fica. | Silencioso; tenta de novo no próximo `timeupdate`. |
| Vídeo termina | Faixa da próxima aula (se ainda não apareceu). Não pula sozinho. | Fica. | - |
| Concluir a última aula que faltava | Janela "Você concluiu o {curso}" com "Rever aulas" e "Emitir certificado". | "Emitir certificado" leva a `certificates?emitir=<slug>` com o painel de emissão já aberto. | - |
| Publicar dúvida dentro da aula | Toast "Dúvida publicada. Avisaremos por e-mail quando responderem". A pergunta aparece no topo da aba Dúvidas. | Fica na aula, aba Dúvidas (`?aba=duvidas`). | Erro embaixo do campo. |
| Nova pergunta na comunidade | Toast "Pergunta publicada. Avisaremos por e-mail quando responderem" com Desfazer (apaga). Item novo no topo, destacado 2 s. | Fica na lista, filtros limpos. | Painel continua aberto com erro no campo. |
| Responder numa conversa | Toast "Resposta publicada". | Fica na conversa. | Texto continua no campo. |
| "Sim, resolveu" | Toast "Obrigado! A dúvida foi marcada como resolvida" com Desfazer. Botão vira "Marcada como resolvida". | Fica. | Toast de erro. |
| Dispensar item de "Próximos passos" | Item some. Toast "Aviso dispensado" com Desfazer. | Fica. | Item volta, toast de erro. |
| Emitir certificado | Toast "Certificado emitido. Enviamos o link para seu e-mail". O card vira "Emitido". | Fica em Certificados. | Painel continua aberto com erro no campo (CPF inválido). |
| Copiar link de verificação | Toast "Link de verificação copiado". | Fica. | - |
| Salvar qualquer seção de Minha conta | Barra de alterações some. Toast "Alterações salvas". | Fica na mesma seção. | Barra continua, resumo "Corrija N campos para salvar." no topo do card e foco no primeiro campo. |
| Atualizar senha | Toast "Senha atualizada. Use a nova senha no próximo acesso". Campos limpos. | Fica em Senha e acesso. | Erros embaixo dos campos. |
| Sair dos outros aparelhos | Toast "Você saiu dos outros aparelhos. Este continua conectado". | Fica. | Toast de erro. |
| Clicar num link com alterações não salvas | Diálogo "Sair sem salvar?" com "Descartar e sair" e "Salvar e sair". | Conforme a escolha. | - |
| Marcar avisos como lidos | Toast "Avisos marcados como lidos". Pontos azuis e contador somem. | Fica. | Toast de erro. |
| Clicar num aviso do sino | Aviso marcado como lido. | URL do aviso. | - |
| Entrar na aula ao vivo | Abre o Google Meet em nova aba. | A área continua aberta. | - |
| Login | Nenhum aviso. | `next` se houver; senão Início. | Erro no formulário (v1). |
| Sair | Toast "Você saiu da sua conta" na tela de login. | Login. | - |

### 4.3 Confirmações por nível de risco (aluno e admin)

| Nível | Quando | Como |
| --- | --- | --- |
| Reversível | Marcar aula, dispensar aviso, excluir aula no admin, ocultar dúvida, arquivar dúvida | **Sem diálogo.** Faz na hora e oferece Desfazer no toast. |
| Afeta pessoas | Remover acesso de aluno, zerar progresso, reembolsar, remover pessoa da equipe | `<dialog class="dialog dialog--warn">` com `dialog__eyebrow` "Afeta alunos", título em pergunta ("Remover acesso ao BLS?"), texto dizendo **quem** é afetado e o que acontece com os dados, checkbox opcional "Avisar o aluno por e-mail", botões "Cancelar" e a ação com o verbo ("Remover acesso"). |
| Irreversível ou em massa | Arquivar curso, excluir curso, ação em massa acima de 20 alunos | `<dialog class="dialog dialog--danger">` com eyebrow "Alto risco" e campo "Digite {SIGLA} para confirmar" (`data-confirm-text`); o botão `btn--danger` só habilita com o texto certo. |

### 4.4 Tabela do painel administrativo

| Ação | Depois da ação | Aviso | Se der erro |
| --- | --- | --- | --- |
| Criar curso (diálogo) | Abre o curso na aba Conteúdo, já com o 1º módulo "Módulo 1" pronto para receber aulas | "Curso criado como rascunho" | Diálogo continua aberto com o erro no campo |
| Salvar curso ou seção | Mesma aba, mesma rolagem | Barra some; "Alterações salvas" | Barra continua; resumo no topo e foco no 1º campo |
| Criar aula (Enter no título) | Aula entra no fim do módulo como rascunho e o painel da aula abre | Linha nova destacada 2 s (`.is-new`) | Campo fica vermelho com a mensagem |
| Salvar aula | Painel lateral fecha; a linha atualiza no lugar | "Aula salva" | Painel continua aberto |
| Reordenar | Nada muda de página | "Ordem salva" (discreto, 3 s) | Item volta ao lugar e toast de erro com "Tentar de novo" |
| Excluir aula | Fica na grade; a linha some | "Aula excluída" com Desfazer (8 s) | Toast de erro |
| Arquivar curso | Volta para Cursos, aba Arquivados | "Curso arquivado" com Desfazer | Diálogo continua aberto |
| Matricular aluno | Abre a ficha do aluno | "Curso liberado. E-mail enviado para {email}" com ação "Ver aluno" quando você não está na ficha | Diálogo mostra o erro |
| Ação em massa em alunos | Fica na lista; seleção limpa | "12 alunos receberam o BLS" (total real) | Toast diz quantos falharam e oferece "Baixar relatório" |
| Importar alunos | Volta para Alunos com o filtro "Importados hoje" | "N novos, M já existiam e receberam os cursos, K ignorados" | Fica no passo Revisar com as linhas problemáticas marcadas |
| Responder dúvida | Abre a próxima sem resposta (se "Ir para a próxima sem resposta" estiver marcado) | Contador do menu diminui na hora; "Resposta publicada" | Texto continua no campo |
| Ocultar dúvida | Some da lista | "Dúvida ocultada" com Desfazer | Toast de erro |
| Reenviar acesso | Fica | "E-mail de acesso enviado para {email}" | Toast de erro |
| Sair com alterações não salvas | Pergunta antes | Diálogo "Sair sem salvar?" | - |

---

## 5. Contratos de JS (resumo; o detalhe está no cabeçalho de cada arquivo)

| Recurso | Atributos no HTML | Resposta da view |
| --- | --- | --- |
| Toast pelo servidor | `toast(request, "Texto", undo_url=..., action=("Rótulo", url))` | - |
| Toast pelo JS | `CTM.toast("Texto", {kind, undo, action})` | - |
| Formulário assíncrono | `<form method="post" data-async>` | `json_ok(toast=, undo_url=, redirect=, reload=, remove=, replace=, counts=)` ou `json_errors(form)` (400) |
| Menu e sino | `.popover[data-popover]` > `[data-popover-toggle]` + `[data-popover-panel]`; `[data-notif-read-all="url"]` | `json_ok()` |
| Painel lateral | `<dialog class="drawer" id>`; abrir com `[data-drawer-open]` ou `a[href="?x=1"][data-drawer-url][data-drawer-target][data-drawer-param][data-drawer-value]`; `data-autoopen="param"` quando a URL já tem o parâmetro; fechar com `[data-drawer-close]` | Para `data-drawer-url`: HTML parcial (só o miolo do drawer) |
| Confirmação digitando | `input[data-confirm-text="BLS"]` + `button[data-confirm-submit][disabled]` | - |
| Alterações não salvas | `form[data-dirty-form][data-dirtybar="id"]`, campos com `data-dirty-label`, `.dirtybar#id` com `[data-dirty-msg]` e `[data-dirty-discard]` | Normal do form (assíncrono ou não) |
| Abas | `[role=tablist][data-tabs][data-tabs-param="aba"]` > `button[role=tab][data-tab][aria-controls]` | Servidor marca a aba inicial pelo `?aba=` |
| Switch | `button.switch[role=switch][aria-checked][data-switch-input="id"]` + `input[type=hidden]` | - |
| Mostrar senha e regras | `[data-reveal="id"]`, `ul.pw-rules[data-pw-rules="id"]` > `li[data-rule=len|mix|diff]` | - |
| Busca Ctrl K | `[data-cmdk-open]`; `dialog.cmdk#cmdk[data-search-url]` | HTML parcial `partials/cmdk_results.html` |
| Seleção em massa | `form[data-bulk][data-bulkbar]`, `[data-bulk-all]`, `[data-bulk-item]`, `.bulkbar#id` com `[data-bulk-count]` e `[data-bulk-clear]` | Normal (POST com `action` e `ids`) |
| Autosave | `textarea[data-autosave-url]` + `[data-autosave-state]` | `json_ok()` |
| Criação rápida | `input[data-inline-create-url]` dentro de `.inline-create` | `json_ok(html=, toast=, open_selector=)` |
| Copiar com aviso | `[data-copy="url"][data-copy-toast="Texto"]` | - |
| Dispensar com Desfazer | `[data-dismiss-url][data-dismiss-target][data-undo-url]` | `json_ok()` nas duas URLs |
| Espelhar texto | `input[data-mirror="#alvo"]` (+ `data-mirror-upper` ou `data-mirror-cpf`) | - |
| Habilitar no horário | `a[aria-disabled=true][data-enable-at="ISO"][data-enabled-href]`, `[data-lock-icon]`, `[data-enable-hint][data-enabled-hint]` | - |
| Sugestões ao digitar | `input[data-suggest-url][data-suggest-box="#id"]` | HTML parcial ou vazio |
| Página da aula | ver seção 7.3 e o cabeçalho de `player.js` | JSON da seção 6.4 |

Teste rápido de todos: abra `demo/componentes.html` direto no navegador.

---

## 6. Backend

### 6.1 Modelos novos e campos novos

Migrations reversíveis, uma por app. Atualize o seed (`data_dump.json`) ao fim da fase que mexer em modelo, com dados coerentes para todas as telas (ver 6.6).

**`users.Notification` (novo)**
```python
class Notification(models.Model):
    KIND = [("answer", "Resposta"), ("live", "Aula ao vivo"), ("certificate", "Certificado"),
            ("module", "Módulo liberado"), ("access", "Acesso")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=20, choices=KIND)
    title = models.CharField(max_length=120)      # "O instrutor respondeu sua dúvida"
    meta = models.CharField(max_length=160, blank=True)  # "BLS · Profundidade da compressão"
    url = models.CharField(max_length=300)        # caminho interno, ex. /community/?duvida=12
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "read_at"])]
```
Quem cria (em `users/notify.py`, função `notify(user, kind, title, meta, url, email=True)` que também manda e-mail se a preferência do aluno permitir):
- comentário de staff/instrutor numa dúvida → para o autor: "O instrutor respondeu sua dúvida", meta "{curso} · {título da dúvida}", url `/community/?duvida=<id>`;
- aluno conclui a última aula de um curso (e ainda não tem certificado) → "Seu certificado está pronto para emitir", meta "{curso} · confira nome e CPF", url `/certificados/?emitir=<slug>`;
- comando `python manage.py live_reminders` (rodar a cada 15 min pelo agendador do servidor): encontro que começa entre 60 e 75 min → "Aula ao vivo hoje às {HH:MM}", meta "{curso} · {título do encontro}", url `/ao-vivo/`; marcar `LiveSession.reminder_sent_at` para não repetir;
- comando `python manage.py release_modules` (diário): módulo programado liberado → "Novo módulo liberado", meta "{curso} · {módulo}".

**`users.StudentProfile` (campos novos)**
| Campo | Tipo | Uso |
| --- | --- | --- |
| `display_name` | `CharField(max_length=40, blank=True)` | "Como prefere ser chamada(o)"; saudação e comunidade |
| `whatsapp` | `CharField(max_length=20, blank=True)` | só dígitos |
| `photo` | `ImageField(upload_to="avatars/", blank=True)` | se o v1 usa `user.avatar`, mantenha o do v1 e ajuste `user_shell` |
| `notify_answers`, `notify_live`, `notify_certificate` | `BooleanField(default=True)` | Avisos por e-mail |
| `notify_marketing` | `BooleanField(default=False)` | "Novos cursos e condições especiais" |
| `dismissed_steps` | `JSONField(default=list, blank=True)` | chaves dispensadas em "Próximos passos" |

**Progresso da aula (modelo existente que o `toggle_progress` grava; confirme o nome com `grep -n "class .*Progress" courses/models.py`)**
- `position_seconds = PositiveIntegerField(default=0)`: última posição do vídeo.
- `updated_at = DateTimeField(auto_now=True)`: para "visto há 2 dias" e "Continue de onde parou".
- O registro passa a existir também para aula **não concluída** (criado na primeira posição salva). `is_completed` (ou o campo equivalente) diferencia. Ajuste todas as contagens para filtrar por concluída.

**`courses.LiveSession` (novo; substitui o embed da Agenda do Google na tela do aluno)**
```python
class LiveSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="live_sessions")
    title = models.CharField(max_length=160)            # "Encontro 3: casos de sala vermelha"
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    host_name = models.CharField(max_length=80, blank=True)   # "Dr. Rafael Souza"
    meet_url = models.URLField(blank=True)              # vazio = usa course.live_meet_url
    recording_url = models.URLField(blank=True)         # Vimeo
    recording_until = models.DateField(null=True, blank=True)  # padrão: starts_at + 30 dias
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ["starts_at"]

    @property
    def join_url(self): return self.meet_url or self.course.live_meet_url
    def state(self, now=None):
        now = now or timezone.now()
        if now > self.ends_at: return "ended"
        if now >= self.starts_at: return "live"
        if now >= self.starts_at - timedelta(minutes=15): return "soon"
        return "scheduled"
```
O campo `Course.live_calendar_url` do v1 fica no banco, mas sai das telas (seção 8.5).

**`courses.Course` (campos novos)**
| Campo | Tipo | Uso |
| --- | --- | --- |
| `status` | `CharField(choices=[("draft","Rascunho"),("published","Publicado"),("archived","Arquivado")], default="draft")` | substitui o booleano de publicado do v1 (data migration: publicado → `published`, senão `draft`). Manter uma propriedade com o nome antigo para não quebrar código. |
| `tagline` | `CharField(max_length=160, blank=True)` | "Chamada curta" da página de venda e dos cards |
| `access_months` | `PositiveSmallIntegerField(null=True, blank=True, choices=[(None,"Vitalício"),(6,...),(12,...),(24,...)])` | prazo de acesso |
| `release_mode` | `CharField(choices=[("all","Tudo na matrícula"),("scheduled","Programada por módulo")], default="all")` | liberação do conteúdo |
| `notify_module_release` | `BooleanField(default=True)` | "Avisar o aluno por e-mail quando um módulo for liberado" |
| `certificate_enabled` | `BooleanField(default=True)` | "Emitir certificado neste curso" |
| `archived_at` | `DateTimeField(null=True, blank=True)` | para "Desfazer" do arquivar |

**`courses.CourseFAQ` (novo):** `course` FK, `question` (160), `answer` (Text), `order`. Substitui o FAQ fixo.

**`courses.CourseSlugRedirect` (novo):** `old_slug`, `course` FK, `created_at`. Ao trocar o slug no painel, grava o antigo; a view pública redireciona (301) por 90 dias.

**`courses.Module` (campos novos):** `release_after_days` (`PositiveSmallIntegerField(null=True, blank=True)`), `release_date` (`DateField(null=True, blank=True)`). Regra de disponibilidade em `Module.is_released_for(enrollment)`: `release_mode == "all"` → sempre; senão pela data ou por `enrollment.created_at + dias`.

**`courses.Lesson` (campos novos):** `status` (`draft`/`published`, mesma estratégia do curso), `is_free_preview` (`BooleanField(default=False)`, "Aula grátis na página de venda"), `deleted_at` (`DateTimeField(null=True)`, exclusão com Desfazer; o manager padrão filtra `deleted_at__isnull=True`; comando `purge_deleted` apaga de vez depois de 7 dias).

**`courses.Enrollment` (campos novos):** `expires_at` (`DateTimeField(null=True, blank=True)`, calculado de `access_months` na criação), `external_ref` (`CharField(max_length=40, blank=True)`, ex. "HP1234" da Hotmart, preenchido na importação quando a coluna existir), `is_active` (`BooleanField(default=True)`, "Remover acesso" desativa sem apagar progresso).

**`courses.Certificate`:** sem campo novo. A emissão deixa de ser automática ao abrir a URL (seção 7.5).

**`community.CommunityPost` (campos novos):** `is_resolved` (aluno marcou "Sim, resolveu"), `is_pinned` (admin "Fixar"), `has_unread_answer` (`BooleanField(default=False)`: vira `True` quando staff comenta; `False` quando o autor abre a conversa), `is_answered_cache` (`BooleanField(default=False)`, atualizado por sinal quando staff comenta; deixa a contagem do menu do painel barata).

**`core.ActivityLog` (novo, para "Atividade recente" do painel e aba Atividade do aluno):** `actor` FK null, `student` FK null, `course` FK null, `verb` (`CharField(60)`: "enrolled", "completed_lesson", "course_updated", "imported", "certificate_issued"), `text` (`CharField(200)` já pronto: "test 1 foi matriculado em Plantão Sem GPT"), `created_at`. Gravar nos pontos onde as ações acontecem (função `log(...)` em `core/activity.py`).

**`users.User` / papéis da equipe:** manter o `role` do v1. Rótulos na tela: superusuário = "Dono"; `ADMIN` = "Administrador" (tudo); `CREATOR` = "Instrutor (conteúdo e comunidade)": edita cursos e responde dúvidas, **não vê** Pedidos nem Configurações (`perms_painel`). Novo campo no perfil de staff: `notify_new_questions` (`BooleanField(default=False)`, "Me avisar por e-mail a cada nova dúvida").

### 6.2 Rotas da área do aluno

| Rota | Nome | Método | Função |
| --- | --- | --- | --- |
| `/dashboard/` | `dashboard` | GET | Início (7.1). `?filtro=todos|andamento|nao_iniciados|concluidos` |
| `/meus-cursos/<slug>/` | `course_home` | GET | Página do curso para quem é aluno (7.2). `?aba=conteudo|materiais|duvidas|ao-vivo` |
| `/courses/<slug>/` | `course_preview` (v1) | GET | Página pública. **Aluno matriculado é redirecionado (302) para `course_home`**, exceto com `?preview=1`. |
| `/courses/<slug>/lessons/<id>/` | `lesson_detail` (v1) | GET | Player (7.3). `?aba=sobre|materiais|duvidas` |
| `/courses/lesson/<id>/toggle/` | `toggle_progress` (v1) | POST | Alterna. Resposta JSON ampliada (6.4) |
| `/courses/lesson/<id>/complete/` | `complete_lesson` (v1) | POST | Idempotente. Mesmo JSON |
| `/courses/lesson/<id>/position/` | `save_position` | POST | `seconds` (int). Grava `position_seconds` e `updated_at`. Resposta `{"ok": true}`. Aceita `sendBeacon` (form-data com `csrfmiddlewaretoken`). |
| `/ao-vivo/` | `live_classes` (v1) | GET | 7.4. `?curso=<slug>` |
| `/ao-vivo/<id>/convite.ics` | `live_session_ics` | GET | Arquivo `.ics` (`text/calendar`), com `DTSTART`/`DTEND` em UTC, `SUMMARY` "{curso} · {título}", `LOCATION` = link do Meet, `DESCRIPTION` com o link. |
| `/certificados/` | `certificates` (v1) | GET | 7.5. `?emitir=<slug>` abre o painel de emissão |
| `/certificados/<slug>/emitir/` | `certificate_issue` | POST | `full_name`, `cpf`, `confirm` (checkbox). Valida, grava no perfil, cria o `Certificate` e manda e-mail com o link. |
| `/community/` | `community` (v1) | GET | 7.6. `?situacao=todas|sem-resposta|respondidas|minhas&curso=<slug>|geral&q=&duvida=<id>&nova=1` |
| `/community/nova/` | `community_create` | POST | `course` (id ou vazio = geral), `lesson` (opcional), `title`, `content` |
| `/community/<id>/responder/` | `community_reply` | POST | `content` |
| `/community/<id>/resolvida/` | `community_resolve` | POST | só o autor; alterna `is_resolved` |
| `/community/<id>/apagar/` | `community_delete_own` | POST | só o autor e só sem respostas (Desfazer do toast) |
| `/community/sugestoes/` | `community_suggest` | GET | `?q=` (título digitado). Devolve HTML parcial com até 3 links de dúvidas parecidas (`icontains` por palavra com 4+ letras). |
| `/settings/` | `settings` (v1) | GET, POST | 7.7. `?secao=perfil|certificado|senha|pedidos|avisos`. Cada seção é um `form` com `name="section"` oculto. |
| `/settings/sair-outros/` | `logout_others` | POST | `update_session_auth_hash` + apagar as outras sessões do usuário |
| `/busca/` | `search` | GET | `?q=` → `partials/cmdk_results.html`. Grupos: Aulas (só cursos matriculados, `title__icontains`), Dúvidas (não ocultas, de cursos matriculados ou gerais), Materiais. Até 5 por grupo. Sem `q`: "Continuar" (a aula do Continue de onde parou) e "Atalhos" (Aulas ao vivo, Certificados, Minha conta). |
| `/avisos/lidos/` | `notifications_read_all` | POST | marca todos como lidos |
| `/avisos/<id>/` | `notification_open` | GET | marca como lido e redireciona para `url` (só do próprio usuário; 404 se não for) |
| `/passos/<chave>/dispensar/` e `/passos/<chave>/restaurar/` | `step_dismiss`, `step_restore` | POST | inclui/remove a chave em `dismissed_steps` |

### 6.3 Rotas do painel (namespace `painel`, todas com `@painel_required`)

| Rota | Nome | Método | Função |
| --- | --- | --- | --- |
| `/painel/` | `dashboard` | GET | 8.1. `?periodo=7|30|90` |
| `/painel/busca/` | `search` | GET | Parcial. Grupos: Alunos (nome, e-mail, CPF só dígitos), Cursos, Aulas, Pedidos (`#1042` ou id), Ações (lista fixa filtrada por palavra: "Matricular aluno", "Importar alunos", "Novo curso", "Exportar alunos") |
| `/painel/cursos/` | `courses` | GET | 8.2. `?status=todos|publicados|rascunhos|arquivados&q=&categoria=` |
| `/painel/cursos/novo/` | `course_create` | POST | diálogo "Novo curso" |
| `/painel/cursos/<id>/conteudo/` | `course_content` | GET | 8.3. `?aula=<id>` abre o painel da aula |
| `/painel/cursos/<id>/aulas/<lid>/painel/` | `lesson_drawer` | GET, POST | GET: parcial do painel da aula; POST: salvar aula |
| `/painel/modulos/<mid>/aulas/nova/` | `lesson_quick_create` | POST | `title` → cria rascunho, devolve `html` da linha e `open_selector` |
| `/painel/aulas/<lid>/excluir/` e `/restaurar/` | `lesson_delete`, `lesson_restore` | POST | exclusão com Desfazer (`deleted_at`) |
| `/painel/cursos/<id>/ordem/` | `course_reorder` (v1) | POST JSON | igual ao v1 |
| `/painel/cursos/<id>/modulos/novo/` | `module_create` | POST | `title` |
| `/painel/cursos/<id>/venda/` | `course_sales` | GET, POST | 8.4 |
| `/painel/cursos/<id>/configuracoes/` | `course_settings` | GET, POST | 8.5. `section` oculto em cada form |
| `/painel/cursos/<id>/arquivar/`, `/desarquivar/`, `/rascunho/`, `/publicar/`, `/duplicar/`, `/excluir/` | `course_archive`, `course_unarchive`, `course_draft`, `course_publish`, `course_duplicate`, `course_delete` | POST | conforme 4.3 e 4.4 |
| `/painel/cursos/<id>/ao-vivo/` | `live_session_save` | POST | criar ou editar `LiveSession` (`id` opcional) |
| `/painel/alunos/` | `students` | GET, POST | 8.6. `?filtro=todos|ativos|nunca|concluiram|sem-dados|importados-hoje&q=&curso=&pagina=`. POST = ação em massa (`action`, `ids`, `course`) |
| `/painel/alunos/matricular/` | `student_enroll` | POST | diálogo "Matricular aluno" |
| `/painel/alunos/<id>/` | `student_detail` | GET | 8.7. `?aba=cursos|pedidos|certificados|atividade` |
| `/painel/alunos/<id>/acao/` | `student_action` | POST | `action=resend_access|reset_password|unenroll|reset_progress|toggle_lesson|edit` + campos |
| `/painel/alunos/<id>/anotacoes/` | `student_notes` | POST | autosave (`notes`) |
| `/painel/alunos/importar/` | `students_import` | GET, POST | 8.8, 4 passos |
| `/painel/pedidos/` | `orders` | GET | 8.9. `?status=&periodo=&pedido=<id>` |
| `/painel/pedidos/<id>/acao/` | `order_action` | POST | `resend_access`, `refund` (diálogo "Afeta alunos") |
| `/painel/comunidade/` | `community` | GET, POST | 8.10. `?aba=sem-resposta|respondidas|ocultas&q=&duvida=<id>` |
| `/painel/comunidade/<id>/acao/` | `community_action` | POST | `reply`, `pin`, `hide`, `unhide` |
| `/painel/configuracoes/` | `settings` | GET, POST | 8.11. `?secao=escola|pagamentos|emails|certificado|equipe` |

As rotas v1 `painel:course_edit` e `painel:course_lessons` passam a redirecionar (301) para `course_settings` e `course_content`.

### 6.4 Serviço de progresso e JSON da aula

Crie `courses/services.py` com as funções abaixo e use em todas as telas (Início, curso, aula, certificados, menu). Nada de cálculo de progresso duplicado em views.

```python
def ordered_lessons(course):           # publicadas e não excluídas, na ordem do v1 (seção 4.5)
def completed_lesson_ids(user, course_ids):  # set de ids concluídos (só aulas publicadas)
def course_progress(user, course):     # dict: done, total, pct, remaining, next_lesson, resume_lesson, resume_seconds, last_seen_at
def lesson_payload(user, lesson):      # o JSON abaixo
```

JSON de `toggle_progress` e `complete_lesson`:
```json
{"is_completed": true, "completed_count": 2, "total_count": 4, "percentage": 50.0,
 "module": {"id": 12, "done": 2, "total": 2}, "remaining": 2, "course_done": false,
 "next": {"url": "/courses/bls/lessons/91/", "title": "Operação e Segurança do DEA"},
 "certificate_url": "/certificados/?emitir=bls"}
```
`next` é a vizinha seguinte na ordem (não a primeira pendente); `null` na última aula. `course_done` é `true` só quando `completed_count == total_count`. Ao virar `course_done` pela primeira vez, chame `notify(... "certificate" ...)`.

"Continue de onde parou" (`resume_lesson`): a aula com progresso mais recente (`updated_at`) **não concluída**; se não houver, a primeira não concluída na ordem; se todas concluídas, `None` (o Início mostra o curso como concluído).

### 6.5 Permissões

- Toda view do painel: `@painel_required` (v1). Pedidos e Configurações: decorator novo `@painel_admin_required` (superusuário, `is_staff` ou `role == "ADMIN"`). Instrutor que abrir a URL recebe 403 com a página de erro do layout.
- Toda view de aluno que recebe `id` de aula, dúvida, aviso ou certificado confere se pertence ao usuário ou a um curso em que ele está matriculado e ativo. Teste com dois usuários.

### 6.6 Seed

Depois da fase que criar os modelos, o seed precisa ter, no mínimo: Jane com BLS em andamento (1 de 4, posição salva de 192 s na aula 2) e Plantão Sem GPT concluído sem certificado; 3 encontros futuros e 2 passados com gravação no Plantão; 4 dúvidas (2 respondidas por instrutor, 1 sem resposta, 1 geral); 3 avisos não lidos para Jane; aula 4 do BLS como rascunho; 2 alunos que nunca acessaram. Assim todas as telas e estados podem ser conferidos sem criar nada à mão.

---

## 7. Área do aluno · tela a tela

Formato de cada tela: referência, rota e template, contexto que a view entrega, estrutura (ordem dos blocos com as classes) e estados. Os textos fixos estão entre aspas e devem sair exatamente assim.

### 7.1 Início · `AlunoV2Inicio.dc.html` · capturas `aluno-inicio*.png`

- Rota `dashboard`, template `courses/dashboard.html` (substitui o do v1), base `base_aluno.html`. `crumbs`: "Área do aluno". `page_title`: "Início".
- Contexto: `greeting` ("Bom dia" 5h a 11h59, "Boa tarde" 12h a 17h59, "Boa noite" no resto, em `America/Campo_Grande`), `summary` (texto da linha abaixo da saudação), `resume` (dict de `course_progress` do curso com atividade mais recente que ainda tem aula pendente, ou `None`), `steps` (lista, máx. 4), `courses` (uma linha por matrícula ativa com `course`, `pct`, `done`, `total`, `status` = `andamento|nao_iniciado|concluido`, `last_seen_at`, `live_count`), `filter`, `filter_counts`, `shop` (cursos publicados em que não está matriculado).
- `{% block page_class %}page--gap-32{% endblock %}`. Ordem:
  1. `div.greeting`: `h2.page-title` "{greeting}, {user_first_name}" (o `h1` é o título do topo) e `p.page-intro` com `summary`: "{n} cursos na sua conta · {c} concluído(s) · {l} aula(s) ao vivo esta semana" (omitir partes com zero; usar `plural_pt`).
  2. Se `resume`: `section.card.continue-v2` com `a.continue-v2__cover.{{ course.cover_class }}` (link para a aula; `img` da capa se houver, senão a sigla; `span.continue-v2__play` com ícone `play` 26; `span.continue-v2__time` "Parou em 03:12 de 07:00" só se `resume_seconds > 15`; `span.continue-v2__bar` com a largura do vídeo assistido) e `div.continue-v2__body`: `span.eyebrow` "Continue de onde parou", `h2.course-hero-v2__title.text-24` título da aula, `span.text-2` "{curso} · Módulo N · Aula X de N", `div.progress-inline` com a barra do curso e `span.progress-label` "25% do curso · 1 de 4 aulas", `div.row.gap-10` com `a.btn.btn--primary` (ícone `play` 16) "Continuar aula" e `a.btn.btn--secondary` "Ver conteúdo do curso" (para `course_home`).
  3. Se `steps`: `section.card.card--clip` com `div.task-list__head` (`h2.card__title` "Próximos passos" + `span.text-13.muted` "N itens") e um `div.task#step-<chave>` por passo: `span.task__icon.task__icon--warn|--ok|` (ícone), `span.task__text` (`span.task__title` + `span.task__meta`), `span.badge` (estado), `a.btn.btn--secondary.btn--xs` (ação) e botão dispensar (`icon-btn icon-btn--plain`, `aria-label="Dispensar este aviso"`, `data-dismiss-url`, `data-dismiss-target="#step-<chave>"`, `data-undo-url`). Passos, nesta prioridade:
     - `cpf` (falta nome ou CPF válido e há matrícula): ícone `alert`, "Informe nome completo e CPF", meta "Sem isso o certificado não pode ser emitido. Leva 1 minuto.", `badge--warning` "Pendente", ação "Completar dados" → `settings?secao=certificado`;
     - `cert:<slug>` (curso concluído sem certificado): ícone `award`, "Seu certificado do {curso} está pronto", meta "Confira nome e CPF e emita", `badge--success` "Pronto", ação "Emitir" → `certificates?emitir=<slug>`;
     - `live:<id>` (próximo encontro em até 7 dias): ícone `video`, "Aula ao vivo · {curso}", meta "{Quinta}, {12/11}, das {20h} às {21h30} (horário de Brasília). O botão de entrar libera 15 min antes.", `badge--blue` "Em N dias" / "Hoje" / `badge--live` "Ao vivo agora", ação "Ver detalhes" → `live_classes`;
     - `resp:<post_id>` (resposta não lida): ícone `check`, "O instrutor respondeu sua dúvida", meta "{curso} · {título}", `badge--success` "Nova resposta", ação "Ler resposta" → `community?duvida=<id>`.
     Passo dispensado não volta, exceto `cpf`, que volta depois de 7 dias se continuar pendente. Se todos dispensados: o card não aparece.
  4. `section.stack.gap-16` "Meus cursos": `div.row.row--between` com `h2.section__title` "Meus cursos" e `div.seg[role=group][aria-label="Filtrar cursos"]` com 4 `a.seg__btn` (links `?filtro=`, `aria-current="page"` no ativo; rótulo "Todos (2)", "Em andamento (1)", "Não iniciados (0)", "Concluídos (1)"). Grade `div.course-grid.course-grid--320` com um `article.card.course-card-v2` por curso: `a.course-card-v2__cover.{cover_class}` (sigla ou imagem + `span.badge` do status: `badge--blue` "Em andamento", `badge--gray` "Não iniciado", `badge--success` "Concluído"), `div.course-card-v2__body` com `span.badge` da categoria, `a.course-card-v2__title`, barra, `span.progress-label` ("1 de 4 aulas · visto há 2 dias", "Não iniciado · 4 aulas", "Concluído · 1 aula"), e `div.course-card-v2__actions`: `a.btn.btn--primary.btn--xs.grow` ("Continuar", "Começar curso" ou "Rever aulas", para a aula certa) e `a.btn.btn--secondary.btn--xs` "Conteúdo" (para `course_home`).
     Filtro sem resultado: `div.card.card--dashed.empty-state` com ícone, título e texto por filtro: Não iniciados → "Nenhum curso por começar" / "Você já começou todos os seus cursos. Quando comprar um novo, ele aparece aqui."; Concluídos → "Nenhum curso concluído ainda" / "Quando você terminar todas as aulas de um curso, ele aparece aqui junto com o certificado."; Em andamento → "Nenhum curso em andamento" / "Comece um curso para ele aparecer aqui.". Botão `btn--secondary btn--xs` "Ver todos".
     Sem nenhuma matrícula: em vez de tudo acima, `div.card.empty-state` "Você ainda não tem cursos" / "Quando sua compra for confirmada, o curso aparece aqui na hora." e a seção da loja.
  5. `section.stack.gap-16` "Outros treinamentos CETREMER" (só se `shop`): `h2.section__title`, `p.page-intro` "Veja o conteúdo completo antes de comprar. Ao comprar, o curso aparece aqui na hora.", grade com `partials/course_card_shop.html` do v1 (badge `badge--overlay` "Não adquirido" com ícone `lock`).

### 7.2 Página do curso para o aluno · `AlunoV2Curso.dc.html` · `aluno-curso*.png`

- Rota `course_home`, template `courses/course_home.html` (novo), base `base_aluno.html`. 404 se não houver matrícula ativa (para quem não é aluno, redirecionar para `course_preview`). `crumbs`: "Início" (link) / "Meus cursos". `page_title`: título do curso.
- Contexto: `course`, `progress` (de `course_progress`), `modules` (cada um com `lessons_list` em que cada aula tem `state` = `done|current|todo|locked`, `position`, `duration_seconds`, `materials_count`, `released_at`), `materials` (todos, com `lesson_position`), `posts` (5 mais recentes do curso), `posts_count`, `live_sessions` (futuras), `enrollment` (para a linha de acesso), `cert_reqs` (lista de 3 requisitos com `ok`).
- Ordem:
  1. `section.card.course-hero-v2`: `div.course-hero-v2__cover.{cover_class}` e `div.course-hero-v2__body` com `div.row.gap-8` de badges (categoria; `badge--gray` "Carga horária 8h"; `badge--gray` "2 módulos · 4 aulas · 28 min"; `badge--success` com ícone `award` "Certificado verificável" se `certificate_enabled`), `h2.course-hero-v2__title`, `p.text-2` com `tagline`, progresso (`progress-inline` largo + "25% · 1 de 4 aulas"), `div.row.gap-10` com `a.btn.btn--primary` "Continuar: Aula 2 · {título curto}" (ou "Começar curso" / "Rever aulas") e `a.btn.btn--secondary` ícone `award` "Requisitos do certificado" (para `certificates`), e `span.text-13.muted` "Acesso vitalício · liberado em 02/11/2026 pela compra na Hotmart" (prazo: "Acesso até dd/mm/aaaa"; origem pelo `source` do v1 + `external_ref`).
  2. `div.split` com `section.card.split__main.card--clip` (abas) e `aside.split__side.split__side--300`.
  3. Abas (`div.tabs[role=tablist][data-tabs][data-tabs-param="aba"]`): "Conteúdo", "Materiais (2)", "Dúvidas (3)", "Aulas ao vivo". Painéis:
     - Conteúdo: `div.row.row--end` com `button.btn.btn--ghost.btn--xs` "Recolher tudo"/"Expandir tudo" (alterna todos os `module__toggle`; texto troca). Um `div.module-card` por módulo: `button.module__toggle[aria-expanded][aria-controls]` com `span.module__text` (`span.module__title` "Módulo 1 · {título}" e `span.module__count` "2 aulas · 1 concluída"), `span.badge` do estado do módulo (`badge--success` "Concluído", `badge--blue` "Em andamento", `badge--gray` "Não iniciado", `badge--warning` "Libera em 12/12" se programado) e chevron; lista de `a.lesson-row` (marca `✓` `.mark-done`, `▶` `.mark-current`, `○` `.mark-todo`, ícone `lock` para bloqueada; título "N. {título}"; meta "Concluída", "Você parou em 03:12", "Não assistida", "Libera em dd/mm"; e `+ · 1 material` quando houver; duração à direita). Aula bloqueada não é link (`span.lesson-row` com `aria-disabled="true"`).
     - Materiais: `p.text-14.muted` "Todos os materiais do curso em um lugar. Cada um mostra de qual aula é." e `a.file-item` por material (meta "PDF · 1,2 MB · Aula 1"). Vazio: `div.empty-state` "Este curso não tem materiais de apoio".
     - Dúvidas: `div.row.row--between` com texto "Dúvidas feitas neste curso, com a aula de origem." e `a.btn.btn--primary.btn--xs` "Nova pergunta" (para `community?nova=1&curso=<slug>`); `a.list-row-link` por dúvida (título, "Aula 2 · Autor · ontem", badge "Respondida"/"Aguardando resposta"); link "Ver todas na comunidade". Vazio: "Ninguém perguntou nada neste curso ainda."
     - Aulas ao vivo: lista compacta dos próximos encontros (`date-mini` + título + horário) com link "Ver agenda completa"; vazio: `div.empty-state` ícone `video` "Este curso não tem encontros ao vivo" / "Se a equipe marcar um encontro, ele aparece aqui e você recebe um e-mail com data e link." / `a.btn.btn--secondary.btn--xs` "Ver agenda de todos os cursos".
  4. Lateral: `div.card.card--pad-sm.stack.gap-14` "Seu certificado" com 3 `div.req-mini` (ícone `check-circle` verde quando ok, `circle` cinza quando não): "Concluir as 4 aulas" / "1 de 4 · faltam 3"; "Informar nome completo e CPF" / link "Completar agora"; "Ter acesso ativo ao curso" / "Vitalício" ou "Até dd/mm/aaaa". Depois `div.card.card--pad-sm` "Precisa de ajuda?" com o texto "Dúvida de conteúdo vai para a comunidade, onde o instrutor responde. Problema de acesso ou pagamento, chame no WhatsApp." e `a.btn.btn--secondary.btn--xs` "Falar com o suporte".

### 7.3 Player da aula · `AlunoV2Aula.dc.html` · `aluno-aula*.png`

- Rota `lesson_detail`, template `courses/lesson_detail.html` (layout próprio, como no v1). Ao abrir: atualizar `Enrollment.last_accessed_at` e criar o registro de progresso se não existir (sem marcar concluída). Aula de módulo ainda não liberado: redirecionar para `course_home` com toast "Este módulo libera em dd/mm." (kind info).
- Contexto: tudo do v1 (seção 6.10) + `resume_seconds` (posição salva desta aula), `module_index`, `next_lesson_nav`, `prev_lesson`, `is_last`, `aba`, `cert` (`remaining`, `ready`), `course_done` (bool).
- `div.lesson-page#lesson-page` com os `data-*` do cabeçalho do `player.js` (`data-lesson-id`, `data-module-id`, `data-toggle-url`, `data-complete-url`, `data-position-url`, `data-resume`, `data-completed`).
- `header.lesson-topbar`: esquerda `a.back-link` ícone `chevron-left` "Voltar ao curso" (para `course_home`), `span.divider-v`, `div.stack` (`span.lesson-topbar__brand` "CETREMER" + `span.lesson-topbar__course`). Direita, `div.row.gap-10`: `div.lesson-topbar__progress` (barra com `data-course-progress` + `span.lesson-topbar__progress-text[data-progress-text]` "25% · 1 de 4 aulas"), `button.btn.btn--secondary.btn--xs[data-focus-toggle][aria-pressed=false]` ícone `sidebar` 16 + `span[data-label]` "Modo foco", `button.icon-btn.icon-btn--plain[data-cmdk-open][aria-label=Buscar]` e `a.avatar` para `settings`.
- `main.lesson-main`, nesta ordem:
  1. `div.player`: iframe do Vimeo (com `data-vimeo`) ou YouTube ou vazio, como no v1. Dentro dele, depois do iframe: `div.resume-chip#resume-chip[hidden]` com ícone `clock` 16, "Continuando de onde você parou: " `<strong data-resume-time>03:12</strong>`, `button.resume-chip__btn[data-resume-restart]` "Recomeçar" e `button.resume-chip__close[data-resume-close][aria-label="Fechar aviso"]`.
  2. `div.done-banner#done-banner[hidden][role=status]`: ícone `check-circle` 26, `div.done-banner__text` (`span.done-banner__title` "Aula concluída", `span.done-banner__sub` "Próxima: " + `span[data-next-title]`), `button.btn.btn--quiet.btn--sm[data-done-stay]` "Ficar nesta aula", `a.btn.btn--primary[data-next-link][href=próxima]` "Ir para a próxima aula" + ícone `chevron-right`. Sem próxima aula: não renderizar o banner.
  3. `div.lesson-head`: `div.stack.gap-4` (`span.text-13.muted` "Módulo 1 · Introdução ao Suporte Básico · Aula 2 de 4" **sem repetir "Módulo 1:"**, ver seção 10 item 2; `h1.lesson-head__title`) e `button.btn.btn--lg[data-complete-toggle][aria-pressed]` com classe `btn--primary` ou `btn--done`, ícone `check` 18 2.4 e `span[data-label]` "Marcar como concluída"/"Concluída".
  4. `p.auto-note` ícone `info` 15 "A aula também é marcada sozinha quando você assiste 90% do vídeo." (só para Vimeo).
  5. `nav.lesson-nav`: anterior e próxima do v1; a próxima com `data-nav-next`. Na última aula, no lugar da próxima: `a.lesson-nav__link.lesson-nav__link--next` para `certificates` com label "Última aula do curso", título "Ver requisitos do certificado" e ícone `award`.
  6. `section.card.card--clip` com abas `[data-tabs][data-tabs-param="aba"]`: "Sobre esta aula", "Materiais (N)", "Dúvidas (N)", e no celular a aba extra "Aulas" (`button.tab.only-mobile`) com a mesma lista da lateral. Painéis (`div.tab-panel`):
     - Sobre: `p.text-2` com a descrição. Vazia: "O instrutor não escreveu uma descrição para esta aula."
     - Materiais: `a.file-item` (v1). Vazio: "Esta aula não tem material de apoio. Os PDFs do curso inteiro ficam na aba Materiais do curso." com link.
     - Dúvidas: lista das dúvidas desta aula (cada uma com título, `badge--success` "Respondida pelo instrutor" ou `badge--warning` "Aguardando resposta", "{autor} · {quando} · N respostas", e a resposta oficial em `div.answer-official` com `<strong>Instrutor CETREMER:</strong>`), link "Abrir conversa na comunidade"; depois o form (`form.stack.gap-8[method=post][action=community_create][data-async]` com `lesson` e `course` ocultos, `label.field__label` "Pergunte sobre esta aula", `textarea.textarea` com placeholder "Ex.: em 02:40, qual a posição correta das mãos?", `div.row.row--between` com `span.hint` "Vai para a comunidade do {curso} com o nome desta aula. Você recebe um e-mail quando responderem." e `button.btn.btn--primary.btn--sm` "Publicar dúvida"). A view responde com `json_ok(toast=..., replace={"#lesson-questions": html_da_lista})`.
- `aside.lesson-side`: card da lista de aulas do v1 (`curriculum__head` com `span.progress-label[data-progress-count][data-suffix=" · 28 min no total"]`; `module__count[data-module-count]` mostra "Concluído" em verde quando completo) e `div.card.cert-mini[data-cert-mini]` (classe `is-ready` quando pronto) com `span.icon-tile.icon-tile--40` ícone `award`, `span.fw-600` "Certificado", `span.text-13.muted[data-cert-text]` "Liberado ao concluir 100% das aulas. Faltam 3 aulas." e `a.link-strong.text-14[data-cert-link]` "Ver requisitos".
- `dialog.dialog.dialog--celebrate#celebrate[aria-labelledby=fim]`: `span.celebrate__icon` ícone `award` 36, `h2.celebrate__title#fim` "Você concluiu o {short_name ou título}", `p.text-2` "Todas as {N} aulas foram concluídas. Falta só conferir nome e CPF para emitir o certificado." (se os dados já estão ok: "Seu certificado já pode ser emitido."), `div.dialog__actions` centralizado com `button.btn.btn--secondary[data-dialog-close]` "Rever aulas" e `a.btn.btn--primary` ícone `award` "Emitir certificado" (`certificates?emitir=<slug>`).
- Atalhos: `M` marca/desmarca, `N` próxima aula, `Ctrl K` busca (player.js e ui.js).

### 7.4 Aulas ao vivo · `AlunoV2AoVivo.dc.html` · `aluno-aovivo*.png`

- Rota `live_classes`, template `courses/live_classes.html` (substitui). `crumbs`: "Área do aluno" / "Aulas ao vivo".
- Contexto: `next_session` (próximo `LiveSession` não encerrado dos cursos matriculados) com `state`, `upcoming` (os seguintes, até 10, filtrados por `?curso=`), `recordings` (encerrados com `recording_url` e `recording_until >= hoje`), `courses_with_live` (para os chips), `selected_course`, `empty_course` (curso do filtro sem encontros).
- Ordem:
  1. Se `next_session`: `section.card.live-next` (+ `is-soon` ou `is-live`): `div.date-tile` (dia da semana "Qui", dia "12", mês "nov") e `div.live-next__body`: `div.row.gap-8` com `span.eyebrow` "Próximo encontro" e o badge do estado (`badge--blue` "Em 2 dias" / "Amanhã" / "Hoje às 20h"; `badge--warning` "Começa em 10 min"; `badge--live` "● Ao vivo agora"), `h2.course-hero-v2__title.text-24` "{curso} · {título}", `div.meta-line` (ícone `clock` "20h00 às 21h30 (horário de Brasília)", ícone `video` "Google Meet", ícone `user` host), `div.row.gap-10`: `a.btn.btn--primary` ícone `video` "Entrar no Google Meet" (`target=_blank rel=noopener`; **quando `state == "scheduled"` renderizar sem `href`, com `aria-disabled="true"` e ícone `lock`**; nesse caso também `data-enable-at="<ISO 15 min antes do início>"`, `data-enabled-href="<link do Meet>"` e o ícone com `data-lock-icon`, e a dica abaixo leva `data-enable-hint` e `data-enabled-hint="A sala já está aberta. O link abre o Google Meet em uma nova aba."`, para o ui.js (item 18) liberar sem recarregar), `a.btn.btn--secondary` ícone `calendar` "Adicionar ao Google Agenda" (link `https://calendar.google.com/calendar/render?action=TEMPLATE&text=...&dates=AAAAMMDDTHHMMSSZ/...&details=...&location=Google%20Meet`), `a.btn.btn--ghost` "Baixar convite (.ics)" (`live_session_ics`); `span.text-13.muted[data-enable-hint]` com a dica do estado: scheduled "O botão de entrar libera 15 minutos antes do início. Você recebe um lembrete por e-mail 1 hora antes."; soon "A sala já está aberta. O link abre o Google Meet em uma nova aba."; live "Começou há N minutos. Ainda dá tempo de entrar."
  2. `section.stack.gap-14` "Agenda": `div.row.row--between` com `h2.section__title` e `div.chips` (`a.chip` "Todos os cursos" + um por curso com encontros + cursos sem encontros também, para mostrar o vazio). `div.card.card--clip` com um `div.list-row-link` por encontro: `div.date-mini`, `span.grow` (título + "20h00 às 21h30 · Google Meet"), badge (`badge--blue` "Próximo" no primeiro, `badge--gray` "Agendado" nos outros), `a.btn.btn--secondary.btn--xs` ícone `calendar` "Agenda". Vazio do filtro: `div.empty-state` ícone `calendar` "O {curso} não tem encontros ao vivo marcados" / "Quando a equipe marcar, você recebe um e-mail com data e link, e o encontro aparece aqui."
  3. Se `recordings`: `section.stack.gap-14` com `h2.section__title` "Gravações" e `p.page-intro` "Perdeu um encontro? A gravação fica disponível por 30 dias."; grade de `article.card.recording` (`a.recording__cover` para a gravação em nova aba, com o botão play e `span.recording__len`; corpo com título e "Gravado em 05/11 · disponível até 05/12").
  4. Nenhum curso com ao vivo: `div.card.empty-state` "Nenhum dos seus cursos tem aulas ao vivo no momento."
- Remover o iframe da Agenda do Google desta tela (seção 10 item 7).

### 7.5 Certificados · `AlunoV2Certificados.dc.html` · `aluno-certificados*.png`

- Rota `certificates`. Contexto: `stats` (`issued`, `ready`, `in_progress`), `items` (um por matrícula: `course`, `state` = `issued|ready|progress`, `done`, `total`, `remaining`, `certificate`, `data_ok`), `open_issue` (slug do `?emitir=`), `profile_name`, `profile_cpf`.
- Ordem:
  1. `div.row.gap-12` com 3 `div.card.stat`: "Emitidos", "Prontos para emitir" (número em `text-success` quando > 0), "Em andamento".
  2. Um `article.card.cert-row` por item, ordem: prontos, emitidos, em andamento.
     - **ready** (+ `is-ready`): `div.cert-row__thumb.{cover_class}`; corpo com título + `badge--success` "Pronto para emitir"; requisitos: `div.req-mini.is-ok` "N de N aulas concluídas" e, se `data_ok` falso, `div.req-mini` ícone `alert` laranja "Confira nome e CPF antes de emitir"; `button.btn.btn--primary` ícone `award` "Conferir dados e emitir" (`data-drawer-open="drawer-emitir-<slug>"`).
     - **issued**: miniatura `div.cert-row__thumb.cert-row__thumb--doc` (marca, "Certificado de conclusão", nome e curso em 10px, filete azul); corpo com título + `badge--success` ícone `check` "Emitido", `span.text-13.muted` "Emitido em 10/11/2026 · código CTM-7F3K-92QA · carga horária 4h" (código com `|codigo_cert`); ações `a.btn.btn--primary` ícone `download` "Baixar PDF" (`certificate?imprimir=1`), `button.btn.btn--secondary` ícone `link` "Copiar link de verificação" (`data-copy` + `data-copy-toast="Link de verificação copiado"`) e `a.btn.btn--secondary` ícone `share` "Adicionar ao LinkedIn" (URL `https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name=<curso>&organizationName=CETREMER&issueYear=AAAA&issueMonth=M&certUrl=<verify_url>&certId=<código>`, nova aba).
     - **progress**: thumb, título + `badge--blue` "Em andamento" (ou `badge--gray` "Não iniciado"), barra + "1 de 4 aulas", requisitos com ícones certos (`circle` cinza pendente, `check-circle` verde cumprido): "Concluir as 4 aulas · faltam 3" e "Informar nome completo e CPF · completar agora" (link) ou "Nome e CPF informados"; `a.btn.btn--secondary` ícone `play` "Continuar curso".
  3. `div.card.card--pad-sm.row.gap-12`: ícone `shield` 22 azul, texto "Qualquer pessoa pode conferir se um certificado CETREMER é verdadeiro pelo código, sem precisar de login." e `a.btn.btn--secondary.btn--xs` "Página de verificação".
- Painel de emissão (um por item `ready`): `dialog.drawer#drawer-emitir-<slug>` com `data-autoopen="emitir"` quando `open_issue == slug`. `form.stack[method=post][action=certificate_issue][data-async]`: `drawer__head` ("Emitir certificado" + fechar), `drawer__body` com `p.text-2` "Esses dados vão impressos no certificado. Depois de emitido, só o suporte consegue corrigir.", campo "Nome completo" (hint "Do jeito que está no seu documento, com acentos."), campo "CPF" (validação ao sair do campo; válido: `input.is-valid` + `span.field-ok` ícone `check` "CPF válido"; inválido: `aria-invalid` + "CPF inválido. Confira os números."), `div.cert-preview-text` (`span.eyebrow.muted` "Prévia do texto" + "Certificamos que <strong id=\"preview-name\">NOME EM MAIÚSCULAS</strong>, CPF <span id=\"preview-cpf\">***.456.789-**</span>, concluiu o curso <strong>{curso}</strong>, com carga horária de {N} horas, em {data}."; os campos têm `data-mirror="#preview-name" data-mirror-upper` e `data-mirror="#preview-cpf" data-mirror-cpf`, e o ui.js (item 17) atualiza a prévia ao digitar), `label.check` "Conferi meu nome e CPF" (obrigatório); `drawer__foot` "Cancelar" (`data-drawer-close`) e `button.btn.btn--primary` "Emitir certificado". Resposta: `json_ok(toast="Certificado emitido. Enviamos o link para seu e-mail", reload=True)`.
- A rota v1 `issue_certificate` continua: com certificado emitido mostra o certificado; sem, mostra `certificate_error.html` com os ícones corrigidos (seção 10 item 9) e o botão "Conferir dados e emitir" quando as aulas estão 100%.

### 7.6 Comunidade · `AlunoV2Comunidade.dc.html` · `aluno-comunidade*.png`

- Rota `community`. Contexto: `posts` filtrados (`situacao`, `curso`, `q`), contagens por situação, `my_courses`, `open_post` (do `?duvida=`, com comentários e `is_author`), `compose_open` (`?nova=1`), `compose_course` e `compose_lesson` (pré-seleção vinda do curso ou da aula). Abrir uma conversa minha com resposta não lida zera `has_unread_answer`.
- Ordem (`div.split`):
  1. `main.split__main.gap-16`: `div.toolbar` com campo de busca (`form[method=get]` com `input.input[type=search][name=q]` "Buscar nas dúvidas", mantém os outros filtros em `hidden`) e `a.btn.btn--primary` ícone `plus` "Nova pergunta" (`href="?nova=1"` + `data-drawer-open="drawer-nova"`). `div.row.row--between` com `div.seg` de situação (`a.seg__btn`: "Todas", "Sem resposta", "Respondidas", "Minhas") e `div.chips` de curso (`a.chip`: "Todos os cursos", um por curso matriculado, "Discussão geral"). **Padrão: Todas + Todos os cursos** (corrige o v1).
  2. `div.card.card--clip` com um `a.list-row-link.thread` por dúvida (`href="?duvida=<id>"` + `data-drawer-url` para o parcial da conversa, `data-drawer-target="drawer-conversa"`, `data-drawer-param="duvida"`; classe `is-unread` se `has_unread_answer` e é minha; fixadas primeiro com ícone `star`): avatar 38 com iniciais, `div.thread__text` (`div.row.gap-8` com `span.thread__title` + badge `badge--success` "Respondida pelo instrutor" ou `badge--warning` "Aguardando resposta"; `span.thread__preview` (2 linhas); `span.text-13.muted` "{autor} · {curso} · Aula N · {título da aula} · {quando}"), `span.thread__replies` ícone `chat` + número.
     Vazio: `div.empty-state` com título e texto pelo filtro ("Você ainda não perguntou nada aqui" / "Use o botão Nova pergunta ou pergunte direto da aula." para Minhas; "Nenhuma dúvida com esses filtros" / "Tente outro curso ou outra situação." para o resto) e `a.btn.btn--secondary.btn--xs` "Limpar filtros".
  3. `aside.split__side.split__side--300`: card "Como funciona" (3 linhas com ícones `check-circle`, `mail`, `star`: "Pergunte de dentro da aula para a dúvida já ir com o nome da aula.", "Você recebe um e-mail quando o instrutor responder.", "Resposta do instrutor aparece em destaque, no topo da conversa.") e card "Combinados" ("Sem dados de pacientes, sem prescrição individual e sem divulgação. A equipe pode ocultar posts fora das regras.").
- Painel da conversa `dialog.drawer.drawer--600#drawer-conversa[data-autoopen="duvida" se open_post]` (miolo em `community/_thread_drawer.html`, também usado pelo `data-drawer-url`): cabeçalho com `drawer__eyebrow` "{curso} · Aula N · {título}" e `drawer__title`; corpo com a pergunta (avatar, autor, quando, texto), depois `div.answer-box` (respostas de staff primeiro: `div.answer-box__by` ícone `shield` "Instrutor CETREMER" + `badge--blue` "Resposta oficial"; texto; se sou o autor: `div.row` com "Isso resolveu sua dúvida?", `form[data-async]` com botão "Sim, resolveu" / "Marcada como resolvida" (`aria-pressed`) e `button.btn.btn--ghost.btn--xs[data-drawer-close]` "Ainda tenho dúvida" que leva o foco para o campo de resposta), demais respostas em lista simples; sem resposta de staff: `div.waiting-box` ícone `clock` "Aguardando o instrutor. A equipe costuma responder em até 1 dia útil, e você recebe um e-mail."; rodapé com `form[data-async]` (`textarea` "Escreva uma resposta" + `button.btn.btn--primary.btn--sm` ícone `reply` "Responder").
- Painel "Nova pergunta" `dialog.drawer.drawer--560#drawer-nova[data-autoopen="nova" se compose_open]`: `form[method=post][action=community_create][data-async]` com select "Curso" (cursos matriculados + "Discussão geral"), select "Aula (opcional)" com todas as aulas dos cursos matriculados agrupadas em `<optgroup label="{curso}">` (o servidor valida que a aula é do curso escolhido; se não for, erro no campo "Escolha uma aula do curso selecionado."), "Título" (`input[data-suggest-url="{% url 'community_suggest' %}"][data-suggest-box="#suggest-box"]`), `div.suggest-box#suggest-box[hidden]` (a view `community_suggest` devolve `<span class="text-13 fw-600 text-2">Talvez já tenha resposta:</span>` + até 3 `<a>` para `?duvida=<id>`, ou vazio; o ui.js item 19 busca ao parar de digitar), "Detalhes" com placeholder "Conte o contexto. Se for sobre um trecho do vídeo, diga o minuto."; rodapé "Cancelar" e "Publicar pergunta".
- Sucesso de "Nova pergunta": `json_ok(toast="Pergunta publicada. Avisaremos por e-mail quando responderem", undo_url=<community_delete_own>, redirect="/community/?nova_id=<id>")`; a lista marca o item novo com `is-new`.

### 7.7 Minha conta · `AlunoV2Conta.dc.html` · `aluno-conta*.png`

- Rota `settings`. `div.settings-layout` com `nav.vtabs[aria-label="Seções da conta"]` à esquerda (links `a.vtab` com `aria-current="page"` no ativo; badge `badge--warning` "Pendente" em "Dados do certificado" quando falta, `badge--gray` com o número em "Pedidos e acessos") e `div.settings-layout__main` com **só a seção ativa** (`?secao=`; padrão `perfil`, exceto se faltar nome ou CPF: padrão `certificado`).
- Cada seção é `form.card.card--pad-lg.stack.gap-18[method=post][data-dirty-form][data-dirtybar="dirtybar"][data-async]` com `input[type=hidden][name=section]` e a `div.dirtybar#dirtybar[hidden]` no fim de `settings-layout__main` (`button[type=submit][form=<id do form>]` "Salvar alterações"). Sem botões "Salvar" soltos no card (corrige os 3 botões do v1).
  - **Perfil**: avatar 64 + `button.btn.btn--secondary.btn--xs` "Trocar foto" (`input[type=file].sr-only` em `label`) + hint "JPG ou PNG até 2 MB. Aparece na comunidade."; `div.form-grid`: "Como prefere ser chamada(o)" (`display_name`, hint "Usado nas saudações e na comunidade."), "E-mail de acesso" (hint "Trocar o e-mail pede confirmação no endereço novo." e o fluxo: grava `pending_email` e manda link; até confirmar, continua o antigo), "WhatsApp" (hint "Só para avisos de aula ao vivo, se você permitir.").
  - **Dados do certificado**: `div.row.row--between` com título + `badge--warning` "Pendente para N certificado(s)" (some quando ok); texto "Esses dados vão impressos em todos os seus certificados. Depois de emitir um certificado, só o suporte consegue corrigir."; grade com "Nome completo" (hint "Com acentos, sem abreviar.") e "CPF" (hint "Só números ou com pontos, como preferir."; válido mostra `span.field-ok` "CPF válido"). Com certificado já emitido, os dois campos ficam `readonly` com hint "Já usado em certificado emitido. Para corrigir, fale com o suporte." e link do WhatsApp.
  - **Senha e acesso**: "Senha atual", "Nova senha" (`div.input-wrap` com `button.input-wrap__btn[data-reveal]` "Mostrar"/"Ocultar" e `ul.pw-rules[data-pw-rules]` "Pelo menos 8 caracteres", "Letras e números", "Diferente da senha atual"), "Confirmar nova senha"; aqui o form **não** usa barra de alterações: tem `button.btn.btn--primary.self-start` "Atualizar senha". Depois `div.danger-row` "Sair de todos os aparelhos" / "Use se você entrou em um computador que não é seu." + `form[data-async]` com `button.btn.btn--danger-outline.btn--xs` "Sair dos outros aparelhos".
  - **Pedidos e acessos**: `div.card.card--clip` (não é form): cabeçalho com texto "De onde veio cada curso da sua conta. Compras feitas na Hotmart ou Eduzz aparecem aqui depois da migração."; `div.table-wrap.table-wrap--bare` > `table.table.table--w640` com Curso, Origem (`badge--gray` "Hotmart · HP1234", "Eduzz · 123", "Compra no site · #1042", "Liberado pela equipe", "Importado"), Liberado em, Acesso (`badge--success` "Vitalício" ou `badge--warning` "Até dd/mm/aaaa"); rodapé "Algum curso que você comprou não aparece?" + `a.btn.btn--secondary.btn--xs` "Avisar o suporte". Pedidos pagos no site continuam listados abaixo com a tabela do v1.
  - **Avisos por e-mail**: 4 `div.switch-row` com `button.switch[role=switch]` + hidden: "Respostas às minhas dúvidas" / "Quando o instrutor ou outro aluno responder."; "Lembrete de aula ao vivo" / "1 hora antes, com o link do Google Meet."; "Certificado pronto" / "Quando você concluir um curso."; "Novos cursos e condições especiais" / "No máximo 2 por mês."
- Respostas: `json_ok(toast="Alterações salvas")`; senha: `json_ok(toast="Senha atualizada. Use a nova senha no próximo acesso", reload=True)`.

### 7.8 Celular · `AlunoV2Mobile.dc.html` · `aluno-celular.png`

Não é uma tela nova: são as mesmas telas abaixo de 720 px. Já está tudo no CSS (seções 48 e 50) e no `bottom_nav.html`. Conferir em 390 × 844: barra inferior com 5 itens e o ativo em azul; sem menu lateral; busca só ícone; no player, o vídeo ocupa a largura toda sem borda arredondada, o botão de concluir ocupa a largura toda, a lista de aulas vira a aba "Aulas" e a faixa "Aula concluída" vira folha presa no rodapé; botões dos cards com largura total; nenhum alvo de toque menor que 44 px; nenhuma rolagem horizontal.

---

## 8. Painel administrativo v2 · tela a tela

Mesmo formato. Em todas: `{% block crumbs %}` com o caminho, `<h1>` dentro do conteúdo, e os padrões da seção 4.

### 8.1 Início · `AdminV2Inicio.dc.html` · `admin-inicio.png`

- Rota `painel:dashboard`, template `painel/dashboard.html` (substitui). `crumbs`: "Início". `topbar_actions`: `a.btn.btn--secondary.btn--sm` ícone `eye` "Ver como aluno" (para `dashboard` do aluno, nova aba).
- Contexto: `period` (7/30/90, padrão 30), `metrics` (receita líquida do período com contagem de pedidos pagos; novos alunos com "+N no período"; alunos ativos "N de M" = assistiram alguma aula no período; certificados emitidos), `attention` (lista), `activity` (8 últimos `ActivityLog`), `courses_table` (publicados com alunos, progresso médio, concluíram, receita do período).
- Ordem: `div.row.row--between` com `div.stack` (`h1.page-title` "{Bom dia|Boa tarde|Boa noite}, {primeiro nome}" e `p.page-intro` "Resumo da escola e o que precisa da sua atenção hoje.") e `div.seg` de período (`a.seg__btn` "7 dias", "30 dias", "90 dias"); `div.metric-grid` com 4 `div.metric` ("Receita", "Novos alunos", "Alunos ativos", "Certificados emitidos"; rodapés como no protótipo: "0 pedidos pagos · últimos 30 dias", "+4 no período", "assistiram a alguma aula", "nenhuma conclusão ainda"); `div.split` com `section.card.card--clip.split__main` "Precisa da sua atenção" (`div.task-list__head` com título + "N pendências") e `aside.split__side` "Atividade recente" (`ul.timeline`, link "Ver tudo"); `section.card.card--clip` "Cursos" com link "Gerenciar cursos" e `table.table` (Curso com `course-tile--thumb`, Alunos, Progresso médio com barra, Concluíram, Receita).
- "Precisa da sua atenção" (cada um só aparece se > 0), `a.task` com ícone, título, meta e `span.btn.btn--secondary.btn--xs`:
  - dúvidas sem resposta: `task__icon--danger` ícone `chat`, "N dúvidas sem resposta", "A mais antiga está esperando há 2 dias", "Responder" → `painel:community`;
  - aulas publicadas com vídeo que não é Vimeo: `--warn` ícone `video`, "N aulas publicadas ainda usam vídeo do YouTube", "Troque pelo link do Vimeo antes de abrir as vendas", "Corrigir" → curso com mais casos;
  - certificado sem responsável (`SiteSettings.signer_name` vazio): `--warn` ícone `award`, "Certificado sem responsável técnico", "Os certificados saem sem assinatura até você preencher", "Configurar" → `painel:settings?secao=certificado`;
  - alunos que nunca acessaram: ícone `users`, "N alunos nunca acessaram", "Reenvie o e-mail de primeiro acesso em massa", "Ver alunos" → `painel:students?filtro=nunca`.
  Vazio: `div.task-list__done` ícone `check-circle` "Nada pendente. Tudo em dia."

### 8.2 Cursos · `AdminV2Cursos.dc.html` · `admin-cursos.png`

- Rota `painel:courses`. `crumbs`: "Cursos". Contexto: `courses` filtrados (`status`, `q`, `categoria`), contagens por status, `categories`.
- Ordem: cabeçalho (`h1.page-title` "Cursos", `p.page-intro` "Conteúdo, página de venda e configurações de cada treinamento.", `button.btn.btn--primary[data-dialog-open=dlg-new-course]` "Novo curso"); `div.row.row--between` com `div.seg` ("Todos 5", "Publicados 5", "Rascunhos 0", "Arquivados 0") e `form.toolbar[method=get]` (busca "Buscar curso" + select "Todas as categorias"); lista de `article.card` (um por curso): `span.course-tile.course-tile--64`, `div.stack` com badge de status (`badge--success` "Publicado", `badge--gray` "Rascunho", `badge--warning` "Arquivado"), título (`a.cell-title` para `course_content`), meta "Essenciais AHA · 2 módulos · 4 aulas · 28 min"; 3 números (Alunos, Progresso médio com "–" quando sem alunos, Preço `|brl`); alertas em `span.text-13.text-danger` com ícone `alert` ("4 aulas ainda usam YouTube", "Carga horária não informada"); `a.btn.btn--secondary.btn--sm` "Abrir curso" e menu `⋯` (`.popover` com `menu__item`s: "Abrir curso", "Ver como aluno", "Abrir página de venda", "Copiar link de venda" (`data-copy` + `data-copy-toast="Link de venda copiado"`), "Duplicar curso" (POST, vai para o novo rascunho com toast "Cópia criada como rascunho"), separador, "Mover para rascunho" (POST, toast com Desfazer), `menu__item--danger` "Arquivar curso" (abre o diálogo de alto risco)). No fim, `button.card.card--dashed` grande "Novo curso" / "Começa como rascunho, só você vê".
- Vazio por filtro: `div.empty-state` "Nenhum curso {arquivado|em rascunho}" + "Limpar filtros". Sem nenhum curso: "Crie seu primeiro curso" + botão.

### 8.3 Curso · Conteúdo · `AdminV2CursoConteudo.dc.html` · `admin-curso-conteudo*.png`

- Rota `painel:course_content`, template `painel/course_content.html` (substitui `course_lessons`). `crumbs`: "Cursos" (link) / título.
- **Cabeçalho do curso** (parcial `painel/_course_head.html`, usado nas 3 abas): `div.card.card--clip` > `div.course-head` (`span.course-tile.course-tile--56`, `div.course-head__text` com `div.row.gap-8` (`h1.course-head__title` + badge de status) e `span.course-head__meta` "2 módulos · 4 aulas · 28 min de vídeo · 3 alunos · R$ 150,00", `div.row.gap-10` com `a.btn.btn--secondary.btn--sm` "Ver como aluno" e `a.btn.btn--ghost.btn--sm` ícone `external` "Página de venda ao vivo" (só publicado)) e `nav.tabs` com `a.tab` "Conteúdo", "Página de venda", "Configurações", "Alunos" + `span.tab__count` (link para `painel:students?curso=<slug>`), `aria-current="page"` na atual.
- Conteúdo: `div.split` com `main.split__main` e `aside.split__side.split__side--320`.
  - `div.row.row--between`: `span.text-14.muted` "Arraste pela alça para reordenar. A ordem salva sozinha." e `button.btn.btn--ghost.btn--xs` "Recolher tudo".
  - Um `section.card.card--clip` por módulo (`builder-module` do v1): cabeçalho com alça, chevron, "Módulo 1 · {título}" e "2 aulas · 2 publicadas", menu `⋯` (Renomear, Programar liberação, Excluir módulo). Linhas `div.builder-lesson` (v1) com: alça, ícone de vídeo em tile (vermelho quando não é Vimeo), título "N. {título}", meta ("Vimeo · 8 min · 1 material"; em vermelho `builder-lesson__meta--warn` "YouTube · troque pelo Vimeo" ou "Sem vídeo"), badge `badge--success` "Publicada" / `badge--warning` "Rascunho", e `a.btn.btn--secondary.btn--xs` "Editar" (`href="?aula=<id>"` + `data-drawer-url="{% url 'painel:lesson_drawer' course.id l.id %}"` + `data-drawer-target="drawer-aula"` + `data-drawer-param="aula"` + `data-drawer-value="<id>"`). A linha toda é clicável do mesmo jeito. Linha aberta: `is-editing`.
  - No fim de cada módulo: `div.inline-create` com `input.input[data-inline-create-url]` placeholder "+ Nova aula: digite o título e tecle Enter". Depois dos módulos: `button.btn.btn--dashed.btn--block` "Adicionar módulo" (abre diálogo simples "Novo módulo" com o título).
  - Lateral: `section.card.card--pad-sm` "Pronto para vender?" com "3 de 6" e `div.ready-item` (`is-ok` com `check-circle`, `is-warn` com `alert`, pendente com `circle`): "Capa e descrição", "Preço e carga horária", "Pelo menos uma aula publicada", "Vídeos no Vimeo" (sub "4 aulas ainda usam YouTube"), "O que o aluno vai aprender" (sub "Aparece na página de venda"), "Assinatura do certificado" (sub "Configuração geral da escola"). Cada pendente é link para onde se resolve. Depois `section.card.card--pad-sm` "Liberação do conteúdo" com o resumo ("Todas as aulas ficam disponíveis assim que o aluno é matriculado.") e `a.btn.btn--secondary.btn--xs` "Programar liberação" (para `course_settings#liberacao`).
- **Painel da aula** `dialog.drawer.drawer--600#drawer-aula` (`data-autoopen="aula"` quando há `?aula=`), miolo `painel/_lesson_drawer.html`: `form.stack[method=post][data-dirty-form][data-dirtybar="lesson-dirty"][data-async]`; cabeçalho com `drawer__eyebrow` "Módulo 1 · Aula 2 de 4", `drawer__title`, botões anterior/próxima (`a.icon-btn.icon-btn--plain` com `data-drawer-url` das vizinhas) e fechar; corpo: `div.seg` "Publicada"/"Rascunho" (radios estilizados `seg__btn`), `label.check` "Aula grátis na página de venda", "Título", "Vídeo" (URL; alerta `alert--warning` "Este link é do YouTube. A plataforma usa o Vimeo, com restrição de domínio. Troque antes de abrir as vendas." quando não for Vimeo; quando for Vimeo e a duração não veio: hint do v1), "Descrição" (hint "Aparece abaixo do vídeo, para o aluno."), "Materiais de apoio" (lista com renomear e excluir + `dropzone` "Adicionar PDF" / "Arraste para cá · até 20 MB por arquivo"), `details` "Mais opções" (duração manual em minutos, data de liberação própria). Rodapé `drawer__foot--between`: `button.btn.btn--danger-text` "Excluir aula" (POST `lesson_delete`, sem diálogo, toast com Desfazer), à direita `span.text-13.fw-600.text-warning[data-dirty-msg]` "● Alterações não salvas" (só quando sujo; use o `[data-dirty-msg]` com a barra `lesson-dirty` em versão inline `span`), "Cancelar" e "Salvar aula".
  Salvar: `json_ok(toast="Aula salva", replace={"#lesson-row-<id>": html_da_linha})` e o drawer fecha.

### 8.4 Curso · Página de venda · `AdminV2CursoVenda.dc.html` · `admin-curso-venda*.png`

- Rota `painel:course_sales`. Mesmo cabeçalho. `div.split`: `form.split__main[data-dirty-form][data-dirtybar="dirtybar"][data-async]` e `aside.split__side.split__side--380` com a prévia.
- Form (cards): "Apresentação" ("Chamada curta" com contador "87 de 160 caracteres" (hint atualizado pelo servidor ao salvar; contador ao vivo é opcional), "Descrição completa"), "Capa" (miniatura 3:2, hint "3:2, mínimo 1200 × 800 px. Você ajusta o enquadramento depois de enviar.", "Trocar imagem", "Remover"), "O que o aluno vai aprender" ("4 itens · ideal entre 4 e 6", repeater do v1 com "+ Adicionar item"), "Para quem é" (hint "Se ficar vazio, a seção não aparece no site."), "Perguntas frequentes" (`CourseFAQ` em repeater: pergunta + resposta; "+ Pergunta"), "Aulas grátis" ("Quem ainda não comprou pode assistir às aulas marcadas como grátis na aba Conteúdo." + lista ou "Nenhuma aula grátis" + "Escolher aula" → `course_content`).
- Prévia (`div.preview-frame` com `div.preview-frame__bar` contendo "Pré-visualização" e `div.seg` com dois `a.seg__btn`: "Computador" (`?previa=computador`) e "Celular" (`?previa=celular`, acrescenta `preview-frame--mobile`)). Conteúdo: miniatura fiel do topo da página pública com os dados salvos e "Abrir página completa em nova aba". A prévia mostra o **salvo**, não o digitado; hint "A prévia atualiza quando você salva."
- Barra: "Você tem alterações não salvas na página de venda." / Descartar / Salvar alterações.

### 8.5 Curso · Configurações · `AdminV2CursoConfig.dc.html` · `admin-curso-config.png`

- Rota `painel:course_settings`. Mesmo cabeçalho. `div.split` com `nav.vtabs` à esquerda (âncoras `#geral`, `#preco`, `#liberacao`, `#ao-vivo`, `#certificado`, `#risco`; não são abas, é um sumário que rola) e um único `form[data-dirty-form][data-dirtybar="dirtybar"][data-async]` com as seções em cards (cada `section` com `id` e `data-dirty-label` nos campos):
  - **Geral** ("Nome e identificação do curso no site e no painel."): Título, Categoria, Sigla da capa, Endereço da página (prefixo "cetremer.com.br/cursos/", hint "Trocar o endereço quebra links já divulgados. O antigo redireciona por 90 dias.").
  - **Preço e acesso** ("Usado no checkout e no certificado."): Preço (`input.input` texto com prefixo R$, ver regra 1.5), Carga horária (sufixo "horas"), Prazo de acesso (select: Vitalício, 6, 12, 24 meses após a matrícula; hint "Alunos importados contam o prazo a partir da importação.").
  - **Liberação do conteúdo** ("Escolha quando cada parte fica disponível para o aluno."): dois `label.option-card` com radio ("Tudo na matrícula" / "O aluno vê todas as aulas no primeiro acesso."; "Programada por módulo" / "Libera em dias após a matrícula ou numa data."); quando programada, `table.table.release-table` (Módulo, Libera [select: Na matrícula, Dias após a matrícula, Em uma data], Valor [número de dias ou data]); `label.check` "Avisar o aluno por e-mail quando um módulo for liberado".
  - **Aulas ao vivo** ("Aparecem em Aulas ao vivo, na área do aluno."): "Link do Google Meet" (padrão do curso) e a **lista de encontros** (`LiveSession`): tabela Data, Horário, Título, Gravação, com `button.btn.btn--secondary.btn--xs` "Adicionar encontro" que abre `dialog` com data, início, fim, título, apresentador, link próprio (opcional), link da gravação (opcional). Salva por `painel:live_session_save` (fora do form principal). O campo "Agenda pública do Google" do protótipo **sai** (seção 11).
  - **Certificado** ("Assinatura e logo ficam em Configurações da escola."): switch "Emitir certificado neste curso" com hint "Liberado com 100% das aulas publicadas concluídas e nome e CPF preenchidos."; alerta quando `signer_name` vazio: "Responsável técnico ainda não definido." + link "Definir"; `a.btn.btn--ghost.btn--xs` "Ver certificado de exemplo" (abre o certificado com dados fictícios marcados "EXEMPLO").
  - **Zona de risco** (`section.card.card--danger`, fora do form, "Ações que mudam o acesso dos alunos."): `div.risk-row` "Mover para rascunho" / "Sai do site. Os N alunos matriculados continuam assistindo." / `btn--secondary` (sem diálogo, toast com Desfazer); "Arquivar curso" / "Some do site e da área do aluno. Pode ser restaurado depois." / `btn--danger-outline` (diálogo alto risco digitando a sigla); "Excluir definitivamente" / "Só disponível para cursos sem alunos e sem pedidos." / `btn--danger` desabilitado quando houver alunos ou pedidos (`title` e `aria-describedby` explicando).
- Barra: "N alterações não salvas: {rótulos}." / Descartar / Salvar alterações. O texto vem do `ui.js` pelos `data-dirty-label` ("liberação do conteúdo", "prazo de acesso", "preço"...).

### 8.6 Alunos · `AdminV2Alunos.dc.html` · `admin-alunos.png`

- Rota `painel:students`. `crumbs`: "Alunos". Contexto: alunos filtrados e paginados (25 por página), contagens por filtro, `courses`.
- Ordem: cabeçalho (`h1.page-title` "Alunos", `p.page-intro` "4 alunos · 7 matrículas em 3 cursos", `a.btn.btn--secondary` "Importar CSV", `button.btn.btn--primary[data-dialog-open=dlg-enroll]` ícone `plus` "Matricular aluno"); `div.chips` de filtro (`a.chip` com número: "Todos", "Ativos", "Nunca acessaram", "Concluíram algum curso", "Sem nome ou CPF"; "Importados hoje" aparece só depois de importar); `form.toolbar[method=get]` (busca "Buscar por nome, e-mail ou CPF" + select curso); `form[method=post][data-bulk][data-bulkbar="bulkbar-alunos"]` com a `div.bulkbar#bulkbar-alunos[hidden]` ("N selecionados", botões `name=action`: "Liberar curso" (abre select de curso no próprio bulkbar), "Reenviar acesso", "Exportar", `btn--danger-text` "Remover de um curso" (diálogo afeta alunos), `button[data-bulk-clear]` "Limpar seleção") e `div.table-wrap` > `table.table.table--w860`: checkbox, Aluno (avatar + nome + e-mail, link para a ficha), Cursos (`badge`s com a sigla na cor da capa), Progresso médio (barra + %), Último acesso ("há 1 hora", "ontem", `text-danger` "Nunca acessou"), Situação (`badge--success` "Ativo", `badge--warning` "Aguardando 1º acesso", `badge--gray` "Sem cursos"), seta `chevron-right`. Rodapé: "Mostrando 4 de 4 alunos" + "Anterior"/"Próxima".
- Vazio geral: `div.empty-state` "Nenhum aluno ainda" / "Importe a lista da Eduzz ou da Hotmart, ou matricule alguém manualmente." / "Importar CSV" + "Matricular". Busca sem resultado: "Nenhum aluno com "{q}" no curso {curso}" / "Confira a grafia ou procure em todos os cursos." / "Limpar filtros".

### 8.7 Ficha do aluno · `AdminV2Aluno.dc.html` · `admin-aluno*.png`

- Rota `painel:student_detail`. `crumbs`: "Alunos" / nome.
- Cabeçalho: avatar 64, `h1.page-title.page-title--sm` nome + badge situação, "aluno@test.com · aluno desde 10/11/2026 · liberado pelo admin"; ações `btn--secondary` "Reenviar e-mail de acesso" (POST, toast "E-mail de acesso enviado para {email}"), `btn--primary` ícone `plus` "Liberar curso" (diálogo matrícula com o e-mail preenchido) e `⋯` (Editar dados, Enviar link para criar nova senha).
- `nav.tabs` (links `?aba=`): "Cursos 3", "Pedidos 0", "Certificados 0", "Atividade 3".
- `div.split`:
  - Cursos: um `section.card.card--clip` por matrícula: `course-tile`, título, barra + "1 de 4 aulas", "desde 10/11", `button.btn.btn--ghost.btn--xs` "Ver aulas"/"Ocultar aulas" (`aria-expanded`), `⋯`. Aberto: linhas por aula com marca (verde concluída), título, "concluída hoje, 08:40" / "não assistida" / "rascunho, não visível", e `form[data-async]` com botão "Desmarcar" ou "Marcar concluída" (`action=toggle_lesson`, toast "Aula marcada como concluída para {nome}" com Desfazer). Rodapé do card: `btn--link` "Zerar progresso do curso" (diálogo afeta alunos: "Zerar o progresso de {nome} no {curso}?" / "As N aulas concluídas voltam para não assistidas. Não dá para desfazer.") e `btn--link-danger` "Remover acesso a este curso" (diálogo do protótipo de Padrões: "Remover acesso ao BLS?" / "{nome} deixa de ver o curso na hora. O progresso (1 de 4 aulas) fica guardado e volta se você liberar de novo." / check "Avisar o aluno por e-mail" / "Remover acesso").
  - Pedidos, Certificados: tabelas simples; vazio "Nenhum pedido deste aluno" / "Nenhum certificado emitido".
  - Atividade: `ul.timeline` com o `ActivityLog` do aluno.
  - Lateral: card "Dados pessoais" (`dl.dl--compact`: Nome completo, CPF em vermelho "Não informado" quando falta, E-mail; botão "Editar" abre drawer com os 3 campos; alerta `alert--warning` "Sem CPF o certificado fica bloqueado." + `btn--link` "Pedir ao aluno por e-mail" (manda e-mail padrão com link para Minha conta, toast "Pedido enviado para {email}")); card "Acesso" (Último acesso, Primeiro acesso "feito em" ou "ainda não", E-mail de acesso "enviado em", `btn--secondary` "Enviar link para criar nova senha"); card "Anotações internas" (`textarea[data-autosave-url]` placeholder "Visível só para a equipe. Ex.: pediu reenvio do certificado por WhatsApp." + `span.autosave-state[data-autosave-state]` e hint "Salva automaticamente.").

### 8.8 Importar alunos · `AdminV2Importar.dc.html` · `admin-importar.png`

- Rota `painel:students_import`. 4 passos com `div.stepper` ("Arquivo", "Colunas", "Cursos", "Revisar"; feitos com `is-done`, atual `is-current`). `p.page-intro` "Nada é importado até você confirmar no último passo." Estado na sessão (v1 4.10), passo por `?passo=`.
  1. Arquivo: origem (`div.seg` "Eduzz", "Hotmart", "Outra planilha") + dropzone "Envie o CSV exportado" + link "Como exportar da Eduzz" / "da Hotmart" (abre `details` com 3 passos).
  2. Colunas: `table.table` "Coluna no arquivo" / "Exemplo" (1ª linha) / "Usar como" (select: Nome completo, E-mail, CPF, Código do pedido, Ignorar), pré-preenchido pelo reconhecimento de cabeçalhos do v1 (+ "Código do pedido" para `external_ref`); `p.text-14` "Reconhecemos 3 de 4 colunas. Ajuste se algo estiver errado."; hint "E-mail é obrigatório. Nome e CPF são opcionais, mas o certificado só sai com os dois."; rodapé "Voltar" / "Passo 2 de 4" / "Continuar".
  3. Cursos: checkboxes dos cursos + check "Enviar e-mail de acesso agora".
  4. Revisar: números (novos, já cadastrados, ignorados com motivo) e tabela das linhas com problema; botão "Importar N alunos". Durante: botão `is-busy` "Importando 125 alunos…" e linhas fantasma. Depois: redirect `painel:students?filtro=importados-hoje` com o toast da seção 4.4.

### 8.9 Pedidos · `AdminV2Pedidos.dc.html` · `admin-pedidos*.png`

- Rota `painel:orders` (só admin). Enquanto o gateway não existir: `div.alert.alert--info` "Os pedidos entram aqui quando o pagamento estiver ligado. Até lá, esta lista mostra só pedidos de teste." e sem dado de exemplo (o protótipo mostra linhas "Aluno Exemplo" só para o layout).
- Ordem: cabeçalho (`h1.page-title` "Pedidos", select "Período" com Últimos 30 dias, Este mês, Mês passado, Este ano; `a.btn.btn--secondary` "Exportar CSV"); `div.metric-grid` com 4 `metric--sm` ("Receita líquida", "Pedidos pagos", "Aguardando pagamento", "Ticket médio"); `div.seg` de status ("Todos", "Pagos", "Aguardando", "Recusados", "Reembolsados"); tabela (Pedido "#1042" + "10/11 · 09:12", Aluno + meio de pagamento "Pix" / "Cartão · 3x", Curso sigla, Valor, Status badge); clicar abre `dialog.drawer#drawer-pedido` (`?pedido=`) com: "#1042 · R$ 450,00" + badge, `dl` (Aluno com link para a ficha, Curso, Pagamento, ID no gateway), "Linha do tempo" (`ul.timeline`: Pedido criado, Pagamento confirmado no Pix, Acesso liberado e e-mail enviado) e rodapé "Reenviar acesso" + `btn--danger-outline` "Reembolsar" (diálogo afeta alunos: "Reembolsar o pedido #1042?" / "{aluno} perde o acesso ao {curso}. O valor volta pelo gateway em até 7 dias." / "Reembolsar").

### 8.10 Comunidade (admin) · `AdminV2Comunidade.dc.html` · `admin-comunidade.png`

- Rota `painel:community`. Cabeçalho: `h1.page-title` "Comunidade", `p.page-intro` "Dúvidas dos alunos, respondidas como CETREMER.", à direita `label.check` com switch "Me avisar por e-mail a cada nova dúvida" (`notify_new_questions`, salva na hora com toast "Preferência salva").
- Mestre e detalhe (`div.card.card--clip` em duas colunas: lista 380 px e conversa): lista com `div.seg` ("Sem resposta (3)", "Respondidas", "Ocultas"), busca "Buscar por aluno, curso ou palavra", e `a.list-row-link` por dúvida (avatar, nome, quando, título, badge "BLS · Aula 2", "esperando há 2 dias" em vermelho acima de 24 h; selecionada `is-selected`; links `?duvida=<id>` sem drawer: a página recarrega a coluna da direita por link normal). Detalhe: título, "{aluno} · {curso} · Aula N · {título da aula}" (link para a aula), ações `btn--ghost.btn--xs` "Fixar", "Ocultar" (toast com Desfazer), "Ver aluno"; a pergunta; respostas; e o form "Responder como CETREMER" (`textarea` "Escreva a resposta. O aluno é avisado por e-mail.", `label.check` "Ir para a próxima sem resposta" marcado por padrão, `btn--primary` "Publicar resposta"). Sucesso: se marcado, redirect para a próxima sem resposta; contador do menu atualiza (`counts={"[data-pending-count]": n}`).
- Vazio "Sem resposta": `div.empty-state` ícone `check-circle` "Nenhuma dúvida esperando resposta" / "Quando um aluno perguntar, ela aparece aqui e você recebe um e-mail se ativou o aviso."

### 8.11 Configurações · `AdminV2Config.dc.html` · `admin-config*.png`

- Rota `painel:settings` (só admin). `h1.page-title` "Configurações", `p.page-intro` "Cada seção salva separadamente." `div.settings-layout` com `nav.vtabs` (links `?secao=`: Escola, Pagamentos, E-mails, Certificado, Equipe) e o form da seção ativa com barra de alterações.
  - **Escola**: "Nome exibido", "WhatsApp de suporte" (hint "Usado no botão de ajuda da área do aluno."), "Logo" (hint "PNG ou SVG com fundo transparente. Aparece no site e no certificado." + "Enviar logo"), "Termos de uso" (hint "Obrigatório para vender. Hoje o link do site leva a lugar nenhum." enquanto vazio), "Política de privacidade". Botões da barra: "Descartar" / "Salvar dados da escola".
  - **Pagamentos**: card de status (`badge--warning` "Modo de teste", "Gateway: [a definir]", "Nenhuma conta conectada. As vendas usam a simulação.", `btn--secondary` "Testar conexão"), "Chave da API" com o campo secreto do v1 ("Nenhuma chave salva" / "Definir chave"; hint "Chaves salvas nunca aparecem completas. Para trocar, defina uma nova."), switch "Usar ambiente de testes" / "Nenhuma cobrança real enquanto estiver ligado.". Barra: "Salvar pagamentos".
  - **E-mails**: campos do v1 (remetente, servidor, porta, usuário, senha secreta, TLS) + `btn--secondary` "Enviar e-mail de teste" (manda para o usuário logado, toast "E-mail de teste enviado para {email}" ou erro com a mensagem do servidor SMTP).
  - **Certificado**: responsável técnico (nome, cargo e registro), imagem da assinatura, prévia pequena do rodapé do certificado.
  - **Equipe**: "Equipe com acesso ao painel" + `btn--primary.btn--sm` "Convidar pessoa" (diálogo: e-mail + papel; cria usuário com senha inutilizável e manda o link de primeiro acesso); lista: avatar, nome, e-mail, papel (select "Administrador" / "Instrutor (conteúdo e comunidade)"; o Dono não muda), `btn--link-danger` "Remover" (diálogo afeta pessoas: "Remover {nome} da equipe?" / "Perde o acesso ao painel na hora. O que essa pessoa criou continua no lugar."); hint "Instrutor edita cursos e responde dúvidas. Não vê pedidos nem configurações."

### 8.12 Padrões · `AdminV2Padroes.dc.html` e `AlunoV2Padroes.dc.html`

São as fichas de regras. O conteúdo delas já está nas seções 4, 9 e 10 deste documento. Use para conferir.

---

## 9. Estados compartilhados

- **Carregando:** no lugar de listas que vêm por fetch (painel lateral, Ctrl K), 3 linhas `.sk` (título 60%, linha 80%, linha 40%). Botão que envia: `.is-busy`. Nenhuma tela inteira em branco.
- **Vazio:** sempre `div.empty-state` com ícone, título que diz o que não tem, texto que diz o próximo passo e, quando houver, um botão. Filtro sem resultado sempre oferece "Limpar filtros".
- **Erro de rede em fetch:** toast de erro que não some; a interface volta ao estado anterior (nada de estado "meio salvo").
- **Erro de formulário:** resumo `div.form-errors[data-form-errors]` no topo do card (`role=alert`, texto em `[data-form-errors-text]`), mensagem embaixo de cada campo (`span.error-text` + `aria-invalid` + `aria-describedby`) e foco no primeiro. O `ui.js` faz isso a partir de `json_errors(form)`; sem JS, o template renderiza o mesmo a partir de `form.errors`.
- **Vídeo indisponível** (o iframe do Vimeo dispara `error` ou a aula não tem vídeo): `div.player__empty` "Este vídeo está indisponível agora. A equipe já foi avisada." + `a.btn.btn--light.btn--sm` "Falar com o suporte"; registrar em log com o id da aula.

---

## 10. Correções do sistema atual (encontradas na auditoria de 10/11/2026)

Cada item tem um teste novo em `tests_v2.py` do app correspondente.

1. **Preço zera ao salvar o curso no painel.** O `<input type="number">` recebe "150,00" e o navegador manda vazio; o form salva 0. Corrigir com campo de texto e `clean_price` (aceita "150", "150,00", "1.234,56"). Teste: POST com "150,00" mantém `Decimal("150.00")`.
2. **Módulo repetido no player:** "Módulo 1 · Módulo 1: Introdução...". O título do módulo no seed já contém "Módulo 1:". Corrigir o dado (data migration que remove o prefixo `^Módulo \d+:\s*` dos títulos) e manter o template com "Módulo {n} · {título}". Teste: título renderizado sem "Módulo 1 · Módulo".
3. **Marcar como concluída não dava aviso** e a lista lateral ("0 de 2 aulas") e o card do certificado ("Faltam 4") não atualizavam. Resolvido pelo `player.js` + JSON da 6.4. Teste da view: JSON tem `module`, `remaining`, `next`.
4. **Desmarcar sem aviso**: resolvido pelo toast com Desfazer.
5. **Última aula sem fechamento**: janela de conclusão.
6. **Vídeo não retomava nem concluía sozinho**: `save_position` + `player.js`.
7. **Aulas ao vivo mostrava uma Agenda do Google com feriados** (o embed apontava para uma agenda pública qualquer) **e o botão do Meet ficava sempre ativo**: trocado por `LiveSession` e estados.
8. **Página do curso do aluno saía da área do aluno** (layout público, sem progresso, botão no fim): `course_home` + redirect.
9. **Certificado bloqueado mostrava o mesmo ✓ em requisito não cumprido**: no `certificate_error.html`, o ícone `check` só aparece dentro de `.req-item.is-ok`; pendente mostra a marca vazia (`req-item__mark` sem ícone). Teste: requisito pendente não contém o SVG de check.
10. **Textos:** "1 aulas" (usar `plural_pt`), logo "Plantão" cortado no card de certificados (usar `course-tile` com `short_name`, nunca a imagem do logo do curso redimensionada), saudação com "jane_student" (usar `user_first_name`).
11. **Comunidade abria em "Discussão geral" (vazia)** em vez de todas; sem busca; formulário sempre aberto ocupando a lateral.
12. **Minha conta** com 3 botões Salvar separados, senha sem mostrar, endereço que não existe mais e "Meus pedidos" vazio para quem tem curso importado.
13. **Topo diferente em cada página** (seção 3.1).
14. **Seed com vídeos do YouTube:** trocar por um vídeo de teste do Vimeo (qualquer vídeo público com incorporação liberada para `localhost`) em pelo menos 2 aulas, para testar retomada e 90%.
15. **Caixa de dúvida da aula não mostrava as dúvidas feitas**: aba Dúvidas.

---

## 11. Onde o protótipo simplifica (siga este texto, não o protótipo)

- **Posição do toast:** nos protótipos do aluno o toast aparece no alto à direita só para ficar visível no canvas. No código: canto inferior direito (seção 4.1), igual ao admin.
- **Tempo do toast:** 5 s, 8 s com Desfazer, erro não some (o protótipo do aluno usa 6 s fixos).
- **"Simular o momento"** em Aulas ao vivo é controle só do protótipo. Não existe na tela real.
- **"Preencher exemplo (protótipo)"** em Minha conta não existe na tela real.
- **E-mail do certificado:** o protótipo diz "Também enviamos o PDF". Não há geração de PDF no servidor; o e-mail leva o link do certificado. Toast: "Certificado emitido. Enviamos o link para seu e-mail".
- **Configurações do curso · Aulas ao vivo:** o protótipo do admin mostra "Agenda pública do Google". Ele sai; entra a lista de encontros (8.5), porque a área do aluno v2 lista os encontros cadastrados.
- **Busca no protótipo** mostra resultados fixos para "compress". Na tela real vêm da view `search`.
- **Dados:** nomes, datas, contagens e pedidos dos protótipos são exemplos. Tudo vem do banco.
- **Página de venda · prévia "Celular":** no protótipo troca na hora; na tela real pode ser link `?previa=celular` (8.4).

---

## 12. Fases, prompts e critério de pronto

Faça na ordem. Ao fim de cada fase: testes passando, `python manage.py check` sem aviso, conferir as capturas da fase lado a lado, commit, e uma linha no `docs/redesign-relatorio.md` (seção "v2"). Não comece a próxima com a anterior quebrada.

| Fase | Escopo | Pronto quando |
| --- | --- | --- |
| A0 | Instalação do pacote (seção 2), rotas provisórias | Todas as páginas abrem; toast de teste aparece com `toast(request, "Teste")` |
| A1 | Modelos e migrations da 6.1, seed da 6.6, `courses/services.py` | `migrate` e `migrate zero` de cada app funcionam; seed carrega; testes de `services` |
| A2 | Layout do aluno: topo, menu, sino, avisos (`Notification` + `notify`), Ctrl K do aluno, barra inferior | Início abre com o topo novo; avisos marcam lidos; busca devolve resultados; 390 px sem rolagem lateral |
| A3 | Player (7.3) com `player.js`; apagar `aluno.js`; endpoints `toggle_progress`/`complete_lesson`/`save_position` | Fluxo completo: marcar, desfazer, faixa de próxima, 90%, retomar, última aula abre a janela |
| A4 | Início (7.1) e Página do curso (7.2), redirect do `course_preview` para aluno | Todos os estados de "Próximos passos" e filtros conferem com as capturas |
| A5 | Aulas ao vivo (7.4), `.ics`, comandos `live_reminders` e `release_modules` | Estados scheduled, soon, live e gravações; `.ics` abre no Google Agenda e no Outlook |
| A6 | Certificados (7.5) com emissão no painel lateral; correção do bloqueado | Emitir, copiar link, LinkedIn; `?emitir=` abre o painel |
| A7 | Comunidade do aluno (7.6) | Filtros, conversa em painel, nova pergunta com sugestões e Desfazer, "Sim, resolveu" |
| A8 | Minha conta (7.7) | Barra de alterações, sair sem salvar, senha com regras, pedidos e acessos, avisos |
| B1 | Layout do admin (menu agrupado, topo, Criar, diálogos globais, Ctrl K do admin) | Instrutor não vê Pedidos nem Configurações e recebe 403 nas URLs |
| B2 | Início (8.1), Cursos (8.2), ActivityLog | Atenção e atividade com dados reais |
| B3 | Curso: Conteúdo (8.3) com painel da aula, criação rápida, excluir com Desfazer | Criar aula com Enter abre o painel; reordenar; excluir e desfazer |
| B4 | Curso: Página de venda (8.4) e Configurações (8.5), correção do preço | Preço "150,00" salva certo; liberação programada; encontros ao vivo |
| B5 | Alunos (8.6), Ficha (8.7), Importar (8.8) | Ação em massa; remover acesso guarda progresso; importação nos 4 passos |
| B6 | Pedidos (8.9), Comunidade (8.10), Configurações (8.11) | Responder abre a próxima; contador do menu cai; equipe com papéis |
| C | Revisão final: seção 13 inteira | Checklist marcado no PR |

### 12.1 Prompt para iniciar (cole no agente)

```
Vamos implementar o redesign v2 da CETREMER (admin v2 e área do aluno v2) em cima do v1 que você já fez.
O pacote está em docs/handoff-v2/. Leia HANDOFF-v2.md inteiro antes de qualquer código, depois abra
demo/componentes.html no navegador e olhe as capturas em capturas/.
Regras: siga a ordem de autoridade da seção 0.1; não invente classe, texto, rota ou comportamento;
se algo faltar, pare e me pergunte. Trabalhe só na branch redesign-v2.
Comece pela fase A0 (seção 2 e 12). Ao terminar a fase, rode os testes, compare com as capturas,
faça o commit "v2 fase A0: ..." e me mostre: lista do que mudou, testes antes e depois, e qualquer
diferença que você não conseguiu resolver. Não siga para a A1 sem minha resposta.
```

### 12.2 Prompt para cada fase seguinte

```
Fase {código} do HANDOFF-v2 (seção 12). Releia as seções citadas na linha da fase e as capturas
correspondentes antes de começar. Ao terminar: testes, python manage.py check, comparação com as
capturas (diga tela por tela o que confere e o que não), commit "v2 fase {código}: ...", e atualize
docs/redesign-relatorio.md. Pare e me mostre o resumo.
```

### 12.3 Prompt para rodar sem parar (quando você confiar)

```
Execute as fases {de} a {até} do HANDOFF-v2 em sequência, sem me esperar entre elas, seguindo o critério
de pronto de cada linha da seção 12. Se uma fase falhar no critério, pare nela, não avance, e escreva no
docs/redesign-relatorio.md o que travou. No fim, me entregue o relatório com: fases concluídas, commits,
testes antes e depois, e a lista de diferenças com as capturas.
```

---

## 13. Checklist final (copiar no PR)

- [ ] `cetremer-v2.css` colado no fim do `cetremer.css`; nenhum `style=""` novo além da barra de progresso (`grep -rn 'style="' templates/ | grep -v progress`)
- [ ] `aluno.js` removido; `player.js` e `ui.js` carregados só onde a seção 2 manda
- [ ] Nenhum `alert(`, `confirm(` ou `prompt(` no projeto (`grep -rn "confirm(\|alert(\|prompt(" static/ templates/`)
- [ ] Nenhum `messages.success` direto nas views novas: tudo por `toast()`
- [ ] Toda ação da seção 4 testada: aviso certo e destino certo
- [ ] Todo formulário funciona com JS desligado (testar 3: emitir certificado, salvar Minha conta, criar curso)
- [ ] Nenhum "1 aulas", "jane_student" ou "Módulo 1 · Módulo 1" em nenhuma tela (`grep` nos templates e conferência visual)
- [ ] Preço "150,00" salvo e reaberto continua R$ 150,00
- [ ] Retomada do vídeo e conclusão em 90% testadas com um vídeo real do Vimeo
- [ ] Instrutor recebe 403 em Pedidos e Configurações
- [ ] Aluno não acessa aula, dúvida, aviso ou certificado de outro aluno (teste com 2 usuários)
- [ ] 390 px: sem rolagem lateral em nenhuma tela; barra inferior no aluno; alvos de 44 px
- [ ] Teclado: Tab percorre topo, menu e conteúdo na ordem; Esc fecha painel, diálogo, menu e busca; foco volta para quem abriu
- [ ] Leitor de tela: abas anunciam selecionada; switch anuncia ligado/desligado; toast é lido
- [ ] Número de testes maior que antes; todos passando
- [ ] `docs/redesign-relatorio.md` com a seção v2 preenchida

---

## 14. Fora de escopo e perguntas para a cliente

Fora de escopo nesta entrega: gateway de pagamento (só a casca de Pedidos e Pagamentos), geração de PDF no servidor, aplicativo de celular, gamificação, chat em tempo real, "ver como este aluno" (impersonar).

Perguntas que dependem da cliente (deixe com valor padrão e anote no relatório):
1. Prazo de acesso padrão por curso (o padrão no seed é Vitalício).
2. Quem é o responsável técnico que assina os certificados (nome, cargo e registro).
3. Lista real de encontros ao vivo do Plantão Sem GPT e se as gravações ficam 30 dias.
4. Links reais de Termos de uso e Política de privacidade.
5. Arquivos reais de exportação da Eduzz e da Hotmart para conferir os cabeçalhos.
