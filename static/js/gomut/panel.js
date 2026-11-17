/* Panel navigation only; all mutations remain authenticated server requests. */
(() => {
 const button=document.querySelector('[data-panel-menu]'),sidebar=document.getElementById('producer-sidebar'),scrim=document.querySelector('[data-panel-scrim]');
 if(!button||!sidebar)return;
 function setOpen(open){sidebar.classList.toggle('is-open',open);button.setAttribute('aria-expanded',String(open));scrim.hidden=!open;}
 button.addEventListener('click',()=>setOpen(button.getAttribute('aria-expanded')!=='true'));
 scrim.addEventListener('click',()=>setOpen(false));
 document.addEventListener('keydown',event=>{if(event.key==='Escape'){setOpen(false);button.focus();}});
})();
