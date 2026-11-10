/* CETREMER · player.js (v2) · página da aula. SUBSTITUI o aluno.js do v1.
   Carregar só em courses/lesson_detail.html, nesta ordem, no bloco extra_js:
     <script src="https://player.vimeo.com/api/player.js"></script>
     <script src="{% static 'js/player.js' %}" defer></script>
   Depende de ui.js (window.CTM) para toasts e POST.

   Contrato com o template (HANDOFF-v2.md, seção 6.3):
   <div class="lesson-page" id="lesson-page"
        data-lesson-id="90" data-module-id="12"
        data-toggle-url="{% url 'toggle_progress' lesson.id %}"
        data-complete-url="{% url 'complete_lesson' lesson.id %}"
        data-position-url="{% url 'save_position' lesson.id %}"
        data-resume="192"                 (segundos salvos; 0 se não houver)
        data-completed="false">
     iframe[data-vimeo] dentro de .player (só para Vimeo; YouTube não tem SDK e fica só com o botão)
     .resume-chip#resume-chip hidden  com [data-resume-time], [data-resume-restart], [data-resume-close]
     button[data-complete-toggle] com [data-label]
     .done-banner#done-banner hidden  com [data-next-title], a[data-next-link], button[data-done-stay]
     dialog#celebrate (fim do curso)
     [data-course-progress] (barras, largura), [data-progress-text] ("50% · 2 de 4 aulas"), [data-progress-count] ("2 de 4 aulas concluídas · 28 min no total" usa data-suffix)
     #status-dot-<id>, [data-lesson-meta="<id>"] (meta da aula na lista lateral)
     [data-module-count="<moduleId>"]
     [data-cert-mini] com [data-cert-text], [data-cert-link]
     button[data-focus-toggle] com [data-label]
   Resposta JSON esperada de toggle e complete:
   {"is_completed": true, "completed_count": 2, "total_count": 4, "percentage": 50.0,
    "module": {"id": 12, "done": 2, "total": 2}, "remaining": 2, "course_done": false,
    "next": {"url": "/courses/bls/lessons/91/", "title": "Operação e Segurança do DEA"} | null,
    "certificate_url": "/certificados/?emitir=bls"}
*/
(function () {
  'use strict';
  var page = document.getElementById('lesson-page');
  if (!page || !window.CTM) return;

  var lessonId = page.getAttribute('data-lesson-id');
  var completed = page.getAttribute('data-completed') === 'true';
  var busy = false;

  function plural(n, one, many) { return n === 1 ? one : many; }

  function apply(data) {
    completed = !!data.is_completed;
    page.setAttribute('data-completed', String(completed));
    var pct = Math.round(Number(data.percentage) || 0);

    document.querySelectorAll('[data-course-progress]').forEach(function (bar) {
      bar.style.width = pct + '%';
      var wrap = bar.closest('[role=progressbar]');
      if (wrap) wrap.setAttribute('aria-valuenow', String(pct));
    });
    document.querySelectorAll('[data-progress-text]').forEach(function (el) {
      el.textContent = pct + '% · ' + data.completed_count + ' de ' + data.total_count + ' ' + plural(data.total_count, 'aula', 'aulas');
    });
    document.querySelectorAll('[data-progress-count]').forEach(function (el) {
      el.textContent = data.completed_count + ' de ' + data.total_count + ' ' + plural(data.total_count, 'aula concluída', 'aulas concluídas') + (el.getAttribute('data-suffix') || '');
    });

    var dot = document.getElementById('status-dot-' + lessonId);
    if (dot) dot.classList.toggle('is-done', completed);
    var meta = document.querySelector('[data-lesson-meta="' + lessonId + '"]');
    if (meta) meta.textContent = (completed ? 'Concluída · ' : 'Assistindo agora · ') + (meta.getAttribute('data-duration') || '');

    if (data.module) {
      document.querySelectorAll('[data-module-count="' + data.module.id + '"]').forEach(function (el) {
        var all = data.module.done === data.module.total;
        el.textContent = all ? 'Concluído' : data.module.done + ' de ' + data.module.total + ' ' + plural(data.module.total, 'aula', 'aulas');
        el.classList.toggle('text-success', all);
      });
    }

    document.querySelectorAll('[data-complete-toggle]').forEach(function (btn) {
      btn.classList.toggle('btn--primary', !completed);
      btn.classList.toggle('btn--done', completed);
      btn.setAttribute('aria-pressed', String(completed));
      var label = btn.querySelector('[data-label]');
      if (label) label.textContent = completed ? 'Concluída' : 'Marcar como concluída';
    });

    var cert = document.querySelector('[data-cert-mini]');
    if (cert && typeof data.remaining === 'number') {
      var ready = data.remaining === 0;
      cert.classList.toggle('is-ready', ready);
      var t = cert.querySelector('[data-cert-text]');
      if (t) t.textContent = ready ? 'Todas as aulas concluídas. Confira seus dados e emita.' : 'Liberado ao concluir 100% das aulas. ' + (data.remaining === 1 ? 'Falta 1 aula.' : 'Faltam ' + data.remaining + ' aulas.');
      var l = cert.querySelector('[data-cert-link]');
      if (l) { l.textContent = ready ? 'Emitir certificado' : 'Ver requisitos'; if (ready && data.certificate_url) l.href = data.certificate_url; }
    }

    var banner = document.getElementById('done-banner');
    if (banner) {
      var showBanner = completed && !data.course_done && data.next;
      banner.hidden = !showBanner;
      if (showBanner) {
        banner.querySelector('[data-next-title]').textContent = data.next.title;
        banner.querySelector('[data-next-link]').href = data.next.url;
      }
    }
    if (completed && data.course_done) {
      var dlg = document.getElementById('celebrate');
      if (dlg && !dlg.open) dlg.showModal();
    }
  }

  function send(url, undoLabel) {
    if (busy) return Promise.resolve();
    busy = true;
    return window.CTM.post(url).then(function (data) {
      apply(data);
      return data;
    }).catch(function () {
      window.CTM.toast('Não foi possível salvar seu progresso. Confira a conexão e tente de novo.', { kind: 'error' });
    }).finally(function () { busy = false; });
  }

  // Botão marcar/desmarcar (alterna) com toast e Desfazer
  function toggle() {
    var toggleUrl = page.getAttribute('data-toggle-url');
    send(toggleUrl).then(function (data) {
      if (!data) return;
      if (data.is_completed) {
        window.CTM.toast('Aula concluída. Progresso salvo', { undo: function () { send(toggleUrl); } });
      } else {
        window.CTM.toast('Aula desmarcada. Seu progresso voltou para ' + Math.round(data.percentage) + '%', { kind: 'info', undo: function () { send(toggleUrl); } });
      }
    });
  }
  document.querySelectorAll('[data-complete-toggle]').forEach(function (btn) { btn.addEventListener('click', toggle); });

  // Faixa de próxima aula
  var stay = document.querySelector('[data-done-stay]');
  if (stay) stay.addEventListener('click', function () { document.getElementById('done-banner').hidden = true; });

  // Modo foco (lembra por aparelho)
  var focusBtn = document.querySelector('[data-focus-toggle]');
  function setFocus(on) {
    page.classList.toggle('is-focus', on);
    if (focusBtn) {
      focusBtn.setAttribute('aria-pressed', String(on));
      var label = focusBtn.querySelector('[data-label]');
      if (label) label.textContent = on ? 'Mostrar aulas' : 'Modo foco';
    }
    try { localStorage.setItem('ctm-focus', on ? '1' : '0'); } catch (e) {}
  }
  try { if (localStorage.getItem('ctm-focus') === '1') setFocus(true); } catch (e) {}
  if (focusBtn) focusBtn.addEventListener('click', function () { setFocus(!page.classList.contains('is-focus')); });

  // Atalhos: M marca/desmarca, N próxima aula (fora de campos de texto)
  document.addEventListener('keydown', function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) || document.activeElement.isContentEditable) return;
    if (e.key === 'm' || e.key === 'M') { e.preventDefault(); toggle(); }
    if (e.key === 'n' || e.key === 'N') { var next = document.querySelector('[data-nav-next]'); if (next) { e.preventDefault(); window.location.href = next.href; } }
  });

  // Vimeo: retomar, salvar posição, concluir em 90%, faixa de próxima no fim
  var frame = document.querySelector('iframe[data-vimeo]');
  if (!frame || !window.Vimeo || !window.Vimeo.Player) return;
  var player = new window.Vimeo.Player(frame);
  var positionUrl = page.getAttribute('data-position-url');
  var completeUrl = page.getAttribute('data-complete-url');
  var resume = parseInt(page.getAttribute('data-resume') || '0', 10);
  var lastSaved = resume, lastSecond = resume, autoSent = completed;

  function mmss(s) { s = Math.floor(s); var m = Math.floor(s / 60), r = s % 60; return (m < 10 ? '0' : '') + m + ':' + (r < 10 ? '0' : '') + r; }
  function savePosition(seconds, beacon) {
    seconds = Math.floor(seconds);
    if (Math.abs(seconds - lastSaved) < 5) return;
    lastSaved = seconds;
    if (beacon && navigator.sendBeacon) {
      var fd = new FormData(); fd.append('seconds', seconds); fd.append('csrfmiddlewaretoken', window.CTM.csrf());
      navigator.sendBeacon(positionUrl, fd);
    } else {
      window.CTM.post(positionUrl, { seconds: seconds }).catch(function () {});
    }
  }

  player.getDuration().then(function (duration) {
    if (resume > 15 && resume < duration * 0.95) {
      player.setCurrentTime(resume).catch(function () {});
      var chip = document.getElementById('resume-chip');
      if (chip) {
        chip.querySelector('[data-resume-time]').textContent = mmss(resume);
        chip.hidden = false;
        chip.querySelector('[data-resume-restart]').addEventListener('click', function () { player.setCurrentTime(0); chip.hidden = true; });
        chip.querySelector('[data-resume-close]').addEventListener('click', function () { chip.hidden = true; });
        player.on('play', function () { setTimeout(function () { chip.hidden = true; }, 4000); });
      }
    }
  });

  var tick = 0;
  player.on('timeupdate', function (d) {
    lastSecond = d.seconds;
    if (++tick % 40 === 0) savePosition(d.seconds); // timeupdate dispara ~4x por segundo: salva a cada ~10 s
    if (!autoSent && !completed && d.percent >= 0.9) {
      autoSent = true;
      send(completeUrl).then(function (data) { if (data) window.CTM.toast('Aula concluída. Progresso salvo'); });
    }
  });
  player.on('pause', function (d) { savePosition(d.seconds); });
  player.on('ended', function () {
    savePosition(0);
    var banner = document.getElementById('done-banner');
    if (banner && completed && banner.querySelector('[data-next-link]').getAttribute('href')) banner.hidden = false;
  });
  window.addEventListener('pagehide', function () { savePosition(lastSecond, true); });
})();
