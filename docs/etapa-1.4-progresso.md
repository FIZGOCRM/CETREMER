# Etapa 1.4 — Meu progresso e resumo no Início

## 1. O que foi feito
- Resumo reutilizado no Início e em Meu progresso: aulas concluídas, restantes, estudo semanal, comparação com semana anterior, sequência e certificados.
- Gráfico dos 7 dias e mapa de constância dos últimos 84 dias, com dados reais de StudyDay.
- Sequência conta dias consecutivos a partir de hoje com pelo menos 60 segundos, conforme critério técnico e direção do protótipo.
- Atividade recente (seis eventos), anéis e progresso por curso, mês e fim do plano.
- Próximos passos limitados a quatro, priorizando continuar antes de começar outro curso.
- Consultas em lote por aluno, sem crescimento de consultas a cada curso; nenhuma estimativa de tempo por duração/completed_at.

## 2. Arquivos
- `courses/selectors.py`
- `courses/services.py`
- `courses/student_views.py`
- `courses/test_progress_dashboard.py`
- `courses/ui_capabilities.py`
- `docs/etapa-1.4-progresso.md`
- `static/css/gomut/members.css`
- `templates/courses/dashboard.html`
- `templates/courses/member_progress.html`
- `templates/partials/gomut/course_hero.html`
- `templates/partials/gomut/course_progress.html`
- `templates/partials/gomut/study_summary.html`

## 3. Migrações
Nenhuma. Nenhum campo/modelo novo. Apenas consultas, views e interface sobre os modelos já entregues.

## 4. Testes
182 testes, zero falhas/erros; seis novos em courses/test_progress_dashboard.py. Primeiro ciclo: cinco falhas pela ausência do resumo. Testes verificam tempo real em vez de duração presumida, comparação semanal, sequência, 84 dias, isolamento, acesso após encerramento, próximos passos e constância da quantidade de consultas ao ampliar de um para seis cursos.

## 5. Causas e efeitos
C15: plano encerrado mantém Meu progresso, com selo Encerrado — teste. O resumo usa a fonte de crédito de C9/C20, sem inventar histórico para conclusões antigas. Os casos de quiz, avaliação e encontro serão ligados às suas fatias, sem números simulados.

## 6. Como conferir na tela
1. aluno@gomut.example → /dashboard/: seção Seu progresso, gráfico, constância e próximos passos.
2. Abrir Ver progresso completo, em /dashboard/recursos/progresso/.
3. Ver Por curso, mês/fim do plano e Atividade recente. A demo tem uma conclusão histórica, mas nenhum tempo inventado: inicialmente pode mostrar 1/8 aulas e 0 min.
4. Assistir uma aula para gerar StudyDay/eventos reais e atualizar os indicadores ao recarregar.
5. Chrome 390/1440: Início e Meu progresso, além das rotas anteriores, HTTP200, sem overflow ou pageerror. Capturas inspecionadas em .venv/v1-qa/. Usar as credenciais locais já entregues.

## 7. Pendências/desvios
Chips e prioridades de quiz/avaliação serão integrados quando seus modelos existirem (1.6/1.7), e próximo encontro na 1.13, conforme dependências expressas no plano. Não foi antecipado modelo nem usado valor fictício. Indicador de certificado usa as regras disponíveis agora e será atualizado junto à elegibilidade na 1.7/1.9. Sem mudanças no painel, dados reais, produção ou dependências.

## 8. Commit
Commit único `feat: progresso real e resumo da etapa 1.4`; hash informado na entrega e diário. Sem push/merge.
