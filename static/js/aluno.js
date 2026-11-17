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

  function postJSON(url, payload) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': csrfToken(), 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json', 'Content-Type': 'application/json' },
      body: payload === undefined ? undefined : JSON.stringify(payload)
    }).then(function (response) {
      return response.json().then(function (data) {
        if (data.access === 'ended') { document.dispatchEvent(new CustomEvent('course-access-ended', {detail: data})); }
        if (!response.ok) throw new Error(data.message || data.error || 'Não foi possível salvar.');
        return data;
      });
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
      btn.classList.toggle('btn--red', !done);
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

    document.querySelectorAll('[data-member-lesson-id="' + lessonId + '"]').forEach(function (node) {
      node.querySelector('[data-completed-mark]').hidden = !done;
      node.querySelector('[data-lesson-number]').hidden = done;
    });

    updateModuleCounters();
    document.dispatchEvent(new CustomEvent('lesson-progress-changed', {detail: data}));
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

  // Vimeo: o servidor calcula todo o crédito; posição nunca concede tempo.
  var frame = document.querySelector('iframe[data-vimeo]');
  var connected = false;
  function connectVimeo() {
    if (connected || !frame || !window.Vimeo || !window.Vimeo.Player) return;
    connected = true;
    var player = new window.Vimeo.Player(frame);
    var playing = false;
    var position = Number(frame.dataset.position) || 0;
    var inFlight = false;
    var accessEnded = false;
    function videoError() {
      var box = document.getElementById('player-error');
      if (box) box.hidden = false;
    }
    function pulse(isPlaying, beacon) {
      if (accessEnded) return Promise.resolve();
      var payload = {position: position, playing: !!isPlaying && !document.hidden};
      if (beacon && navigator.sendBeacon) {
        var form = new FormData();
        form.append('csrfmiddlewaretoken', csrfToken());
        form.append('payload', JSON.stringify(payload));
        navigator.sendBeacon(frame.dataset.heartbeatUrl, form);
        return Promise.resolve();
      }
      if (inFlight) return Promise.resolve();
      inFlight = true;
      return postJSON(frame.dataset.heartbeatUrl, payload).then(function (data) {
        applyProgress(data, frame.dataset.lessonId);
        document.dispatchEvent(new CustomEvent('lesson-tracked', {detail: data}));
        showError(false);
      }).catch(function () { if (!accessEnded) showError(true); })
        .finally(function () { inFlight = false; });
    }
    document.addEventListener('course-access-ended', function (event) {
      accessEnded = true;
      playing = false;
      player.pause().catch(function () {});
      window.location.assign(event.detail.url || window.location.href);
    });
    var readyTimer = setTimeout(videoError, 12000);
    player.ready().then(function () {
      clearTimeout(readyTimer);
      var duration = Number(frame.dataset.duration) || 0;
      if (frame.dataset.completed === 'true' && duration && position >= duration * .95) position = 0;
      if (position > 0) return player.setCurrentTime(position);
    }).catch(videoError);
    player.on('error', videoError);
    player.on('timeupdate', function (data) { position = data.seconds; document.dispatchEvent(new CustomEvent('lesson-position', {detail: {seconds: position}})); });
    document.addEventListener('lesson-seek', function (event) { var seconds = Number(event.detail.seconds); if (Number.isFinite(seconds) && seconds >= 0) player.setCurrentTime(seconds).catch(videoError); });
    player.on('play', function () { playing = true; pulse(true); });
    player.on('pause', function () { playing = false; pulse(false); });
    setInterval(function () {
      if (playing && !document.hidden) player.getCurrentTime().then(function (seconds) {
        position = seconds; pulse(true);
      }).catch(videoError);
    }, 15000);
    document.addEventListener('visibilitychange', function () { pulse(playing && !document.hidden, document.hidden); });
    window.addEventListener('pagehide', function () { pulse(false, true); });
    player.on('ended', function () {
      pulse(true).then(function () {
        playing = false;
        return postJSON(frame.dataset.endedUrl);
      }).then(function (data) {
        applyProgress(data, frame.dataset.lessonId);
        document.dispatchEvent(new CustomEvent('lesson-video-ended', {detail: data}));
      }).catch(function () { showError(true); }).finally(function () { pulse(false); });
    });
  }
  connectVimeo();
  var sdk = document.querySelector('[data-vimeo-sdk]');
  if (sdk) {
    sdk.addEventListener('load', connectVimeo, { once: true });
    sdk.addEventListener('error', function () { var error = document.getElementById('player-error'); if (error) error.hidden = false; });
  }
})();
