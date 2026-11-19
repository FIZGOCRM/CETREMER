/* Etapas e anotações da aula: somente estado recebido do servidor. */
(() => {
  'use strict';
  const guide = document.getElementById('lesson-guide');
  if (!guide) return;
  const reactionError = guide.querySelector('[data-reaction-error]');
  guide.querySelectorAll('[data-lesson-reaction]').forEach(button => {
    if (document.body.dataset.memberPreview === 'true') { button.disabled = true; return; }
    button.addEventListener('click', async () => {
      button.disabled = true;
      reactionError.hidden = true;
      try {
        const response = await fetch(button.dataset.lessonReaction, {
          method: 'POST', credentials: 'same-origin',
          headers: {'Content-Type': 'application/json', 'Accept': 'application/json',
                    'X-CSRFToken': guide.querySelector('[name=csrfmiddlewaretoken]').value},
          body: JSON.stringify({active: button.getAttribute('aria-pressed') !== 'true'}),
        });
        if (!response.ok) throw new Error();
        const {active} = await response.json();
        if (typeof active !== 'boolean') throw new Error();
        button.setAttribute('aria-pressed', String(active));
        button.classList.toggle('is-on', active);
      } catch { reactionError.hidden = false; }
      finally { button.disabled = false; }
    });
  });
  const hasQuiz = guide.dataset.hasQuiz === 'true';
  let completed = guide.dataset.completed === 'true';
  let countdown = null;
  const time = seconds => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
  document.querySelectorAll('[data-format-time]').forEach(node => { node.textContent = time(Number(node.dataset.formatTime)); });
  document.addEventListener('lesson-position', event => {
    const seconds = Math.max(0, Math.floor(Number(event.detail.seconds) || 0));
    document.querySelectorAll('[data-note-position]').forEach(node => { node.value = seconds; });
    document.querySelectorAll('[data-note-at]').forEach(node => { node.textContent = time(seconds); });
  });
  document.addEventListener('lesson-progress-changed', event => {
    completed = !!event.detail.is_completed;
    guide.dataset.completed = String(completed);
    if (!completed) cancelNext();
    const banner = document.querySelector('[data-lesson-completed]');
    if (banner) banner.hidden = !completed;
    const watch = document.querySelector('[data-watch-step]');
    if (watch) { watch.classList.toggle('is-done', completed); watch.classList.toggle('is-current', !completed); }
    document.querySelectorAll('[data-open-quiz]').forEach(node => { node.disabled = !completed; });
    const quizStep = document.querySelector('[data-quiz-step]'); if (quizStep) quizStep.classList.toggle('is-current', completed && guide.dataset.quizPending === 'true');
    const nextStep = document.querySelector('[data-next-step]'); if (nextStep) nextStep.classList.toggle('is-current', completed && (!hasQuiz || guide.dataset.quizPending === 'false'));
    document.querySelectorAll('[data-quiz-lock]').forEach(node => { node.textContent = completed ? 'Liberado' : 'Conclua a aula para liberar'; });
  });
  document.addEventListener('lesson-tracked', event => {
    document.querySelectorAll('[data-watch-pct]').forEach(node => { node.textContent = event.detail.watched_pct == null ? '—' : event.detail.watched_pct; });
  });
  document.querySelectorAll('[data-open-quiz]').forEach(button => button.addEventListener('click', () => {
    if (!completed) return;
    const tab = document.getElementById('tab-quiz');
    if (tab) { tab.click(); tab.focus(); tab.scrollIntoView({behavior: 'smooth', block: 'center'}); }
  }));
  const notice = document.querySelector('[data-quiz-notice]');
  const dismiss = document.querySelector('[data-dismiss-quiz-notice]');
  if (dismiss) dismiss.addEventListener('click', () => { notice.hidden = true; });
  function cancelNext() {
    clearInterval(countdown); countdown = null;
    const node = document.querySelector('[data-next-countdown]'); if (node) node.hidden = true;
  }
  const cancel = document.querySelector('[data-cancel-next]');
  if (cancel) cancel.addEventListener('click', cancelNext);
  document.addEventListener('lesson-video-ended', () => {
    cancelNext();
    if (!completed || (hasQuiz && guide.dataset.quizPending === 'true') || !guide.dataset.nextUrl) return;
    let seconds = 5;
    const line = document.querySelector('[data-next-countdown]');
    const number = document.querySelector('[data-next-seconds]');
    if (!line || !number) return;
    line.hidden = false; number.textContent = seconds;
    countdown = setInterval(() => { seconds -= 1; number.textContent = seconds; if (seconds <= 0) { cancelNext(); window.location.assign(guide.dataset.nextUrl); } }, 1000);
  });
  const noteForm = document.querySelector('[data-note-form]');
  const noteList = document.querySelector('[data-note-list]');
  const noteError = document.querySelector('[data-note-error]');
  async function submit(form) {
    const response = await fetch(form.action, {method: 'POST', credentials: 'same-origin', headers: {'Accept': 'application/json'}, body: new FormData(form)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Não foi possível salvar a anotação.');
    return data;
  }
  if (noteForm) noteForm.addEventListener('submit', async event => {
    event.preventDefault();
    const button = noteForm.querySelector('button[type="submit"]'); button.disabled = true; noteError.hidden = true;
    try {
      const data = await submit(noteForm);
      const row = document.getElementById('note-template').content.cloneNode(true);
      const article = row.querySelector('article'); article.dataset.noteId = data.id;
      const seek = row.querySelector('[data-seek]'); seek.dataset.seek = data.position_seconds; seek.textContent = time(data.position_seconds);
      row.querySelector('p').textContent = data.text;
      row.querySelector('form').action = noteForm.action + data.id + '/delete/';
      const empty = noteList.querySelector('[data-empty-notes]'); if (empty) empty.remove();
      noteList.append(row); noteForm.querySelector('textarea').value = '';
    } catch (error) { noteError.textContent = 'Não foi possível salvar a anotação. Confira os dados e tente novamente.'; noteError.hidden = false; }
    finally { button.disabled = false; }
  });
  if (noteList) {
    noteList.addEventListener('click', event => { const button = event.target.closest('[data-seek]'); if (button) document.dispatchEvent(new CustomEvent('lesson-seek', {detail: {seconds: Number(button.dataset.seek)}})); });
    noteList.addEventListener('submit', async event => {
      if (!event.target.matches('[data-delete-note]')) return;
      event.preventDefault(); noteError.hidden = true;
      const button = event.target.querySelector('button'); button.disabled = true;
      try { await submit(event.target); event.target.closest('[data-note-id]').remove(); }
      catch (error) { noteError.textContent = 'Não foi possível apagar a anotação. Tente novamente.'; noteError.hidden = false; button.disabled = false; }
    });
  }
})();
