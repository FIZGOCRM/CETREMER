/* Certificados — impressão nativa, sem serviço externo de PDF. */
(() => {
  'use strict';
  const status = document.querySelector('[data-copy-status]');
  document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
    if (status) status.textContent = '';
    try {
      if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(button.dataset.copy);
      else { const field = document.createElement('textarea'); field.value = button.dataset.copy; document.body.append(field); field.select(); if (!document.execCommand('copy')) throw new Error(); field.remove(); }
      if (status) status.textContent = 'Copiado.';
    } catch (error) { if (status) status.textContent = 'Não foi possível copiar automaticamente. Selecione o código ou link no certificado.'; }
  }));
  document.querySelectorAll('[data-print]').forEach(button => button.addEventListener('click', () => window.print()));
  if (new URL(window.location.href).searchParams.get('imprimir') === '1') {
    window.addEventListener('load', () => { document.fonts.ready.then(() => window.print()); }, {once:true});
  }
})();
