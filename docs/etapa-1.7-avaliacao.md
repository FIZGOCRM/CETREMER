# Etapa 1.7 — avaliação final e elegibilidade

## 1. O que foi feito
- Avaliação final opcional por curso, liberada só com todas as aulas publicadas concluídas e acesso ativo.
- Envio completo transacional, sem gabarito ou correção durante o preenchimento; respostas parciais pela API também não revelam correção.
- Nota calculada no servidor, tentativas ilimitadas e melhor nota; aprovação a partir de 70%.
- Requisitos do certificado incluem a avaliação somente quando há perguntas finais ativas.
- Registro do cumprimento dos requisitos durante o acesso, para permitir emissão depois do fim sem inventar elegibilidade retroativa.
- Estados new/progress/waiting_release/exam/done/ended no hero, curso e próximos passos.
- Editor da avaliação no painel atual, reutilizando as mesmas regras/editor das perguntas.
- prepare_demo acrescenta as quatro perguntas finais ilustrativas de cada curso do objeto C do protótipo.

## 2. Arquivos
- `core/urls.py`
- `courses/certificate_views.py`
- `courses/demo_quizzes.py`
- `courses/management/commands/prepare_demo.py`
- `courses/migrations/0017_certificate_qualification.py`
- `courses/models.py`
- `courses/quiz_views.py`
- `courses/selectors.py`
- `courses/services.py`
- `courses/student_views.py`
- `courses/test_final_assessment.py`
- `docs/etapa-1.7-avaliacao.md`
- `painel/urls.py`
- `painel/views/quizzes.py`
- `static/js/gomut/quiz.js`
- `templates/courses/certificates.html`
- `templates/courses/course_detail.html`
- `templates/courses/final_assessment.html`
- `templates/painel/course_lessons.html`
- `templates/painel/lesson_quiz.html`
- `templates/partials/gomut/course_hero.html`
- `templates/partials/gomut/course_progress.html`
- `users/views.py`

## 3. Migrações
courses/0017_certificate_qualification: Enrollment.certificate_qualified_at (nullable). Registra a evidência temporal necessária a C14; não é preenchido retroativamente com data presumida. Progress.completed_at e QuizAttempt.finished_at complementam a conferência histórica. Nenhuma alteração em certificado já emitido. Migração aplicada na demo e criada do zero pela suíte.

## 4. Testes
210 testes, zero falhas/erros; dez novos em courses/test_final_assessment.py. RED inicial: avaliação recusada/rotas inexistentes; GREEN após implementação. Cobrem bloqueio acadêmico, ausência de gabarito parcial, reprovação, maior nota, corte exato de 70%, envio inválido atômico, curso sem avaliação, emissão após fim por serviço e HTTP e estados do curso. Sintaxe JS válida; migrations sem pendências.

## 5. Causas e efeitos
C14: conclui/é aprovado com dados válidos durante o acesso, encerra e emite depois — testes serviço/HTTP. C19: sem avaliação ativa, não mostra CTA nem exige nota — teste. C15: incompleto após fim não recebe elegibilidade retroativa — teste. Certificados existentes continuam retornando o snapshot antes de qualquer revalidação, como na suíte anterior.

## 6. Como conferir na tela
1. aluno@gomut.example → curso → concluir as aulas publicadas → Fazer avaliação final.
2. /dashboard/cursos/gomut-demo-cardiologia/avaliacao/: quatro perguntas ilustrativas, botão só habilita com todas respondidas. A correção só aparece após Enviar respostas.
3. A inspeção concluiu as quatro aulas de cardiologia pelos botões reais e enviou 3/4 respostas corretas: 75% calculados no servidor, com aprovação e revisão. Isso não inventa minutos de estudo. A outra disciplina mantém seu próprio progresso.
4. O certificado continua exigindo nome/CPF; a interface completa de emissão é a 1.9. Em Minha conta, salvar dados pessoais atualiza a evidência de elegibilidade quando todos os requisitos estão satisfeitos e o acesso permite.
5. admin@gomut.example → Aulas do curso → Avaliação final (/painel/cursos/<id>/avaliacao/) para o mesmo editor de perguntas.
6. Chrome 390/1440: avaliação/resultado sem overflow ou pageerror; capturas final-result-390.png e final-result-1440.png inspecionadas. Credenciais locais anteriores.

## 7. Pendências/desvios
Perguntas reais continuam pendentes. A evidência de C14 segue literalmente todos os requisitos do plano, incluindo dados pessoais válidos durante o acesso; um registro legado sem evidência não ganha data inventada. Aprovação não depende de quiz da aula. Percentual é guardado com duas casas, arredondando para baixo para não aprovar um resultado real abaixo de 70 por arredondamento. Sem produção ou dependências novas.

## 8. Commit
Commit único `feat: avaliacao final e elegibilidade da etapa 1.7`; hash informado na entrega/diário. Sem push/merge.
