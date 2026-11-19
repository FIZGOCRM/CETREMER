(() => {
  const workspace = document.querySelector('.course-workspace');
  if (!workspace) return;
  workspace.querySelectorAll('.course-form').forEach(form => {
    form.querySelectorAll('textarea').forEach(field => field.classList.add('gp-textarea'));
    form.querySelectorAll('select').forEach(field => field.classList.add('gp-select'));
    form.querySelectorAll('input:not([type]),input[type=text],input[type=url],input[type=number]').forEach(field => field.classList.add('gp-input'));
  });
  const confirmations = workspace.querySelectorAll('[data-course-confirm]');
  let confirmation;
  if (confirmations.length) {
    confirmation = document.createElement('dialog');
    confirmation.className = 'gp-dialog';
    confirmation.setAttribute('aria-labelledby', 'course-confirm-title');
    confirmation.innerHTML = '<h2 class="gp-dialog__head" id="course-confirm-title"></h2><p class="gp-dialog__body"></p><div class="gp-dialog__foot"><button class="btn" type="button" data-gp-close>Cancelar</button><button class="btn btn--danger-solid" type="button"></button></div>';
    workspace.append(confirmation);
    confirmation.addEventListener('close', () => confirmation.opener?.focus());
    confirmation.querySelector('.btn--danger-solid').addEventListener('click', () => {
      const button = confirmation.opener;
      confirmation.close();
      button.form.requestSubmit(button);
    });
  }
  confirmations.forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      confirmation.opener = button;
      confirmation.querySelector('h2').textContent = button.dataset.courseConfirm;
      confirmation.querySelector('p').textContent = button.dataset.courseImpact || 'A alteração será aplicada ao curso.';
      confirmation.querySelector('.btn--danger-solid').textContent = button.textContent.trim() || 'Remover PDF';
      confirmation.showModal();
      confirmation.querySelector('[data-gp-close]').focus();
    });
  });
  workspace.querySelectorAll('input[form="lesson-add-pdf"]').forEach(input => {
    for (const type of ['change', 'input']) input.addEventListener(type, event => event.stopPropagation());
  });
  const newQuestion = workspace.querySelector('[data-course-new-question]');
  newQuestion?.addEventListener('click', () => { location.search = '?nova=1'; });
  workspace.querySelectorAll('[data-gp-sortable]').forEach(list => {
    new MutationObserver(() => {
      Array.from(list.children).forEach((row, index) => {
        const label = row.querySelector('[data-item-position]');
        if (label) label.textContent = index + 1;
      });
    }).observe(list, {childList:true});
  });
  const form = workspace.querySelector('#new-course');
  if (!form) return;
  const cover = form.querySelector('#course-preview .course-cover');
  const preview = form.querySelector('[data-preview-title]');
  let imageUrl;
  function paint() {
    const title = form.elements.title.value || 'Nome do curso';
    const category = form.elements.category.selectedOptions[0];
    cover.querySelector('.gp-cover__title').textContent = title;
    cover.querySelector('.gp-cover__cat').textContent = category?.value ? category.textContent : 'Formação';
    cover.dataset.category = category?.textContent.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/\s+/g, '-');
    cover.dataset.color = form.elements.cover_color.value;
    preview.textContent = title;
  }
  form.addEventListener('input', paint);
  form.addEventListener('change', event => {
    paint();
    if (event.target.name !== 'cover_image') return;
    cover.querySelector('.course-cover-image')?.remove();
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    if (!event.target.files.length) return;
    const img = document.createElement('img');
    img.className = 'course-cover-image';
    img.alt = '';
    imageUrl = URL.createObjectURL(event.target.files[0]);
    img.src = imageUrl;
    cover.append(img);
  });
  paint();
})();
