# Etapa 1.6 — quiz da aula

## 1. O que foi feito
- Quiz opcional por aula, com bloqueio até a conclusão e plano ativo.
- Start/answer/finish com CSRF, posse da tentativa, correção exclusivamente no servidor e recusa de resposta duplicada.
- Gabarito/comentário não vão no HTML nem no payload inicial; só saem após resposta.
- Janela de perguntas, correção, comentário e revisão; tentativas ilimitadas, última nota e melhor nota.
- Tentativas congelam perguntas/alternativas/gabarito, para edição valer só nas próximas e preservar notas antigas.
- Editor do painel: criar, editar, ordenar, ativar/desativar e exclusão recusada quando há tentativas.
- Selos, etapas e próximos passos ligados ao resultado real; quiz continua sem contar para certificado.
- prepare_demo cria duas perguntas ilustrativas do QB em uma aula de cada curso; outras ficam sem quiz.

## 2. Arquivos
- `core/urls.py`
- `courses/demo_quizzes.py`
- `courses/forms.py`
- `courses/management/commands/prepare_demo.py`
- `courses/migrations/0016_lesson_quizzes.py`
- `courses/models.py`
- `courses/quiz_views.py`
- `courses/selectors.py`
- `courses/services.py`
- `courses/student_views.py`
- `courses/test_lesson_quiz.py`
- `docs/etapa-1.6-quizzes.md`
- `painel/forms.py`
- `painel/urls.py`
- `painel/views/quizzes.py`
- `static/css/gomut/members.css`
- `static/js/gomut/lesson-guide.js`
- `static/js/gomut/quiz.js`
- `templates/courses/lesson_detail.html`
- `templates/painel/course_lessons.html`
- `templates/painel/lesson_quiz.html`
- `templates/partials/gomut/course_progress.html`
- `templates/partials/gomut/lesson_steps.html`
- `templates/partials/gomut/module_list.html`
- `templates/partials/gomut/quiz_tab.html`

## 3. Migrações
courses/0016_lesson_quizzes: Quiz(kind, lesson único opcional, course, is_active, is_demo); QuizQuestion(quiz, order, text, explanation, is_active); QuizChoice(question, order, text, is_correct, is_active); QuizAttempt(student, quiz, started_at, finished_at, correct, total, score_pct, answers, question_snapshot). Constraints de vínculo kind/lesson, avaliação única por curso, ordens ativas e no máximo uma correta ativa por pergunta; o serviço exige exatamente uma e 2–4 alternativas. is_active nas alternativas preserva versões; snapshot é privado do servidor. Kind final existe como contrato de dados, sem liberar avaliação antes da 1.7.
Aplicada na demo e schema vazio dos testes.

## 4. Testes
200 testes, zero falhas/erros; 12 novos em courses/test_lesson_quiz.py. Primeiro RED: oito falhas pela ausência do modelo. Testes de liberação, gabarito, edição congelada, alternativas inválidas, resposta repetida, conclusão idempotente, dono da tentativa, CSRF, plano encerrado, maior nota, editor e independência do certificado. Scripts com sintaxe válida e migrations sem mudanças pendentes.

## 5. Causas e efeitos
C16: edição não altera a tentativa/nota anterior — teste de snapshot; C17: exclusão de quiz/pergunta com tentativas recusada e desativação disponível — teste/editor; C18: aulas sem quiz continuam sem aba/indicação — suíte e demo. Prioridade do quiz liberado e chips Quizzes da 1.4 foram ligados agora ao dado real. Histórico de aula/módulo também considera tentativas.

## 6. Como conferir na tela
1. aluno@gomut.example → Emergências cardiovasculares → primeira aula, já concluída na demo.
2. Conferir aviso de quiz, etapas, aba, selos e Começar quiz/Refazer. A demonstração tem duas perguntas ilustrativas.
3. Responder: correção e comentário após cada resposta; Ver resultado mostra revisão e melhor nota.
4. No navegador foi concluída uma tentativa real demo com 2/2 (100%); os dados são salvos no banco. A aula inicial de Plantão, ainda não concluída, manteve o botão bloqueado.
5. admin@gomut.example → editar aula → Gerenciar quiz da aula (/painel/aulas/<id>/quiz/). Adicionar/editar e desativar; histórico não é apagado. Editor foi exercitado e corrigida uma alternativa que faltou na cópia inicial de demonstração, conforme QB.
6. Chrome 390/1440: janela/resultado sem overflow ou pageerror; editor e rotas anteriores HTTP200. Capturas locais quiz-result-390.png, quiz-result-1440.png e quiz-editor-1440.png inspecionadas. Credenciais locais anteriores.

## 7. Pendências/desvios
Perguntas reais e quais aulas terão quiz continuam pendentes do cliente. Demo é explicitamente identificada e idempotente, preserva senhas/dados existentes. Avaliação final só será implementada na 1.7. Sem dependências novas, gateway, produção, push ou merge.

## 8. Commit
Commit único `feat: quizzes da aula e editor da etapa 1.6`; hash informado na entrega/diário.
