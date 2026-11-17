# Diagnóstico do projeto GoMut / Emergensimples

Diagnóstico somente leitura do diretório atual.

- Nenhum arquivo de aplicação foi criado, editado ou apagado.
- Nenhuma migração foi aplicada à base local.
- A base local foi consultada com SQLite em modo somente leitura.
- A suíte foi executada com banco de teste em memória: 138 testes passaram.
- Não foram reproduzidos valores de senhas, chaves, tokens ou arquivos de ambiente.
- “EXISTE” significa implementação encontrada no código; não significa homologação em produção.
- “PARCIAL” significa que há parte do recurso, mas não todo o comportamento descrito no contexto.
- Funcionalidade presente apenas no protótipo não foi considerada implementação do produto.

## 1. STACK E AMBIENTE

### 1.1 — EXISTE: framework, Python e dependências

Django 4.2.30, tanto no requirements quanto instalado no ambiente virtual examinado.

Python observado no ambiente virtual: 3.13.17.
Versão de Python fixada formalmente pelo projeto: não encontrada.
O README informa Python 3.9+.

requirements.txt:

    asgiref==3.11.1
    Django==4.2.30
    cryptography==46.0.3
    pillow==11.3.0
    sqlparse==0.5.5
    typing_extensions==4.16.0

Não foi encontrado pyproject.toml.

Fontes: requirements.txt:1; README.md; core/settings.py:4.
Versões instaladas: consulta ao interpretador de .venv, sem instalação de pacotes.

### 1.2 — PARCIAL: bancos de desenvolvimento e produção

O backend de banco configurado é SQLite:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.environ.get('DJANGO_DATABASE_PATH')
                    or BASE_DIR / 'db.sqlite3',
        }
    }

- Caminho padrão: db.sqlite3 na raiz.
- O arquivo padrão não existe atualmente neste diretório.
- Há uma base de demonstração em .venv/gomut-demo.sqlite3.
- DJANGO_DATABASE_PATH permite escolher outro arquivo.
- Não foi encontrada configuração específica de PostgreSQL, MySQL ou banco remoto.
- Banco efetivamente utilizado em produção: não confirmado.
- A documentação orienta SQLite em disco local persistente.

Fontes: core/settings.py:100; docs/operacao-sqlite.md:1; docs/area-aluno-demonstracao.md.

### 1.3 — EXISTE: frontend renderizado no servidor

- Templates Django.
- HTML, CSS e JavaScript próprios.
- Formulários GET/POST tradicionais.
- Algumas operações usam fetch e respostas JSON.
- Não foram encontrados HTMX, Alpine, React, Vue ou DRF.
- Não foram encontrados package.json, Vite, webpack ou Tailwind CLI.

CSS em duas famílias:

1. Legado:
   - static/css/cetremer.css
   - Inter e Montserrat.
   - Utilizado pelo painel administrativo e por telas secundárias antigas.

2. Novo visual:
   - static/css/gomut/tokens.css
   - static/css/gomut/base.css
   - static/css/gomut/components.css
   - static/css/gomut/members.css
   - static/css/gomut/login.css
   - static/css/gomut/admin.css
   - Archivo variável e Inter.

A existência de admin.css não significa que o painel já o utilize.

Fontes: templates/base_core.html:10; templates/base_gomut.html:10; templates/base_admin.html:1.

### 1.4 — PARCIAL: execução local e Docker

Comandos documentados para preparação de uma instalação:

    python -m venv venv
    pip install -r requirements.txt
    python manage.py migrate

Comando de execução:

    python manage.py runserver 127.0.0.1:8016

O README também documenta runserver 8000.

Para usar a demonstração atual, é necessário manter a configuração de banco separado, incluindo DJANGO_DATABASE_PATH e GOMUT_DEMO_MODE. As variáveis SECRET_KEY e FIELD_ENCRYPTION_KEY também participam da configuração.

O roteiro para reutilizar a configuração local está em docs/area-aluno-demonstracao.md.

Dockerfile, docker-compose e configuração equivalente: não encontrados.

Os comandos acima são informação de operação; não foram executados para modificar a instalação neste diagnóstico.

Fontes: README.md; docs/area-aluno-demonstracao.md; core/settings.py:34; core/settings.py:103.

### 1.5 — PARCIAL: tarefas, e-mail e arquivos

Tarefas assíncronas:
- Não foram encontrados Celery, RQ, Redis, scheduler ou cron configurado.
- Existem comandos manuais de backup e reconciliação do Asaas.
- A documentação recomenda agendar backups, mas não implementa o agendamento.

E-mail:
- Backend próprio SiteEmailBackend.
- Utiliza SMTP configurado em SiteSettings.
- Provedor efetivamente contratado/configurado: não confirmado.
- Sem SMTP e com DEBUG ativo, envia para console.
- Sem SMTP fora de DEBUG, registra a ausência e não entrega o e-mail.
- Não há fila de e-mail.

Arquivos:
- Armazenamento local em MEDIA_ROOT.
- Não foram encontrados S3, R2, django-storages ou backend remoto.
- STATIC_ROOT está definido para arquivos estáticos coletados.

Fontes: core/email_backend.py:15; core/settings.py:146; core/settings.py:148; docs/operacao-sqlite.md:5; sales/management/commands/reconcile_asaas_charges.py.

### 1.6 — PARCIAL: testes, lint, CI e deploy

EXISTE:
- Testes Django com TestCase e SimpleTestCase.
- 25 arquivos de testes encontrados.
- Execução atual: 138 testes passaram.
- Comando usual:

    python manage.py test --verbosity 0

NÃO ENCONTRADO:
- Medição percentual de cobertura.
- Pipeline de CI.
- Configuração formal de lint/formatação.
- Pipeline de deploy.
- Docker.
- Procedimento completo de produção com servidor de aplicação e proxy.

Existem:
- core/wsgi.py
- core/asgi.py
- STATIC_ROOT.
- Documentação operacional de SQLite.

Há .ruff_cache no diretório, mas isso não comprova configuração ou obrigação de executar Ruff.

Fontes: core/tests.py; courses/tests.py; painel/tests.py; sales/test_asaas_webhooks.py; requirements.txt; core/wsgi.py; core/asgi.py.

### 1.7 — PARCIAL: Git e regras do repositório

- Branch principal remota: origin/main.
- Branch atual: feat/area-aluno-handoff.
- Também existem branches de redesign e trabalho anteriores.
- O histórico utiliza prefixos feat: e docs:.
- Convenção formal obrigatória de branches/commits: não encontrada.
- Existem alterações locais e arquivos ainda não versionados: 93 entradas no git status.
- Portanto, git log sozinho não representa toda a implementação examinada.

README: existe.
CLAUDE.md: não encontrado.
AGENTS.md dentro do projeto pesquisado: não encontrado.
CONTRIBUTING: não encontrado.

Regras relevantes documentadas:
- Preservar o CSS normativo e os SVG do handoff.
- Separar identidade GoMut da identidade do cliente.
- Não copiar login simulado nem localStorage do protótipo como backend.
- Manter o aluno separado do painel.
- Registrar pendências sem inventar comportamento.
- O plano aprovado mantém Django, templates, CSS e JS próprios, sem introduzir frontend separado.

Fontes: git branch -a; git log; git status; README.md; docs/handoff-design/01-regras-inviolaveis.md; docs/superpowers/plans/2026-11-16-area-aluno-design.md.

## 2. ESTRUTURA

### 2.1 — EXISTE: árvore até três níveis

Árvore resumida. Arquivos de testes e documentos semelhantes foram agrupados.
Excluídos ambientes virtuais, migrations, caches, node_modules e static coletado.
Nomes de uploads não foram enumerados.

/
├── community/
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│   ├── apps.py
│   └── tests.py
├── core/
│   ├── settings.py
│   ├── urls.py
│   ├── decorators.py
│   ├── context_processors.py
│   ├── crypto.py
│   ├── email_backend.py
│   ├── http.py
│   ├── sqlite_backup.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── tests.py / test_*.py
├── courses/
│   ├── integrations/
│   │   └── vimeo.py
│   ├── management/
│   │   └── commands/
│   ├── templatetags/
│   │   ├── cetremer.py
│   │   └── custom_filters.py
│   ├── models.py
│   ├── views.py
│   ├── student_views.py
│   ├── certificate_views.py
│   ├── access.py
│   ├── selectors.py
│   ├── services.py
│   ├── ui_capabilities.py
│   └── tests.py / test_*.py
├── painel/
│   ├── views/
│   │   ├── common.py
│   │   ├── overview.py
│   │   ├── course_management.py
│   │   ├── students.py
│   │   ├── orders.py
│   │   ├── community.py
│   │   └── settings.py
│   ├── forms.py
│   ├── urls.py
│   └── tests.py / test_*.py
├── sales/
│   ├── integrations/
│   │   └── asaas/
│   ├── management/
│   │   └── commands/
│   ├── models.py
│   ├── gateway_models.py
│   ├── views.py
│   ├── payment_services.py
│   ├── webhook_services.py
│   ├── webhook_views.py
│   ├── migration_import.py
│   ├── migration_services.py
│   └── tests.py / test_*.py
├── users/
│   ├── models.py
│   ├── views.py
│   ├── backends.py
│   ├── first_access.py
│   ├── services.py
│   ├── importing.py
│   ├── validators.py
│   ├── admin.py
│   └── tests.py / test_*.py
├── templates/
│   ├── base_core.html
│   ├── base_public.html
│   ├── base_admin.html
│   ├── base_aluno.html
│   ├── base_gomut.html
│   ├── base_membros.html
│   ├── login.html / register.html / landing.html
│   ├── courses/
│   │   └── dashboard, course_detail, lesson_detail, progresso,
│   │       certificados, ao vivo, acesso e página pública
│   ├── painel/
│   │   └── cursos, edição, aulas, alunos, pedidos,
│   │       comunidade, configurações e importação
│   ├── partials/
│   │   ├── gomut/
│   │   └── componentes e menus legados
│   ├── community/
│   │   └── hub.html
│   ├── registration/
│   │   └── primeiro acesso e recuperação de senha
│   ├── sales/
│   │   └── checkout.html
│   └── users/
│       └── settings.html
├── static/
│   ├── css/
│   │   ├── cetremer.css
│   │   └── gomut/
│   ├── js/
│   │   ├── aluno.js
│   │   ├── painel-grade.js
│   │   ├── site.js
│   │   └── gomut/
│   ├── gomut/
│   │   ├── icones/
│   │   ├── marca/
│   │   └── motivos/
│   └── modelos/
│       ├── importar-alunos.csv
│       └── migrar-mensalidades.csv
├── docs/
│   ├── handoff-design/
│   │   ├── 02-tokens/
│   │   ├── 03-componentes/
│   │   ├── 04-icones/
│   │   ├── 05-telas/
│   │   ├── prototipo/
│   │   └── telas/
│   ├── superpowers/
│   │   └── plans/
│   └── documentos de arquitetura, operação e demonstração
├── media/
├── requirements.txt
├── README.md
├── manage.py
├── data_dump.json
├── seed.py
└── .gitignore

Fonte: listagem do diretório atual.

### 2.2 — EXISTE: apps e responsabilidades

Apps próprios em INSTALLED_APPS:
- users: usuário, perfis, primeiro acesso, autenticação e configurações globais.
- courses: cursos, módulos, aulas, matrícula, períodos de acesso, progresso e certificados.
- sales: pedidos, ofertas, assinaturas, migração financeira e infraestrutura Asaas.
- community: publicações e comentários.

Também estão habilitados os apps padrão de admin, auth, contenttypes, sessions, messages e staticfiles.

painel:
- É um pacote de URLs, forms e views.
- Não aparece como app próprio em INSTALLED_APPS.
- Reúne a gestão usando os modelos dos outros apps.

Fontes: core/settings.py:50; painel/urls.py:1; painel/forms.py:1.

### 2.3 — EXISTE, com coexistência de layouts

Novo aluno:
- templates/base_gomut.html: estrutura HTML, fontes e CSS novo.
- templates/base_membros.html: cabeçalho, rodapé e navegação móvel.
- templates/partials/gomut/: hero, cartões, módulos, progresso, ícones e recursos pendentes.

Aluno legado:
- templates/base_aluno.html.
- Ainda utilizado por telas secundárias, como conta, comunidade, certificados e ao vivo.

Produtor:
- templates/base_admin.html.
- Herda base_core.html e carrega o CSS legado.
- Usa templates/partials/sidebar_admin.html.

Componentes antigos:
- templates/partials/icon.html
- templates/partials/messages.html
- templates/partials/progress.html
- templates/partials/sidebar_aluno.html

Não há um único sistema visual aplicado a todas as telas.

Fontes: templates/base_gomut.html:1; templates/base_membros.html:1; templates/base_admin.html:1; templates/base_core.html:11.

## 3. MARCA E MULTI-CLIENTE

### 3.1 — NÃO EXISTE: infraestrutura multi-tenant

O código examinado corresponde a uma instalação compartilhando um banco e configurações globais.

Não foram encontrados:
- Modelo Tenant/Organization para isolamento.
- Campo tenant nos modelos.
- Roteamento de cliente por subdomínio.
- Schemas separados.
- Middleware de resolução de cliente.

Course.creator vincula um curso a um produtor, mas não implementa isolamento multi-tenant.

SiteSettings.load() utiliza um registro global com pk=1.
As consultas administrativas de cursos não são limitadas ao proprietário.

Fontes: users/models.py:72; users/models.py:94; courses/models.py:36; painel/views/course_management.py:24.

### 3.2 — PARCIAL: marca e personalização do aluno

Novo aluno:
- “Emergensimples” está escrito diretamente no cabeçalho e no rodapé.
- Cores e fontes estão em arquivos CSS.
- Archivo variável e Inter são carregadas por Google Fonts.
- SVG e artes estão em static/gomut/.

Configurações existentes no banco:
- SiteSettings.school_name, logo e informações institucionais.
- CreatorProfile.primary_color e logo.

Esses campos não constituem um tema por cliente aplicado integralmente ao novo layout.
A identidade nova não é resolvida dinamicamente a partir de um tenant.

Fontes: templates/partials/gomut/member_header.html:2; templates/base_membros.html:4; templates/base_gomut.html:10; static/css/gomut/tokens.css; users/models.py:44; users/models.py:72.

### 3.3 — PARCIAL: separação GoMut / Emergensimples

Já separado:
- Login com identidade GoMut.
- Área principal do aluno com identidade escura Emergensimples.
- Escopos de tokens e arquivos preparados para diferentes contextos.

Ainda não aplicado:
- O painel real continua usando base_admin → base_core → cetremer.css.
- Não corresponde integralmente ao painel GoMut claro/verde do handoff.
- Telas legadas ainda apresentam referências à identidade anterior.

Fontes: templates/login.html:1; templates/base_gomut.html:11; templates/base_admin.html:1; templates/base_core.html:11.

## 4. MODELOS DE DADOS

### 4.1 — PARCIAL: usuários, papéis e permissões

User herda AbstractUser e acrescenta:
- role.
- avatar.
- bio.

Papéis:
- STUDENT.
- CREATOR.
- ADMIN.

StudentProfile:
- Relação 1:1 com User.
- full_name, cpf, address.
- points, level e title.

CreatorProfile:
- Relação 1:1 com User.
- Dados de empresa, marca e campos históricos de integrações.

Coprodutor, suporte e editor de conteúdo como papéis distintos: NÃO EXISTEM.

Permissão administrativa:
- painel_required exige login.
- Permite is_staff ou role ADMIN/CREATOR.
- Não há matriz de permissões por recurso/equipe.

Permissão de aluno:
- Views verificam papel, matrícula e access_decision.
- Progresso também valida acesso no serviço.

A herança de AbstractUser disponibiliza os mecanismos padrão de grupos/permissões do Django, mas não foi encontrada configuração desses grupos para os papéis do contexto.

Fontes: users/models.py:8; users/models.py:25; users/models.py:44; core/decorators.py:7; courses/access.py:20; courses/services.py:29.

### 4.2 — PARCIAL: curso, módulo e aula

Course:
- title, slug, description, cover_image.
- creator → CreatorProfile.
- category → Category, opcional.
- short_name, cover_color.
- workload_hours, learning_objectives, target_audience.
- price, is_published, created_at.
- live_calendar_url, live_meet_url e live_schedule_embed.

Module:
- course → Course.
- title, description, order.

Lesson:
- module → Module.
- title, description.
- video_url, vimeo_id, vimeo_hash.
- duration_seconds, order.

NÃO EXISTEM:
- Publicada/rascunho por módulo.
- Publicada/rascunho por aula.
- Liberação de aula por data.
- Liberação por dias após entrada.
- Modelo independente de tema/matéria.

O curso tem publicação; módulos e aulas não têm a mesma situação editorial.

Fontes: courses/models.py:31; courses/models.py:107; courses/models.py:153; painel/forms.py:75.

### 4.3 — PARCIAL: matrícula, plano e períodos

Enrollment:
- student → StudentProfile.
- course → Course.
- enrolled_at.
- source.
- last_accessed_at.
- access_policy: unrestricted ou periods.
- Unicidade aluno/curso.

AccessPeriod:
- enrollment → Enrollment.
- starts_on.
- ends_on, exclusivo.
- grace_days.
- source: legacy, payment ou manual.
- reference.
- created_at e created_by.

Subscription:
- Relação 1:1 com Enrollment.
- offer → Offer.
- status: migrating, draft, active, canceled.
- amount, next_due_on, gateway_id.
- Referências e situação da renovação anterior.

EXISTE:
- Cadastro de período manual no painel.
- Conversão da data final inclusiva para fim exclusivo.
- Três dias de tolerância no serviço manual.
- Preservação de histórico e recusa de sobreposição.

NÃO EXISTE como fluxo completo:
- Configurar/cancelar/reativar plano no painel conforme o protótipo.
- Observação interna de plano.
- Revogação de acesso já quitado ao cancelar.
- Correção retroativa de períodos pela interface.

Alterar Subscription.status, isoladamente, não é a regra central de acesso: access_decision consulta a matrícula e os períodos.

Fontes: courses/models.py:258; courses/models.py:289; sales/models.py:112; courses/services.py:142; painel/forms.py:11; painel/views/students.py:94.

### 4.4 — PARCIAL: progresso

Progress:
- student → StudentProfile.
- lesson → Lesson.
- is_completed.
- completed_at.
- Unicidade aluno/aula.

EXISTE:
- Conclusão e desfazer conclusão.
- Percentual e contagem por curso.
- Próxima aula não concluída.
- Último acesso por matrícula.
- Pontos e nível.

NÃO EXISTE:
- Posição do vídeo.
- Segundos efetivamente assistidos.
- Sessões de estudo.
- Minutos por dia.
- Sequência de dias.
- Log histórico de atividade.
- Mapa de constância.

completed_at é atualizado nas alterações e não constitui um histórico de eventos.
last_accessed_at também não permite reconstruir tempo estudado.

Fontes: courses/models.py:239; courses/models.py:277; courses/selectors.py:14; courses/services.py:29.

### 4.5 — NÃO EXISTE: quiz e avaliação final

Não foram encontrados modelos para:
- Quiz por aula.
- Perguntas.
- Alternativas.
- Resposta correta.
- Comentário por pergunta.
- Tentativas.
- Nota.
- Melhor nota.
- Avaliação final com aprovação em 70%.

A aba Quiz da aula existe apenas como indicação de recurso pendente.
O protótipo possui simulação de quiz em JavaScript.

Fontes: templates/courses/lesson_detail.html; docs/handoff-design/prototipo/assets/js/app.js:1107; inventário de classes em courses/models.py e demais apps.

### 4.6 — PARCIAL: certificado

Certificate:
- enrollment → Enrollment, relação 1:1.
- code único de 12 caracteres.
- student_name.
- student_cpf.
- course_title.
- workload_hours.
- completed_at e issued_at.

Requisitos atuais:
- Matrícula.
- Acesso regular para emitir certificado novo.
- Todas as aulas concluídas.
- Nome completo.
- CPF válido pelos dígitos verificadores.

NÃO EXISTE:
- Exigência de avaliação final com 70%.
- Verificação de tempo mínimo assistido.
- Regra separada de certificado baseada em quiz.

CPF:
- StudentProfile.cpf e Certificate.student_cpf são campos de texto.
- A aplicação guarda os 11 dígitos sem criptografia de campo.
- Criptografia do disco/backup em produção: não confirmada.
- A verificação pública omite CPF.
- A página privada do certificado exibe CPF.

PDF:
- O botão “Baixar PDF” chama a impressão do navegador.
- Não há geração e armazenamento de PDF no servidor.

LinkedIn:
- Integração ou botão de adicionar certificado: não encontrado.

Conformidade LGPD completa não pode ser confirmada pelo código.
Não foram encontrados fluxos específicos de retenção, anonimização ou atendimento ao titular.

Fontes: courses/models.py:329; courses/services.py:18; courses/services.py:70; users/validators.py:9; templates/courses/certificate.html:1; templates/courses/verify_certificate.html:1; static/js/site.js:31.

### 4.7 — PARCIAL: materiais e e-books

LessonMaterial:
- lesson → Lesson.
- title.
- file.
- url.
- order.

Upload:
- PDF.
- Validação de extensão e tipo de conteúdo declarado.
- Limite de 20 MB.
- Armazenamento em media/materials/.

EXISTE:
- PDF associado à aula.
- Link para abrir/baixar.
- Listagem na aba E-book da aula.

NÃO EXISTE:
- Modelo de e-book independente.
- Material diretamente associado ao curso sem passar por aula.
- Biblioteca de e-books.
- Leitor integrado.
- Página atual, percentual ou progresso de leitura.
- Download autenticado por endpoint específico.

Fontes: courses/models.py:208; courses/models.py:222; core/settings.py:150; courses/services.py:124; templates/courses/lesson_detail.html.

### 4.8 — NÃO EXISTE: anotações do aluno

Não há modelo, endpoint ou persistência de anotação vinculada ao minuto do vídeo.

Fontes: inventário dos modelos; core/urls.py; static/js/aluno.js.

### 4.9 — PARCIAL: ao vivo

Existem campos de curso para:
- Link de sala.
- URL de Google Calendar.
- Campo legado de incorporação de agenda.

EXISTE:
- Tela do aluno com os links dos cursos acessíveis.
- Configuração desses links no cadastro do curso.

NÃO EXISTE:
- Modelo de encontro individual.
- Tipo de encontro.
- Data/hora/duração como registro próprio.
- Gravação vinculada ao encontro.
- Inscrição ou lembrete por aluno.
- Disparo de lembrete.

Fontes: courses/models.py:57; courses/models.py:86; courses/student_views.py:214; painel/forms.py:27.

### 4.10 — PARCIAL: comunidade

CommunityPost:
- course opcional.
- lesson opcional.
- author.
- title, content, created_at.
- is_hidden.

Comment:
- post.
- author.
- content.
- parent opcional, apontando para outro Comment.
- created_at.

EXISTE:
- Publicar tópico.
- Vínculo com curso e aula.
- Criar resposta.
- Responder e ocultar/mostrar tópico no painel.
- Indicador is_answered quando existe resposta de staff/ADMIN/CREATOR.

NÃO EXISTE:
- Curtida ou “útil”.
- Solução escolhida.
- Marcação de solução pelo autor.
- Fixação.
- Papel específico de mentora.

A existência de Comment.parent não comprova uma interface completa de respostas encadeadas.
O endpoint examinado cria comentário sem receber parent.

Fontes: community/models.py:5; community/models.py:20; community/models.py:27; community/views.py:59; community/views.py:85; community/views.py:129; painel/views/community.py:14.

### 4.11 — NÃO EXISTE: suporte do contexto

Não há modelos para:
- Chamado.
- Assunto/status operacional.
- Histórico.
- “Também tenho esse problema”.
- Chamado público para a turma.
- FAQ.

Existe uma rota visual de Central de ajuda com indicação de backend pendente.

Fontes: courses/ui_capabilities.py:3; courses/student_views.py:98; templates/courses/feature_pending.html.

### 4.12 — NÃO EXISTE: notificações persistentes e preferências

Não há modelos para:
- Aviso por destinatário.
- Lido/não lido.
- Contador persistente.
- Preferência de e-mail de novas aulas ou encontros.

O sininho leva a uma tela pendente.
Django messages fornece avisos de operação, não uma central de notificações.

Fontes: templates/partials/gomut/member_header.html; courses/ui_capabilities.py:3; templates/partials/messages.html.

### 4.13 — PARCIAL: trilhas, vendas, vitrine, fileiras e áreas

Trilhas:
- NÃO EXISTE modelo nem ordem persistida de cursos em uma trilha.

Cursos à venda:
- Course.price e is_published.
- Página pública de apresentação.
- Order e OrderBump.
- Offer com modalidade mensal/avulsa e termos.

Offer possui:
- course, code, name, kind, amount.
- term_type.
- payment_count.
- access_days.
- grace_days.
- is_active.

Não existe o conjunto completo:
- Link externo de checkout por oferta.
- Garantia configurável.
- Condições de parcelamento apresentadas e contratadas.
- Gestão de vitrine conforme o protótipo.

Fileiras:
- NÃO EXISTE configuração persistida de ordem/ativação da página inicial.
- O hero atual é derivado das matrículas e do último acesso.

Áreas:
- Category possui name, slug, color e order.
- Course possui uma categoria opcional.
- Não existe a hierarquia mais ampla de áreas/temas/trilhas descrita no contexto.

Fontes: courses/models.py:11; courses/models.py:31; sales/models.py:15; sales/models.py:44; sales/models.py:57; courses/views.py:38; courses/student_views.py:19.

### 4.14 — EXISTE: outros modelos relevantes

- SiteSettings: configuração institucional global, SMTP e assinatura do certificado.
- CreatorProfile: dados do produtor e campos históricos de integrações.
- FirstAccessCode: código com hash, validade e tentativas.
- HeroBanner: banner da página pública; não controla o carrossel atual do aluno.
- GatewayCharge: registro local de cobrança para conferência.
- GatewayAttempt: tentativas técnicas de consulta/conferência.
- WebhookEvent: entrada de eventos recebidos, sem processamento financeiro.

Fontes: users/models.py:44; users/models.py:72; users/models.py:106; courses/models.py:345; sales/gateway_models.py:16; sales/gateway_models.py:82; sales/gateway_models.py:93.

## 5. ROTAS E TELAS

### 5.1 — EXISTE: mapa das rotas de aplicação

Prefixos das views abaixo:
- users = users/views.py
- student = courses/student_views.py
- certificate = courses/certificate_views.py
- public = courses/views.py
- community = community/views.py
- painel = módulos em painel/views/
- sales = sales/views.py

| URL | View | Template ou resultado |
|---|---|---|
| / | public.landing | landing.html |
| /login/ | users.login_view | login.html |
| /logout/ | users.logout_view | Encerra sessão e redireciona |
| /register/ | users.register_view | register.html |
| /primeiro-acesso/ | users.first_access_view | registration/first_access.html |
| /senha/esqueci/ | users.PasswordResetView | registration/password_reset_form.html |
| /senha/enviado/ | users.PasswordResetDoneView | registration/password_reset_done.html |
| /senha/nova/<uidb64>/<token>/ | users.PasswordResetConfirmView | registration/password_reset_confirm.html |
| /senha/pronto/ | users.PasswordResetCompleteView | Mensagem e redirecionamento ao login |
| /dashboard/ | student.dashboard | courses/dashboard.html |
| /dashboard/cursos/<course_slug>/ | student.member_course | courses/course_detail.html ou access_pending.html |
| /dashboard/recursos/<section>/ | student.member_section | member_progress.html ou feature_pending.html |
| /settings/ | users.settings_view | users/settings.html |
| /ao-vivo/ | student.live_classes | courses/live_classes.html |
| /certificados/ | certificate.certificates | courses/certificates.html |
| /certificado/verificar/ | certificate.verify_certificate | courses/verify_certificate.html |
| /courses/<course_slug>/ | public.course_preview | courses/course_preview.html |
| /courses/<course_slug>/lessons/<lesson_id>/ | student.lesson_detail | courses/lesson_detail.html ou access_pending.html |
| /courses/lesson/<lesson_id>/complete/ | student.complete_lesson | JSON, POST |
| /courses/lesson/<lesson_id>/toggle-progress/ | student.toggle_progress | JSON, POST |
| /courses/<course_slug>/certificate/ | certificate.issue_certificate | certificate.html, certificate_error.html, certificate_ready.html ou access_pending.html |
| /courses/<course_slug>/checkout/ | sales.checkout | sales/checkout.html |
| /courses/<course_slug>/checkout/process/ | sales.process_checkout | JSON de indisponibilidade, POST |
| /community/ | community.community_hub | community/hub.html |
| /community/post/new/ | community.create_hub_post | POST e redirecionamento |
| /courses/<course_slug>/community/post/ | community.create_post | POST e redirecionamento |
| /community/posts/<post_id>/comment/ | community.create_comment | POST e redirecionamento |
| /painel/ | painel.overview.dashboard | painel/dashboard.html |
| /painel/cursos/ | painel.course_management.courses | painel/courses.html |
| /painel/cursos/novo/ | painel.course_management.course_edit | painel/course_edit.html |
| /painel/cursos/<course_id>/ | painel.course_management.course_edit | painel/course_edit.html |
| /painel/cursos/<course_id>/aulas/ | painel.course_management.course_lessons | painel/course_lessons.html |
| /painel/cursos/<course_id>/aulas/ordem/ | painel.course_management.course_reorder | JSON, POST |
| /painel/alunos/ | painel.students.students | painel/students.html; ações por POST |
| /painel/alunos/exportar/ | painel.students.students_export | CSV |
| /painel/alunos/importar/ | painel.students.students_import | painel/students_import.html |
| /painel/pedidos/ | painel.orders.orders | painel/orders.html |
| /painel/pedidos/exportar/ | painel.orders.orders_export | CSV |
| /painel/comunidade/ | painel.community.community | painel/community.html |
| /painel/configuracoes/ | painel.settings.settings | painel/settings.html |
| /webhooks/asaas/ | sales.webhook_views.asaas_webhook | JSON, POST |
| /admin/ | Django Admin | Templates administrativos do Django |

Aliases antigos:
- /creator/ → painel.
- /creator/course/new/ → novo curso.
- /creator/course/<id>/edit/ → editar curso.
- /creator/course/<id>/builder/ → aulas.
- /creator/payments/ → configurações.
- /creator/integrations/ → configurações.

São redirecionamentos permanentes.

Com DEBUG, há também a rota auxiliar de media/.
O Django Admin inclui suas próprias subrotas de autenticação e CRUD.

Fontes: core/urls.py:15; painel/urls.py:5; painel/views/common.py:45; arquivos de views indicados na tabela.

### 5.2 — PARCIAL: telas e partes pendentes

Telas inteiramente pendentes:
- /dashboard/recursos/trilhas/
- /dashboard/recursos/minha-lista/
- /dashboard/recursos/notificacoes/
- /dashboard/recursos/ajuda/

Partes pendentes:
- Quiz na página da aula.
- Curtir e Minha lista na página da aula.
- Tempo de estudo e sequência de dias em Meu progresso.

Meu progresso NÃO é inteiramente vazio:
- Mostra conclusões reais.
- Mostra cursos e percentuais reais.
- Não tem gráfico diário, mapa de constância ou histórico de atividade.

Não existem rotas reais para as telas de Relatórios e Controle de acesso do novo painel.
Não confundir telas provisórias do protótipo com views Django.

Fontes: courses/ui_capabilities.py:3; courses/student_views.py:98; templates/courses/member_progress.html; templates/courses/lesson_detail.html.

### 5.3 — PARCIAL: API

Não existe API DRF ou GraphQL.

Existem views JSON:
- POST /courses/lesson/<id>/complete/
- POST /courses/lesson/<id>/toggle-progress/
- POST /painel/cursos/<id>/aulas/ordem/
- POST /courses/<slug>/checkout/process/ — bloqueado.
- POST /webhooks/asaas/ — recepção técnica.

O modal busca HTML autenticado de /dashboard/cursos/<slug>/ por fetch.
Isso não é uma API JSON.

Fontes: courses/student_views.py:186; painel/views/course_management.py:192; sales/views.py:35; sales/webhook_views.py:23; static/js/gomut/course-dialog.js:12.

## 6. VÍDEO E PLAYER

### 6.1 — EXISTE: iframe e SDK Vimeo

- Lesson.player_url monta a URL do iframe.
- ID e hash de vídeo não listado são armazenados.
- O template utiliza iframe.
- O SDK oficial player.js é carregado.
- O JavaScript conecta o evento ended.
- O backend também aceita YouTube.
- A consulta de duração usa oEmbed do Vimeo.

O vídeo público de exemplo carregou o player em verificações anteriores, mas a reprodução não foi homologada; isso está documentado.

Fontes: courses/models.py:153; courses/models.py:192; courses/integrations/vimeo.py:12; templates/courses/lesson_detail.html; static/js/aluno.js:108; docs/area-aluno-demonstracao.md.

### 6.2 — PARCIAL: eventos, sem telemetria de tempo

EXISTE:
- Evento ended.
- Envio POST ao endpoint complete_lesson.

NÃO EXISTE:
- timeupdate persistido.
- Captura periódica de posição.
- getCurrentTime/setCurrentTime para retomada.
- Registro de segundos assistidos.
- Endpoint de heartbeat.
- Registro de sessão diária.

Trecho relevante:

    player.on('ended', function () {
        postJSON(frame.getAttribute('data-complete-url'));
    });

O destino é:
POST /courses/lesson/<id>/complete/

Fontes: static/js/aluno.js:108; core/urls.py:27; courses/student_views.py:188.

### 6.3 — PARCIAL: conclusão automática

A implementação automática atual é ao FINAL do vídeo, pelo evento ended.

A regra de 90% NÃO EXISTE.
Também é possível concluir/desfazer pelo botão manual.

O endpoint automático é idempotente: marca concluída, sem alternar.
O endpoint manual alterna o estado.

Não há comprovação de tempo assistido no servidor para autorizar a conclusão.

Fontes: static/js/aluno.js:116; courses/student_views.py:188; courses/student_views.py:194; courses/services.py:29.

## 7. AUTENTICAÇÃO

### 7.1 — EXISTE: login, recuperação e primeiro acesso

Login:
- Sessão Django.
- E-mail ou username pelo EmailBackend.
- Destino padrão separado entre aluno e administração.
- next validado para evitar redirecionamento externo.

Recuperação:
- Views e tokens padrão do Django.
- Envio pelo backend SMTP configurado.

Primeiro acesso:
- Administrador cadastra/matricula o aluno.
- Conta pode ficar sem senha utilizável.
- Código temporário exibido uma vez para entrega externa.
- Código guardado como hash.
- Validade de sete dias.
- Bloqueio após cinco erros.
- Aluno informa e-mail/código e define sua própria senha.
- Existe opção explícita de enviar link por e-mail.

Não há envio automático pelo WhatsApp.
O cadastro público /register/ continua existindo, embora não seja promovido no login novo.

Fontes: users/backends.py:5; users/views.py:16; users/views.py:77; users/views.py:99; users/first_access.py:11; painel/views/students.py:34; painel/views/common.py:15.

### 7.2 — PARCIAL: integração financeira

Provedor preparado: Asaas.

EXISTE:
- Configuração ASAAS_* no servidor.
- Consulta de cobranças.
- Conferência por identificador/referência.
- Registros técnicos locais.
- Webhook autenticado e idempotente.

NÃO EXISTE:
- Compra operacional.
- Criação de cobrança.
- Criação de assinatura.
- Processamento financeiro de eventos.
- Matrícula automática por pagamento.
- Renovação de acesso por pagamento.

O checkout retorna 503.
create_payment e create_subscription lançam billing_not_enabled.

Hotmart/Eduzz aparecem como origem de migração de períodos quitados.
Não existe integração operacional com suas APIs/webhooks.
Não foram encontradas integrações Kiwify ou Stripe.

Fontes: sales/views.py:35; sales/integrations/asaas/client.py:111; sales/payment_services.py:15; sales/webhook_services.py:141; sales/migration_services.py:24.

### 7.3 — NÃO EXISTE: impersonação operacional

Não foi encontrado fluxo real de “Visualizar como membro” com:
- Sessão de visualização.
- Aluno/curso selecionado.
- Auditoria.
- Retorno ao administrador.
- Distinção de ações permitidas na visualização.

O protótipo tem essa experiência.
No backend atual, views do aluno normalmente redirecionam quem não é STUDENT.

Fontes: courses/student_views.py:19; courses/student_views.py:78; docs/handoff-design/05-telas/area-de-membros.md.

## 8. PAINEL DO PRODUTOR

### 8.1 — PARCIAL: painel funcional, redesign incompleto

O painel Django existe e permite:
- Indicadores básicos.
- Listar/criar/editar cursos.
- Publicar/despublicar curso.
- Gerenciar módulos e aulas.
- Reordenar módulos e aulas.
- Cadastrar link de vídeo e PDF.
- Gerenciar alunos e matrículas.
- Importar CSV com prévia.
- Registrar períodos quitados.
- Consultar/exportar pedidos.
- Responder e ocultar publicações.
- Configurar dados institucionais, SMTP e assinatura.

Não reproduz integralmente o design GoMut de handoff/telas/painel.
Continua no layout administrativo anterior.

Não há percentual medido de fidelidade visual.
A migração recente priorizou login e telas principais do aluno.

Fontes: painel/urls.py:5; painel/views/; templates/base_admin.html:1; templates/base_core.html:11; docs/area-aluno-demonstracao.md.

### 8.2 — EXISTE: protótipo independente anterior

Encontrados:
- docs/handoff-design/prototipo/index.html
- docs/handoff-design/prototipo/coprodutor.html
- docs/handoff-design/prototipo/assets/js/app.js
- docs/handoff-design/prototipo/assets/js/admin.js
- docs/handoff-design/prototipo/assets/js/data.js

O admin.js usa localStorage e inclui o texto:
“as alterações ficam salvas só neste navegador”.

O protótipo do aluno também usa localStorage e sessionStorage.

A versão descrita no contexto como “um HTML só”, com todos os recursos novos, NÃO FOI CONFIRMADA neste repositório. O pacote encontrado tem duas entradas HTML e arquivos JS separados.

Fontes: docs/handoff-design/prototipo/assets/js/admin.js:10; admin.js:139; admin.js:274; docs/handoff-design/prototipo/assets/js/app.js:17; app.js:180.

## 9. DADOS E SEEDS

### 9.1 — EXISTE: três mecanismos

1. data_dump.json
   - Fixture para loaddata.
   - Pode representar dados anteriores à nova demonstração.

2. seed.py
   - Apaga dados antes de recriar.
   - Não é seguro executá-lo para complementar uma base existente.
   - Não foi executado neste diagnóstico.

3. prepare_demo
   - Comando não destrutivo.
   - Exige GOMUT_DEMO_MODE.
   - Cria cursos, módulos, aulas, contas fictícias, matrículas e períodos.
   - Preserva senhas existentes.
   - Usa os slugs gomut-demo-plantao e gomut-demo-cardiologia.

Comando de população, apenas como referência:

    python manage.py prepare_demo --password <SENHA-DE-DEMONSTRACAO>

Deve ser usado com banco separado.
Nenhuma população de dados foi executada nesta etapa.

Fontes: README.md; seed.py:15; courses/management/commands/prepare_demo.py:13.

### 9.2 — EXISTE: contagem atual da base de demonstração

Consulta SQLite somente leitura em .venv/gomut-demo.sqlite3:

| Registro | Quantidade |
|---|---:|
| Cursos | 2 |
| Módulos | 4 |
| Aulas | 8 |
| Usuários com role STUDENT | 1 |
| Matrículas | 2 |
| Períodos de acesso | 2 |
| Registros de progresso | 2 |
| Certificados | 0 |
| Assinaturas Subscription | 0 |
| Publicações de comunidade | 0 |

Cursos:
- gomut-demo-plantao
- gomut-demo-cardiologia

Os cerca de 36 alunos do cliente não estão nessa base.
Não existe db.sqlite3 na raiz atualmente.
Contagens de produção: não confirmadas.

## 10. QUALIDADE E RESTRIÇÕES

### 10.1 — PARCIAL: testes e cobertura

Execução atual:
- 138 testes.
- Zero falhas.
- Django system check sem problemas reportados durante a execução.
- Banco de teste em memória, sem alterar a base de demonstração.

Há testes de:
- Login, cadastro, recuperação e primeiro acesso.
- Permissões e matrícula.
- Períodos quitados e datas.
- Progresso e certificados.
- Importação e validação.
- Reordenação.
- Checkout bloqueado.
- Asaas com transporte simulado.
- Webhooks.
- Backup SQLite.
- Demonstração e hero por curso.

Cobertura percentual e relatório de linhas: NÃO EXISTEM no material encontrado.
Testes passando não comprovam streaming Vimeo, envio SMTP ou fidelidade de todas as telas.

Fontes: core/test_*.py; users/test_*.py; courses/test_*.py; painel/test_*.py; sales/test_*.py; execução atual da suíte.

### 10.2 — PARCIAL: restrições

Navegadores:
- Chrome e Edge tiveram fluxos principais verificados anteriormente.
- Firefox teve conferência visual do login.
- Opera não foi verificado.
- Matriz formal de versões mínimas: não encontrada.
- Código novo depende de recursos como dialog, inert, ResizeObserver, document.fonts e CSS de fonte variável.

Acessibilidade:
- Existem labels, foco visível, ARIA, abas por teclado e tratamento de movimento reduzido.
- Não há auditoria completa ou declaração de conformidade WCAG.
- Há padrões diferentes entre telas antigas e novas.

Idioma/fuso:
- LANGUAGE_CODE = pt-br.
- TIME_ZONE = America/Campo_Grande.
- USE_TZ ativo.
- O calendário incorporado também utiliza America/Campo_Grande.

LGPD:
- CPF em texto no banco.
- Verificação pública de certificado omite CPF.
- Políticas de retenção, anonimização e gestão de consentimento não foram encontradas.
- Proteção da infraestrutura e backups não confirmada.

Performance:
- Sem benchmark.
- Sem cache/fila configurados.
- Algumas telas montam listas e fazem cálculos em Python.
- Consultas de progresso por curso podem multiplicar consultas.
- SQLite exige atenção à serialização de escrita e ao disco persistente.

Fontes: core/settings.py:130; courses/models.py:86; static/js/gomut/course-carousel.js:1; static/js/gomut/course-dialog.js:1; courses/selectors.py:14; courses/services.py:29; docs/operacao-sqlite.md.

### 10.3 — PARCIAL: débitos e fragilidades identificados

1. Dois sistemas de layout coexistem.
   Novo aluno e telas antigas têm CSS, fontes e componentes diferentes.
   Fontes: templates/base_gomut.html; templates/base_core.html.

2. Marca nova parcialmente fixa em templates.
   O painel de configuração não controla integralmente o tema novo.
   Fontes: templates/partials/gomut/member_header.html:2; users/models.py:72.

3. Permissões administrativas amplas.
   CREATOR pode consultar/gerenciar o conjunto de cursos; não há isolamento por cliente.
   Fontes: core/decorators.py:7; painel/views/course_management.py:24.

4. Datas de acesso exigem cuidado.
   ends_on é exclusivo; interface usa último dia inclusive; há tolerância.
   Fontes: courses/models.py:289; courses/services.py:142.

5. Cancelar assinatura não equivale automaticamente a bloquear acesso.
   AccessPeriod e Subscription são estruturas diferentes.
   Fontes: courses/access.py:20; sales/models.py:112.

6. Progresso atual não é telemetria.
   Não usar completed_at para fabricar minutos ou sequência de estudos.
   Fontes: courses/models.py:239; courses/services.py:29.

7. Certificado não exige avaliação final.
   Acrescentar a regra muda critérios de emissão e precisa preservar certificados anteriores.
   Fontes: courses/services.py:70; courses/models.py:329.

8. PDF é link direto de media.
   Bloquear a aula não revoga automaticamente uma URL de arquivo já conhecida.
   Fontes: templates/courses/lesson_detail.html; core/urls.py:68.

9. Upload PDF não tem inspeção profunda de conteúdo.
   A validação encontrada usa extensão, tipo declarado e tamanho.
   Fontes: courses/models.py:222.

10. Campos legados de integrações permanecem no banco.
    Alguns são CharField/TextField históricos; não presumir que todos são cifrados.
    O Asaas atual utiliza configuração do servidor e ignora campos antigos.
    Fontes: users/models.py:44; users/models.py:72; docs/asaas-integracao-tecnica.md.

11. Configurações do painel usam atribuições diretas e validação desigual.
    O fluxo não usa o mesmo padrão de ModelForm dos cursos.
    Fontes: painel/views/settings.py:16; painel/forms.py:27.

12. Renderização pode criar SiteSettings quando ausente.
    SiteSettings.load() chama get_or_create.
    Não utilizar navegação HTTP como auditoria estritamente sem escrita sobre uma base vazia.
    Fontes: users/models.py:94; core/context_processors.py:1.

13. Hero tem ajuste de altura em JavaScript e regras adicionais ao CSS normativo.
    Alterações de fontes, tamanhos e observadores precisam de teste responsivo.
    Fontes: static/js/gomut/course-carousel.js:6; static/css/gomut/members.css.

14. seed.py é destrutivo.
    Não utilizar para cadastrar os alunos reais.
    Fonte: seed.py:15.

15. Parte expressiva da implementação está sem commit.
    Um checkout de main em outra máquina não necessariamente terá o estado diagnosticado.
    Fonte: git status e branch atual.

### 10.4 — EXISTE: preferências; proibições parciais

Preferências documentadas:
- Django e templates.
- CSS e JavaScript próprios.
- SQLite mantido.
- Separar forms, serviços, consultas, integrações e adaptadores HTTP.
- Evitar abstrações e infraestrutura sem necessidade.
- Preservar autenticação e regras reais ao aplicar o design.
- Utilizar fontes e SVG do handoff.

Decisões registradas:
- React e Vue fora desta etapa.
- Não introduzir API/frontend separados para o MVP.
- Gateway fica para etapa posterior.
- Recursos não implementados devem ser identificados explicitamente.

Regras visuais:
- Painel claro, sem alternador de tema.
- Não substituir ícones ou fontes por semelhantes.
- Não expor caminho administrativo ao aluno.
- Não copiar localStorage/login simulado como implementação real.

Não foi encontrada política formal de dependências proibidas além das decisões e regras do handoff/plano.

Fontes: README.md; docs/handoff-design/01-regras-inviolaveis.md; docs/superpowers/plans/2026-11-16-area-aluno-design.md.

## 11. MAPA DE LACUNAS

Nesta tabela, “não existe” se refere ao produto Django, mesmo quando há simulação no protótipo.

| Funcionalidade | Status | Onde está | O que falta | Risco ou observação |
|---|---|---|---|---|
| Login do aluno | existe | users/views.py:16; templates/login.html | Homologação completa dos ambientes | Usa sessão real |
| Início com hero por curso | existe | courses/student_views.py:19; course_hero.html; course-carousel.js | Configuração editorial opcional | Usa matrículas acessíveis |
| Retomar curso/aula pendente | parcial | courses/selectors.py:14 | Retomar minuto do vídeo | Não confundir aula pendente com posição |
| Meus cursos | existe | templates/courses/dashboard.html | — | Um ou dois cursos suportados |
| Contagem de aulas concluídas | existe | courses/member_progress.html; Progress | — | Dados reais |
| Progresso por curso | existe | courses/selectors.py:14 | — | Baseado em conclusão |
| Minutos estudados por dia | não existe | Sem modelo de telemetria | Sessões/eventos e agregação | Não derivar de duração cadastrada |
| Sequência de dias | não existe | Sem modelo de atividade | Critério e registros diários | Exige regra de dia/fuso |
| Mapa de constância de 12 semanas | não existe | Sem histórico diário | Histórico e agregação | Não reconstruível com um timestamp |
| Atividade recente | não existe | Sem event log | Eventos históricos | Último acesso não basta |
| Próximos passos | parcial | courses/selectors.py:14 | Composição do painel completo | Existe próxima aula não concluída |
| Certificados no painel de progresso | parcial | courses/certificate_views.py:15 | Integração com o painel novo | Tela separada existe |
| Página interna do curso | parcial | courses/student_views.py:78; course_detail.html | Composição completa do contexto | Módulos e acesso funcionam |
| Módulos e aulas do curso | existe | courses/models.py:107; :153 | — | Sem liberação individual |
| Materiais na página do curso | parcial | LessonMaterial; aula | Agregação/biblioteca no curso | Atualmente associados à aula |
| Dúvidas da turma no curso | parcial | CommunityPost; community/views.py | Integração visual completa | Vínculos existem |
| Requisitos do certificado | parcial | courses/services.py:70 | Avaliação final de 70% | Hoje exige aulas e dados pessoais |
| Player Vimeo | parcial | Lesson.player_url; aluno.js | Homologação de reprodução | Dependência externa |
| Retomada da posição | não existe | Sem campo/endpoint | Salvar/restaurar posição | Precisa tratar dispositivos diferentes |
| Conclusão automática aos 90% | não existe | aluno.js:116 usa ended | Regra e processamento de 90% | Cliente sozinho não comprova audiência |
| Conclusão manual | existe | courses/services.py:29 | — | Pode ser desfeita |
| Conclusão ao fim do vídeo | parcial | aluno.js:116; complete_lesson | Homologação Vimeo | Endpoint idempotente |
| Contagem para próxima aula | não existe | Apenas protótipo | Estado e navegação automática | Deve permitir cancelar |
| Anotações no minuto do vídeo | não existe | Sem modelo | Persistência e interface | Devem ter escopo definido |
| Etapas Assistir → Quiz → Próxima | não existe | Navegação e aba visual | Máquina de estados/regras | Definir bloqueio ou orientação |
| Quiz por aula | não existe | Aba pendente | Modelos, tentativas e correção | Protótipo não é persistência |
| Liberação do quiz após aula | não existe | Sem quiz real | Regra de liberação | Depende da conclusão definida |
| Comentário por pergunta | não existe | Só protótipo | Conteúdo e respostas | Não expor gabarito indevidamente |
| Avaliação final com 70% | não existe | Sem modelos | Prova, tentativas e nota | Afeta certificado |
| Nome/CPF para certificado | existe | users/validators.py; Certificate | Política de dados | CPF sem cifra de campo |
| Código público de certificado | existe | certificate_views.py:93 | — | Página pública omite CPF |
| PDF do certificado | parcial | certificate.html; site.js:31 | PDF gerado no servidor, se exigido | Hoje depende da impressão |
| LinkedIn | não existe | Sem integração | Link e campos necessários | Não confundir com copiar URL |
| Agenda ao vivo | parcial | Course.live_calendar_url; live_classes | Encontros próprios | Calendário externo |
| Lembretes ao vivo | não existe | Sem modelo/job | Preferências e envio | Requer agendamento |
| Gravação vinculada a encontro | não existe | Sem modelo LiveEvent | Relação e publicação | Pode reutilizar aula futuramente |
| PDF por aula | existe | courses/models.py:208 | — | Download direto |
| Biblioteca de e-books | não existe | Sem rota/modelo próprios | Catálogo agregado | Não duplicar arquivos sem necessidade |
| Leitor integrado | não existe | Links para PDF | Leitor e navegação | Arquivo externo pode ter restrições |
| Progresso de leitura | não existe | Sem modelo | Páginas/eventos e sincronização | Definir o que significa concluir |
| Comunidade por curso/aula | parcial | CommunityPost | Interface completa em todas as telas | Vínculos e autorização existem |
| Respostas da comunidade | existe | Comment; create_comment | Encadeamento completo na UI | parent existe no modelo |
| “Útil”/curtida | não existe | Sem modelo | Relação usuário/resposta | Precisa impedir duplicidade |
| Solução marcada | não existe | is_answered não é solução | Referência e permissões | Autor e mentora têm regras diferentes |
| Fixar tópico | não existe | Sem campo | Ordem e moderação | Definir escopo |
| Ocultar tópico | existe | is_hidden; painel/community.py | Revisão completa das permissões | Ocultar não é apagar |
| FAQ de suporte | não existe | Ajuda pendente | Modelo e gestão | Conteúdo editorial |
| Chamados públicos | não existe | Ajuda pendente | Modelo, visibilidade e UI | Evitar exposição de dados pessoais |
| Status do chamado | não existe | Sem modelo | Aberto/Em análise/Resolvido | Precisa registrar transições |
| “Também tenho esse problema” | não existe | Sem relação | Associação única por usuário | Contagem não é comentário |
| Linha do tempo do chamado | não existe | Sem event log | Histórico de eventos | Não sobrescrever status sem histórico |
| Notificações/sininho | não existe | Rota pendente | Destinatário, leitura e contador | Django messages não substitui |
| Preferências de e-mail | não existe | Sem campos | Persistência por usuário | SMTP global já existe |
| Busca | parcial | static/js/gomut/navigation.js | Busca de aulas e outras entidades | Hoje filtra cursos da tela |
| Minha conta | parcial | users/views.py:134 | Campos e visual completos do protótipo | Tela antiga funcional |
| Minha lista/favoritos | não existe | Rota pendente | Modelo e operações | Não usar localStorage no produto |
| Login do produtor | existe | users/views.py:16 | — | Destino por papel |
| Meus cursos no painel | existe | painel/course_management.py:24 | Visual GoMut novo | Backend funcional |
| Criar curso | existe | painel/course_management.py:55 | Campos novos do produto | Estrutura básica existente |
| Aba Básico | parcial | painel/course_edit.html | Correspondência integral ao handoff | Não há todas as configurações novas |
| Visão geral do curso | parcial | Contagens em course_edit e dashboard | Página/aba completa | Não é o relatório do protótipo |
| Gestão de módulos/aulas | existe | painel/course_management.py:89 | — | Edição e exclusão alteram conteúdo real |
| Reordenação | existe | course_reorder:192; painel-grade.js | — | Valida IDs do curso |
| Link Vimeo e duração | existe | LessonForm; integrations/vimeo.py | Homologar metadados privados | Consulta de duração pode falhar |
| E-book no editor de aula | parcial | LessonMaterial; course_lessons.html | Leitor/progresso e gestão ampliada | Upload básico existe |
| Quiz no editor | não existe | Só protótipo | Modelos e editor | Não há persistência |
| Rascunho/publicação de aula | não existe | Lesson sem situação | Campos e filtros de acesso | Course.is_published não resolve |
| Liberação imediata/data/dias | não existe | Sem campos | Regras e cálculo por matrícula | Exige preservar acesso por curso |
| Trilhas no painel | não existe | Só protótipo | Modelo e ordenação | Não confundir com módulos |
| Cursos à venda | parcial | Course.price; Offer; página pública | Gestão completa e contratação | Checkout bloqueado |
| Link externo de checkout | não existe | Sem campo operacional específico | Configuração e uso | Não presumir provedor |
| Vitrine e garantia | parcial | Landing e cursos publicados | Gestão de vitrine e garantia | Regras comerciais ausentes |
| Fileiras da página inicial | não existe | Hero derivado de matrícula | Configuração de ordem/ativação | Sem modelo editorial |
| Áreas | parcial | Category | Gestão conforme o novo painel | Categoria simples existe |
| Ao vivo no painel | parcial | Campos de Course | CRUD de encontros | Hoje são links por curso |
| Tabela de alunos | existe | painel/views/students.py:34 | Visual novo | Usa dados reais |
| Filtro por curso | existe | painel/views/students.py | — | Visão administrativa global |
| Adicionar aluno/matricular | existe | users/services.py:16; painel/students.py | — | Primeiro acesso separado |
| Importação em lote | existe | users/importing.py:39; students_import | Validar arquivo real do cliente | Tem prévia e confirmação |
| Período manual de acesso | existe | courses/services.py:142 | Correção retroativa | Preserva histórico |
| Configurar/cancelar/reativar plano | parcial | Subscription; AccessPeriod | Fluxo administrativo completo | Cancelamento não bloqueia períodos sozinho |
| Moderação da comunidade | parcial | painel/views/community.py:14 | Útil, solução, fixação e papéis | Responder/ocultar existem |
| Painel de certificados | não existe | Há tela do aluno e Django Admin | Tela operacional própria | Admin técnico não é o novo painel |
| Painel de chamados | não existe | Sem modelos/rotas | Fluxo completo | Depende do suporte |
| Relatórios | parcial | painel/views/overview.py:18 | Tela e métricas do contexto | Há indicadores básicos |
| Controle de acesso da equipe | não existe | Apenas painel_required | Papéis e permissões | Não é a matrícula do aluno |
| Configuração da mentoria | não existe | Sem entidade/configuração completa | Modelo de produto definido | Protótipo usa outro vocabulário |
| Configuração da área de membros | parcial | SiteSettings | Integrar tema novo e seções | Parte da marca está fixa |
| Configuração do plano do aluno | parcial | Offer/Subscription/períodos | Interface e regras completas | Não há cobrança automática |
| Configuração da FAQ | não existe | Sem FAQ | CRUD e publicação | — |
| Configuração de avisos | não existe | Sem modelo de aviso | Autoria, destino e publicação | — |
| “Visualizar como membro” | não existe | Só protótipo | Preview autorizado e auditado | Não usar senha do aluno |
| Pagamento e matrícula automática | não existe | Fundação Asaas parcial | Contratação e processamento financeiro | Gateway desativado por padrão |

## 12. SUAS RECOMENDAÇÕES

### 12.1 — RECOMENDAÇÃO baseada no código existente

1. Consolidar a especificação vigente.
   Separar o que é curso, módulo, aula, trilha e eventual mentoria.
   Conciliar o contexto novo com o handoff antigo, que contém regras diferentes de certificado.
   Referências: docs/handoff-design/06-comportamentos-e-regras.md; courses/models.py.

2. Estabilizar a base atual e registrar o trabalho em Git.
   Preservar as alterações existentes, a base separada de demonstração e os testes.
   Referências: git status; docs/area-aluno-demonstracao.md.

3. Fechar autorização e ciclo de matrícula.
   Definir cancelamento, reativação, correção de períodos e escopo dos papéis antes de acrescentar telas administrativas.
   Referências: courses/access.py; courses/services.py:142; core/decorators.py.

4. Completar o modelo editorial.
   Publicação de aula, regras de liberação, metadados e materiais.
   Isso fornece a base correta para player, quiz e navegação.
   Referências: Lesson, Module e LessonMaterial.

5. Implementar telemetria do player.
   Posição, sessões, tempo efetivo e regra de 90%, com contrato de eventos e testes.
   Depois derivar minutos por dia, constância e atividade recente.
   Referências: Progress; static/js/aluno.js.

6. Implementar quiz por aula e avaliação final como recursos distintos.
   O quiz pedagógico não deve ser confundido com o requisito de aprovação final.
   Referências: ausência dos modelos em 4.5.

7. Atualizar a emissão de certificado.
   Aplicar os requisitos novos e preservar o histórico já emitido.
   Decidir PDF de servidor e LinkedIn.
   Referências: courses/services.py:70; Certificate.

8. Completar as telas de aluno com dados reais.
   Progresso ampliado, página do curso, e-books e conta.
   Migrar as telas legadas sem misturar CSS.
   Referências: base_membros, base_aluno e bases CSS distintas.

9. Expandir comunidade e suporte.
   Solução, útil, fixação, chamados e histórico, com autorização por curso.
   Referências: CommunityPost e Comment.

10. Implementar encontros, notificações e tarefas agendadas.
    Lembretes dependem de dados persistentes e infraestrutura de envio.
    Referências: links atuais de Course; ausência de scheduler.

11. Migrar o painel para o design GoMut por funcionalidade.
    Reutilizar os serviços existentes, em vez de transportar o estado do protótipo.
    Referências: painel/views e prototipo/assets/js/admin.js.

12. Deixar a contratação financeira para a etapa prevista.
    Conectar o Asaas somente depois das regras de acesso e dos fluxos operacionais estarem fechados.
    Referências: sales/integrations/asaas e docs/asaas-integracao-tecnica.md.

Essa ordem não exige reescrever o projeto em outro framework.

### 12.2 — NÃO CONFIRMADO: decisões que preciso antes da implementação completa

1. Onde está a versão mais recente do protótipo em HTML único?
   O repositório encontrado contém duas entradas e um conjunto anterior de JS.

2. Qual é a relação definitiva entre curso, mentoria, tema e trilha?
   Hoje o backend tem Curso → Módulo → Aula.

3. Quais papéis de equipe existirão de fato?
   Apenas administrador/produtor ou também suporte, editor e coprodutor?

4. O que cancelar um plano faz com um período já quitado?
   Bloqueia imediatamente, aguarda o fim ou permite uma data escolhida?

5. Como serão corrigidos períodos manuais registrados incorretamente?
   Preservando qual histórico e exigindo qual confirmação?

6. O que libera a avaliação final?
   Todas as aulas concluídas, determinado prazo ou outra condição?

7. Quais são as regras de tentativas da avaliação final?
   Limite, intervalo, melhor nota, embaralhamento e comportamento após aprovação.

8. “Assistir → Quiz → Próxima” é bloqueio obrigatório ou orientação?
   O contexto já informa que o quiz da aula não conta para o certificado.

9. Qual é o critério operacional para tempo de estudo?
   Como tratar pausa, aba em segundo plano, velocidade, repetição e múltiplos dispositivos?

10. Como será medido o progresso de leitura de e-books?
    Página visitada, percentual percorrido ou confirmação manual?

11. Quem pode ver cada chamado público?
    Todo aluno, alunos do mesmo curso ou uma turma específica?
    Como tratar dados pessoais eventualmente enviados?

12. As anotações são sempre privadas?
    E quais ações autor/mentora/equipe podem realizar na comunidade?

13. O PDF do certificado precisa ser gerado e armazenado no servidor?
    E quais dados institucionais devem aparecer no documento e no LinkedIn?

14. Qual é o ambiente real de produção?
    Servidor, disco persistente, backups, SMTP, entrega de arquivos e domínio autorizado no Vimeo.

15. Quais dados e períodos dos cerca de 36 alunos serão importados?
    A base examinada contém apenas o aluno fictício com duas matrículas.

16. Como será a manutenção da identidade do cliente?
    Configuração global desta instalação ou necessidade real de atender vários clientes na mesma aplicação?

Nenhuma dessas decisões foi implementada ou alterada durante este diagnóstico.
