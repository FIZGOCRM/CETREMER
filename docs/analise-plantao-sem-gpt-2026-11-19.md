# Análise do projeto GoMut / Emergensimples

Data da análise: 19/11/2026.

Escopo: leitura do código atual, da base local de demonstração e do PDF completo, incluindo suas imagens de referência. Não houve alteração de arquivos, criação de branch, instalação, execução de migrations ou acesso à VPS.

Documento encontrado: `docs/Plantao_Sem_GPT_Solicitacoes_TI.pdf`.
O nome difere do solicitado originalmente, `docs/solicitacoes-plantao-sem-gpt.pdf`. O arquivo encontrado tem 14 páginas: os itens 1 a 13 estão presentes, com o item 11 dividido entre as páginas 11 e 12.

“Existe” neste relatório significa identificado no código ou no banco local. Não significa que foi novamente homologado no navegador ou na produção nesta análise.

## 1. Stack e estrutura

### Framework, Python e dependências

O projeto usa Django.

| Item | Situação encontrada | Fonte |
|---|---|---|
| Django declarado | 5.2.19 | `requirements.txt:2` |
| Django instalado no ambiente virtual local | 4.2.30, confirmado por importação | `.venv/Lib/site-packages/django/` |
| Python do ambiente virtual local | 3.13.17 | `.venv/pyvenv.cfg` e consulta ao interpretador |
| Python do Docker | Imagem da família 3.13, fixada por digest | `deploy/Dockerfile:1` |
| Runtime anteriormente publicado | O relatório registra Python 3.13.18 e Django 5.2.19; não reconfirmado remotamente nesta análise | `docs/relatorio-publicacao-https.md` |

Dependências declaradas em `requirements.txt`:

- Django 5.2.19.
- asgiref 3.11.1.
- cryptography 46.0.3.
- Pillow 11.3.0.
- sqlparse 0.5.5.
- typing_extensions 4.16.0.
- Gunicorn 27.0.1.
- WhiteNoise 6.12.0.

Existe divergência entre as dependências declaradas e o Django instalado no ambiente virtual local. O comentário inicial de `core/settings.py` também ainda menciona a geração do projeto com Django 4.2.30.

### Organização e responsabilidades

| Diretório | Responsabilidade |
|---|---|
| `core/` | Settings, URLs principais, segurança, separação dos portais, e-mail, criptografia, arquivos de produção e backup SQLite |
| `users/` | Usuários, perfis, autenticação, primeiro acesso, importação, preferências, notificações, visitas e prévia administrativa |
| `courses/` | Cursos, módulos, aulas, acesso, progresso, player, quizzes, certificados, materiais e encontros ao vivo |
| `painel/` | Painel próprio do produtor: views, formulários, relatórios, gestão e URLs |
| `sales/` | Pedidos, ofertas, assinaturas, migração de mensalidades e infraestrutura técnica do Asaas |
| `community/` | Tópicos, respostas, indicação de utilidade, solução e moderação |
| `support/` | FAQ, assuntos, chamados, histórico e votos |
| `templates/` | Templates Django, layouts e componentes compartilhados |
| `static/` | CSS, JavaScript, fontes referenciadas e recursos de marca |
| `deploy/` | Docker, Compose, agendador e backup |
| `docs/` | Handoff, decisões, relatórios e PDF analisado |

`painel` funciona como pacote de interface e gestão; não consta em `INSTALLED_APPS` e não possui models próprios. Os models estão nos outros apps.

Fontes: `core/settings.py:51`, `core/urls.py`, `painel/urls.py`.

Existe separação entre consultas, regras de negócio e HTTP:

- Consultas: `courses/selectors.py`, `painel/selectors.py`, `painel/reporting.py`.
- Casos de uso: `courses/services.py`, `users/services.py`, `community/services.py`, `support/services.py`.
- HTTP: arquivos de views desses módulos.
- Integrações: `courses/integrations/vimeo.py`, `sales/integrations/asaas/`.

É um repositório com backend e frontend integrados. Não foi encontrada aplicação frontend independente.

### Banco local

O banco configurado é SQLite, acessado pelo ORM do Django.

- Caminho padrão: `db.sqlite3`, conforme `core/settings.py:103`.
- Esse arquivo padrão não existe atualmente na raiz.
- Base local encontrada e consultada: `.venv/gomut-demo.sqlite3`.
- O lançador `.venv/run_v1.py` aponta explicitamente para essa base.
- A consulta foi realizada com `mode=ro` e `PRAGMA query_only=ON`.
- Os registros das migrations dos apps próprios correspondem aos arquivos encontrados. Isso foi conferido por leitura de `django_migrations`, sem executar migrations.

Contagens atuais da base local:

| Tabela / entidade | Registros |
|---|---:|
| `users_user` | 4 |
| `users_studentprofile` | 3 |
| `users_creatorprofile` | 1 |
| `courses_category` | 1 |
| `courses_course` | 3 |
| `courses_module` | 6 |
| `courses_lesson` | 13 |
| `courses_enrollment` | 4 |
| `courses_accessperiod` | 4 |
| `courses_accesschange` | 16 |
| `courses_progress` | 10 |
| `courses_studyday` | 64 |
| `courses_activityevent` | 18 |
| `courses_quiz` | 6 |
| `courses_quizquestion` | 18 |
| `courses_quizchoice` | 79 |
| `courses_quizattempt` | 7 |
| `courses_lessonnote` | 3 |
| `courses_lessonmaterial` | 3 |
| `courses_coursematerial` | 2 |
| `courses_materialopen` | 2 |
| `courses_certificate` | 2 |
| `courses_liveevent` | 3 |
| `courses_livereminder` | 0 |
| `community_communitypost` | 3 |
| `community_comment` | 2 |
| `community_helpful` | 0 |
| `support_faqitem` | 9 |
| `support_supportsubject` | 7 |
| `support_ticket` | 2 |
| `support_ticketevent` | 4 |
| `users_notification` | 5 |
| `users_emaillog` | 0 |
| `users_studentvisit` | 3 |
| `users_memberpreviewlog` | 3 |

Pedidos, ofertas, assinaturas, cobranças técnicas, tentativas de gateway e eventos de webhook estão com zero registros nessa base.

Os três cursos locais são:

- Plantão sem GPT.
- Emergências cardiovasculares.
- Um curso de QA identificado pela execução `QA-GM-20261117-105209`.

Os três estão publicados. Existem três usuários com papel `STUDENT` e um com papel `CREATOR`. As quatro matrículas usam acesso por períodos.

Esses números pertencem à demonstração local. Não representam o cadastro atual da produção.

### Frontend e temas

O frontend usa:

- Templates Django renderizados no servidor.
- CSS próprio com variáveis e tokens.
- JavaScript próprio, incluindo chamadas `fetch` para endpoints JSON do mesmo Django.
- SDK externo do Vimeo para o player.

Não foram encontrados React, Vue, HTMX, Alpine, Tailwind ou pipeline Vite/webpack no código de aplicação analisado.

Layouts principais:

- Aluno: `templates/base_membros.html`.
- Produtor: `templates/base_painel_gomut.html`.
- Base visual compartilhada: `templates/base_gomut.html`.
- Navegação do aluno: `templates/partials/gomut/member_header.html`.

Estilos principais:

- `static/css/gomut/tokens.css`.
- `static/css/gomut/base.css`.
- `static/css/gomut/components.css`.
- `static/css/gomut/members.css`.
- `static/css/gomut/admin.css`.
- `static/css/gomut/panel-v1.css`.

Existe tema escuro na área do aluno, com identidade Emergensimples, e tema claro no painel GoMut. A separação usa contextos como `data-area`, não uma preferência individual de alternância claro/escuro.

Archivo e Inter são carregadas pelo Google Fonts em `templates/base_gomut.html`; Archivo inclui o eixo variável de largura.

### Testes

Foram identificados 392 métodos de teste nos arquivos Python:

| Módulo | Métodos |
|---|---:|
| `courses` | 164 |
| `users` | 54 |
| `sales` | 52 |
| `painel` | 50 |
| `core` | 48 |
| `community` | 13 |
| `support` | 11 |

Usam a infraestrutura de testes do Django, com testes de models, serviços, HTTP, permissões, importação, player, quizzes, certificados, notificações e deploy.

Exemplos:

- `courses/test_player_tracking.py`.
- `courses/test_content_release.py`.
- `courses/test_lesson_quiz.py`.
- `courses/test_material_library.py`.
- `painel/test_lesson_editor.py`.
- `painel/test_reporting.py`.
- `users/test_notifications.py`.
- `core/test_public_portals.py`.

Comando geral, em ambiente com as dependências e variáveis necessárias:

    python -B manage.py test

Exemplo de execução parcial:

    python -B manage.py test courses.test_lesson_quiz painel.test_lesson_editor

Não executei a suíte nesta análise, pois ela cria banco e pode criar arquivos temporários.

O log anterior `.venv/public-https/suite.txt` registra 392 testes aprovados. Esse é um resultado histórico, não uma execução desta etapa.

Não encontrei configuração versionada de cobertura, lint ou CI entre os arquivos pesquisados.

## 2. Modelagem atual

Foram identificados 46 models próprios. Abaixo estão os campos principais e os relacionamentos; campos herdados e tabelas internas do Django são indicados separadamente.

### Usuários e configuração

| Model | Campos e relacionamentos principais | Fonte |
|---|---|---|
| `User` | Herda `AbstractUser`; acrescenta `role`, `avatar`, `bio`. Herda nome, e-mail, username, senha, flags de acesso, grupos e permissões | `users/models.py:8` |
| `StudentProfile` | Relação 1:1 com usuário; nome completo, CPF, endereço, pontos, nível, título, preferências de e-mail e estado compartilhado do heartbeat | `users/models.py:25` |
| `CreatorProfile` | Relação 1:1 com usuário; empresa, cor, logo, dados bancários e campos históricos de SMTP, gateway, IA e assinatura de certificado | `users/models.py:48` |
| `SiteSettings` | Marca da escola, apresentação de mentor/equipe, suporte, WhatsApp, termos, privacidade, SMTP, assinatura e campos históricos de gateway | `users/models.py:76` |
| `FirstAccessCode` | Relação 1:1 com usuário; hash do código, expiração e tentativas incorretas | `users/models.py:114` |
| `Notification` | Usuário, tipo, referência, título, corpo, URL e datas de criação/leitura | `users/models.py:137` |
| `EmailLog` | Usuário, tipo, referência, assunto, corpo, status, prazo de envio e reserva de entrega | `users/models.py:150` |
| `StudentVisit` | Aluno, data e primeiro acesso do dia; unicidade aluno/data | `users/models.py:163` |
| `MemberPreviewLog` | Administrador, aluno visualizado e início/fim da prévia | `users/models.py:169` |

### Cursos, conteúdo e aprendizagem

| Model | Campos e relacionamentos principais | Fonte |
|---|---|---|
| `Category` | Nome, slug único, cor e ordem | `courses/models.py:11` |
| `Course` | Criador, categoria opcional, título, slug, descrição, capa, cor, carga horária, objetivos, público, preço, publicação, duração do plano e campos de encontros/calendário | `courses/models.py:31` |
| `Module` | Curso, título, descrição, ordem, situação e mês de liberação | `courses/models.py:108` |
| `Lesson` | Módulo, título, descrição, URL do vídeo, ID/hash Vimeo, duração, ordem, situação e data de publicação | `courses/models.py:157` |
| `LessonMaterial` | Aula, título, arquivo PDF ou URL e ordem | `courses/models.py:214` |
| `CourseMaterial` | Curso, título, PDF, ordem e situação ativa | `courses/models.py:237` |
| `MaterialOpen` | Aluno, tipo/ID do material e data de abertura; não armazena posição de leitura | `courses/models.py:252` |
| `Progress` | Aluno/aula, posição do vídeo, segundos creditados, último heartbeat, conclusão e data de conclusão; único por aluno/aula | `courses/models.py:262` |
| `Quiz` | Curso, aula opcional, tipo aula/final, ativo e demonstrativo | `courses/models.py:284` |
| `QuizQuestion` | Quiz, ordem, enunciado, explicação geral e ativo | `courses/models.py:302` |
| `QuizChoice` | Pergunta, ordem, texto, correta e ativa; ordem limitada de 1 a 4 | `courses/models.py:314` |
| `QuizAttempt` | Aluno, quiz, datas, acertos, total, nota, respostas e snapshot das perguntas | `courses/models.py:330` |
| `LessonNote` | Aluno, aula, minuto/segundo, texto e criação | `courses/models.py:345` |
| `StudyDay` | Aluno, data e segundos estudados; único por aluno/dia | `courses/models.py:356` |
| `ActivityEvent` | Aluno, tipo, aula/curso opcionais, payload e criação | `courses/models.py:365` |
| `Enrollment` | Aluno/curso, origem, entrada, último acesso, política de acesso, início original do plano, observação interna e qualificação para certificado | `courses/models.py:377` |
| `AccessPeriod` | Matrícula, início, fim exclusivo, tolerância, encerramento antecipado, origem, referência, autor e criação | `courses/models.py:411` |
| `AccessChange` | Matrícula, ação, datas anteriores/novas, motivo, responsável e criação | `courses/models.py:453` |
| `Certificate` | Relação 1:1 com matrícula; código único, nome, CPF, curso, carga horária e datas preservadas da emissão | `courses/models.py:475` |
| `HeroBanner` | Título, subtítulo, imagens/vídeo de fundo, botões e situação; estrutura de banner legado | `courses/models.py:491` |
| `LiveEvent` | Curso opcional, título, tipo, início, duração, descrição, sala, gravação e ativo | `courses/models.py:531` |
| `LiveReminder` | Aluno/encontro; combinação única | `courses/models.py:543` |

### Comercial e gateway

| Model | Campos e relacionamentos principais | Fonte |
|---|---|---|
| `Order` | Aluno, curso, valor, forma de pagamento, status, transação e criação | `sales/models.py:15` |
| `OrderBump` | Curso principal, curso adicional e preço com desconto | `sales/models.py:44` |
| `Offer` | Curso, código, nome, modalidade mensal/avulsa, valor, tipo de recorrência, quantidade, prazo, tolerância e ativa | `sales/models.py:57` |
| `Subscription` | Relação 1:1 com matrícula, oferta, valor, status, próximo vencimento, ID no gateway e referências da plataforma anterior | `sales/models.py:112` |
| `GatewayCharge` | Pedido, assinatura opcional, ambiente, referência, IDs externos, valor, meio de pagamento, vencimento e estado de conferência | `sales/gateway_models.py:16` |
| `GatewayAttempt` | Cobrança, operação, resultado, erro, status HTTP e criação | `sales/gateway_models.py:82` |
| `WebhookEvent` | Ambiente, identificador/tipo do evento, recurso, payload, fingerprint, estado e recebimento | `sales/gateway_models.py:93` |

Esses models não significam que o checkout ou a renovação financeira automática estejam ativos.

### Comunidade

| Model | Campos e relacionamentos principais | Fonte |
|---|---|---|
| `CommunityPost` | Autor, curso/aula opcionais, título, conteúdo, solução, situação da equipe, nota interna, fixação e ocultação | `community/models.py:5` |
| `Comment` | Tópico, autor, resposta pai, conteúdo, assinatura exibida e ocultação | `community/models.py:34` |
| `Helpful` | Usuário e tópico ou resposta; garante um único alvo e voto por usuário/alvo | `community/models.py:50` |

### Suporte

| Model | Campos e relacionamentos principais | Fonte |
|---|---|---|
| `FaqItem` | Categoria textual, pergunta, resposta, ordem e publicado | `support/models.py:4` |
| `SupportSubject` | Nome, ordem e ativo | `support/models.py:12` |
| `Ticket` | Número, aluno, assunto, título, descrição, dispositivo, privacidade, status, resposta e datas | `support/models.py:19` |
| `TicketEvent` | Chamado, status, autor, observação e criação | `support/models.py:41` |
| `TicketVote` | Chamado e usuário; combinação única | `support/models.py:49` |

### Como o conteúdo é agrupado hoje

A hierarquia principal é:

    Categoria → Curso → Módulo → Aula → Materiais / Quiz

Observações:

- A categoria pertence ao curso, não diretamente à aula ou ao módulo.
- Cada aula pertence a um módulo.
- Cada módulo pertence a um curso.
- Uma aula não possui vários módulos ou temas associados.
- Não há model próprio de Área, Tema, Trilha, Favorito, Curtida de aula ou Seleção semanal.
- Não há campo de capa própria em `Lesson` ou `Module`.
- A categoria do FAQ é um texto independente de `courses.Category`.

Portanto, os módulos já podem representar assuntos como Vertigem e Pancreatite, mas a navegação temática solicitada no PDF ainda não existe.

### Publicação e liberação

Existe:

- Publicação do curso por `Course.is_published`.
- Rascunho/publicado no módulo e na aula.
- Registro `Lesson.published_at`.
- Liberação do módulo no mês N a partir de `Enrollment.plan_started_on`.

A regra efetiva está em `courses/access.py:84` e `courses/access.py:91`.

`published_at` é preenchido pelo serviço ao publicar. Não encontrei uma regra de agendamento por data/hora individual da aula. A disponibilidade não é determinada por uma data futura nesse campo.

Fontes: `courses/services.py:134`, `courses/services.py:355`.

O sistema suporta vários cursos/produtos. O PDF concentra a experiência na mentoria Plantão sem GPT, mas o código não está limitado a uma mentoria única.

## 3. Alunos e acesso — sem gateway de pagamento

### Criação e importação

Existem três caminhos relevantes:

1. Cadastro manual pelo produtor, com curso e datas do plano.
   - `painel/views/students.py:36`.
   - `users/services.py:115`.

2. Importação CSV com prévia e confirmação.
   - `users/importing.py:39`.
   - `users/services.py:61`.
   - `painel/views/students.py:242`.

3. Importação de mensalidades quitadas em outra plataforma.
   - `sales/migration_import.py`.
   - `sales/migration_services.py`.
   - Preserva período pago e referências de migração, sem criar cobrança.

Existe cadastro aberto em `users/views.py:56` e na URL base `/register/`, mas ele é bloqueado pelo URLConf de deploy em `core/urls_deploy.py:7`.

Assim, é importante distinguir desenvolvimento com `core.settings` de produção com `core.settings_public`: o cadastro aberto não é uma funcionalidade pública do deploy atual.

### Primeiro acesso

O administrador pode gerar um código:

- Dez dígitos.
- Guardado como hash.
- Válido por sete dias.
- Bloqueado após cinco tentativas incorretas.
- Usado pelo aluno para definir sua senha.
- Consumido após a definição da senha.

Fontes: `users/first_access.py:10`, `users/first_access.py:24`, `users/views.py:135`.

Também existe envio de link para definição/recuperação de senha por e-mail, dependente de SMTP.

Fontes: `painel/views/common.py:15`, `users/services.py:127`.

Não encontrei login por link mágico que substitua permanentemente a senha. O link existente serve para criar ou redefinir a senha.

### Liberação e bloqueio

O vínculo é `Enrollment`, único por aluno/curso.

Políticas:

- `unrestricted`: concessão administrativa sem prazo.
- `periods`: acesso conforme os períodos de `AccessPeriod`.

O fim de `AccessPeriod` é exclusivo. O cálculo distingue acesso ativo, tolerância, vencido, pendente e ausência de matrícula.

Fontes: `courses/models.py:377`, `courses/models.py:411`, `courses/access.py:20`.

O plano pode ser:

- Criado.
- Encerrado antecipadamente.
- Reativado.
- Corrigido nas datas.

As mudanças geram `AccessChange`, com datas, motivo e responsável.

Fontes: `courses/services.py:223`, `courses/services.py:251`, `courses/services.py:269`, `courses/services.py:287`.

O plano criado pelo fluxo atual recebe três dias de tolerância. Encerramento antecipado possui tratamento específico para não manter a tolerância natural.

Publicação, matrícula, validade e liberação do módulo são verificadas antes do acesso às aulas. Materiais e quizzes também possuem verificações próprias.

Não existe um simples campo `Enrollment.is_active`; a situação é calculada a partir da política e dos períodos. Já `User.is_active` controla a possibilidade de autenticação.

### Login e recuperação

- Login por e-mail e senha.
- Username também é aceito pelo backend.
- Sessão Django.
- Recuperação pelo fluxo padrão de token do Django, adaptado ao portal e ao papel.
- Produção separa host de aluno e host de produtor.

Fontes: `users/backends.py:8`, `users/views.py:18`, `users/views.py:94`, `core/portal_routing.py`, `core/settings_public.py`.

### Dados do aluno

São guardados:

- Nome e sobrenome herdados de `User`.
- Nome completo em `StudentProfile`.
- E-mail e username.
- Senha como hash do Django.
- CPF validado.
- Endereço.
- Avatar e biografia.
- Preferências de e-mail.
- Matrículas, períodos, progresso, atividades, quizzes e demais vínculos.

Não encontrei telefone ou WhatsApp individual no model do aluno nem no importador básico.

`SiteSettings.whatsapp` é o contato da escola, não o telefone de cada aluno.

Fontes: `users/models.py:8`, `users/models.py:25`, `users/importing.py`.

O CPF de perfil e certificado é armazenado em campos de texto, sem criptografia aplicada nesses models.

### Resquícios de plataformas e gateway

- Eduzz e Hotmart aparecem como origens de migração, não como integrações ativas de matrícula por webhook.
- Existem referências históricas de assinatura em `Subscription`.
- Existe infraestrutura técnica do Asaas: cliente HTTP, DTOs, configuração, webhook e reconciliação.
- O processamento do checkout retorna HTTP 503, sem criar conta, pedido ou matrícula.
- O settings público força API e webhook Asaas desligados.

Fontes: `sales/migration_import.py`, `sales/models.py:112`, `sales/integrations/asaas/`, `sales/webhook_views.py`, `sales/payment_services.py`, `sales/views.py`, `core/settings_public.py`.

A concessão de acesso atual pode operar administrativamente sem gateway.

## 4. Painel do produtor

### Onde fica

Existem ambos:

- Painel próprio em `/painel/`.
- Administração técnica Django em `/admin/`.

Fontes: `painel/urls.py`, `core/urls.py`.

O painel próprio usa templates e CSS GoMut. O Django Admin possui registros específicos dos models.

Fontes: `templates/base_painel_gomut.html`, `users/admin.py`, `courses/admin.py`, `sales/admin.py`, `community/admin.py`.

### Funcionalidades existentes

O painel permite:

- Criar e editar cursos.
- Publicar/despublicar cursos.
- Criar e editar módulos.
- Configurar mês de liberação dos módulos.
- Criar aulas rápidas em rascunho.
- Editar título, descrição, módulo, situação, vídeo e duração da aula.
- Enviar PDF da aula e materiais do curso.
- Reordenar módulos e aulas.
- Criar quizzes e avaliação final.
- Cadastrar/importar alunos.
- Vincular aluno a mais de um curso.
- Gerenciar datas e histórico do plano.
- Gerar código de primeiro acesso ou enviar link.
- Gerenciar encontros ao vivo.
- Moderar comunidade.
- Gerenciar chamados, FAQ e assuntos.
- Consultar certificados e relatórios.
- Configurar escola e SMTP.
- Visualizar como membro.

Fontes principais: `painel/urls.py`, `painel/views/`.

O editor de aula permite selecionar módulo existente. A criação de módulo ocorre no gerenciamento de conteúdo; não encontrei criação do módulo dentro do próprio formulário de edição da aula.

Fontes: `painel/views/lessons.py`, `painel/views/course_management.py:90`, `painel/forms.py:200`.

### Papéis e permissões

Os papéis próprios são somente:

- `ADMIN`.
- `CREATOR`.
- `STUDENT`.

Não existem papéis independentes de mentor, suporte, editor ou coprodutor.

O painel próprio é autorizado por `ADMIN` ou `CREATOR` em `core/decorators.py`. O Django Admin usa também os mecanismos de staff/permissões do Django.

A assinatura “Mentor” ou “Equipe” nas respostas da comunidade não cria um papel de autenticação separado.

Fontes: `users/models.py:8`, `core/decorators.py`, `community/models.py:34`.

Não encontrei isolamento do painel por proprietário do curso nas views consultadas: administradores/criadores operam a base compartilhada. Isso é relevante se os mentores receberem acesso restrito apenas a determinados conteúdos.

A prévia de membro é auditada e bloqueia operações de escrita.

Fontes: `users/member_preview.py`, `users/preview_middleware.py`, `painel/views/preview.py`.

## 5. Vídeo, materiais e mídia

### Vimeo

O vídeo é exibido por iframe de `player.vimeo.com`.

Templates:

- Aula do aluno: `templates/courses/lesson_detail.html:10`.
- Prévia no editor: `templates/painel/lesson_edit.html`.

O SDK `https://player.vimeo.com/api/player.js` é carregado na aula. `static/js/aluno.js` conecta os eventos do player aos endpoints da GoMut.

O cadastro usa URL do vídeo. O campo atual não aceita o HTML completo de um iframe: é um `URLField` com validação do host/formato.

Fontes: `courses/models.py:157`, `painel/forms.py:223`.

O model extrai ID e hash de privacidade. A URL do player é reconstruída pela aplicação, incluindo o hash quando presente.

Os parâmetros atuais incluem `dnt`, `title`, `byline` e `portrait`. Não há parâmetro de remoção de logo nessa propriedade.

Fonte: `courses/models.py:175` e `courses/models.py:198`.

Privacidade, domínios permitidos e predefinições visuais continuam sendo configurações do Vimeo; o backend não consulta nem confirma essas configurações.

Existe consulta opcional de duração por oEmbed, com timeout e fallback.

Fonte: `courses/integrations/vimeo.py:12`.

### Progresso e conclusão

Existe registro de:

- Posição para retomada.
- Segundos creditados pelo servidor.
- Conclusão e data.
- Minutos estudados por dia.
- Atividades recentes.
- Anotações vinculadas ao minuto do vídeo.

O JavaScript acompanha reprodução, pausa, mudança de tempo, visibilidade e encerramento. Envia heartbeats periódicos e tenta salvar ao sair da página.

Fontes: `static/js/aluno.js`, `courses/player_views.py`, `courses/services.py:401`.

A conclusão pode ocorrer:

- Manualmente.
- Automaticamente ao alcançar 90% de tempo creditado, quando há duração cadastrada.
- Pelo evento de término, com a validação adicional encontrada em `finish_video`.

Fontes: `courses/services.py:29`, `courses/services.py:401`, `courses/services.py:451`.

Limite importante: segundos creditados são acumulados; não há mapa dos trechos únicos assistidos. A marcação manual também pode concluir uma aula sem comprovar que o vídeo chegou ao fim. Isso afeta a interpretação das métricas solicitadas pelo PDF.

### Materiais e e-books

Existe upload de PDF por aula e por curso.

- Validação de extensão, tipo, assinatura inicial e limite de 20 MB.
- Abertura por endpoint autenticado.
- Verificação de matrícula, validade e liberação.
- Respostas com `Cache-Control: private, no-store`.
- Acesso direto a `/media/materials/` bloqueado.

Fontes: `courses/validators.py:5`, `courses/material_views.py:14`, `courses/material_views.py:20`.

O PDF é servido para o visualizador do navegador. O endpoint atual não força download por anexo. A biblioteca registra “já abriu”, não progresso de leitura ou página atual.

Materiais legados com URL externa são redirecionados após a autorização. A GoMut não controla a proteção do arquivo no destino externo.

### Armazenamento e imagens

- Desenvolvimento: `MEDIA_ROOT` em `media/`, conforme `core/settings.py`.
- Deploy: caminho persistente definido por `DJANGO_MEDIA_ROOT`.
- Compose monta diretórios próprios de produção e homologação.
- Imagens de cursos, banners, logos e escola podem ser servidas pelo handler de produção.
- Avatares exigem autenticação.
- PDFs não são liberados por esse handler de imagens.

Fontes: `core/settings_deploy.py`, `core/settings_public.py`, `deploy/compose.yaml`, `core/deploy_media.py`.

As gravações cadastradas em Ao vivo possuem outro fluxo: `courses/live_views.py` autoriza e redireciona para `recording_url`. Não passam necessariamente pelo player interno da aula.

## 6. Notificações e tarefas agendadas

### E-mail

O backend é `core.email_backend.SiteEmailBackend`.

A configuração efetiva de SMTP vem de `SiteSettings`:

- `email_host`.
- `email_port`.
- `email_username`.
- `email_password_encrypted`.
- `email_use_tls`.
- `email_from`.
- `email_from_name`.

Não há um provedor obrigatório fixado. Os campos históricos de SMTP em `CreatorProfile` não são a fonte usada pelo backend atual.

Fontes: `core/email_backend.py`, `users/models.py:76`, `users/services.py:143`.

Na base local consultada, o servidor SMTP está vazio.

Sem configuração:

- Em DEBUG, o backend pode escrever no console.
- Fora de DEBUG, o envio é ignorado com registro de erro.
- A fila pode permanecer como não enviada.

Não confirmei a configuração SMTP atual da VPS nesta análise.

### Notificações existentes

Existem:

- Sininho e central de notificações.
- Marcação de leitura.
- Avisos de nova aula.
- Liberação de módulo.
- Vencimento de acesso.
- Encontro no dia.
- Lembretes por e-mail de encontros.

Fontes: `users/notifications.py`, `users/notification_views.py`, `users/models.py:137`.

O processamento diário gera avisos de aulas publicadas e disponíveis. Não encontrei eventos próprios equivalentes para novo e-book ou nova gravação de encontro.

O lembrete de encontro depende de:

- O aluno ter ativado o lembrete.
- Preferência de e-mail habilitada.
- Acesso válido.
- Evento vigente.
- SMTP configurado.

A janela encontrada é até uma hora antes do início.

Fonte: `users/notifications.py:129`.

### WhatsApp

Existe contato da escola e link `wa.me`.

Não encontrei integração de disparo automático, provedor WhatsApp, fila de mensagens ou telefone individual de aluno.

Fontes: `users/models.py:83`, `users/models.py:107`, `painel/settings_forms.py`.

### Rotinas

Existem management commands:

- `run_daily_notifications`.
- `run_live_reminders`.
- `backup_sqlite`.
- `prepare_demo`.
- `import_quizzes`.
- `reconcile_asaas_charges`.

Fontes: diretórios `management/commands/` dos apps.

O deploy possui um processo próprio de agendamento, `deploy/jobs.py`:

- Notificações diárias a partir das 04h.
- Lembretes a cada intervalo de 15 minutos.
- Backup diário a partir das 04h15.
- Checkpoint persistente.
- Lock para evitar dois agendadores simultâneos.
- Tentativas posteriores em caso de falha.

O fuso usado é `America/Campo_Grande`.

Não encontrei Celery, RQ ou dependência de Redis para essas rotinas. O Compose executa o agendador no serviço `scheduler`.

## 7. Ambiente e deploy

### Variáveis de ambiente — somente nomes

Configuração da aplicação e segurança:

- `DJANGO_SETTINGS_MODULE`
- `SECRET_KEY`
- `FIELD_ENCRYPTION_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DJANGO_DATABASE_PATH`
- `DJANGO_MEDIA_ROOT`
- `CSRF_TRUSTED_ORIGINS`

Modos e portais:

- `GOMUT_DEMO_MODE`
- `GOMUT_TUNNEL_ONLY`
- `GOMUT_ENVIRONMENT`
- `GOMUT_STUDENT_HOST`
- `GOMUT_PRODUCER_HOST`

Asaas:

- `ASAAS_ENVIRONMENT`
- `ASAAS_API_ENABLED`
- `ASAAS_API_KEY`
- `ASAAS_WEBHOOK_ENABLED`
- `ASAAS_WEBHOOK_TOKEN`
- `ASAAS_TIMEOUT`

Imagem e execução:

- `GOMUT_IMAGE`
- `PYTHONDONTWRITEBYTECODE`
- `PYTHONUNBUFFERED`
- `PIP_DISABLE_PIP_VERSION_CHECK`

Também aparece `PORT` em `.env.example`; não identifiquei seu uso para configurar o bind do Gunicorn no Dockerfile atual.

Fontes: `core/settings.py`, `core/settings_deploy.py`, `core/settings_public.py`, `core/asgi.py`, `core/wsgi.py`, `deploy/Dockerfile`, `deploy/compose.yaml`, `deploy/compose.public.yaml`, `.env.example`.

O SMTP atual é configurado no banco, não por um conjunto próprio de variáveis de ambiente SMTP.

Nenhum valor de credencial foi incluído neste relatório.

### Configuração de produção encontrada

- Dockerfile com Python e dependências fixadas.
- Gunicorn como servidor WSGI.
- WhiteNoise para estáticos.
- `collectstatic` durante o build.
- Usuário sem privilégios dentro do container.
- Sistema de arquivos do container somente leitura, com volumes específicos graváveis.
- SQLite e uploads persistentes.
- Serviços separados de produção, homologação e agendamento.
- Override público com rotas HTTPS no Traefik.
- Host de aluno e host de produtor distintos.
- Cookies Secure e restritos a cada host.
- Cadastro aberto bloqueado.
- Asaas desligado no settings público.

Fontes: `deploy/Dockerfile`, `deploy/compose.yaml`, `deploy/compose.public.yaml`, `core/settings_public.py`, `core/urls_deploy.py`.

O wrapper `deploy/compose.sh` aplica os dois arquivos Compose. Usar somente o arquivo base pode remover a configuração pública.

O relatório de deploy registra operação na KVM4 por Docker Compose, sem cadastro da GoMut na interface Coolify. Não executei inspeção remota nem atualização nesta etapa.

Fonte histórica: `docs/relatorio-publicacao-https.md`.

Não encontrei Procfile.

### Demonstração e seeds

Existe base separada de demonstração:

- `.venv/gomut-demo.sqlite3`.
- Lançador `.venv/run_v1.py`.
- Comando `courses/management/commands/prepare_demo.py`.
- Complementos em `courses/demo_study.py`, `courses/demo_quizzes.py`, `courses/demo_materials.py` e `support/demo.py`.

`prepare_demo` exige modo de demonstração e preserva dados existentes.

Existe também `seed.py` legado, documentado como destrutivo para dados de demonstração. Não foi executado.

Fontes: `courses/management/commands/prepare_demo.py`, `README.md`, `docs/area-aluno-demonstracao.md`.

## 8. Mapa do documento vs. código atual

O PDF foi lido integralmente e suas imagens foram conferidas. A tabela considera tanto o texto quanto as referências visuais.

| Item do PDF | Situação | O que já existe | O que falta ou difere | Impacto estimado | Fontes |
|---|---|---|---|---|---|
| 1 — Continue de onde parou e métricas do produtor | PARCIAL | Retomada no minuto, progresso, conclusão e hero por curso; relatórios de progresso por curso e aulas mais concluídas | Fileira personalizada com todas as aulas iniciadas/incompletas e minuto visível; a escolha atual da próxima aula é sequencial, não necessariamente a última aula assistida. Falta relatório por aula com iniciantes, posição por aluno e taxa de conclusão entre iniciantes | Front + back; histórico adicional conforme a definição das métricas | PDF p.1; `courses/models.py:262`; `courses/selectors.py:36`; `courses/student_views.py:19`; `painel/reporting.py:11`; `templates/courses/dashboard.html` |
| 2 — Top 10 no Plantão desta semana | NÃO EXISTE como funcionalidade | Relatório de até cinco aulas mais concluídas, que pode apoiar uma seleção humana | Seleção manual ordenada de até dez aulas, publicação da seleção semanal, cards numerados e regras da semana. O relatório existente não é um Top 10 editorial | Front + back; rotina agendada se a troca semanal for automática | PDF p.2; `painel/reporting.py:11`; `courses/models.py`; `templates/courses/dashboard.html` |
| 3 — Novidades e aviso de aula, gravação e e-book | PARCIAL | Notificação interna e e-mail de nova aula/liberação de módulo; central de notificações | Fileira de novidades na home; eventos de novo e-book e gravação; aviso no momento da publicação; WhatsApp. O agendador atual processa novas aulas diariamente | Front + back + rotina agendada/integração | PDF p.3; `users/notifications.py:97`; `deploy/jobs.py:12`; `courses/models.py:214`; `courses/models.py:531` |
| 4 — Próximos encontros ao vivo na home e lembrete | PARCIAL | Eventos com data, sala, gravação, agenda e lembrete opt-in por e-mail | Fileira na home conforme referência. Definir se o lembrete será para todos ou apenas opt-in e qual antecedência; hoje depende de SMTP e da ativação do aluno | Front + back + rotina agendada/configuração de e-mail | PDF p.4; `courses/live_selectors.py`; `courses/live_services.py`; `users/notifications.py:129`; `templates/courses/dashboard.html` |
| 5 — Minha Lista | NÃO EXISTE | Não há model ou serviço de favoritos de aula | Adicionar/remover aula, persistência individual, botão na aula, fileira na home e página da lista completa | Front + back | PDF p.5; `courses/models.py`; `core/urls.py`; `courses/student_views.py:94` |
| 6 — Home consolidada e outros cursos | PARCIAL | Home com hero, cursos, progresso e comunidade; a view calcula `other_courses` | Composição das novas fileiras; renderização da vitrine de outros cursos. O template atual não utiliza `other_courses`. Checkout permanece indisponível | Front + back; pagamento não integra esta etapa | PDF p.6; `courses/student_views.py:19`; `templates/courses/dashboard.html`; `sales/views.py` |
| 7 — Curtir, adicionar à lista e concluir abaixo do vídeo | PARCIAL | Marcação manual de conclusão e navegação anterior/próxima | Curtida de aula e seu registro; botão de Minha Lista; composição visual solicitada. Curtidas/“útil” da comunidade não atendem esse requisito | Front + back | PDF p.7; `templates/courses/lesson_detail.html:21`; `courses/services.py:29`; `community/models.py:50` |
| 8 — Abas Visão geral, E-book e Quiz | PARCIAL | Descrição, material, quiz e anotações já possuem abas | Nomes e ordem exatos. Hoje são “Sobre a aula”, “Material”, quiz condicional e “Anotações”. O quiz é executado em janela, não integralmente dentro da aba | Principalmente front; back se mudar a liberação do quiz | PDF p.8; `templates/courses/lesson_detail.html:25`; `static/js/gomut/quiz.js`; `courses/services.py:491` |
| 9 — Quiz com justificativa por alternativa | PARCIAL | Perguntas, alternativas, uma correta, feedback de acerto/erro, cores, tentativas, nota e editor do produtor | Justificativa específica em cada alternativa; exibir explicação da escolhida e da correta; suporte à alternativa E; interação da referência. Hoje há uma explicação por pergunta, limite de quatro alternativas, botão “Responder” e janela de quiz | Front + back, incluindo alteração de modelagem, validações e importação | PDF p.9; `courses/models.py:302`; `courses/models.py:314`; `painel/forms.py:151`; `courses/services.py:511`; `courses/quiz_importing.py`; `static/js/gomut/quiz.js` |
| 10 — E-book da aula e acesso a todos | PARCIAL | Material da aula, título, abertura de PDF e link para biblioteca | Rótulos e disposição exatos, identificação explícita da aula e link contextual para todos os e-books da mentoria. Hoje o link é geral e o PDF abre no navegador | Front + back para contexto de curso e eventual download dedicado | PDF p.10; `templates/courses/lesson_detail.html:35`; `courses/material_views.py:20` |
| 11 — Trilha por tema/módulo | PARCIAL na estrutura; página NÃO EXISTE | Curso → módulo → aula, ordenação, publicação, liberação e lista de módulos no curso | Página Trilha, item no menu, filtros superiores por assunto, cards e navegação temática; criação de módulo dentro do cadastro da aula. Categoria atual é do curso | Front + back | PDF pp.11–12; `courses/models.py:108`; `courses/selectors.py:6`; `painel/views/course_management.py:90`; `painel/forms.py:200`; `templates/partials/gomut/member_header.html` |
| 12 — E-books abaixo das aulas do módulo na Trilha | PARCIAL na modelagem | PDFs estão ligados às aulas, que pertencem ao módulo | Página/seção que agrupe e apresente os PDFs do módulo sem abrir cada aula, preservando as verificações de acesso | Front + back | PDF p.13; `courses/models.py:214`; `courses/selectors.py:271`; `templates/partials/gomut/module_list.html` |
| 13 — Biblioteca de e-books organizada por módulo | PARCIAL | Menu E-books, biblioteca, filtros, relação com aula/curso e publicação automática do material já vinculado e liberado | Agrupar por módulo/tema em vez de curso; frases do topo, contagem, número da aula e botões conforme referência. Cadastro atual já permite anexar PDF ao editar a aula | Front + back | PDF p.14; `templates/courses/ebooks.html`; `courses/selectors.py:271`; `courses/services.py:770`; `templates/partials/gomut/member_header.html` |

Observação sobre recursos antigos: `courses/ui_capabilities.py` ainda lista nomes como “trilhas” e “minha-lista”, mas não encontrei uso dessa constante no código consultado. A view atual `member_section` retorna 404 para esses nomes. Portanto, não devem ser tratados como telas funcionais já prontas.

## 9. Riscos e inconsistências

### Riscos e pontos frágeis do código atual

1. **Ambiente local divergente do requirements.**
   O ambiente virtual tem Django 4.2.30; o requirements declara 5.2.19. Um resultado local não representa automaticamente o runtime de produção.
   Fontes: `requirements.txt`, `.venv/pyvenv.cfg`, pacote Django instalado.

2. **Árvore de trabalho já contém mudanças sem commit e arquivos não rastreados.**
   Há alterações anteriores de QA, autenticação e deploy. Um futuro trabalho baseado somente em `HEAD` pode perder parte do estado atual.
   Fonte: leitura de `git status` e `git diff --stat`.

3. **Métricas de aprendizagem não equivalem diretamente às métricas pedidas.**
   `Progress` guarda estado atual, posição e tempo acumulado, mas não primeira reprodução, sessões completas ou trechos únicos assistidos. `StudyDay` é agregado por aluno/dia, sem aula. Conclusão manual não comprova término real do vídeo.
   Fontes: `courses/models.py:262`, `courses/models.py:356`, `courses/services.py:29`, `courses/services.py:401`.

4. **“Continuar” atual é principalmente sequencial por curso.**
   `progress_info` escolhe a primeira aula disponível não concluída. Isso não produz automaticamente a lista de todas as aulas interrompidas solicitada no PDF.
   Fonte: `courses/selectors.py:36`.

5. **Quiz exige mudanças em vários pontos coordenados.**
   O limite de quatro alternativas aparece no banco, serviço, formulário, validação de tentativa e CSV. As tentativas guardam snapshots, que precisam continuar coerentes com o histórico existente.
   Fontes: `courses/models.py:314`, `courses/services.py:511`, `courses/services.py:549`, `painel/forms.py:151`, `courses/quiz_importing.py`.

6. **Notificação de publicação não é imediata.**
   A nova aula é detectada pelo processamento diário. Não existem eventos específicos de novo PDF e nova gravação.
   Fontes: `users/notifications.py:97`, `deploy/jobs.py:12`.

7. **SMTP e WhatsApp não podem ser considerados prontos para entrega real.**
   SMTP está vazio na base local. Não há integração de WhatsApp nem telefone individual do aluno.
   Fontes: leitura da base; `core/email_backend.py`; `users/models.py:25`.

8. **Novo acesso por cards precisa continuar respeitando a mesma política.**
   Favoritos, Top 10, Trilha e novos atalhos de PDF não podem expor aula em rascunho, curso sem matrícula, módulo não liberado ou plano vencido.
   Fontes: `courses/access.py`, `courses/material_views.py`.

9. **Administração não possui perfis granulares de mentor/editor.**
   Criadores e administradores compartilham permissões amplas no painel; não foi encontrado isolamento por proprietário nas views consultadas.
   Fontes: `core/decorators.py`, `painel/views/course_management.py`, `painel/views/lessons.py`.

10. **URL de vídeo não aceita HTML de incorporação.**
    Colar o iframe completo no campo atual falha na validação. O código extrai ID/hash de uma URL e monta seu próprio iframe.
    Fontes: `painel/forms.py:223`, `courses/models.py:175`.

11. **Fluxos de vídeo não são uniformes.**
    Aula usa iframe/SDK; gravação de encontro usa redirecionamento externo. Um requisito de gravação sempre dentro da GoMut também afetaria esse segundo fluxo.
    Fontes: `templates/courses/lesson_detail.html`, `courses/live_views.py`.

12. **Proteção de arquivos externos é limitada ao endpoint.**
    Materiais armazenados como URL externa podem continuar acessíveis diretamente no destino depois que o aluno conhece o endereço.
    Fonte: `courses/material_views.py:46`.

13. **Dados pessoais e campos legados precisam de atenção.**
    CPF está em texto nos models; há campos históricos de credenciais em `CreatorProfile`, embora vários estejam ocultos do admin. SMTP ativo usa o campo criptografado de `SiteSettings`.
    Fontes: `users/models.py:25`, `users/models.py:48`, `users/models.py:76`, `users/admin.py`.

14. **Documentação antiga contém regras posteriormente ajustadas.**
    Exemplo: o corpo de `docs/decisoes-produto.md` menciona avisos em 30/15/7 dias, mas o ajuste posterior e o código atual restringem os avisos ao aluno aos últimos três dias. Não é seguro implementar apenas pelo primeiro trecho encontrado.
    Fontes: `docs/decisoes-produto.md`, `docs/ajuste-avisos-vencimento.md`, `courses/services.py:340`.

15. **Templates legados e contexto não utilizado podem induzir diagnóstico incorreto.**
    Existem templates de prévia/catálogo antigos, `HeroBanner` e variáveis como `other_courses` que não correspondem a uma seção atualmente renderizada.
    Fontes: `courses/views.py`, `courses/student_views.py:19`, `templates/courses/dashboard.html`, `courses/models.py:491`.

16. **Os novos requisitos ainda não possuem testes próprios.**
    A suíte existente cobre a V1. Não foram encontrados testes de favoritos de aula, curtidas de aula, seleção semanal ou justificativas por alternativa, pois essas funcionalidades não existem.
    Fontes: arquivos de teste e models examinados.

### Ambiguidades do próprio PDF

- O item 11 ocupa duas páginas e usa uma referência visual com o título “Cursos”, mas o texto pede uma página chamada “Trilha”.
- O item 13 exige remover divisões por semana, embora sua imagem ainda mostre “Semana 1” e “Semana 2”.
- O item 9 exemplifica alternativas A–E; a imagem mostra A–D. O texto é mais amplo que a imagem.
- “Tema”, “área” e “módulo” aparecem próximos, mas não está definido se serão o mesmo conceito ou níveis distintos.
- O texto fala de aulas nos cards, enquanto algumas referências vieram de um catálogo com aparência de cursos.
- Não há definição formal de “começou”, “chegou ao final” ou da janela temporal das métricas.
- O Top 10 é manual, mas não está definido como a semana começa/termina, se haverá agendamento ou histórico de seleções.
- “E-mail ou WhatsApp” não define canal preferencial, escolha por aluno, provedor ou necessidade de ambos.
- “No momento da publicação” não define tratamento para atualizações, republicações e substituições de material.
- O PDF não esclarece se o quiz deve continuar bloqueado até concluir a aula.
- Não define se a home é específica do Plantão sem GPT ou continua agregando todos os cursos de cada aluno.

Fontes: PDF pp.1–14.

### Decisões humanas necessárias antes da implementação

1. **Contexto da navegação:** a nova home, Trilha e biblioteca serão específicas da mentoria Plantão sem GPT ou terão visão conjunta dos cursos do aluno?

2. **Estrutura temática:** módulo será o próprio tema mostrado na faixa superior? Haverá também áreas amplas, como Cardiologia, contendo vários módulos?

3. **Métricas:** qual ação conta como início e qual conta como conclusão para o produtor? A conclusão manual entra no percentual? O relatório será acumulado ou por período?

4. **Top 10:** qual o escopo da seleção, como será feita a troca semanal e se as seleções anteriores precisam permanecer consultáveis?

5. **Notificações:** usar e-mail inicialmente ou contratar/configurar também WhatsApp? Qual atraso máximo aceitável após publicação e quais preferências o aluno pode controlar?

6. **Encontros:** lembrete obrigatório para todos os alunos elegíveis ou opt-in como hoje? Qual antecedência? Os eventos serão cadastrados individualmente ou precisam de recorrência automática?

7. **Quiz:** confirmar cinco alternativas ou quantidade variável; obrigatoriedade das justificativas por alternativa; resposta ao selecionar ou após clicar em “Responder”; manter ou mudar a exigência de concluir a aula antes.

8. **Navegação existente:** onde permanecerão Meu progresso, Comunidade, Ao vivo, Suporte e Anotações no desenho com Visão geral, Trilha e E-books?

9. **E-books:** manter vários PDFs por aula ou exatamente um? O botão deve baixar diretamente ou abrir o visualizador? A numeração da aula será global na mentoria ou reiniciará por módulo?

10. **Capas:** as imagens de aula/módulo serão fornecidas ou será reutilizada a capa do curso? Hoje não há campo próprio para essas capas.

11. **Mentores:** todos terão gestão completa pelo papel `CREATOR` ou haverá restrição a cursos/conteúdos específicos?

12. **Outros cursos:** nesta entrega a seção será apenas informativa, com link externo ou contato, preservando o checkout indisponível? O PDF coloca vendas como possibilidade futura, sem definir sua implementação agora.

O relatório acima descreve a situação encontrada e as lacunas. Nenhuma dessas decisões foi assumida ou implementada nesta etapa.
