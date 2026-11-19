/* ==========================================================================
   GoMut · Painel do produtor · Comportamentos de interface
   JS puro, sem dependências. Incluir no fim do <body> com defer.
   Tudo é ligado por atributos data-gp-*; nenhuma regra de negócio aqui.
   ========================================================================== */
(function () {
  'use strict';
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]):not([type=hidden]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

  /* ---------- Toast ----------
     gpToast('Aula salva', { actionLabel: 'Desfazer', onAction: fn })
     Mensagens do Django: <template data-gp-messages><p data-level="success">Curso salvo</p></template> */
  function gpToast(text, opts) {
    opts = opts || {};
    var box = $('.gp-toasts');
    if (!box) { box = document.createElement('div'); box.className = 'gp-toasts'; box.setAttribute('aria-live', 'polite'); document.body.appendChild(box); }
    var t = document.createElement('div');
    t.className = 'gp-toast';
    t.innerHTML = '<svg class="gp-icon" aria-hidden="true"><use href="#i-check-circle"></use></svg><span style="flex:1"></span>';
    t.querySelector('span').textContent = text;
    if (opts.actionLabel) {
      var b = document.createElement('button');
      b.className = 'btn btn--sm'; b.type = 'button'; b.textContent = opts.actionLabel;
      b.addEventListener('click', function () { if (opts.onAction) opts.onAction(); t.remove(); });
      t.appendChild(b);
    }
    box.appendChild(t);
    setTimeout(function () { t.remove(); }, opts.duration || 5000);
  }
  window.gpToast = gpToast;
  $$('template[data-gp-messages]').forEach(function (tpl) {
    $$('p', tpl.content).forEach(function (p) { if (p.dataset.level !== 'error') gpToast(p.textContent.trim()); });
  });

  /* ---------- Filtros instantâneos ----------
     <form data-gp-autofilter data-gp-results="#lista-alunos" method="get"> ... </form>
     Texto: espera 300 ms; select/checkbox/radio: imediato. Substitui só o bloco de resultados
     (o servidor renderiza a página inteira; pegamos o mesmo id na resposta) e atualiza a URL. */
  function debounce(fn, ms) { var t; return function () { var a = arguments, c = this; clearTimeout(t); t = setTimeout(function () { fn.apply(c, a); }, ms); }; }
  $$('form[data-gp-autofilter]').forEach(function (form) {
    var target = form.dataset.gpResults;
    var revision = 0;
    var run = function () {
      var version = ++revision;
      var params = new URLSearchParams(new FormData(form));
      Array.from(params.keys()).forEach(function (k) { if (params.get(k) === '') params.delete(k); });
      var url = (form.getAttribute('action') || location.pathname) + (params.toString() ? '?' + params : '');
      var region = target && $(target);
      if (!region || !window.fetch) {
        var active = document.activeElement;
        if (active && active.id && typeof active.selectionStart === 'number') {
          try { sessionStorage.setItem('gp-filter-focus', JSON.stringify({path: location.pathname, id: active.id, caret: active.selectionStart})); } catch {}
        }
        location.replace(url); return;
      }
      region.setAttribute('aria-busy', 'true');
      fetch(url, { headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { if (!r.ok || r.redirected) throw new Error(); return r.text(); })
        .then(function (html) {
          if (version !== revision) return;
          var doc = new DOMParser().parseFromString(html, 'text/html');
          var fresh = doc.querySelector(target);
          if (!fresh) throw new Error();
          region.replaceWith(fresh); bindAll(fresh);
          document.querySelectorAll('[data-filter-summary]').forEach(function (summary) {
            var next = doc.getElementById(summary.id);
            if (next) summary.replaceWith(next);
          });
          history.replaceState(null, '', url);
        })
        .catch(function () { if (version === revision) location.replace(url); });
    };
    var slow = debounce(run, 300);
    form.addEventListener('input', function (e) { if (e.target.matches('input[type=search],input[type=text],input:not([type])')) slow(); });
    form.addEventListener('change', function (e) { if (!e.target.matches('input[type=search],input[type=text],input:not([type])')) run(); });
    form.addEventListener('submit', function (e) { e.preventDefault(); run(); });
  });

  try {
    var savedFocus = JSON.parse(sessionStorage.getItem('gp-filter-focus'));
    sessionStorage.removeItem('gp-filter-focus');
    if (savedFocus && savedFocus.path === location.pathname) {
      var field = document.getElementById(savedFocus.id);
      if (field) { field.focus(); field.setSelectionRange(savedFocus.caret, savedFocus.caret); }
    }
  } catch {}

  /* ---------- Modal (<dialog>) ----------
     <button data-gp-open="#dlg-x">  ·  dentro do dialog: <button data-gp-close>
     <dialog data-gp-guard> pergunta antes de fechar se algo foi digitado. */
  function openDialog(dlg, opener) {
    if (!dlg || dlg.open) return;
    dlg._opener = opener || document.activeElement;
    dlg._dirty = false;
    dlg.showModal();
    var first = dlg.querySelector('[autofocus]') || dlg.querySelector(FOCUSABLE);
    if (first) first.focus();
  }
  function closeDialog(dlg) {
    if (dlg.id === 'first-code' && !dlg.dataset.copied && !window.confirm('Você já copiou o código? Ele não aparece de novo.')) return;
    if (dlg.hasAttribute('data-gp-guard') && dlg._dirty && !window.confirm('Descartar o que foi preenchido?')) return;
    dlg.close();
    if (dlg._opener && dlg._opener.focus) dlg._opener.focus();
    return true;
  }
  document.addEventListener('click', function (e) {
    var o = e.target.closest('[data-gp-open]');
    if (o) { e.preventDefault(); openDialog($(o.dataset.gpOpen), o); return; }
    var next = e.target.closest('[data-code-next]');
    if (next && !closeDialog(next.closest('dialog'))) { e.preventDefault(); return; }
    var c = e.target.closest('[data-gp-close]');
    if (c) { var d = c.closest('dialog'); if (d) { e.preventDefault(); closeDialog(d); } }
  });
  $$('dialog.gp-dialog').forEach(function (d) {
    d.addEventListener('input', function () { d._dirty = true; });
    d.addEventListener('cancel', function (e) { e.preventDefault(); closeDialog(d); });
    d.addEventListener('click', function (e) { if (e.target === d) closeDialog(d); });
  });
  $$('dialog[data-gp-autoopen]').forEach(function (d) { openDialog(d); });

  /* ---------- Gaveta ----------
     <div class="gp-overlay" data-gp-drawer-overlay></div>
     <aside class="gp-drawer" role="dialog" aria-modal="true" aria-labelledby="…" data-gp-drawer data-gp-drawer-param="aluno">
     Aberta pelo servidor quando ?aluno=ID existe. Fechar remove o parâmetro da URL sem recarregar. */
  function trapFocus(container, e) {
    var f = $$(FOCUSABLE, container).filter(function (el) { return el.offsetParent !== null; });
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }
  $$('[data-gp-drawer]').forEach(function (drawer) {
    var overlay = $('[data-gp-drawer-overlay]');
    var param = drawer.dataset.gpDrawerParam;
    var close = function () {
      drawer.hidden = true; if (overlay) overlay.hidden = true;
      document.body.style.overflow = '';
      if (param) { var u = new URL(location.href); u.searchParams.delete(param); if (param === 'aluno') { ['plano','aba','estender','matricular'].forEach(function (k) { u.searchParams.delete(k); }); u.hash = ''; } history.replaceState(null, '', u); }
      var row = $('[data-gp-drawer-origin]'); if (row) row.focus();
    };
    if (!drawer.hidden) {
      document.body.style.overflow = 'hidden';
      var title = drawer.querySelector('[data-gp-drawer-title]') || drawer.querySelector('h2');
      if (title && !document.querySelector('dialog[open]')) { title.setAttribute('tabindex', '-1'); title.focus(); }
    }
    drawer.addEventListener('keydown', function (e) { if (e.target.closest('dialog[open]')) return; if (e.key === 'Escape') close(); if (e.key === 'Tab') trapFocus(drawer, e); });
    $$('[data-gp-drawer-close]', drawer).forEach(function (b) { b.addEventListener('click', close); });
    if (overlay) overlay.addEventListener('click', close);
  });

  /* ---------- Barra de salvar ----------
     <form data-gp-dirty> … <div class="gp-savebar" hidden> <button type="button" data-gp-discard>Descartar</button> <button class="btn btn--primary">Salvar…</button></div></form>
     Botões de salvar do cabeçalho que ficam fora do form: form="id-do-form". */
  $$('form[data-gp-dirty]').forEach(function (form) {
    var bar = form.querySelector('.gp-savebar') || (form.id && $('.gp-savebar[data-gp-for="' + form.id + '"]'));
    var dirty = false;
    var mark = function () { if (!dirty) { dirty = true; if (bar) bar.hidden = false; } };
    form.addEventListener('input', mark);
    form.addEventListener('change', mark);
    form.addEventListener('submit', function () { dirty = false; });
    $$('[data-gp-discard]', bar || form).forEach(function (b) {
      b.addEventListener('click', function () { form.reset(); dirty = false; if (bar) bar.hidden = true; form.dispatchEvent(new Event('gp:reset')); });
    });
    window.addEventListener('beforeunload', function (e) { if (dirty) { e.preventDefault(); e.returnValue = ''; } });
  });

  /* ---------- Copiar ----------
     <button data-gp-copy="4827190356" data-gp-copied="Código copiado">  ou  data-gp-copy-from="#mensagem" */
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-gp-copy],[data-gp-copy-from]');
    if (!b) return;
    var text = b.dataset.gpCopy;
    if (!text && b.dataset.gpCopyFrom) { var src = $(b.dataset.gpCopyFrom); text = src ? (src.value || src.innerText) : ''; }
    if (!text) return;
    (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject())
      .then(function () { gpToast(b.dataset.gpCopied || 'Copiado'); })
      .catch(function () { window.prompt('Copie o texto:', text); });
  });

  /* ---------- Menu "…" ----------
     <div class="gp-menu-wrap" style="position:relative">
       <button class="btn btn--ghost btn--icon btn--sm" aria-haspopup="menu" aria-expanded="false" data-gp-menu aria-label="Mais ações">…</button>
       <div class="gp-menu" role="menu" hidden> <a role="menuitem" class="gp-menu__item">…</a> </div>
     </div> */
  function closeMenus(except) {
    $$('[data-gp-menu][aria-expanded="true"]').forEach(function (b) {
      if (b === except) return;
      b.setAttribute('aria-expanded', 'false');
      var m = b.parentElement.querySelector('.gp-menu'); if (m) m.hidden = true;
    });
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-gp-menu]');
    if (!b) { if (!e.target.closest('.gp-menu')) closeMenus(); return; }
    var m = b.parentElement.querySelector('.gp-menu');
    var open = b.getAttribute('aria-expanded') === 'true';
    closeMenus(b);
    b.setAttribute('aria-expanded', String(!open));
    if (m) {
      m.hidden = open;
      if (!open) {
        /* posição fixa calculada pelo botão: o menu nunca é cortado por cards com overflow:hidden ou tabelas com rolagem */
        var r = b.getBoundingClientRect();
        m.style.position = 'fixed';
        m.style.right = Math.max(8, window.innerWidth - r.right) + 'px';
        m.style.left = 'auto';
        var below = r.bottom + 4, h = m.offsetHeight;
        m.style.top = (below + h > window.innerHeight - 8 ? Math.max(8, r.top - 4 - h) : below) + 'px';
        var f = m.querySelector('[role=menuitem]'); if (f) f.focus();
      }
    }
  });
  window.addEventListener('scroll', function () { closeMenus(); }, true);
  window.addEventListener('resize', function () { closeMenus(); });
  document.addEventListener('keydown', function (e) {
    var menu = e.target.closest && e.target.closest('.gp-menu');
    if (e.key === 'Escape') { var open = $('[data-gp-menu][aria-expanded="true"]'); closeMenus(); if (open) open.focus(); }
    if (menu && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      e.preventDefault();
      var items = $$('[role=menuitem]', menu), i = items.indexOf(document.activeElement);
      var n = e.key === 'ArrowDown' ? (i + 1) % items.length : (i - 1 + items.length) % items.length;
      items[n].focus();
    }
  });

  /* ---------- Busca rápida: Ctrl K / ⌘K ---------- */
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      var q = $('[data-gp-quicksearch]'); if (q) { e.preventDefault(); q.focus(); q.select(); }
    }
  });

  /* ---------- Reordenar (arrastar e teclado) ----------
     <ol data-gp-sortable data-gp-sortable-url="/painel/…/ordenar/" data-gp-sortable-csrf="{{ csrf_token }}">
       <li data-id="12"> <button class="btn btn--ghost btn--icon btn--sm gp-handle" data-gp-handle aria-label="Mover {nome}. Use as setas para cima e para baixo.">…</button> … </li>
     Envia POST JSON {ids:[…]} com a nova ordem. Se o servidor recusar, desfaz e avisa. */
  function bindSortable(list) {
    var dragged = null, before = null;
    var save = function () {
      var ids = $$(':scope > [data-id]', list).map(function (li) { return li.dataset.id; });
      if (!list.dataset.gpSortableUrl) return;
      fetch(list.dataset.gpSortableUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': list.dataset.gpSortableCsrf || '' },
        body: JSON.stringify({ ids: ids })
      }).then(function (r) {
        if (!r.ok) throw new Error();
        gpToast('Ordem salva');
      }).catch(function () {
        if (before) before.forEach(function (li) { list.appendChild(li); });
        gpToast('Não foi possível salvar a nova ordem. Tente de novo.');
      });
    };
    $$(':scope > [data-id]', list).forEach(function (li) {
      var handle = li.querySelector('[data-gp-handle]');
      if (!handle) return;
      handle.addEventListener('mousedown', function () { li.draggable = true; });
      li.addEventListener('dragstart', function (e) { dragged = li; before = $$(':scope > [data-id]', list); li.classList.add('gp-sortable-ghost'); e.dataTransfer.effectAllowed = 'move'; });
      li.addEventListener('dragend', function () { li.classList.remove('gp-sortable-ghost'); li.draggable = false; dragged = null; save(); });
      li.addEventListener('dragover', function (e) {
        if (!dragged || dragged === li) return;
        e.preventDefault();
        var r = li.getBoundingClientRect();
        list.insertBefore(dragged, (e.clientY - r.top) > r.height / 2 ? li.nextSibling : li);
      });
      handle.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
        e.preventDefault();
        before = $$(':scope > [data-id]', list);
        if (e.key === 'ArrowUp' && li.previousElementSibling) list.insertBefore(li, li.previousElementSibling);
        else if (e.key === 'ArrowDown' && li.nextElementSibling) list.insertBefore(li.nextElementSibling, li);
        else return;
        handle.focus(); save();
      });
    });
  }

  /* ---------- Dropzone ----------
     <label class="gp-dropzone" data-gp-dropzone> … <input type="file" name="cover_image" accept="image/*"> </label>
     Mostra o nome do arquivo escolhido; prévia de imagem em [data-gp-preview] se existir. */
  function bindDropzone(z) {
    var input = z.querySelector('input[type=file]');
    if (!input) return;
    ['dragenter', 'dragover'].forEach(function (ev) { z.addEventListener(ev, function () { z.classList.add('is-dragover'); }); });
    ['dragleave', 'drop'].forEach(function (ev) { z.addEventListener(ev, function () { z.classList.remove('is-dragover'); }); });
    input.addEventListener('change', function () {
      var f = input.files && input.files[0]; if (!f) return;
      var hint = z.querySelector('.gp-dropzone__hint'); if (hint) hint.textContent = f.name;
      var prev = z.dataset.gpPreview && $(z.dataset.gpPreview);
      if (prev && f.type.indexOf('image/') === 0) { prev.style.backgroundImage = 'url(' + URL.createObjectURL(f) + ')'; }
    });
  }

  function bindAll(root) {
    $$('[data-gp-sortable]', root).forEach(bindSortable);
    $$('[data-gp-dropzone]', root).forEach(bindDropzone);
  }
  bindAll(document);
})();
