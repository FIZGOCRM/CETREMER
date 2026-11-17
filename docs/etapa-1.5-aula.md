# Etapa 1.5 — etapas da aula e anotações

## 1. O que foi feito
- Etapas Assistir → Próxima aula; a etapa Quiz só aparece quando houver quiz ativo na fatia 1.6.
- Percentual creditado ao vivo e indicação de conclusão com 90% assistido.
- Aviso Aula concluída e contagem de cinco segundos para próxima aula liberada ao terminar o vídeo, com Cancelar.
- Sem próxima aula liberada, mostra data do próximo módulo, sem contagem.
- Abas Sobre a aula, Material e Anotações; nenhuma indicação/aba de quiz em aulas sem quiz.
- Anotações privadas por aluno, salvas no minuto do vídeo, com listagem, exclusão e salto ao minuto via Vimeo SDK.
- Atalho Tirar dúvida com a turma preparado com curso e aula.

## 2. Arquivos
- `core/urls.py`
- `courses/access.py`
- `courses/forms.py`
- `courses/migrations/0015_private_lesson_notes.py`
- `courses/models.py`
- `courses/note_views.py`
- `courses/services.py`
- `courses/student_views.py`
- `courses/test_lesson_notes.py`
- `courses/test_member_redesign.py`
- `docs/etapa-1.5-aula.md`
- `static/css/gomut/members.css`
- `static/js/aluno.js`
- `static/js/gomut/lesson-guide.js`
- `templates/courses/lesson_detail.html`
- `templates/partials/gomut/lesson_notes.html`
- `templates/partials/gomut/lesson_steps.html`

## 3. Migrações
courses/0015_private_lesson_notes: LessonNote(student, lesson, position_seconds, text, created_at). Aplicada na demo; schema vazio criado pela suíte. Conteúdo com anotações também é preservado contra exclusão, com orientação de despublicar.

## 4. Testes
188 testes, zero falhas/erros; seis novos em courses/test_lesson_notes.py. Primeiro ciclo RED: quatro falhas por rotas/experiência ausentes. Cobrem privacidade entre dois alunos do mesmo curso, exclusão por dono, matrícula, plano encerrado, CSRF, texto vazio/tempo inválido e escape de HTML. Verificação de sintaxe dos dois scripts e migrations sem pendências.

## 5. Causas e efeitos
C18: aula sem quiz não renderiza aba nem indicação — teste. C20: desmarcar reflete nas etapas e cancela contagem. Fluxo sem quiz: contagem/cancelamento conferidos no navegador com evento de fim controlado. Fluxos com quiz serão ligados ao modelo/resultado real na 1.6, sem simulação no produto.

## 6. Como conferir na tela
1. aluno@gomut.example → /courses/gomut-demo-cardiologia/lessons/5/ (credenciais locais já entregues).
2. Conferir as etapas e as abas; não há Quiz até a próxima fatia cadastrar quizzes demo.
3. Abrir Anotações, escrever, salvar no minuto atual; clicar no minuto busca esse ponto no Vimeo. Apagar remove só a anotação própria.
4. Aula concluída mostra o próximo passo. Fim do vídeo sem quiz pendente inicia contagem de 5 s; Cancelar interrompe a navegação.
5. Tirar dúvida com a turma inclui curso/aula no link (formulário completo na 1.11).
6. Chrome 390/1440: aula e demais rotas HTTP200 sem overflow/pageerror. A inspeção criou e apagou uma anotação pela interface e cancelou a contagem; captura local .venv/v1-qa/lesson-notes-390.png conferida. Nenhum dado de aluno real utilizado.

## 7. Pendências/desvios
A indicação, bloqueio e fim de aula com quiz dependem do modelo da 1.6: contexto/template já preparado, sem criar um quiz fictício em memória. O formulário completo de tópico vem na 1.11. Recursos Minha lista/Curtir saíram desta tela por estarem fora da V1; nenhum backend simulado. Sem novas dependências ou produção.

## 8. Commit
Commit único `feat: etapas da aula e anotacoes privadas da etapa 1.5`; hash informado na entrega/diário. Sem push/merge.
