/* The server also rejects every unsafe member request in this mode. */
(() => {
 if(document.body.dataset.memberPreview!=='true')return;
 document.querySelectorAll('form').forEach(form=>{
  if(form.method.toLowerCase()!=='post')return;
  form.querySelectorAll('input,textarea,select,button').forEach(control=>{control.disabled=true;control.title='Modo visualização: ações desativadas';});
 });
 document.querySelectorAll('.btn-toggle-complete,[data-quiz-start],[data-open-quiz]').forEach(button=>{button.disabled=true;button.title='Modo visualização: ações desativadas';});
 document.addEventListener('submit',event=>{if(event.target.method?.toLowerCase()==='post'){event.preventDefault();event.stopImmediatePropagation();}},true);
})();
