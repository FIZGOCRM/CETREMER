/* Fetch authorized server markup; normal links remain usable without JS. */
(() => {
  'use strict';
  let loading = false;
  document.querySelectorAll('[data-course-dialog]').forEach(link => link.addEventListener('click', async event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || !HTMLDialogElement.prototype.showModal) return;
    event.preventDefault();
    if (loading) return;
    loading = true;
    link.setAttribute('aria-busy', 'true');
    try {
      const response = await fetch(link.href, { credentials: 'same-origin', headers: { Accept: 'text/html' } });
      if (!response.ok || response.redirected) { location.assign(link.href); return; }
      const parsed = new DOMParser().parseFromString(await response.text(), 'text/html');
      const detail = parsed.querySelector('[data-course-detail]');
      if (!detail) { location.assign(link.href); return; }
      const dialog = document.createElement('dialog');
      dialog.className = 'member-dialog';
      dialog.setAttribute('aria-label', detail.querySelector('h1').textContent);
      const close = document.createElement('button');
      close.className = 'rbtn member-dialog-close'; close.type = 'button';
      close.setAttribute('aria-label', 'Fechar informações do curso'); close.append(document.getElementById('dialog-close-icon').content.cloneNode(true));
      const toolbar = document.createElement('div');
      toolbar.className = 'member-dialog-toolbar';
      const expand = document.createElement('button');
      expand.className = 'btn btn--outline btn--sm member-dialog-expand';
      expand.type = 'button'; expand.textContent = 'Expandir janela';
      expand.setAttribute('aria-pressed', 'false');
      expand.addEventListener('click', () => {
        const expanded = dialog.classList.toggle('is-expanded');
        expand.textContent = expanded ? 'Recolher janela' : 'Expandir janela';
        expand.setAttribute('aria-pressed', String(expanded));
      });
      const fullPage = document.createElement('a');
      fullPage.className = 'btn btn--dim btn--sm';
      fullPage.href = link.href; fullPage.textContent = 'Página do curso';
      toolbar.append(fullPage, expand, close);
      dialog.append(toolbar, document.importNode(detail, true));
      document.getElementById('modal-root').append(dialog);
      close.addEventListener('click', () => dialog.close());
      dialog.addEventListener('click', e => { if (e.target === dialog) { const r = dialog.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close(); } });
      dialog.addEventListener('close', () => { dialog.remove(); document.body.classList.remove('has-modal'); link.focus(); });
      document.body.classList.add('has-modal'); dialog.showModal();
    } catch { location.assign(link.href); }
    finally { loading = false; link.removeAttribute('aria-busy'); }
  }));
})();
