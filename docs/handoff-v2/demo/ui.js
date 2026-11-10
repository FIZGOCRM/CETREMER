/* CETREMER · ui.js (v2) · padrões de interação compartilhados por aluno e admin.
   Carregar em base_core.html, com defer, DEPOIS de site.js:
     <script src="{% static 'js/ui.js' %}" defer></script>
   Tudo é opt-in por atributo data-*. Expõe window.CTM com: toast, post, postForm, csrf, openDrawer, closeDrawer.
   Contratos completos no HANDOFF-v2.md, seção 5.

   Índice
   1. Utilidades (csrf, post, plural)
   2. Toasts (+ mensagens do Django vindas do servidor)
   3. Formulários assíncronos [data-async]
   4. Menus suspensos e sino [data-popover]
   5. Painel lateral (drawer) [data-drawer-open], [data-drawer-url], dialog.drawer[data-autoopen]
   6. Diálogos: confirmação digitando o nome [data-confirm-text]
   7. Barra de alterações não salvas form[data-dirty-form] + "Sair sem salvar?"
   8. Abas [data-tabs]
   9. Liga e desliga button.switch
   10. Mostrar senha [data-reveal]
   11. Busca global Ctrl K dialog.cmdk
   12. Seleção em massa [data-bulk]
   13. Salvamento automático textarea[data-autosave-url]
   14. Criação rápida input[data-inline-create-url]
   15. Copiar com aviso [data-copy-toast]
   16. Dispensar item com Desfazer [data-dismiss-url]
   17. Espelhar texto [data-mirror]
   18. Habilitar no horário [data-enable-at]
   19. Sugestões ao digitar [data-suggest-url]
*/
(function () {
  'use strict';

  /* ---------- 1. Utilidades ---------- */
  function csrf() {
    var field = document.querySelector('[name=csrfmiddlewaretoken]');
    if (field) return field.value;
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  // POST com corpo opcional (objeto vira form-urlencoded). Sempre espera JSON de volta.
  function post(url, data) {
    var body = null;
    if (data instanceof FormData) body = data;
    else if (data) {
      body = new URLSearchParams();
      Object.keys(data).forEach(function (k) { body.append(k, data[k]); });
    }
    return fetch(url, {
      method: 'POST', credentials: 'same-origin', body: body,
      headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'fetch', 'Accept': 'application/json' }
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (json) {
        if (!r.ok) { var e = new Error(json.error || ('HTTP ' + r.status)); e.data = json; e.status = r.status; throw e; }
        return json;
      });
    });
  }

  function plural(n, one, many) { return n + ' ' + (n === 1 ? one : many); }

  var ICON_OK = '<svg class="icon toast__icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/></svg>';
  var ICON_ERR = '<svg class="icon toast__icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/></svg>';
  var ICON_INFO = '<svg class="icon toast__icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/></svg>';
  var ICON_X = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';

  /* ---------- 2. Toasts ----------
     CTM.toast("Aula concluída. Progresso salvo", {
       kind: "ok" | "error" | "info",        // padrão "ok"
       undo: function () {...} | "/url/post/", // mostra "Desfazer"; string = POST nessa URL e recarrega se a resposta tiver reload:true
       action: { label: "Ver aluno", href: "/painel/alunos/?aluno=3" }, // ou { label, onClick }
       duration: 5000                         // padrão 5000; 8000 com undo; erro não some sozinho
     })
     Container no layout base: <div class="toast-stack" id="toast-stack" aria-live="polite" aria-atomic="false"></div>
  */
  function stack() {
    var s = document.getElementById('toast-stack');
    if (!s) {
      s = document.createElement('div');
      s.id = 'toast-stack'; s.className = 'toast-stack';
      s.setAttribute('aria-live', 'polite');
      document.body.appendChild(s);
    }
    return s;
  }

  function toast(message, opts) {
    opts = opts || {};
    var kind = opts.kind || 'ok';
    var el = document.createElement('div');
    el.className = 'toast' + (kind === 'error' ? ' toast--error' : kind === 'info' ? ' toast--info' : '');
    el.setAttribute('role', kind === 'error' ? 'alert' : 'status');
    el.innerHTML = (kind === 'error' ? ICON_ERR : kind === 'info' ? ICON_INFO : ICON_OK) + '<span class="toast__msg"></span>';
    el.querySelector('.toast__msg').textContent = message;

    function remove() {
      if (!el.parentNode) return;
      el.classList.add('is-leaving');
      setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 160);
    }

    if (opts.undo) {
      var u = document.createElement('button');
      u.type = 'button'; u.className = 'toast__action'; u.textContent = 'Desfazer';
      u.addEventListener('click', function () {
        remove();
        if (typeof opts.undo === 'function') { opts.undo(); return; }
        post(opts.undo).then(function (json) {
          if (json.toast) toast(json.toast, { kind: 'info' });
          if (json.reload) window.location.reload();
          if (json.redirect) window.location.href = json.redirect;
        }).catch(function () { toast('Não foi possível desfazer. Tente de novo.', { kind: 'error' }); });
      });
      el.appendChild(u);
    }
    if (opts.action) {
      var a = document.createElement(opts.action.href ? 'a' : 'button');
      a.className = 'toast__action'; a.textContent = opts.action.label;
      if (opts.action.href) a.href = opts.action.href; else { a.type = 'button'; a.addEventListener('click', function () { remove(); opts.action.onClick(); }); }
      el.appendChild(a);
    }
    var close = document.createElement('button');
    close.type = 'button'; close.className = 'toast__close'; close.setAttribute('aria-label', 'Fechar aviso'); close.innerHTML = ICON_X;
    close.addEventListener('click', remove);
    el.appendChild(close);

    stack().appendChild(el);
    var duration = opts.duration || (opts.undo ? 8000 : 5000);
    if (kind !== 'error') {
      var timer = setTimeout(remove, duration);
      el.addEventListener('mouseenter', function () { clearTimeout(timer); });
      el.addEventListener('mouseleave', function () { timer = setTimeout(remove, 2500); });
    }
    return el;
  }

  // Mensagens do Django: o layout renderiza <template data-toast data-kind="ok|error|info" data-undo-url data-action-label data-action-href>texto</template>
  document.querySelectorAll('template[data-toast]').forEach(function (t) {
    var opts = { kind: t.getAttribute('data-kind') || 'ok' };
    if (t.getAttribute('data-undo-url')) opts.undo = t.getAttribute('data-undo-url');
    if (t.getAttribute('data-action-label')) opts.action = { label: t.getAttribute('data-action-label'), href: t.getAttribute('data-action-href') };
    toast(t.innerHTML.trim().replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#x27;/g, "'"), opts);
    t.remove();
  });

  /* ---------- 3. Formulários assíncronos ----------
     <form method="post" action="..." data-async> ... </form>
     Sem JS, o form faz POST normal e a view redireciona com messages (toast no próximo carregamento).
     Com JS, envia por fetch e a view devolve JSON (ver core/ajax.py no kit):
       {"ok": true, "toast": "Texto", "undo_url": "/x/desfazer/", "redirect": "/url/", "reload": false,
        "remove": "#seletor", "replace": {"#seletor": "<html>"}, "counts": {"#seletor": "3"}}
     Erro de validação: status 400 com {"ok": false, "errors": {"campo": ["msg"]}, "error": "Corrija 1 campo para salvar."}
  */
  function applyResponse(json) {
    if (!json) return;
    if (json.replace) Object.keys(json.replace).forEach(function (sel) {
      var node = document.querySelector(sel);
      if (node) node.outerHTML = json.replace[sel];
    });
    if (json.remove) document.querySelectorAll(json.remove).forEach(function (n) { n.remove(); });
    if (json.counts) Object.keys(json.counts).forEach(function (sel) {
      document.querySelectorAll(sel).forEach(function (n) { n.textContent = json.counts[sel]; n.setAttribute('data-count', json.counts[sel]); });
    });
    if (json.toast) toast(json.toast, { undo: json.undo_url || null, action: json.action || null });
    if (json.redirect) { window.location.href = json.redirect; return; }
    if (json.reload) window.location.reload();
  }

  function showErrors(form, json) {
    form.querySelectorAll('[aria-invalid="true"]').forEach(function (f) { f.removeAttribute('aria-invalid'); });
    form.querySelectorAll('.error-text[data-js-error]').forEach(function (e) { e.remove(); });
    var summary = form.querySelector('[data-form-errors]');
    if (summary) { summary.hidden = !json.error; summary.querySelector('[data-form-errors-text]').textContent = json.error || ''; }
    var first = null;
    Object.keys(json.errors || {}).forEach(function (name) {
      var field = form.querySelector('[name="' + name + '"]');
      if (!field) return;
      field.setAttribute('aria-invalid', 'true');
      var msg = document.createElement('span');
      msg.className = 'error-text'; msg.setAttribute('data-js-error', '');
      msg.id = 'err-' + name; msg.textContent = json.errors[name][0];
      field.setAttribute('aria-describedby', msg.id);
      (field.closest('.field') || field.parentNode).appendChild(msg);
      if (!first) first = field;
    });
    if (first) first.focus();
    else if (json.error) toast(json.error, { kind: 'error' });
  }

  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!form.matches('form[data-async]')) return;
    e.preventDefault();
    var btn = e.submitter || form.querySelector('[type=submit]');
    var data = new FormData(form);
    if (btn && btn.name) data.append(btn.name, btn.value);
    if (btn) btn.classList.add('is-busy');
    post(form.action || window.location.href, data)
      .then(function (json) {
        form.dispatchEvent(new CustomEvent('ctm:saved', { bubbles: true, detail: json }));
        var dlg = form.closest('dialog');
        if (dlg && !json.keep_open) dlg.close();
        applyResponse(json);
      })
      .catch(function (err) {
        if (err.data && err.data.replace) applyResponse({ replace: err.data.replace });
        if (err.data && (err.data.errors || err.data.error)) showErrors(form, err.data);
        else toast('Não foi possível salvar. Confira sua conexão e tente de novo.', { kind: 'error' });
      })
      .finally(function () { if (btn) btn.classList.remove('is-busy'); });
  });

  /* ---------- 4. Menus suspensos e sino ----------
     <div class="popover" data-popover>
       <button type="button" aria-haspopup="true" aria-expanded="false" data-popover-toggle>...</button>
       <div class="menu" data-popover-panel hidden> ... </div>
     </div>
     Sino: no botão, data-notif-seen-url="/avisos/vistos/" (POST ao abrir, zera o contador .bell__count).
     "Marcar todos como lidos": <button data-notif-read-all="/avisos/lidos/">.
  */
  function closePopovers(except) {
    document.querySelectorAll('[data-popover]').forEach(function (p) {
      if (p === except) return;
      var t = p.querySelector('[data-popover-toggle]');
      var panel = p.querySelector('[data-popover-panel]');
      if (t) t.setAttribute('aria-expanded', 'false');
      if (panel) panel.hidden = true;
    });
  }
  document.addEventListener('click', function (e) {
    var toggle = e.target.closest('[data-popover-toggle]');
    if (toggle) {
      var pop = toggle.closest('[data-popover]');
      var panel = pop.querySelector('[data-popover-panel]');
      var open = toggle.getAttribute('aria-expanded') !== 'true';
      closePopovers(pop);
      toggle.setAttribute('aria-expanded', String(open));
      panel.hidden = !open;
      if (open) {
        var first = panel.querySelector('a, button');
        if (first) first.focus({ preventScroll: true });
        var seen = toggle.getAttribute('data-notif-seen-url');
        if (seen) post(seen).then(function () {
          document.querySelectorAll('.bell__count').forEach(function (c) { c.textContent = '0'; c.setAttribute('data-count', '0'); });
        }).catch(function () {});
      }
      return;
    }
    var readAll = e.target.closest('[data-notif-read-all]');
    if (readAll) {
      post(readAll.getAttribute('data-notif-read-all')).then(function () {
        document.querySelectorAll('.notif__item.is-unread').forEach(function (i) { i.classList.remove('is-unread'); });
        document.querySelectorAll('.bell__count').forEach(function (c) { c.textContent = '0'; c.setAttribute('data-count', '0'); });
        toast('Avisos marcados como lidos');
      }).catch(function () { toast('Não foi possível marcar os avisos.', { kind: 'error' }); });
      return;
    }
    if (!e.target.closest('[data-popover-panel]')) closePopovers(null);
  });

  /* ---------- 5. Painel lateral (drawer) ----------
     Abrir conteúdo que já está na página:  <button data-drawer-open="drawer-id">
     Abrir buscando HTML parcial:           <a href="?aula=12" data-drawer-url="/painel/cursos/3/aulas/12/painel/" data-drawer-target="drawer-aula" data-drawer-param="aula" data-drawer-value="12">
       A view devolve só o miolo (template parcial) e o JS coloca dentro de [data-drawer-content] do dialog.
       O href continua funcionando sem JS (a página carrega com o painel aberto).
     Abrir no carregamento (quando a URL já tem ?aula=12): <dialog class="drawer" data-autoopen>
     Fechar: [data-drawer-close] dentro do dialog, Esc ou clique fora. Ao fechar, remove o parâmetro da URL.
     Se o dialog tiver um form[data-dirty-form] com mudanças, pergunta antes de fechar.
  */
  function openDrawer(dialog, param, value) {
    if (!dialog) return;
    if (!dialog.open) dialog.showModal();
    if (param) {
      var url = new URL(window.location.href);
      url.searchParams.set(param, value);
      history.replaceState(null, '', url);
      dialog.setAttribute('data-param', param);
    }
    var focusable = dialog.querySelector('[autofocus], input, textarea, select, button');
    if (focusable) focusable.focus();
  }
  function closeDrawer(dialog, force) {
    if (!dialog) return;
    var dirty = dialog.querySelector('form[data-dirty-form].is-dirty');
    if (dirty && !force) { askLeave(function () { resetDirty(dirty); closeDrawer(dialog, true); }); return; }
    dialog.close();
    var param = dialog.getAttribute('data-param');
    if (param) {
      var url = new URL(window.location.href);
      url.searchParams.delete(param);
      history.replaceState(null, '', url);
    }
  }
  document.addEventListener('click', function (e) {
    var opener = e.target.closest('[data-drawer-open]');
    if (opener) { e.preventDefault(); openDrawer(document.getElementById(opener.getAttribute('data-drawer-open')), opener.getAttribute('data-drawer-param'), opener.getAttribute('data-drawer-value')); return; }
    var remote = e.target.closest('[data-drawer-url]');
    if (remote) {
      e.preventDefault();
      var dlg = document.getElementById(remote.getAttribute('data-drawer-target'));
      var box = dlg && dlg.querySelector('[data-drawer-content]');
      if (!dlg || !box) { window.location.href = remote.href; return; }
      box.innerHTML = '<div class="drawer__body"><span class="sk sk--title sk--w60"></span><span class="sk sk--line sk--w80"></span><span class="sk sk--line sk--w40"></span></div>';
      openDrawer(dlg, remote.getAttribute('data-drawer-param'), remote.getAttribute('data-drawer-value'));
      fetch(remote.getAttribute('data-drawer-url'), { credentials: 'same-origin', headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then(function (html) { box.innerHTML = html; initWithin(box); var f = box.querySelector('[autofocus], input, textarea'); if (f) f.focus(); })
        .catch(function () { window.location.href = remote.href; });
      return;
    }
    var closer = e.target.closest('[data-drawer-close]');
    if (closer) { closeDrawer(closer.closest('dialog')); return; }
    // clique no fundo escuro do dialog (o alvo é o próprio <dialog>)
    if (e.target.matches('dialog.drawer, dialog.cmdk, dialog.sheet')) {
      if (e.target.classList.contains('drawer')) closeDrawer(e.target); else e.target.close();
    }
  });
  document.addEventListener('cancel', function (e) {
    if (e.target.matches('dialog.drawer')) { e.preventDefault(); closeDrawer(e.target); }
  }, true);
  document.querySelectorAll('dialog.drawer[data-autoopen], dialog.dialog[data-autoopen], dialog.sheet[data-autoopen]').forEach(function (d) {
    d.showModal();
    if (d.getAttribute('data-autoopen')) d.setAttribute('data-param', d.getAttribute('data-autoopen'));
  });

  /* ---------- 6. Confirmação digitando o nome (alto risco) ----------
     <input class="input" data-confirm-text="BLS" aria-describedby="..."> e o botão <button data-confirm-submit disabled>
     O botão só habilita quando o texto digitado é igual (sem diferenciar maiúsculas).
  */
  document.addEventListener('input', function (e) {
    var input = e.target.closest('[data-confirm-text]');
    if (!input) return;
    var scope = input.closest('form, dialog') || document;
    var ok = input.value.trim().toLowerCase() === input.getAttribute('data-confirm-text').trim().toLowerCase();
    scope.querySelectorAll('[data-confirm-submit]').forEach(function (b) { b.disabled = !ok; });
  });

  /* ---------- 7. Barra de alterações não salvas ----------
     <form method="post" data-dirty-form data-dirtybar="dirtybar-curso"> ... campos com data-dirty-label="prazo de acesso" ... </form>
     <div class="dirtybar" id="dirtybar-curso" hidden role="region" aria-label="Alterações não salvas">
       <svg class="icon dirtybar__icon">...</svg>
       <span class="dirtybar__msg" data-dirty-msg>Alterações não salvas</span>
       <button type="button" class="dirtybar__discard" data-dirty-discard>Descartar</button>
       <button type="submit" class="btn btn--primary" form="ID-DO-FORM">Salvar alterações</button>
     </div>
     A mensagem vira "2 alterações não salvas: liberação do conteúdo e prazo de acesso." quando os campos têm data-dirty-label.
     Ctrl+S salva. Sair da página com mudanças abre o dialog #leave-dialog (ver base_core no HANDOFF).
  */
  function snapshot(form) {
    var out = {};
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name || el.type === 'submit' || el.type === 'button' || el.name === 'csrfmiddlewaretoken') return;
      var key = el.name + (el.type === 'radio' || el.type === 'checkbox' ? '::' + el.value : '');
      out[key] = (el.type === 'radio' || el.type === 'checkbox') ? el.checked : el.value;
      if (el.getAttribute('role') === 'switch' && el.tagName === 'BUTTON') out[key] = el.getAttribute('aria-checked');
    });
    return out;
  }
  function changedLabels(form) {
    var base = form._ctmBase || {}, now = snapshot(form), labels = [], count = 0, seen = {};
    Object.keys(now).forEach(function (k) {
      if (now[k] === base[k]) return;
      var name = k.split('::')[0];
      if (seen[name]) return;
      seen[name] = true; count++;
      var field = form.querySelector('[name="' + name + '"]');
      var holder = field ? field.closest('[data-dirty-label]') : null;
      var label = holder ? holder.getAttribute('data-dirty-label') : null;
      if (label && labels.indexOf(label) === -1) labels.push(label);
    });
    return { count: count, labels: labels };
  }
  function joinPt(list) { return list.length <= 1 ? list.join('') : list.slice(0, -1).join(', ') + ' e ' + list[list.length - 1]; }
  function refreshDirty(form) {
    var info = changedLabels(form);
    var dirty = info.count > 0;
    form.classList.toggle('is-dirty', dirty);
    var bar = document.getElementById(form.getAttribute('data-dirtybar'));
    if (!bar) return;
    bar.hidden = !dirty;
    var msg = bar.querySelector('[data-dirty-msg]');
    if (msg && dirty) {
      var text = info.count === 1 ? '1 alteração não salva' : info.count + ' alterações não salvas';
      if (info.labels.length) text += ': ' + joinPt(info.labels) + '.';
      msg.textContent = text;
    }
  }
  function resetDirty(form) {
    form.reset();
    form.querySelectorAll('button.switch[role=switch][data-initial]').forEach(function (s) { s.setAttribute('aria-checked', s.getAttribute('data-initial')); });
    form._ctmBase = snapshot(form);
    refreshDirty(form);
  }
  function initDirty(root) {
    root.querySelectorAll('form[data-dirty-form]').forEach(function (form) {
      if (form._ctmBase) return;
      form.querySelectorAll('button.switch[role=switch]').forEach(function (s) { s.setAttribute('data-initial', s.getAttribute('aria-checked')); });
      form._ctmBase = snapshot(form);
      form.addEventListener('input', function () { refreshDirty(form); });
      form.addEventListener('change', function () { refreshDirty(form); });
      form.addEventListener('ctm:switch', function () { refreshDirty(form); });
      form.addEventListener('ctm:saved', function () { form._ctmBase = snapshot(form); refreshDirty(form); });
      form.addEventListener('submit', function () { form._ctmSubmitting = true; });
      var bar = document.getElementById(form.getAttribute('data-dirtybar'));
      if (bar) {
        var discard = bar.querySelector('[data-dirty-discard]');
        if (discard) discard.addEventListener('click', function () { resetDirty(form); toast('Alterações descartadas', { kind: 'info' }); });
      }
    });
  }
  function anyDirty() {
    var f = document.querySelector('form[data-dirty-form].is-dirty');
    return f && !f._ctmSubmitting ? f : null;
  }
  window.addEventListener('beforeunload', function (e) { if (anyDirty()) { e.preventDefault(); e.returnValue = ''; } });
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      var f = anyDirty();
      if (f) { e.preventDefault(); f.requestSubmit(); }
    }
  });
  // Links internos com alterações pendentes: pergunta no dialog #leave-dialog
  var pendingLeave = null;
  function askLeave(onDiscard) {
    var dlg = document.getElementById('leave-dialog');
    if (!dlg) { if (window.confirm('Sair sem salvar?')) onDiscard(); return; }
    pendingLeave = onDiscard;
    dlg.showModal();
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href]');
    if (!a || a.target === '_blank' || a.hasAttribute('download') || a.hasAttribute('data-drawer-url') || a.hasAttribute('data-drawer-open')) return;
    if (a.getAttribute('href').charAt(0) === '#') return;
    var f = anyDirty();
    if (!f || f.closest('dialog')) return;
    e.preventDefault();
    askLeave(function () { f._ctmSubmitting = true; window.location.href = a.href; });
  });
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-leave]');
    if (!b) return;
    var dlg = document.getElementById('leave-dialog');
    var action = b.getAttribute('data-leave');
    if (dlg) dlg.close();
    if (action === 'discard' && pendingLeave) pendingLeave();
    if (action === 'save') { var f = anyDirty(); if (f) f.requestSubmit(); }
    pendingLeave = null;
  });

  /* ---------- 8. Abas ----------
     <div class="tabs" role="tablist" data-tabs data-tabs-param="aba">
       <button type="button" role="tab" class="tab" id="tab-conteudo" aria-controls="panel-conteudo" aria-selected="true" data-tab="conteudo">Conteúdo</button>
     </div>
     <div class="tab-panel" role="tabpanel" id="panel-conteudo" aria-labelledby="tab-conteudo">...</div>
     O servidor marca a aba inicial pelo parâmetro (?aba=materiais). O JS troca sem recarregar e atualiza a URL.
     Setas esquerda/direita navegam entre abas.
  */
  function selectTab(list, tab) {
    list.querySelectorAll('[role=tab]').forEach(function (t) {
      var on = t === tab;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      var panel = document.getElementById(t.getAttribute('aria-controls'));
      if (panel) panel.hidden = !on;
    });
    var param = list.getAttribute('data-tabs-param');
    if (param) { var url = new URL(window.location.href); url.searchParams.set(param, tab.getAttribute('data-tab')); history.replaceState(null, '', url); }
  }
  document.addEventListener('click', function (e) {
    var tab = e.target.closest('[data-tabs] [role=tab]');
    if (tab && tab.tagName === 'BUTTON') selectTab(tab.closest('[data-tabs]'), tab);
  });
  document.addEventListener('keydown', function (e) {
    var tab = e.target.closest('[data-tabs] [role=tab]');
    if (!tab || (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft' && e.key !== 'ArrowDown' && e.key !== 'ArrowUp')) return;
    var tabs = Array.prototype.slice.call(tab.closest('[data-tabs]').querySelectorAll('[role=tab]'));
    var i = tabs.indexOf(tab) + (e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : -1);
    var next = tabs[(i + tabs.length) % tabs.length];
    e.preventDefault(); next.focus(); if (next.tagName === 'BUTTON') selectTab(next.closest('[data-tabs]'), next);
  });

  /* ---------- 9. Liga e desliga ----------
     <button type="button" class="switch" role="switch" aria-checked="true" aria-label="Lembrete de aula ao vivo" data-switch-input="pref_live"></button>
     <input type="hidden" name="pref_live" id="pref_live" value="1">
     Com data-switch-url="/conta/avisos/" o valor é salvo na hora (POST {name: 0|1}) e mostra toast "Preferência salva".
  */
  document.addEventListener('click', function (e) {
    var sw = e.target.closest('button.switch[role=switch]');
    if (!sw) return;
    var on = sw.getAttribute('aria-checked') !== 'true';
    sw.setAttribute('aria-checked', String(on));
    var input = document.getElementById(sw.getAttribute('data-switch-input'));
    if (input) input.value = on ? '1' : '0';
    sw.dispatchEvent(new CustomEvent('ctm:switch', { bubbles: true }));
    var url = sw.getAttribute('data-switch-url');
    if (url && input) {
      var payload = {}; payload[input.name] = input.value;
      post(url, payload).then(function (json) { toast(json.toast || 'Preferência salva'); })
        .catch(function () { sw.setAttribute('aria-checked', String(!on)); input.value = on ? '0' : '1'; toast('Não foi possível salvar. Tente de novo.', { kind: 'error' }); });
    }
  });

  /* ---------- 10. Mostrar senha ----------
     <div class="input-wrap"><input id="new_password1" type="password" class="input"><button type="button" class="input-wrap__btn" data-reveal="new_password1">Mostrar</button></div>
     Regras ao vivo: <ul class="pw-rules" data-pw-rules="new_password1"><li data-rule="len">...</li><li data-rule="mix">...</li><li data-rule="diff" data-diff-from="old_password">...</li></ul>
  */
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-reveal]');
    if (!b) return;
    var input = document.getElementById(b.getAttribute('data-reveal'));
    var show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    b.textContent = show ? 'Ocultar' : 'Mostrar';
    b.setAttribute('aria-pressed', String(show));
  });
  document.addEventListener('input', function (e) {
    var input = e.target;
    if (!input.id) return;
    document.querySelectorAll('[data-pw-rules="' + input.id + '"]').forEach(function (list) {
      var v = input.value;
      list.querySelectorAll('[data-rule]').forEach(function (li) {
        var r = li.getAttribute('data-rule'), ok = false;
        if (r === 'len') ok = v.length >= 8;
        if (r === 'mix') ok = /[a-zA-Z]/.test(v) && /\d/.test(v);
        if (r === 'diff') { var o = document.getElementById(li.getAttribute('data-diff-from')); ok = !!v && (!o || o.value !== v); }
        li.classList.toggle('is-ok', ok);
      });
    });
  });

  /* ---------- 11. Busca global (Ctrl K) ----------
     Botão no topo: <button type="button" class="topbar-search" data-cmdk-open>...</button>
     <dialog class="cmdk" id="cmdk" data-search-url="/busca/" aria-label="Buscar">
       <div class="cmdk__field"><svg .../><input class="cmdk__input" type="search" placeholder="Buscar aula, curso ou dúvida" aria-label="Buscar" autocomplete="off"><span class="kbd">Esc</span></div>
       <div class="cmdk__results" data-cmdk-results role="listbox"></div>
       <div class="cmdk__foot">...</div>
     </dialog>
     A view de busca (GET ?q=) devolve HTML parcial com .cmdk__group e a.cmdk__item (role="option").
     Atalhos: Ctrl+K ou Cmd+K em qualquer lugar; "/" fora de campos de texto.
  */
  var cmdk = document.getElementById('cmdk');
  if (cmdk) {
    var cInput = cmdk.querySelector('.cmdk__input');
    var cResults = cmdk.querySelector('[data-cmdk-results]');
    var cTimer = null, cCtrl = null;
    var openCmdk = function () { if (!cmdk.open) { cmdk.showModal(); cInput.value = ''; load(''); cInput.focus(); } };
    var items = function () { return Array.prototype.slice.call(cResults.querySelectorAll('.cmdk__item')); };
    var mark = function (i) { var list = items(); list.forEach(function (it, n) { it.setAttribute('aria-selected', String(n === i)); }); if (list[i]) list[i].scrollIntoView({ block: 'nearest' }); };
    var load = function (q) {
      if (cCtrl) cCtrl.abort();
      cCtrl = new AbortController();
      fetch(cmdk.getAttribute('data-search-url') + '?q=' + encodeURIComponent(q), { credentials: 'same-origin', signal: cCtrl.signal, headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { return r.text(); })
        .then(function (html) { cResults.innerHTML = html || '<div class="cmdk__empty">Nada encontrado para "' + q.replace(/</g, '') + '".</div>'; mark(0); })
        .catch(function () {});
    };
    document.addEventListener('click', function (e) { if (e.target.closest('[data-cmdk-open]')) { e.preventDefault(); openCmdk(); } });
    document.addEventListener('keydown', function (e) {
      var typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) || document.activeElement.isContentEditable;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openCmdk(); }
      else if (e.key === '/' && !typing && !cmdk.open) { e.preventDefault(); openCmdk(); }
    });
    cInput.addEventListener('input', function () { clearTimeout(cTimer); cTimer = setTimeout(function () { load(cInput.value.trim()); }, 180); });
    cInput.addEventListener('keydown', function (e) {
      var list = items(), cur = list.findIndex(function (it) { return it.getAttribute('aria-selected') === 'true'; });
      if (e.key === 'ArrowDown') { e.preventDefault(); mark(Math.min(list.length - 1, cur + 1)); }
      if (e.key === 'ArrowUp') { e.preventDefault(); mark(Math.max(0, cur - 1)); }
      if (e.key === 'Enter' && list[cur]) { e.preventDefault(); list[cur].click(); }
    });
  }

  /* ---------- 12. Seleção em massa (admin, lista de alunos) ----------
     <form data-bulk data-bulkbar="bulkbar-alunos"> com <input type="checkbox" data-bulk-all aria-label="Selecionar todos">
     e em cada linha <input type="checkbox" name="ids" value="45" data-bulk-item aria-label="Selecionar Jane Student">.
     <div class="bulkbar" id="bulkbar-alunos" hidden><span data-bulk-count></span> ... botões submit com name="action" value="enroll|resend|export|unenroll"
     <button type="button" data-bulk-clear>Limpar seleção</button></div>
  */
  function refreshBulk(form) {
    var items = form.querySelectorAll('[data-bulk-item]');
    var checked = form.querySelectorAll('[data-bulk-item]:checked');
    var all = form.querySelector('[data-bulk-all]');
    if (all) { all.checked = checked.length && checked.length === items.length; all.indeterminate = checked.length > 0 && checked.length < items.length; }
    items.forEach(function (i) { var tr = i.closest('tr'); if (tr) tr.classList.toggle('is-selected', i.checked); });
    var bar = document.getElementById(form.getAttribute('data-bulkbar'));
    if (bar) {
      bar.hidden = checked.length === 0;
      var c = bar.querySelector('[data-bulk-count]');
      if (c) c.textContent = checked.length === 1 ? '1 selecionado' : checked.length + ' selecionados';
    }
  }
  document.addEventListener('change', function (e) {
    var form = e.target.closest('[data-bulk]');
    if (!form) return;
    if (e.target.matches('[data-bulk-all]')) form.querySelectorAll('[data-bulk-item]').forEach(function (i) { i.checked = e.target.checked; });
    refreshBulk(form);
  });
  document.addEventListener('click', function (e) {
    var c = e.target.closest('[data-bulk-clear]');
    if (!c) return;
    var form = document.querySelector('[data-bulkbar="' + c.closest('.bulkbar').id + '"]');
    if (form) { form.querySelectorAll('[data-bulk-item]').forEach(function (i) { i.checked = false; }); refreshBulk(form); }
  });

  /* ---------- 13. Salvamento automático ----------
     <textarea class="textarea" name="notes" data-autosave-url="/painel/alunos/45/anotacoes/"></textarea>
     <span class="autosave-state" data-autosave-state aria-live="polite"></span>
  */
  function initAutosave(root) {
    root.querySelectorAll('[data-autosave-url]').forEach(function (field) {
      if (field._ctmAuto) return;
      field._ctmAuto = true;
      var timer = null;
      var state = field.parentNode.querySelector('[data-autosave-state]');
      field.addEventListener('input', function () {
        clearTimeout(timer);
        if (state) { state.classList.remove('is-saved'); state.classList.add('is-saving'); }
        timer = setTimeout(function () {
          var payload = {}; payload[field.name] = field.value;
          post(field.getAttribute('data-autosave-url'), payload)
            .then(function () { if (state) { state.classList.remove('is-saving'); state.classList.add('is-saved'); } })
            .catch(function () { if (state) state.classList.remove('is-saving'); toast('As anotações não foram salvas. Confira a conexão.', { kind: 'error' }); });
        }, 800);
      });
    });
  }

  /* ---------- 14. Criação rápida ----------
     <div class="inline-create"><input class="input" name="title" placeholder="Título da nova aula e Enter" data-inline-create-url="/painel/modulos/7/aulas/nova/"></div>
     A view cria como rascunho e devolve {"ok":true,"html":"<div class='builder-lesson is-new'...>","open_url":"...","toast":"Aula criada como rascunho"}.
     O JS insere o html antes do campo, limpa o campo e, se vier open_url, abre o painel lateral via um link [data-drawer-url] gerado.
  */
  document.addEventListener('keydown', function (e) {
    var input = e.target.closest('[data-inline-create-url]');
    if (!input || e.key !== 'Enter') return;
    e.preventDefault();
    var title = input.value.trim();
    if (!title) { input.setAttribute('aria-invalid', 'true'); return; }
    input.disabled = true;
    post(input.getAttribute('data-inline-create-url'), { title: title })
      .then(function (json) {
        input.removeAttribute('aria-invalid');
        var holder = input.closest('.inline-create');
        if (json.html) holder.insertAdjacentHTML('beforebegin', json.html);
        input.value = '';
        if (json.toast) toast(json.toast);
        if (json.open_selector) { var link = document.querySelector(json.open_selector); if (link) link.click(); }
      })
      .catch(function (err) { input.setAttribute('aria-invalid', 'true'); toast((err.data && err.data.error) || 'Não foi possível criar.', { kind: 'error' }); })
      .finally(function () { input.disabled = false; input.focus(); });
  });

  /* ---------- 15. Copiar com aviso ----------
     <button type="button" data-copy="https://..." data-copy-toast="Link de verificação copiado">
     (o site.js do v1 já copia; este só mostra o toast)
  */
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-copy-toast]');
    if (b) setTimeout(function () { toast(b.getAttribute('data-copy-toast')); }, 50);
  });

  /* ---------- 16. Dispensar item com Desfazer ----------
     <div class="task" id="step-cpf"> ... <button type="button" class="icon-btn icon-btn--plain" aria-label="Dispensar este aviso"
        data-dismiss-url="/passos/cpf/dispensar/" data-dismiss-target="#step-cpf" data-undo-url="/passos/cpf/restaurar/">
     Esconde o item na hora, POST na URL, toast "Aviso dispensado" com Desfazer (POST na undo-url e mostra o item de novo).
  */
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-dismiss-url]');
    if (!b) return;
    var target = document.querySelector(b.getAttribute('data-dismiss-target'));
    if (target) target.hidden = true;
    post(b.getAttribute('data-dismiss-url')).then(function () {
      toast('Aviso dispensado', { undo: function () { post(b.getAttribute('data-undo-url')).then(function () { if (target) target.hidden = false; }); } });
    }).catch(function () { if (target) target.hidden = false; toast('Não foi possível dispensar.', { kind: 'error' }); });
  });

  /* ---------- 17. Espelhar texto (prévia do certificado) ----------
     <input name="full_name" data-mirror="#preview-name" data-mirror-upper>  ->  <strong id="preview-name">JANE STUDENT</strong>
     <input name="cpf" data-mirror="#preview-cpf" data-mirror-cpf>          ->  <span id="preview-cpf">***.456.789-**</span>
  */
  document.addEventListener('input', function (e) {
    var input = e.target.closest('[data-mirror]');
    if (!input) return;
    var out = document.querySelector(input.getAttribute('data-mirror'));
    if (!out) return;
    var v = input.value.trim();
    if (input.hasAttribute('data-mirror-upper')) v = v.toUpperCase();
    if (input.hasAttribute('data-mirror-cpf')) {
      var d = v.replace(/\D/g, '');
      v = d.length === 11 ? '***.' + d.substr(3, 3) + '.' + d.substr(6, 3) + '-**' : '***.***.***-**';
    }
    out.textContent = v || out.getAttribute('data-empty') || '';
  });

  /* ---------- 18. Habilitar no horário ----------
     <a class="btn btn--primary" aria-disabled="true" data-enable-at="2026-11-12T23:45:00Z" data-enabled-href="https://meet.google.com/...">
     A cada 30 s confere o relógio; na hora, troca aria-disabled por href, tira o ícone [data-lock-icon] e recarrega a dica [data-enable-hint] com o texto de data-enabled-hint.
  */
  function checkEnableAt() {
    document.querySelectorAll('[data-enable-at]').forEach(function (el) {
      if (Date.now() < Date.parse(el.getAttribute('data-enable-at'))) return;
      el.removeAttribute('aria-disabled');
      el.removeAttribute('data-enable-at');
      if (el.getAttribute('data-enabled-href')) { el.href = el.getAttribute('data-enabled-href'); el.target = '_blank'; el.rel = 'noopener'; }
      var lock = el.querySelector('[data-lock-icon]'); if (lock) lock.remove();
      var hint = document.querySelector('[data-enable-hint]');
      if (hint && hint.getAttribute('data-enabled-hint')) hint.textContent = hint.getAttribute('data-enabled-hint');
    });
  }
  if (document.querySelector('[data-enable-at]')) { checkEnableAt(); setInterval(checkEnableAt, 30000); }
  document.addEventListener('click', function (e) {
    var dis = e.target.closest('a[aria-disabled="true"]');
    if (dis) e.preventDefault();
  });

  /* ---------- 19. Sugestões ao digitar o título (nova pergunta) ----------
     <input name="title" data-suggest-url="/community/sugestoes/" data-suggest-box="#suggest-box">
     <div class="suggest-box" id="suggest-box" hidden></div>
     Ao parar de digitar (500 ms, mínimo 8 letras) busca GET ?q= e coloca o HTML na caixa. Resposta vazia esconde a caixa.
  */
  var sTimer = null;
  document.addEventListener('input', function (e) {
    var input = e.target.closest('[data-suggest-url]');
    if (!input) return;
    clearTimeout(sTimer);
    var box = document.querySelector(input.getAttribute('data-suggest-box'));
    sTimer = setTimeout(function () {
      var q = input.value.trim();
      if (q.length < 8 || !box) { if (box) box.hidden = true; return; }
      fetch(input.getAttribute('data-suggest-url') + '?q=' + encodeURIComponent(q), { credentials: 'same-origin', headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { return r.text(); })
        .then(function (html) { box.innerHTML = html; box.hidden = !html.trim(); })
        .catch(function () {});
    }, 500);
  });

  function initWithin(root) { initDirty(root); initAutosave(root); }
  initWithin(document);

  window.CTM = { toast: toast, post: post, csrf: csrf, plural: plural, applyResponse: applyResponse, openDrawer: openDrawer, closeDrawer: closeDrawer, initWithin: initWithin };
})();
