# Etapa 1.2 — publicação e liberação mensal

## 1. O que foi feito
- Situação publicado/rascunho em módulos e aulas; mês de liberação por módulo.
- Liberação calculada por meses de calendário a partir do início original, com ajuste de dia inexistente.
- Checagem central na abertura e conclusão da aula; rascunhos ficam ocultos.
- Contagens consideram só aulas e módulos publicados, inclusive aulas de módulos futuros no total.
- Continuar/Próxima não apontam para aula bloqueada; próxima liberação é indicada.
- Painel atual permite configurar publicação e mês; adiamento com impacto exige confirmação prévia.
- Exclusão de módulo/aula com progresso é recusada e oferece despublicar.

## 2. Arquivos
- `courses/access.py`
- `courses/migrations/0013_published_monthly_release.py`
- `courses/models.py`
- `courses/selectors.py`
- `courses/services.py`
- `courses/student_views.py`
- `courses/test_content_release.py`
- `courses/views.py`
- `docs/etapa-1.2-liberacao.md`
- `painel/forms.py`
- `painel/views/course_management.py`
- `static/css/gomut/members.css`
- `templates/courses/course_detail.html`
- `templates/courses/lesson_detail.html`
- `templates/courses/lesson_locked.html`
- `templates/painel/course_lessons.html`
- `templates/painel/module_confirmation.html`
- `templates/partials/gomut/course_hero.html`
- `templates/partials/gomut/module_list.html`

## 3. Migrações
courses/0013_published_monthly_release: Module.status, Module.release_month (mínimo 1 e constraint SQL), Lesson.status. Padrões published e mês 1 preservam a demonstração. Aplicada na base demo e do zero pela suíte.

## 4. Testes
162 testes; zero falhas/erros. 11 novos em courses/test_content_release.py. Primeiro ciclo: sete falhas esperadas antes da implementação; depois todos passaram. Incluem fronteiras HTTP, publicação, datas de calendário, confirmação de impacto e preservação do histórico. makemigrations --check --dry-run sem mudanças.

## 5. Causas e efeitos
C1/C2: liberação por âncora própria de cada curso; C3: 31/01 → 29/02 em ano bissexto e 31/03; C4: publicar rascunho em módulo liberado aparece imediatamente (notificação fica na 1.14); C5: adiamento só persiste após confirmação, mantém conclusão e bloqueia aula pendente; C6: exclusão de aula e módulo com progresso recusada. Todos cobertos por testes.

## 6. Como conferir na tela
1. aluno@gomut.example: /dashboard/ → curso → módulos/aula. Demo permanece toda no mês 1; credenciais locais já entregues.
2. admin@gomut.example: /painel/cursos/1/aulas/ → Renomear (configura também mês/situação), Novo módulo ou Editar aula.
3. Ao adiar um módulo liberado para mês futuro, aparece a quantidade de alunos afetados e a confirmação antes de salvar.
4. Tentar excluir conteúdo com progresso mostra a orientação para despublicar.
5. Chrome 390/1440: Início, conta, página do curso, alunos, planos, vencimentos e editor de conteúdo HTTP200, sem overflow nem erro JS. Capturas locais em .venv/v1-qa/. Layout do painel continua o atual.

## 7. Pendências/desvios
Mês real de cada módulo ainda depende do cliente; demo permanece em 1 conforme plano. Notificações são da 1.14. Matrículas históricas sem âncora não ganham data inventada: módulo posterior ao mês 1 fica pendente de definição de início. Sem dependências novas, produção ou pagamento.

## 8. Commit
Commit único `feat: publicacao e liberacao mensal da etapa 1.2`; hash informado na entrega. Sem push/merge.
