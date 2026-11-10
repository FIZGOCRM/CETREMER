/* CETREMER · página da aula
   Carregar só em courses/lesson_detail.html, depois do player.js do Vimeo.
   Contrato com o template (ver HANDOFF.md, tela "Página da aula"):
   - .module__toggle[aria-controls] abre/fecha a lista do módulo (lista com id igual ao aria-controls)
   - .btn-toggle-complete[data-lesson-id][data-url] alterna concluída (POST, resposta JSON)
   - iframe[data-vimeo][data-lesson-id][data-complete-url] marca concluída ao terminar o vídeo
   - #status-dot-<id>, [data-lesson-meta=<id>], [data-module-count=<id>], [data-course-progress],
     [data-progress-pct], [data-progress-count], [data-progress-error] são atualizados
   Resposta esperada do backend: {"is_completed": bool, "completed_count": int, "total_count": int, "percentage": number}
*/
(function () {
  'use strict';

  function csrfToken() {
    var field = document.querySelector('[name=csrfmiddlewaretoken]');
    if (field) return field.value;
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function postJSON(url) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': csrfToken(), 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
    }).then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    });
  }

  function plural(n, singular, pluralWord) { return n === 1 ? singular : pluralWord; }

  function updateModuleCounters() {
    document.querySelectorAll('[data-module-count]').forEach(function (el) {
      var list = document.getElementById('module-' + el.getAttribute('data-module-count'));
      if (!list) return;
      var total = list.querySelectorAll('.status-dot').length;
      var done = list.querySelectorAll('.status-dot.is-done').length;
      el.textContent = done + ' de ' + total + ' ' + plural(total, 'aula', 'aulas');
    });
  }

  function applyProgress(data, lessonId) {
    var done = !!data.is_completed;
    var pct = Math.round(Number(data.percentage) || 0);

    var dot = document.getElementById('status-dot-' + lessonId);
    if (dot) dot.classList.toggle('is-done', done);

    var meta = document.querySelector('[data-lesson-meta="' + lessonId + '"]');
    if (meta && !meta.closest('[aria-current="page"]')) {
      var duration = meta.getAttribute('data-duration') || '';
      meta.textContent = done ? ('Concluída' + (duration ? ' · ' + duration : '')) : duration;
    }

    document.querySelectorAll('.btn-toggle-complete[data-lesson-id="' + lessonId + '"]').forEach(function (btn) {
      btn.classList.toggle('btn--primary', !done);
      btn.classList.toggle('btn--done', done);
      btn.setAttribute('aria-pressed', String(done));
      var label = btn.querySelector('[data-label]');
      if (label) label.textContent = done ? 'Concluída' : 'Marcar como concluída';
    });

    document.querySelectorAll('[data-course-progress]').forEach(function (bar) {
      bar.style.width = pct + '%';
      if (bar.parentElement) bar.parentElement.setAttribute('aria-valuenow', String(pct));
    });
    document.querySelectorAll('[data-progress-pct]').forEach(function (el) { el.textContent = pct + '%'; });
    document.querySelectorAll('[data-progress-count]').forEach(function (el) {
      el.textContent = data.completed_count + ' de ' + data.total_count;
    });

    updateModuleCounters();
  }

  function showError(show) {
    document.querySelectorAll('[data-progress-error]').forEach(function (el) { el.hidden = !show; });
  }

  // Acordeão dos módulos
  document.querySelectorAll('.module__toggle[aria-controls]').forEach(function (button) {
    button.addEventListener('click', function () {
      var list = document.getElementById(button.getAttribute('aria-controls'));
      var isOpen = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', String(!isOpen));
      if (list) list.hidden = isOpen;
    });
  });

  // Botão marcar como concluída (alterna)
  document.querySelectorAll('.btn-toggle-complete').forEach(function (button) {
    button.addEventListener('click', function () {
      button.disabled = true;
      showError(false);
      postJSON(button.getAttribute('data-url'))
        .then(function (data) { applyProgress(data, button.getAttribute('data-lesson-id')); })
        .catch(function () { showError(true); })
        .finally(function () { button.disabled = false; });
    });
  });

  // Vimeo: concluir automaticamente ao fim do vídeo (endpoint idempotente, nunca alterna)
  var frame = document.querySelector('iframe[data-vimeo]');
  if (frame && window.Vimeo && window.Vimeo.Player) {
    var player = new window.Vimeo.Player(frame);
    var sent = false;
    player.on('ended', function () {
      if (sent) return;
      sent = true;
      postJSON(frame.getAttribute('data-complete-url'))
        .then(function (data) { applyProgress(data, frame.getAttribute('data-lesson-id')); })
        .catch(function () { sent = false; showError(true); });
    });
  }
})();
