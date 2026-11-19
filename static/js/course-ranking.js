(() => {
  const weekPicker = document.querySelector('[data-week-picker]');
  weekPicker?.addEventListener('change', () => weekPicker.requestSubmit());
  const form = document.querySelector('#weekly-ranking');
  if (!form) return;

  const library = JSON.parse(document.querySelector('#ranking-data').textContent);
  const byId = new Map(library.map(lesson => [lesson.id, lesson]));
  const slots = Array.from(form.querySelectorAll('[data-ranking-slot]'));
  const initial = slots.map(slot => byId.has(slot.dataset.initial) ? slot.dataset.initial : '');
  let selection = [...initial];
  const art = new Map();
  const dialog = document.querySelector('#ranking-art');
  const status = form.querySelector('[data-ranking-status]');
  let dragged = null;

  function node(tag, className, text) {
    const element = document.createElement(tag);
    element.className = className;
    if (text) element.textContent = text;
    return element;
  }
  function button(text, label, action) {
    const element = node('button', 'btn btn--sm', text);
    element.type = 'button';
    element.setAttribute('aria-label', label);
    element.addEventListener('click', action);
    return element;
  }
  function controls(id, position) {
    if (!art.has(id)) {
      const wrapper = node('div', 'gp-rail');
      const uploadLabel = node('label', 'gp-dropzone', 'Escolher imagem');
      const upload = node('input', '');
      upload.type = 'file';
      upload.accept = 'image/*';
      upload.setAttribute('form', form.id);
      uploadLabel.append(upload);
      wrapper.append(uploadLabel);
      const clear = node('input', '');
      clear.type = 'checkbox';
      clear.setAttribute('form', form.id);
      const clearLabel = node('label', 'gp-check');
      clearLabel.append(clear, ' Remover arte atual');
      clearLabel.hidden = !byId.get(id).art;
      wrapper.append(clearLabel);
      const hint = node('p', 'gp-help');
      wrapper.append(hint);
      wrapper.addEventListener('change', () => {
        hint.textContent = upload.files[0]?.name || '';
        if (upload.files.length) clear.checked = false;
        form.dispatchEvent(new Event('input', {bubbles: true}));
      });
      art.set(id, {wrapper, upload, clear});
    }
    const control = art.get(id);
    control.upload.name = 'art_' + position;
    control.clear.name = 'art_' + position + '-clear';
    return control;
  }
  function updateLibrary() {
    const query = form.querySelector('[data-ranking-search]').value.trim().toLocaleLowerCase();
    let visible = 0;
    form.querySelectorAll('[data-library-id]').forEach(row => {
      const lesson = byId.get(row.dataset.libraryId);
      row.hidden = selection.includes(lesson.id) || !(lesson.title + ' ' + lesson.module).toLocaleLowerCase().includes(query);
      row.querySelector('button').disabled = selection.every(Boolean);
      if (!row.hidden) visible++;
    });
    form.querySelector('[data-library-empty]').hidden = visible > 0;
  }
  function render() {
    slots.forEach((slot, index) => {
      const id = selection[index];
      const lesson = byId.get(id);
      const box = slot.querySelector('[data-slot-content]');
      box.replaceChildren();
      slot.classList.toggle('is-filled', Boolean(lesson));
      const field = node('input', '');
      field.type = 'hidden';
      field.name = 'lesson_' + (index + 1);
      field.value = id;
      box.append(field);
      if (!lesson) {
        box.append(node('span', 'gp-help', 'Posição livre · arraste uma aula da lista ao lado'));
        return;
      }
      const handle = button('⠿', 'Mover ' + lesson.title + '. Use as setas para cima e para baixo.', () => {});
      handle.classList.add('gp-handle');
      handle.draggable = true;
      handle.addEventListener('dragstart', event => {
        dragged = {from:index};
        event.dataTransfer.setData('text/plain', id);
      });
      handle.addEventListener('keydown', event => {
        if (!['ArrowUp', 'ArrowDown'].includes(event.key)) return;
        event.preventDefault();
        const to = index + (event.key === 'ArrowUp' ? -1 : 1);
        if (to < 0 || to >= slots.length) return;
        move(index, to);
        slots[to].querySelector('.gp-handle').focus();
      });
      const poster = node('span', 'ranking-poster');
      const source = lesson.art || lesson.cover;
      if (source) {
        const image = node('img', '');
        image.src = source;
        image.alt = '';
        poster.append(image);
      }
      const info = node('span', 'gp-list__body');
      info.append(node('strong', 'gp-list__title', lesson.title),
        node('span', 'gp-help', lesson.module + ' · ' + lesson.started + ' iniciaram' +
          (lesson.average === null ? '' : ' · avanço médio ' + lesson.average + '%')));
      const control = controls(id, index + 1);
      control.wrapper.hidden = true;
      const artwork = button('Arte 2:3', 'Editar arte de ' + lesson.title, () => {
        control.wrapper.hidden = false;
        dialog.querySelector('[data-ranking-art-control]').replaceChildren(control.wrapper);
        dialog.addEventListener('close', () => {
          control.wrapper.hidden = true;
          box.append(control.wrapper);
          artwork.focus();
        }, {once:true});
      });
      artwork.dataset.gpOpen = '#ranking-art';
      const remove = button('×', 'Remover ' + lesson.title + ' do Top 10', () => {
        selection[index] = '';
        art.delete(id);
        changed('Aula removida.');
        form.querySelector('[data-ranking-search]').focus();
      });
      box.append(handle, poster, info, artwork, remove, control.wrapper);
    });
    form.querySelector('[data-ranking-count]').textContent = selection.filter(Boolean).length;
    updateLibrary();
  }
  function changed(message) {
    render();
    status.textContent = message;
    form.dispatchEvent(new Event('input', {bubbles:true}));
  }
  function move(from, to) {
    if (from === to) return;
    if (selection[to]) {
      const [id] = selection.splice(from, 1);
      selection.splice(to, 0, id);
    } else {
      selection[to] = selection[from];
      selection[from] = '';
    }
    changed('Ordem alterada. Salve o Top 10 para confirmar.');
  }
  form.querySelector('[data-ranking-fill]').addEventListener('click', () => {
    const available = library.filter(item => !selection.includes(item.id));
    const next = selection.map(id => id || available.shift()?.id || '');
    if (next.some((id, i) => id !== selection[i])) {
      selection = next;
      changed('Posições livres preenchidas pelo engajamento.');
    }
  });
  const search = form.querySelector('[data-ranking-search]');
  search.addEventListener('input', event => {event.stopPropagation(); updateLibrary();});
  search.addEventListener('change', event => event.stopPropagation());
  search.addEventListener('keydown', event => {if (event.key === 'Enter') event.preventDefault();});
  form.querySelectorAll('[data-library-id]').forEach(row => {
    const id = row.dataset.libraryId;
    row.querySelector('button').addEventListener('click', () => {
      const index = selection.indexOf('');
      if (index < 0 || selection.includes(id)) return;
      selection[index] = id;
      changed('Aula adicionada à posição ' + (index + 1) + '.');
      slots[index].querySelector('.gp-handle').focus();
    });
    row.addEventListener('dragstart', event => {
      dragged = {id};
      event.dataTransfer.setData('text/plain', id);
    });
  });
  document.addEventListener('dragend', () => { dragged = null; });
  slots.forEach((slot, index) => {
    slot.addEventListener('dragover', event => {
      if (dragged) event.preventDefault();
    });
    slot.addEventListener('drop', event => {
      event.preventDefault();
      if (!dragged) return;
      if (dragged.from !== undefined) move(dragged.from, index);
      else if (!selection.includes(dragged.id)) {
        if (selection[index]) {
          const empty = selection.indexOf('');
          if (empty >= 0) selection[empty] = selection[index];
          else art.delete(selection[index]);
        }
        selection[index] = dragged.id;
        changed('Aula adicionada à posição ' + (index + 1) + '.');
      }
      dragged = null;
    });
  });
  form.addEventListener('gp:reset', () => {
    selection = [...initial];
    art.clear();
    render();
    status.textContent = 'Seleção restaurada.';
  });
  render();
})();
