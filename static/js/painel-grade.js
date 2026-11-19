(() => {
  const root = document.querySelector('[data-reorder-url]');
  if (!root) return;
  const status = document.querySelector('[data-order-status]');
  const key = 'gp-modules-' + root.dataset.course;
  const modules = () => Array.from(root.children).filter(item => item.matches('section[data-module-id]'));
  const buttons = Array.from(root.querySelectorAll('[data-module-toggle]'));
  let preferences = {};
  try { preferences = JSON.parse(localStorage.getItem(key)) || {}; } catch {}
  function expand(button, open) {
    button.setAttribute('aria-expanded', String(open));
    document.getElementById(button.getAttribute('aria-controls')).hidden = !open;
    const expandAll = document.querySelector('[data-expand-modules]');
    expandAll.textContent = buttons.every(item => item.getAttribute('aria-expanded') === 'true') ? 'Recolher tudo' : 'Expandir tudo';
  }
  function remember(button, open) {
    expand(button, open);
    preferences[button.getAttribute('aria-controls')] = open;
    try { localStorage.setItem(key, JSON.stringify(preferences)); } catch {}
  }
  buttons.forEach(button => {
    const saved = preferences[button.getAttribute('aria-controls')];
    expand(button, typeof saved === 'boolean' ? saved : button.getAttribute('aria-expanded') === 'true');
    button.addEventListener('click', () => remember(button, button.getAttribute('aria-expanded') !== 'true'));
  });
  document.querySelector('[data-expand-modules]').addEventListener('click', () => {
    const open = buttons.some(button => button.getAttribute('aria-expanded') !== 'true');
    buttons.forEach(button => remember(button, open));
  });

  function snapshot() {
    return modules().map(module => {
      const list = module.querySelector('ul.module__list');
      return {module, list, lessons:Array.from(list.children)};
    });
  }
  function displayOrder() {
    modules().forEach((module, index) => {
      module.querySelector('.gp-module__num').textContent = index + 1;
      const hint = module.querySelector('.gp-module__head .gp-help');
      const count = module.querySelectorAll('[data-lesson-id]').length;
      hint.textContent = hint.textContent.split(' · ')[0] + ' · ' + count + (count === 1 ? ' aula' : ' aulas');
    });
  }
  function payload(order) {
    return {
      modules:order.map(row => Number(row.module.dataset.moduleId)),
      lessons:Object.fromEntries(order.map(row => [row.module.dataset.moduleId, row.lessons.map(item => Number(item.dataset.lessonId))])),
    };
  }
  let saving = false;
  async function save(before) {
    const next = payload(snapshot());
    if (JSON.stringify(next) === JSON.stringify(payload(before))) return;
    saving = true;
    status.textContent = 'Salvando ordem…';
    try {
      const response = await fetch(root.dataset.reorderUrl, {
        method:'POST', credentials:'same-origin',
        headers:{'Content-Type':'application/json', 'X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]').value},
        body:JSON.stringify(next),
      });
      if (!response.ok || !(await response.json()).ok) throw Error();
      status.textContent = 'Ordem salva.';
    } catch {
      before.forEach(({module, list, lessons}) => {
        root.append(module);
        lessons.forEach(item => list.append(item));
      });
      status.textContent = 'Não foi possível salvar a nova ordem. Tente de novo.';
    } finally {
      saving = false;
      displayOrder();
      window.gpToast?.(status.textContent);
    }
  }
  let armed = null;
  let dragging = null;
  let before = null;
  root.addEventListener('pointerdown', event => {
    armed = event.target.closest('.drag-handle')?.closest('[draggable=true]');
  });
  root.addEventListener('dragstart', event => {
    if (saving || event.target.closest('[draggable=true]') !== armed) {
      event.preventDefault();
      return;
    }
    dragging = armed;
    before = snapshot();
    dragging.classList.add('gp-sortable-ghost');
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', 'course-order');
  });
  function destination(event) {
    if (!dragging) return null;
    if (dragging.hasAttribute('data-lesson-id')) {
      const list = event.target.closest('.module__list');
      return list && {parent:list, target:event.target.closest('[data-lesson-id]')};
    }
    const module = event.target.closest('section[data-module-id]');
    return module && {parent:root, target:module};
  }
  root.addEventListener('dragover', event => { if (destination(event)) event.preventDefault(); });
  root.addEventListener('drop', event => {
    const dest = destination(event);
    if (!dest) return;
    event.preventDefault();
    if (dest.target === dragging) return;
    const rect = dest.target?.getBoundingClientRect();
    const insert = rect && event.clientY > rect.top + rect.height / 2 ? dest.target.nextSibling : dest.target;
    dest.parent.insertBefore(dragging, insert || null);
    save(before);
  });
  root.addEventListener('dragend', () => {
    dragging?.classList.remove('gp-sortable-ghost');
    dragging = null;
    armed = null;
  });
  root.addEventListener('keydown', event => {
    const handle = event.target.closest('.drag-handle');
    if (!handle || saving || !['ArrowUp', 'ArrowDown'].includes(event.key)) return;
    event.preventDefault();
    const item = handle.closest('[draggable=true]');
    const previous = snapshot();
    const up = event.key === 'ArrowUp';
    const neighbor = up ? item.previousElementSibling : item.nextElementSibling;
    if (neighbor?.matches('[draggable=true]')) {
      item.parentElement.insertBefore(item, up ? neighbor : neighbor.nextSibling);
    } else if (item.hasAttribute('data-lesson-id')) {
      const groups = modules();
      const target = groups[groups.indexOf(item.closest('section[data-module-id]')) + (up ? -1 : 1)];
      if (!target) return;
      remember(target.querySelector('[data-module-toggle]'), true);
      const list = target.querySelector('ul.module__list');
      list.insertBefore(item, up ? null : list.firstElementChild);
    } else return;
    handle.focus();
    save(previous);
  });
})();
