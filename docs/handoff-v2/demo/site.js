/* CETREMER · comportamentos gerais (todas as páginas). Carregar em base_core.html com defer.
   Tudo é opt-in por atributo data-*; páginas sem esses atributos não são afetadas.
*/
(function () {
  'use strict';

  // 1. Filtro por categoria (landing): botões [data-filter="slug|all"] e cards [data-category]
  var filterButtons = document.querySelectorAll('[data-filter]');
  filterButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      var value = button.getAttribute('data-filter');
      filterButtons.forEach(function (b) { b.setAttribute('aria-pressed', String(b === button)); });
      document.querySelectorAll('[data-category]').forEach(function (card) {
        card.hidden = value !== 'all' && card.getAttribute('data-category') !== value;
      });
    });
  });

  // 2. Copiar texto: <button data-copy="https://..."><span data-label>Copiar link de verificação</span></button>
  document.querySelectorAll('[data-copy]').forEach(function (button) {
    button.addEventListener('click', function () {
      var label = button.querySelector('[data-label]') || button;
      var original = label.textContent;
      navigator.clipboard.writeText(button.getAttribute('data-copy')).then(function () {
        label.textContent = 'Link copiado';
        setTimeout(function () { label.textContent = original; }, 2000);
      });
    });
  });

  // 3. Imprimir / salvar PDF: <button data-print>. Com ?imprimir=1 na URL, abre a impressão ao carregar.
  var printButtons = document.querySelectorAll('[data-print]');
  printButtons.forEach(function (button) {
    button.addEventListener('click', function () { window.print(); });
  });
  if (printButtons.length && new URLSearchParams(window.location.search).get('imprimir') === '1') {
    window.addEventListener('load', function () { window.print(); });
  }

  // 4. Diálogo nativo: <button data-dialog-open="id-do-dialog">, dentro do dialog <button data-dialog-close>
  document.querySelectorAll('[data-dialog-open]').forEach(function (button) {
    button.addEventListener('click', function () {
      var dialog = document.getElementById(button.getAttribute('data-dialog-open'));
      if (dialog && dialog.showModal) dialog.showModal();
    });
  });
  document.querySelectorAll('[data-dialog-close]').forEach(function (button) {
    button.addEventListener('click', function () {
      var dialog = button.closest('dialog');
      if (dialog) dialog.close();
    });
  });

  // 5. Campo secreto: <div data-secret> com [data-secret-display] (.secret-field) e [data-secret-input] (hidden)
  //    O botão [data-secret-replace] troca a exibição pelo input vazio. Input vazio no POST = manter a chave atual.
  document.querySelectorAll('[data-secret-replace]').forEach(function (button) {
    button.addEventListener('click', function () {
      var wrap = button.closest('[data-secret]');
      if (!wrap) return;
      var display = wrap.querySelector('[data-secret-display]');
      var input = wrap.querySelector('[data-secret-input]');
      if (display) display.hidden = true;
      if (input) { input.hidden = false; input.focus(); }
    });
  });

  // 6. Dropzone: <label class="dropzone" data-dropzone> com <input type="file" class="sr-only"> e [data-dropzone-name]
  document.querySelectorAll('[data-dropzone]').forEach(function (zone) {
    var input = zone.querySelector('input[type=file]');
    var name = zone.querySelector('[data-dropzone-name]');
    function show() {
      if (name && input && input.files.length) {
        name.textContent = Array.prototype.map.call(input.files, function (f) { return f.name; }).join(', ');
      }
    }
    ['dragenter', 'dragover'].forEach(function (evt) {
      zone.addEventListener(evt, function (e) { e.preventDefault(); zone.classList.add('is-dragover'); });
    });
    ['dragleave', 'drop'].forEach(function (evt) {
      zone.addEventListener(evt, function () { zone.classList.remove('is-dragover'); });
    });
    zone.addEventListener('drop', function (e) {
      e.preventDefault();
      if (input && e.dataTransfer.files.length) { input.files = e.dataTransfer.files; show(); }
    });
    if (input) input.addEventListener('change', show);
  });

  // 7. Lista de objetivos editável (admin, editar curso): [data-repeater] com template [data-repeater-template]
  document.querySelectorAll('[data-repeater]').forEach(function (wrap) {
    var list = wrap.querySelector('[data-repeater-list]');
    var template = wrap.querySelector('[data-repeater-template]');
    var add = wrap.querySelector('[data-repeater-add]');
    if (!list || !template || !add) return;
    add.addEventListener('click', function () {
      var node = template.content.firstElementChild.cloneNode(true);
      list.appendChild(node);
      var field = node.querySelector('input');
      if (field) field.focus();
    });
    list.addEventListener('click', function (e) {
      var remove = e.target.closest('[data-repeater-remove]');
      if (remove) remove.closest('[data-repeater-item]').remove();
    });
  });
})();
