/* Quiz: perguntas públicas; gabarito só chega após responder. */
(() => {
  'use strict';
  const root = document.querySelector('[data-quiz-root]');
  if (!root) return;
  const modal = root.querySelector('[data-quiz-dialog]');
  const body = root.querySelector('[data-quiz-modal-body]');
  const errorBox = root.querySelector('[data-quiz-error]');
  const start = root.querySelector('[data-quiz-start]');
  let attempt = null, current = 0;
  if (window.location.hash === '#quiz') { const tab = document.getElementById('tab-quiz'); if (tab) tab.click(); }
  function node(tag, text, className) { const element = document.createElement(tag); if (text !== undefined) element.textContent = text; if (className) element.className = className; return element; }
  function csrf() { const field = document.querySelector('[name=csrfmiddlewaretoken]'); return field ? field.value : ''; }
  async function api(url, payload, method = 'POST') {
    const response = await fetch(url, {method, credentials: 'same-origin', headers: {'X-CSRFToken': csrf(), 'Content-Type': 'application/json', 'Accept': 'application/json'}, body: method === 'GET' ? undefined : JSON.stringify(payload || {})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Não foi possível salvar o quiz.');
    return data;
  }
  function error(message) { errorBox.textContent = message; errorBox.hidden = false; }
  function showModal() { if (typeof modal.showModal === 'function') { if (!modal.open) modal.showModal(); } else { modal.hidden = false; } errorBox.hidden = true; }
  function closeModal() { if (typeof modal.close === 'function') modal.close(); else modal.hidden = true; }
  function ready() { const guide = document.getElementById('lesson-guide'); return guide ? guide.dataset.completed === 'true' : root.dataset.ready === 'true'; }
  const closeButton = root.querySelector('[data-quiz-close]'); if (closeButton) closeButton.addEventListener('click', closeModal);
  document.addEventListener('lesson-progress-changed', event => {
    start.disabled = !event.detail.is_completed;
    root.querySelector('[data-quiz-blocked]').hidden = !!event.detail.is_completed;
  });
  async function begin() {
    start.disabled = true; errorBox.hidden = true;
    try { attempt = await api(root.dataset.startUrl); current = 0; if (attempt.kind === 'final') renderFinalQuestions(); else renderQuestion(); showModal(); }
    catch (problem) { error(problem.message); }
    finally { start.disabled = !ready(); }
  }
  start.addEventListener('click', begin);
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
      try { const result = await api(root.dataset.attemptPrefix + attempt.id + '/submit-final/', {answers}); renderResult(result); }
      catch (problem) { error(problem.message); submit.disabled = false; }
    });
    body.append(count, submit);
  }
  function renderQuestion() {
    const question = attempt.questions[current];
    body.replaceChildren();
    body.append(node('p', `Pergunta ${current + 1} de ${attempt.questions.length}`, 'muted'));
    const progress = node('progress'); progress.max = attempt.questions.length; progress.value = current; body.append(progress);
    body.append(node('h3', question.text));
    const options = node('div', undefined, 'quiz-options');
    question.choices.forEach(choice => {
      const label = node('label', undefined, 'quiz-option'); label.dataset.choiceId = choice.id;
      const input = node('input'); input.type = 'radio'; input.name = 'quiz-choice'; input.value = choice.id;
      label.append(input, node('span', choice.text)); options.append(label);
    });
    const feedback = node('div'); feedback.setAttribute('role', 'status');
    const submit = node('button', 'Responder', 'btn btn--red'); submit.type = 'button'; submit.disabled = true;
    options.addEventListener('change', () => { submit.disabled = false; });
    submit.addEventListener('click', async () => {
      const selected = options.querySelector('input:checked'); if (!selected) return;
      submit.disabled = true;
      try {
        const result = await api(root.dataset.attemptPrefix + attempt.id + '/answer/', {question_id: question.id, choice_id: Number(selected.value)});
        options.querySelectorAll('input').forEach(input => { input.disabled = true; const label = input.closest('label'); label.classList.toggle('is-right', Number(input.value) === result.correct_choice_id); label.classList.toggle('is-wrong', input.checked && !result.correct); });
        feedback.append(node('strong', result.correct ? 'Resposta correta' : 'Vamos revisar'), node('p', result.explanation));
        submit.hidden = true;
        const next = node('button', current + 1 < attempt.questions.length ? 'Próxima pergunta' : 'Ver resultado', 'btn btn--light'); next.type = 'button';
        next.addEventListener('click', async () => {
          next.disabled = true;
          if (current + 1 < attempt.questions.length) { current += 1; renderQuestion(); return; }
          try { const result = await api(root.dataset.attemptPrefix + attempt.id + '/finish/'); renderResult(result); }
          catch (problem) { feedback.append(node('p', problem.message)); next.disabled = false; }
        });
        feedback.append(next);
      } catch (problem) { feedback.append(node('p', problem.message)); submit.disabled = false; }
    });
    body.append(options, submit, feedback);
  }
  function renderResult(result) {
    body.replaceChildren(node('h3', root.dataset.kind === 'final' ? 'Avaliação concluída' : 'Quiz concluído'), node('p', `${result.correct}/${result.total} respostas corretas · ${result.score_pct}%`), node('p', `Melhor nota: ${result.best_score}%`));
    const summary = root.querySelector('[data-quiz-summary]'); summary.replaceChildren(node('p', `Última tentativa: ${result.score_pct}% · Melhor nota: ${result.best_score}%`));
    start.textContent = root.dataset.kind === 'final' ? 'Refazer avaliação' : 'Refazer';
    if (root.dataset.kind === 'final') body.append(node('strong', result.best_score >= 70 ? 'Aprovado · certificado disponível com os demais requisitos' : 'Mínimo de 70% para aprovação'));
    const guide = document.getElementById('lesson-guide');
    if (guide) {
      guide.dataset.quizPending = 'false';
      const quizStep = document.querySelector('[data-quiz-step]'); if (quizStep) { quizStep.classList.remove('is-current'); quizStep.classList.add('is-done'); }
      const nextStep = document.querySelector('[data-next-step]'); if (nextStep) nextStep.classList.add('is-current');
    }
    result.questions.forEach(question => {
      const section = node('section', undefined, 'quiz-review'); section.append(node('h4', question.text));
      question.choices.forEach(choice => { const line = node('p', choice.text); if (choice.id === question.correct_choice_id) line.className = 'is-right'; else if (choice.id === question.chosen_choice_id) line.className = 'is-wrong'; section.append(line); });
      section.append(node('p', question.explanation, 'muted')); body.append(section);
    });
    const close = node('button', root.dataset.kind === 'final' ? 'Fechar resultado' : 'Voltar à aula', 'btn btn--outline'); close.type = 'button'; close.addEventListener('click', closeModal); body.append(close);
    if (root.dataset.kind === 'final' && result.best_score >= 70) { const certificate = node('a', 'Ver requisitos do certificado', 'btn btn--red'); certificate.href = '/certificados/'; body.append(certificate); }
    if (guide && guide.dataset.nextUrl) { const next = node('a', 'Próxima aula', 'btn btn--red'); next.href = guide.dataset.nextUrl; body.append(next); }
  }
  const review = root.querySelector('[data-quiz-review]');
  if (review) review.addEventListener('click', async () => { try { const result = await api(review.dataset.quizReview, null, 'GET'); renderResult(result); showModal(); } catch (problem) { error(problem.message); } });
})();
