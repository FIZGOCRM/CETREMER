# Etapa 1.1 — planos e vencimentos

**Status: concluída**, com a regra adicional aprovada em 17/11/2026.

## 1. O que foi feito

- Serviços de criar plano, encerrar, reativar e corrigir com histórico AccessChange.
- Limite de reativação acompanha o fim contratual corrigido, conforme aprovação.
- Formulários de último dia com acesso convertem data inclusiva para fim exclusivo.
- Encerramento usa o primeiro dia sem acesso e zera a tolerância.
- Plano em Minha conta, avisos dispensáveis por marco no Início e selos nos cursos.
- Gestão de plano/histórico/observação e página de Vencimentos no painel atual.
- Campo support_email e configuração de duração padrão do curso.
- Datas demo preservadas; âncora preenchida a partir do período mais antigo.

## 2. Arquivos criados e alterados

- `core/urls.py`
- `courses/migrations/0010_v1_student_plans.py`
- `courses/migrations/0011_backfill_plan_anchor.py`
- `courses/models.py`
- `courses/services.py`
- `courses/student_views.py`
- `courses/test_access_periods.py`
- `courses/test_member_redesign.py`
- `courses/test_plan_lifecycle.py`
- `docs/decisoes-produto.md`
- `painel/forms.py`
- `painel/urls.py`
- `painel/views/plans.py`
- `painel/views/settings.py`
- `painel/views/students.py`
- `static/css/gomut/members.css`
- `templates/courses/access_pending.html`
- `templates/courses/dashboard.html`
- `templates/painel/course_edit.html`
- `templates/painel/expirations.html`
- `templates/painel/plan.html`
- `templates/painel/settings.html`
- `templates/painel/students.html`
- `templates/partials/gomut/course_card.html`
- `templates/partials/gomut/course_hero.html`
- `templates/partials/gomut/my_plans.html`
- `templates/partials/sidebar_admin.html`
- `templates/users/settings.html`
- `users/migrations/0007_v1_student_plans.py`
- `users/models.py`
- `users/views.py`

- `courses/migrations/0012_early_end_empty_interval.py`

Este relatório também foi criado. A lista corresponde ao trabalho após o checkpoint da Etapa 0.

## 3. Migrações

- courses/0010_v1_student_plans: Course.plan_months; Enrollment.plan_started_on e admin_note; AccessChange com ação, datas anteriores/novas, motivo, responsável e data do evento.
- courses/0011_backfill_plan_anchor: preenche a âncora de matrículas que já têm período; preserva datas e casos sem dados.
- courses/0012_early_end_empty_interval: marcador ended_early e constraint que permite intervalo vazio somente se ended_early=True e grace_days=0. Criação normal continua recusando fim igual ao início.
- users/0007_v1_student_plans: SiteSettings.support_email.

Aplicadas somente na base demo .venv/gomut-demo.sqlite3. Testes criam schema vazio; migração histórica existente continua coberta pela suíte. Nenhum seed.py, dado real ou serviço externo utilizado.

## 4. Testes

Última suíte completa: 151 testes; zero falhas; zero erros. 13 testes novos em courses/test_plan_lifecycle.py. Primeiro ciclo RED: oito falhas por ausência dos serviços; implementação passou esses oito. Foram acrescentadas verificações de permissão, motivo obrigatório e limite exato de tolerância.

Dois testes antigos foram alinhados ao plano: selo Encerrado e permanência do curso encerrado no hero. Não foram removidas verificações de isolamento/progresso.

Chrome: Início, Minha conta, Alunos, Vencimentos e Plano abriram com HTTP 200 em 390/1440 px, sem overflow nem erro JavaScript. Capturas locais em .venv/v1-qa/ (não versionadas). A inspeção encontrou sobreposição inicial da faixa com o header; a faixa foi movida para baixo do hero e a captura foi conferida novamente.

## 5. Causas e efeitos

- C2: planos independentes por curso — teste.
- C11: três dias exatos de tolerância natural — teste.
- C12: encerramento hoje bloqueia hoje quando o início é anterior; caso início também hoje aprovado e coberto por teste de intervalo vazio, sem tolerância e com dois eventos no histórico.
- C13: reativação limitada ao fim corrigido e preservação do progresso — teste.
- C15: acesso às aulas bloqueado sem apagar progresso — testes existentes e novos. Certificado depende das etapas 1.7/1.9.
- C10: rechecagem de acesso no pulso depende da 1.3; não declarada pronta.

## 6. Como conferir na tela

1. Servidor local: http://127.0.0.1:8016/.
2. Aluno aluno@gomut.example: entrar em /dashboard/ e ver hero, selos e faixas dos planos. Fechar a faixa só dispensa o marco atual.
3. Em /settings/, consultar Meu plano por curso.
4. Admin admin@gomut.example: /painel/alunos/, selecionar o aluno e abrir Gerenciar plano e histórico.
5. Conferir formulários Criar/Encerrar/Reativar/Corrigir, observação interna e histórico. Os formulários explicam último dia inclusivo e primeiro dia sem acesso.
6. /painel/vencimentos/ lista próximos 60 dias com progresso. Em Alunos, há filtro Vence em 30 dias.
7. /painel/configuracoes/: campo E-mail de suporte.
8. Usar as credenciais locais já entregues; nenhuma senha foi registrada aqui. A inspeção automatizada foi somente de leitura nas telas, com sessões dos usuários demo.

## 7. Pendências e desvios

**Conflito resolvido:** usuário aprovou intervalo vazio exclusivamente para encerramento antecipado. A criação normal continua exigindo fim posterior. Encerrar no dia de início bloqueia nesse mesmo dia, sem apagar o período nem o histórico.

**Pergunta antecipada da 1.3:** sem duration_seconds, falta a referência para calcular 50% de tempo creditado no evento ended. Recomendação enviada: duração conhecida no servidor para conclusão automática; manual continua disponível. Nenhuma implementação de player começou.

Importação real 1.16 aguarda planilha. Dados de produção, perguntas reais e identidade do mentor continuam pendentes, conforme plano.

O link Abrir chamado já está preparado; o fluxo de chamados será implementado na 1.12. O painel mantém o layout atual nesta fase.

## 8. Commit

Commit único com mensagem `feat: planos auditados e vencimentos da etapa 1.1`. O hash é informado na entrega e no diário de execução. Sem push/merge.
