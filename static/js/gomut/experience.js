(() => {
  const requests = new Set();
  let shelfVersion = 0;
  function enableShelfNavigation(shelf) {
    const frame = document.createElement('div');
    frame.className = 'xp-shelf-frame';
    shelf.before(frame);
    frame.append(shelf);
    const heading = frame.closest('section').querySelector('h2').textContent.trim();
    function addArrow(next) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'xp-shelf-arrow xp-shelf-arrow--' + (next ? 'next' : 'prev');
      button.textContent = next ? '›' : '‹';
      button.setAttribute('aria-label', heading + (next ? ' · Avançar' : ' · Voltar'));
      button.addEventListener('click', () => {
        const step = shelf.firstElementChild.getBoundingClientRect().width + parseFloat(getComputedStyle(shelf).columnGap);
        const count = Math.max(1, Math.floor(shelf.clientWidth / step));
        shelf.scrollBy({left: (next ? 1 : -1) * step * count,
          behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
      });
      frame.append(button);
      return button;
    }
    const previous = addArrow(false);
    const next = addArrow(true);
    function update() {
      previous.hidden = shelf.scrollLeft <= 1;
      next.hidden = shelf.scrollLeft + shelf.clientWidth >= shelf.scrollWidth - 1;
    }
    shelf.addEventListener('scroll', update, {passive: true});
    new ResizeObserver(update).observe(shelf);
    new MutationObserver(update).observe(shelf, {childList: true});
    update();
  }
  document.querySelectorAll('.xp-body .xp-shelf').forEach(enableShelfNavigation);
  function announce(text) {
    document.querySelector('#toasts').textContent = text;
  }
  async function refreshSavedShelf(restoreFocus) {
    const shelf = document.querySelector('[data-saved-list]');
    if (!shelf) return;
    const version = ++shelfVersion;
    const response = await fetch(shelf.dataset.savedList);
    if (!response.ok) throw new Error();
    const page = new DOMParser().parseFromString(await response.text(), 'text/html');
    const updated = page.querySelector('[data-saved-list]');
    if (!updated || version !== shelfVersion) return;
    const cards = [...updated.children];
    const limit = Number(shelf.dataset.limit) || cards.length;
    shelf.replaceChildren(...cards.slice(0, limit));
    const empty = document.querySelector('[data-saved-empty]');
    empty.hidden = cards.length > 0;
    if (restoreFocus) (shelf.querySelector('button') || empty).focus();
  }
  document.addEventListener('submit', async event => {
    const form = event.target.closest('[data-save], [data-reminder]');
    if (!form || event.defaultPrevented || document.body.dataset.memberPreview) return;
    event.preventDefault();
    if (requests.has(form.action)) return;
    requests.add(form.action);
    const button = form.querySelector('button');
    const token = form.elements.csrfmiddlewaretoken.value;
    button.disabled = true;
    try {
      const response = await fetch(form.action, {
        method: 'POST', body: new FormData(form),
        headers: {'X-CSRFToken': token, 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}
      });
      if (!response.ok) throw new Error();
      const {active} = await response.json();
      if (typeof active !== 'boolean') throw new Error();
      if (form.hasAttribute('data-save')) {
        const peers = [...document.querySelectorAll('[data-save]')].filter(peer => peer.dataset.save === form.dataset.save);
        peers.forEach(peer => {
          peer.querySelector('button').setAttribute('aria-pressed', String(active));
          peer.elements.active.value = String(!active);
          peer.querySelector('[data-state]').textContent = active ? '✓ Na minha lista' : '+ Minha lista';
        });
        announce(active ? 'Aula adicionada à sua lista.' : 'Aula removida da sua lista.');
        await refreshSavedShelf(Boolean(form.closest('[data-saved-list]')));
      } else {
        button.setAttribute('aria-pressed', String(active));
        button.querySelector('[data-state]').textContent = active ? '✓ Lembrete ativado' : 'Lembrar-me';
        announce(active ? 'Lembrete ativado.' : 'Lembrete removido.');
      }
    } catch {
      announce('Não foi possível atualizar a tela. Recarregue para conferir.');
    } finally {
      button.disabled = false;
      requests.delete(form.action);
    }
  });
})();
