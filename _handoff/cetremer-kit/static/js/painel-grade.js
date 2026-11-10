/* CETREMER · reordenar aulas e módulos por arrastar (admin, tela "Aulas do curso").
   Carregar só em painel/course_lessons.html.
   Contrato:
   - container [data-reorder-url] com os módulos <section data-module-id draggable="true">
   - cada lista de aulas <ul class="module__list" data-module-id> com <li class="builder-lesson" data-lesson-id draggable="true">
   - arrasta pela alça .drag-handle; ao soltar, envia POST JSON para data-reorder-url:
       {"modules": [<module_id>, ...], "lessons": {"<module_id>": [<lesson_id>, ...], ...}}
   - o backend regrava Module.order e Lesson.order (1..n dentro de cada módulo) e Lesson.module (aula pode mudar de módulo)
   - teclado: a alça é um <button>; setas para cima/baixo movem o item e salvam
*/
(function () {
  'use strict';
  var root = document.querySelector('[data-reorder-url]');
  if (!root) return;

  function csrfToken() {
    var field = document.querySelector('[name=csrfmiddlewaretoken]');
    return field ? field.value : '';
  }

  function save() {
    var payload = { modules: [], lessons: {} };
    root.querySelectorAll('[data-module-id][draggable]').forEach(function (section) {
      payload.modules.push(Number(section.getAttribute('data-module-id')));
    });
    root.querySelectorAll('ul.module__list[data-module-id]').forEach(function (list) {
      payload.lessons[list.getAttribute('data-module-id')] = Array.prototype.map.call(
        list.querySelectorAll('[data-lesson-id]'), function (li) { return Number(li.getAttribute('data-lesson-id')); }
      );
    });
    return fetch(root.getAttribute('data-reorder-url'), {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify(payload)
    });
  }

  var dragged = null;

  root.addEventListener('dragstart', function (e) {
    var item = e.target.closest('[draggable="true"]');
    if (!item) return;
    dragged = item;
    item.classList.add('is-dragging');
    e.dataTransfer.effectAllowed = 'move';
  });

  root.addEventListener('dragend', function () {
    if (dragged) dragged.classList.remove('is-dragging');
    dragged = null;
    save();
  });

  root.addEventListener('dragover', function (e) {
    if (!dragged) return;
    var isLesson = dragged.hasAttribute('data-lesson-id');
    var target = isLesson ? e.target.closest('[data-lesson-id]') : e.target.closest('section[data-module-id]');
    var list = isLesson ? e.target.closest('ul.module__list') : root;
    if (!list) return;
    e.preventDefault();
    if (!target || target === dragged) {
      if (isLesson && !list.querySelector('[data-lesson-id]')) list.appendChild(dragged);
      return;
    }
    var rect = target.getBoundingClientRect();
    var after = (e.clientY - rect.top) > rect.height / 2;
    target.parentNode.insertBefore(dragged, after ? target.nextSibling : target);
  });

  root.addEventListener('keydown', function (e) {
    var handle = e.target.closest('.drag-handle');
    if (!handle || (e.key !== 'ArrowUp' && e.key !== 'ArrowDown')) return;
    e.preventDefault();
    var item = handle.closest('[draggable="true"]');
    var sibling = e.key === 'ArrowUp' ? item.previousElementSibling : item.nextElementSibling;
    if (!sibling || !sibling.hasAttribute('draggable')) return;
    item.parentNode.insertBefore(item, e.key === 'ArrowUp' ? sibling : sibling.nextSibling);
    handle.focus();
    save();
  });
})();
