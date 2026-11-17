/* Progressive enhancement; account and course state stay on the server. */
(() => {
  'use strict';
  const dropdowns = [...document.querySelectorAll('[data-dropdown]')];
  function closeMenus(except) {
    dropdowns.forEach(button => {
      if (button === except) return;
      button.setAttribute('aria-expanded', 'false');
      button.closest('.dd').classList.remove('is-open');
    });
  }
  dropdowns.forEach(button => button.addEventListener('click', () => {
    const open = button.getAttribute('aria-expanded') !== 'true';
    closeMenus(button);
    button.setAttribute('aria-expanded', String(open));
    button.closest('.dd').classList.toggle('is-open', open);
  }));
  document.addEventListener('click', event => { if (!event.target.closest('.dd')) closeMenus(); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      const open = dropdowns.find(button => button.getAttribute('aria-expanded') === 'true');
      closeMenus();
      if (open) open.focus();
    }
  });
  const nav = document.getElementById('nav');
  if (nav) {
    const solid = () => nav.classList.toggle('is-solid', scrollY > 12 || !document.querySelector('.hero'));
    addEventListener('scroll', solid, { passive: true }); solid();
  }
  const search = document.getElementById('member-search');
  const toggle = document.querySelector('[data-search-toggle]');
  if (search && toggle) {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      search.closest('.search').classList.toggle('is-open', open);
      search.tabIndex = open ? 0 : -1;
      if (open) search.focus();
    });
    search.addEventListener('input', () => {
      const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
      const cards = [...document.querySelectorAll('[data-course-card]')];
      const term = normalize(search.value.trim());
      cards.forEach(card => { card.hidden = !normalize(card.dataset.searchText).includes(term); });
      const empty = document.getElementById('search-empty');
      if (empty) empty.hidden = cards.some(card => !card.hidden) || !cards.length;
      if (cards.length && term) document.getElementById('meus-cursos').scrollIntoView({ block: 'start' });
    });
  }
  document.querySelectorAll('[data-tab]').forEach(tab => tab.addEventListener('click', () => {
    const group = tab.closest('[data-tabs]');
    group.querySelectorAll('[data-tab]').forEach(button => {
      const selected = button === tab;
      button.classList.toggle('is-on', selected);
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
      document.getElementById(button.getAttribute('aria-controls')).hidden = !selected;
    });
  }));
  document.querySelectorAll('[data-tabs]').forEach(group => group.addEventListener('keydown', event => {
    const buttons = [...group.querySelectorAll('[data-tab]')];
    const index = buttons.indexOf(document.activeElement);
    if (index < 0 || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length;
    buttons[next].click(); buttons[next].focus();
  }));
})();
