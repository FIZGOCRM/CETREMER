/* Quiz: perguntas públicas; gabarito só chega após responder. */
(() => {
  'use strict';
  const root = document.querySelector('[data-quiz-root]');
  if (!root) return;
  const workspace = root.querySelector('[data-quiz-workspace]');
  const body = root.querySelector('[data-quiz-body]');
  const errorBox = root.querySelector('[data-quiz-error]');
  const start = root.querySelector('[data-quiz-start]');
  let attempt = null;
  function node(tag, text, className) { const element = document.createElement(tag); if (text !== undefined) element.textContent = text; if (className) element.className = className; return element; }
  function csrf() { const field = document.querySelector('[name=csrfmiddlewaretoken]'); return field ? field.value : ''; }
  async function api(url, payload, method = 'POST') {
    const response = await fetch(url, {method, credentials: 'same-origin', headers: {'X-CSRFToken': csrf(), 'Content-Type': 'application/json', 'Accept': 'application/json'}, body: method === 'GET' ? undefined : JSON.stringify(payload || {})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Não foi possível salvar o quiz.');
    return data;
  }
  function error(message) { errorBox.textContent = message; errorBox.hidden = false; }
  function showWorkspace() {
    workspace.hidden = false;
    start.hidden = true;
    root.querySelector('[data-quiz-summary]').hidden = true;
    errorBox.hidden = true;
    const heading = body.querySelector('h2,h3');
    heading.tabIndex = -1;
    heading.focus();
  }
  function closeWorkspace() {
    workspace.hidden = true;
    start.hidden = false;
    root.querySelector('[data-quiz-summary]').hidden = false;
    start.focus();
  }
  function ready() { const guide = document.getElementById('lesson-guide'); return guide ? guide.dataset.completed === 'true' : root.dataset.ready === 'true'; }
  document.addEventListener('lesson-progress-changed', event => {
    start.disabled = !event.detail.is_completed;
    root.querySelector('[data-quiz-blocked]').hidden = !!event.detail.is_completed;
  });
  async function begin() {
    start.disabled = true; errorBox.hidden = true;
    try {
      attempt = await api(root.dataset.startUrl);
      if (attempt.kind === 'final') renderFinalQuestions();
      else renderLessonQuestions();
      showWorkspace();
    }
    catch (problem) { error(problem.message); }
    finally { start.disabled = !ready(); }
  }
  start.addEventListener('click', begin);
  const quizTab = document.getElementById('tab-quiz');
  if (quizTab) {
    quizTab.addEventListener('click', () => {
      if (!attempt && !start.disabled && !root.querySelector('[data-quiz-review]')) begin();
    });
    if (window.location.hash === '#quiz') quizTab.click();
  }
  document.addEventListener('lesson-tracked', event => { const bar = root.querySelector('[data-quiz-unlock-progress]'); if (bar) bar.value = event.detail.watched_pct || 0; });
  function renderFinalQuestions() {
    body.replaceChildren(node('h2', 'Responda todas as perguntas'));
    const answers = {};
    const count = node('p', `0 de ${attempt.questions.length} respondidas`, 'muted');
    const submit = node('button', 'Enviar respostas', 'btn btn--red'); submit.type = 'button'; submit.disabled = true;
    attempt.questions.forEach((question, index) => {
      const section = node('fieldset', undefined, 'quiz-review');
      section.append(node('legend', `${index + 1}. ${question.text}`));
      question.choices.forEach(choice => {
        const label = node('label', undefined, 'quiz-option');
        const input = node('input'); input.type = 'radio'; input.name = 'final-question-' + question.id; input.value = choice.id;
        input.addEventListener('change', () => { answers[String(question.id)] = choice.id; const answered = Object.keys(answers).length; count.textContent = `${answered} de ${attempt.questions.length} respondidas`; submit.disabled = answered !== attempt.questions.length; });
        label.append(input, node('span', choice.text)); section.append(label);
      });
      body.append(section);
    });
    submit.addEventListener('click', async () => {
      submit.disabled = true;
      try { const result = await api(root.dataset.attemptPrefix + attempt.id + '/submit-final/', {answers}); renderResult(result); showWorkspace(); }
      catch (problem) { error(problem.message); submit.disabled = false; }
    });
    body.append(count, submit);
  }
  function renderLessonQuestions() {
    body.replaceChildren();
    const finish = node('button', 'Ver resultado', 'btn btn--light');
    finish.type = 'button';
    finish.disabled = true;
    let answered = 0;
    attempt.questions.forEach((question, index) => {
      body.append(lessonQuestion(question, index, () => {
        answered += 1;
        finish.disabled = answered !== attempt.questions.length;
      }));
    });
    finish.addEventListener('click', async () => {
      finish.disabled = true;
      try { renderResult(await api(root.dataset.attemptPrefix + attempt.id + '/finish/')); showWorkspace(); }
      catch (problem) { error(problem.message); finish.disabled = false; }
    });
    body.append(finish);
  }
  function lessonQuestion(question, index, onAnswer) {
    const section = node('section', undefined, 'q');
    section.append(node('p', `Pergunta ${index + 1} de ${attempt.questions.length}`, 'eyebrow'), node('h3', question.text));
    const options = node('div', undefined, 'q__opts');
    question.choices.forEach((choice, index) => {
      const button = node('button', undefined, 'q__opt');
      button.type = 'button';
      button.dataset.choiceId = choice.id;
      button.append(node('i', String.fromCharCode(65 + index)), node('span', choice.text));
      options.append(button);
    });
    const feedback = node('div'); feedback.setAttribute('role', 'status');
    options.addEventListener('click', async event => {
      const selected = event.target.closest('button');
      if (!selected || selected.disabled) return;
      const buttons = options.querySelectorAll('button');
      buttons.forEach(button => { button.disabled = true; });
      feedback.replaceChildren();
      try {
        const result = await api(root.dataset.attemptPrefix + attempt.id + '/answer/', {question_id: question.id, choice_id: Number(selected.dataset.choiceId)});
        buttons.forEach(button => {
          const correct = Number(button.dataset.choiceId) === result.correct_choice_id;
          button.classList.toggle('is-right', correct);
          button.classList.toggle('is-wrong', button === selected && !correct);
        });
        appendFeedback(feedback, question, result);
        onAnswer();
      } catch (problem) { feedback.append(node('p', problem.message)); buttons.forEach(button => { button.disabled = false; }); }
    });
    section.append(options, feedback);
    return section;
  }
  function appendFeedback(container, question, result) {
    const box = node('div', undefined, 'q__why');
    const add = (heading, id, explanation) => {
      const index = question.choices.findIndex(choice => choice.id === id);
      box.append(node('strong', heading + ' · ' + String.fromCharCode(65 + index)));
      if (explanation) box.append(node('p', explanation));
    };
    if (!result.correct) add('Sua resposta está incorreta', result.chosen_choice_id, result.chosen_explanation);
    add('Resposta correta', result.correct_choice_id, result.correct_explanation);
    container.append(box);
  }
  function renderResult(result) {
    body.replaceChildren(node('h3', root.dataset.kind === 'final' ? 'Avaliação concluída' : 'Quiz concluído'), node('p', `${result.correct}/${result.total} respostas corretas · ${result.score_pct}%`), node('p', `Melhor nota: ${result.best_score}%`));
    const summary = root.querySelector('[data-quiz-summary]');
    const review = node('button', 'Revisar tentativa', 'btn btn--outline');
    review.type = 'button';
    review.dataset.quizReview = root.dataset.attemptPrefix + result.id + '/';
    summary.replaceChildren(node('p', `Última tentativa: ${result.score_pct}% · Melhor nota: ${result.best_score}%`), review);
    start.textContent = root.dataset.kind === 'final' ? 'Refazer avaliação' : 'Refazer quiz';
    if (root.dataset.kind === 'final') body.append(node('strong', result.best_score >= 70 ? 'Aprovado · certificado disponível com os demais requisitos' : 'Mínimo de 70% para aprovação'));
    const guide = document.getElementById('lesson-guide');
    if (guide) {
      guide.dataset.quizPending = 'false';
      const quizStep = document.querySelector('[data-quiz-step]'); if (quizStep) { quizStep.classList.remove('is-current'); quizStep.classList.add('is-done'); }
      const nextStep = document.querySelector('[data-next-step]'); if (nextStep) nextStep.classList.add('is-current');
    }
    result.questions.forEach(question => {
      const section = node('section', undefined, 'quiz-review'); section.append(node('h4', question.text));
      question.choices.forEach((choice, i) => { const line = node('p', String.fromCharCode(65 + i) + '. ' + choice.text); if (choice.id === question.correct_choice_id) line.className = 'is-right'; else if (choice.id === question.chosen_choice_id) line.className = 'is-wrong'; section.append(line); });
      appendFeedback(section, question, question);
      body.append(section);
    });
    const close = node('button', 'Fechar resultado', 'btn btn--outline'); close.type = 'button'; close.addEventListener('click', closeWorkspace); body.append(close);
    if (root.dataset.kind === 'final' && result.best_score >= 70) { const certificate = node('a', 'Ver requisitos do certificado', 'btn btn--red'); certificate.href = '/certificados/'; body.append(certificate); }
    if (guide && guide.dataset.nextUrl) { const next = node('a', 'Próxima aula', 'btn btn--red'); next.href = guide.dataset.nextUrl; body.append(next); }
  }
  root.querySelector('[data-quiz-summary]').addEventListener('click', async event => {
    const review = event.target.closest('[data-quiz-review]');
    if (!review) return;
    review.disabled = true;
    try { renderResult(await api(review.dataset.quizReview, null, 'GET')); showWorkspace(); }
    catch (problem) { error(problem.message); review.disabled = false; }
  });
})();
