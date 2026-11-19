(() => {
  function styleFields(root) {
    root.querySelectorAll('main :is(input,textarea,select), dialog :is(input,textarea,select)').forEach(field => {
      if (field.matches('select')) {
        field.classList.add('gp-select');
        for (const opt of field.options) if (/^-{3,}$/.test(opt.text)) opt.text = 'Escolha…';
      } else if (field.matches('textarea')) field.classList.add('gp-textarea');
      else if (field.type === 'file' && !field.closest('.gp-dropzone')) {
        const zone = document.createElement('span');
        zone.className = 'gp-dropzone'; zone.dataset.gpDropzone = '';
        const hint = document.createElement('span'); hint.className = 'gp-dropzone__hint';
        hint.textContent = 'Escolher arquivo ou arrastar aqui';
        field.before(zone); zone.append(hint, field);
        field.addEventListener('change', () => { hint.textContent = field.files[0]?.name || 'Escolher arquivo'; });
      } else if (!['checkbox','radio','file','submit','hidden','color'].includes(field.type)) field.classList.add('gp-input');
    });
  }
  styleFields(document);
  document.querySelectorAll('select[data-plan-months]').forEach(select => {
    const {starts_on: start, last_day: last} = select.form.elements;
    function calculate() {
      if (!start.value || !select.value || !last) return;
      const [year, month, day] = start.value.split('-').map(Number);
      const endMonth = month - 1 + Number(select.selectedOptions[0].dataset.months);
      const maxDay = new Date(Date.UTC(year, endMonth + 1, 0)).getUTCDate();
      const end = new Date(Date.UTC(year, endMonth, Math.min(day, maxDay) - 1));
      last.value = end.toISOString().slice(0,10);
    }
    select.addEventListener('change', calculate); start.addEventListener('change', calculate);
  });
  document.addEventListener('submit', event => {
    const button = event.submitter;
    const question = button?.dataset.actionConfirm || event.target.dataset.actionConfirm;
    if (question && !window.confirm(question)) event.preventDefault();
  });
  document.querySelectorAll('form[method="get" i]').forEach(form => {
    if (form.closest('.gp-topbar') || form.hasAttribute('data-gp-autofilter')) return;
    const action = form.querySelector('button:not([type]),button[type=submit],input[type=submit]');
    if (!action || !/^(Filtrar|Buscar|Atualizar|Aplicar filtros)$/i.test(action.textContent.trim() || action.value || '')) return;
    form.dataset.gpAutofilter = '';
    action.hidden = true;
  });
})();
