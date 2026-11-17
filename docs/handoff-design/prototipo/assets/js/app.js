/* ==========================================================================
   Emergensimples — protótipo navegável
   Sem dependências e sem build: abre direto no navegador.
   Seções: utilitários · ícones e capas · estado · componentes · casca ·
   páginas · janela do curso · roteador · interações globais
   ========================================================================== */
(function () {
  'use strict';

  const DB = window.DB;
  const { marca, usuario, areas, instrutores, cursos, ofertas, trilhas, lives, novidades, top10, notificacoes, comunidade, capitulos, quiz, estudoSemana, ajuda } = DB;
  /* As duas áreas são separadas: index.html é a área de membros e coprodutor.html é a do coprodutor.
     Sessão do protótipo: guarda, só nesta aba, se quem entrou tem permissão de coprodutor e se ele
     está visualizando como membro. Na plataforma real, quem decide isso é o login. */
  const AREA = window.EMS_AREA === 'coprodutor' ? 'coprodutor' : 'membros';
  const sessao = {
    ler(k) { try { return sessionStorage.getItem('emergensimples:' + k); } catch (e) { return null; } },
    gravar(k, v) { try { if (v == null) sessionStorage.removeItem('emergensimples:' + k); else sessionStorage.setItem('emergensimples:' + k, v); } catch (e) { /* ignora */ } },
  };
  const ehCoprodutor = () => sessao.ler('papel') === 'coprodutor';
  const byId = Object.fromEntries(cursos.map((c) => [c.id, c]));
  const ofertaById = Object.fromEntries(ofertas.map((c) => [c.id, c])); /* cursos à venda, fora do plano */
  const MENTORIA = byId['plantao-sem-gpt'];
  const turmaTxt = () => 'Turma ' + marca.turma; /* marca.turma devolve sempre o ano atual (data.js) */

  /* ------------------------------------------------------------ utilitários */
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const esc = (s) => String(s).replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
  const norm = (s) => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

  function fmtPreco(v) { return 'R$\u00a0' + v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function fmtMin(m) {
    m = Math.round(m);
    if (m < 60) return m + ' min';
    const h = Math.floor(m / 60), r = m % 60;
    return r ? h + 'h ' + String(r).padStart(2, '0') + 'min' : h + 'h';
  }
  function fmtClock(s) {
    s = Math.max(0, Math.floor(s));
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
    return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(r).padStart(2, '0');
  }
  const sameDay = (a, b) => a.toDateString() === b.toDateString();
  function fmtHora(d) { return d.getHours() + 'h' + (d.getMinutes() ? String(d.getMinutes()).padStart(2, '0') : ''); }
  function fmtQuando(d) {
    const hoje = new Date(), amanha = new Date();
    amanha.setDate(hoje.getDate() + 1);
    if (sameDay(d, hoje)) return 'hoje, ' + fmtHora(d);
    if (sameDay(d, amanha)) return 'amanhã, ' + fmtHora(d);
    return d.toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' }) + ', ' + fmtHora(d);
  }
  function fmtData(d) { return String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0'); }
  function emDias(n) { const d = new Date(); d.setDate(d.getDate() + n); return d; }

  /* -------------------------------------------------------- ícones e capas */
  const ICONS = {
    play: '<path d="M7 4.5v15l12.5-7.5z" fill="currentColor" stroke="none"/>',
    pause: '<path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z" fill="currentColor" stroke="none"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.8-3.8"/>',
    bell: '<path d="M6 9a6 6 0 0112 0c0 6 2.5 7 2.5 7h-17S6 15 6 9zM10 20a2 2 0 004 0"/>',
    right: '<path d="M9 5l7 7-7 7"/>',
    left: '<path d="M15 5l-7 7 7 7"/>',
    down: '<path d="M5 9l7 7 7-7"/>',
    close: '<path d="M6 6l12 12M18 6L6 18"/>',
    thumb: '<path d="M7 11v9H4v-9zM7 11l4-8a2.5 2.5 0 012.5 2.5V9h5a2 2 0 012 2.3l-1.2 7a2 2 0 01-2 1.7H7"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    download: '<path d="M12 4v11M7 11l5 5 5-5M5 20h14"/>',
    fullscreen: '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
    volume: '<path d="M4 9.5h3l5-4v13l-5-4H4zM16 9a4 4 0 010 6M18.5 6.5a8 8 0 010 11"/>',
    mute: '<path d="M4 9.5h3l5-4v13l-5-4H4zM16 9.5l5 5M21 9.5l-5 5"/>',
    captions: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 12h4M13 12h4M7 15.5h2M11 15.5h6"/>',
    cinema: '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M8 10l-2 2 2 2M16 10l2 2-2 2"/>',
    sliders: '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>',
    flame: '<path d="M12 3s5 4 5 9.5a5 5 0 01-10 0c0-2 1-3.5 2-4.5.3 1.5 1 2.5 2 3 0-3 1-6 1-8z"/>',
    award: '<circle cx="12" cy="9" r="5.5"/><path d="M8.5 13.5L7 21l5-2.5 5 2.5-1.5-7.5"/>',
    calendar: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M8 3v4M16 3v4"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0113 0M16 4.8a3.5 3.5 0 010 6.4M18 14.5a6.5 6.5 0 013.5 5.5"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0116 0"/>',
    cart: '<path d="M3 4h2.6l2.2 10.5h10L20 7.5H7"/><circle cx="9.5" cy="19" r="1.4"/><circle cx="16.8" cy="19" r="1.4"/>',
    file: '<path d="M7 3h7l5 5v13H7zM14 3v5h5"/>',
    book: '<path d="M5 19.5V5.5A2.5 2.5 0 017.5 3H19v14H7.5A2.5 2.5 0 005 19.5zM5 19.5A2.5 2.5 0 007.5 22H19M9.5 8h5.5"/>',
    pencil: '<path d="M4 20l1-4L16.5 4.5a2.1 2.1 0 013 3L8 19zM14.5 6.5l3 3"/>',
    help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 114 2c-.9.6-1.5 1.2-1.5 2.5M12 17v.5"/>',
    back10: '<path d="M12 5a7.5 7.5 0 11-7.2 5.4M12 5L9 2.5M12 5L9 7.5"/><text x="12" y="15.6" font-size="6.6" font-weight="700" text-anchor="middle" fill="currentColor" stroke="none" font-family="sans-serif">10</text>',
    fwd10: '<path d="M12 5a7.5 7.5 0 107.2 5.4M12 5l3-2.5M12 5l3 2.5"/><text x="12" y="15.6" font-size="6.6" font-weight="700" text-anchor="middle" fill="currentColor" stroke="none" font-family="sans-serif">10</text>',
    next: '<path d="M6 5v14l10-7z" fill="currentColor" stroke="none"/><path d="M18 5v14"/>',
    home: '<path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z"/>',
    grid: '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/>',
    live: '<circle cx="12" cy="12" r="2.5" fill="currentColor" stroke="none"/><path d="M7.8 7.8a6 6 0 000 8.4M16.2 7.8a6 6 0 010 8.4M4.9 4.9a10 10 0 000 14.2M19.1 4.9a10 10 0 010 14.2"/>',
    lock: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
    share: '<path d="M12 15V4M8 7.5L12 4l4 3.5M6 12v7h12v-7"/>',
    route: '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/><path d="M8.5 18H15a3 3 0 000-6H9a3 3 0 010-6h6.5"/>',
    logout: '<path d="M10 4H5v16h5M15 8l4 4-4 4M19 12H9"/>',
    star: '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9L12 16.9 6.8 19.7l1-5.9L3.5 9.7l5.9-.8z" fill="currentColor" stroke="none"/>',
    message: '<path d="M4 5h16v11H9l-5 4z"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1" fill="currentColor"/>',
    bolt: '<path d="M13 3L5 13.5h6L10 21l8-10.5h-6z"/>',
    list: '<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/>',
    heart: '<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0112 7.6 4.3 4.3 0 0119.5 10c0 5.4-7.5 10-7.5 10z"/>',
    trash: '<path d="M5 7h14M10 7V4h4v3M7 7l1 13h8l1-13"/>',
    table: '<rect x="4" y="5" width="16" height="14" rx="1.5"/><path d="M4 10h16M4 14.5h16M10 5v14"/>',
  };
  function icon(n, cls) { return '<svg class="ico' + (cls ? ' ' + cls : '') + '" viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[n] || '') + '</svg>'; }

  /* Motivos das capas: desenhos em linha, um por tema. */
  const MOTIFS = {
    ecg: '<path d="M-10 118h52l9-16 9 16h12l10-74 13 124 10-50h16q11-26 22 0h60"/><path d="M-10 164h220M-10 44h220" opacity=".22"/>',
    rings: '<circle cx="118" cy="100" r="22"/><circle cx="118" cy="100" r="48"/><circle cx="118" cy="100" r="74" opacity=".7"/><circle cx="118" cy="100" r="100" opacity=".35"/>',
    wave: '<path d="M-10 70q26-44 52 0t52 0 52 0 52 0"/><path d="M-10 108q26-44 52 0t52 0 52 0 52 0" opacity=".6"/><path d="M-10 146q26-44 52 0t52 0 52 0 52 0" opacity=".3"/>',
    cross: '<path d="M84 30h44v54h54v44h-54v54H84v-54H30V84h54z"/><path d="M96 48h20v48h48v20h-48v48H96v-48H48V96h48z" opacity=".35"/>',
    drop: '<path d="M116 26c26 36 44 60 44 86a44 44 0 01-88 0c0-26 18-50 44-86z"/><path d="M96 120a22 22 0 0020 20" opacity=".6"/><path d="M40 178q76 22 152 0" opacity=".3"/>',
    hex: '<path d="M100 36l34 20v40l-34 20-34-20V56z"/><path d="M134 96l34 20v40l-34 20-34-20v-40" opacity=".6"/><path d="M66 96l-34 20v40l34 20 34-20" opacity=".35"/>',
    bars: '<path d="M34 170v-58M58 170V74M82 170v-38M106 170V42M130 170V96M154 170V62M178 170v-48"/><path d="M20 170h172" opacity=".4"/>',
    scan: '<path d="M104 22L26 158q78 38 156 0z"/><path d="M73 76q31 13 62 0M52 112q52 22 104 0M36 140q68 30 136 0" opacity=".55"/>',
    pill: '<g transform="rotate(-38 112 100)"><rect x="42" y="68" width="140" height="64" rx="32"/><path d="M112 68v64"/><path d="M62 84h30" opacity=".5"/></g>',
    clock: '<circle cx="112" cy="100" r="74"/><path d="M112 52v48l34 22"/><path d="M112 16v12M112 172v12M28 100h12M184 100h12" opacity=".5"/>',
    net: '<path d="M50 60l60-20 50 44-30 62-66 6-34-50z"/><path d="M110 40l20 106M50 60l80 86M160 84l-96 68M30 102l130-18" opacity=".45"/><g fill="currentColor" stroke="none"><circle cx="50" cy="60" r="5"/><circle cx="110" cy="40" r="5"/><circle cx="160" cy="84" r="5"/><circle cx="130" cy="146" r="5"/><circle cx="64" cy="152" r="5"/><circle cx="30" cy="102" r="5"/></g>',
    chat: '<path d="M34 40h106a12 12 0 0112 12v50a12 12 0 01-12 12H84l-28 24v-24H34a12 12 0 01-12-12V52a12 12 0 0112-12z"/><path d="M104 136h44l24 20v-20h6a10 10 0 0010-10V86" opacity=".5"/>',
    stitch: '<path d="M22 100q78-26 160 0" opacity=".45"/><path d="M48 70l10 46M78 62l8 46M110 60l4 46M142 62l-2 46M172 70l-8 46"/>',
    xray: '<rect x="46" y="24" width="124" height="152" rx="8"/><path d="M108 40v120M108 66q-36 4-42 40M108 66q36 4 42 40M108 98q-32 4-38 38M108 98q32 4 38 38" opacity=".6"/>',
  };

  function cover(o) {
    return '<span class="cover' + (o.shape ? ' cover--' + o.shape : '') + '" style="--h:' + o.h + '">' +
      '<svg class="cover__motif" viewBox="0 0 200 200" aria-hidden="true">' + (MOTIFS[o.motif] || MOTIFS.ecg) + '</svg>' +
      (o.kicker ? '<span class="cover__kicker">' + esc(o.kicker) + '</span>' : '') +
      (o.title ? '<span class="cover__title">' + esc(o.title) + '</span>' : '') +
      '</span>';
  }
  function courseCover(c, o) {
    return cover(Object.assign({ h: c.h, motif: c.motif, title: c.titulo, kicker: c.tipo === 'mentoria' ? 'Mentoria' : areas[c.area].nome }, o));
  }
  function ring(p, size, stroke) {
    size = size || 44; stroke = stroke || 4;
    const r = (size - stroke) / 2, len = 2 * Math.PI * r, mid = size / 2;
    return '<svg class="ring" width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + ' ' + size + '" role="img" aria-label="' + p + '% concluído">' +
      '<circle cx="' + mid + '" cy="' + mid + '" r="' + r + '" fill="none" stroke="rgba(255,255,255,.18)" stroke-width="' + stroke + '"/>' +
      '<circle cx="' + mid + '" cy="' + mid + '" r="' + r + '" fill="none" stroke="var(--c-red)" stroke-width="' + stroke + '" stroke-linecap="round" stroke-dasharray="' + len + '" stroke-dashoffset="' + (len * (1 - Math.min(p, 100) / 100)) + '" transform="rotate(-90 ' + mid + ' ' + mid + ')"/>' +
      '</svg>';
  }

  /* ----------------------------------------------------------------- estado */
  /* Guardado só neste navegador (localStorage), para o protótipo lembrar o que foi clicado. */
  const KEY = 'emergensimples:prototipo:v1';
  function seed() {
    const s = {
      list: ['pocus', 'avc', 'ventilacao'], recent: ['plantao-sem-gpt', 'ecg-no-plantao', 'sepse', 'via-aerea'],
      progress: {}, posts: [], replies: {}, study: {}, tickets: [], likes: {}, reminders: { 'l-mentoria-1': true }, liked: {},
      prefs: { cinema: false, emailAulas: true, emailLives: true },
    };
    const mark = (id, n, partial) => {
      const c = byId[id], p = (s.progress[id] = { done: {}, pos: {}, last: null });
      c.aulas.slice(0, n).forEach((a) => { p.done[a.id] = true; });
      const nx = c.aulas[n];
      if (nx) { p.last = nx.id; if (partial) p.pos[nx.id] = Math.round(nx.min * 60 * partial); }
    };
    mark('plantao-sem-gpt', 9, 0.4);
    mark('ecg-no-plantao', 4, 0.55);
    mark('via-aerea', 2, 0.2);
    mark('sepse', 5, 0.7);
    mark('primeiro-plantao', 99); /* 99 = todas as aulas */
    mark('prescricao-segura', 99);
    return s;
  }
  function load() {
    try {
      const s = JSON.parse(localStorage.getItem(KEY));
      if (s && s.progress && s.prefs && s.list) return s;
    } catch (e) { /* sem armazenamento: segue com os dados de exemplo */ }
    return seed();
  }
  let S = load();
  let dirty = false;
  function save() { dirty = true; try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* ignora */ } }

  /* Minutos de estudo por dia. O reprodutor soma o tempo assistido ao dia de hoje (em segundos) e o
     gráfico de Meu progresso lê daqui, então ele se atualiza sozinho conforme o aluno estuda.
     estudoSemana (data.js) é só o histórico de exemplo dos últimos sete dias. */
  const diaKey = (d) => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  function addStudy(seg) { const e = S.study || (S.study = {}), k = diaKey(new Date()); e[k] = (e[k] || 0) + seg; }
  /* i: 0 = seis dias atrás … 6 = hoje */
  const minutosDoDia = (i) => estudoSemana[i] + Math.floor(((S.study || {})[diaKey(emDias(i - 6))] || 0) / 60);

  const P = (id) => S.progress[id];
  function ensureP(id) { return S.progress[id] || (S.progress[id] = { done: {}, pos: {}, last: null }); }
  const isDone = (c, a) => !!(P(c.id) && P(c.id).done[a.id]);
  /* Regra do progresso: total de aulas e percentual são sempre calculados a partir da lista atual
     de aulas, nunca fixos. Quando o coprodutor adiciona aulas, o painel "X de Y aulas concluídas",
     o percentual e os demais totais (aulas, horas, e-books) mudam sozinhos. */
  const doneCount = (c) => c.aulas.filter((a) => isDone(c, a)).length;
  const pct = (c) => Math.round((doneCount(c) / c.aulas.length) * 100);
  const started = (c) => !!P(c.id) && (doneCount(c) > 0 || !!P(c.id).last);
  function nextAula(c) {
    const p = P(c.id);
    if (p && p.last) {
      const a = c.aulas.find((x) => x.id === p.last);
      if (a && !p.done[a.id] && !a.bloqueada) return a;
    }
    return c.aulas.find((a) => !a.bloqueada && !isDone(c, a)) || c.aulas[0];
  }
  function lessonPct(c, a) {
    const p = P(c.id);
    if (!p) return 0;
    if (p.done[a.id]) return 100;
    return Math.min(100, Math.round(((p.pos[a.id] || 0) / (a.min * 60)) * 100));
  }
  const inList = (id) => S.list.includes(id);
  function touchRecent(id) { S.recent = [id].concat((S.recent || []).filter((x) => x !== id)); }
  const modLabel = (c, m) => (c.tipo === 'mentoria' ? 'Semana ' : 'Módulo ') + (m.i + 1) + ' · ' + m.titulo;
  const emAndamento = () => {
    const ord = S.recent || [];
    return cursos.filter((c) => started(c) && pct(c) < 100).sort((a, b) => {
      const ia = ord.indexOf(a.id), ib = ord.indexOf(b.id);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });
  };

  /* ------------------------------------------------------------ componentes */
  function toast(msg, ic) {
    const box = $('#toasts');
    while (box.children.length > 2) box.firstChild.remove();
    const t = document.createElement('div');
    t.className = 'toast';
    t.innerHTML = icon(ic || 'check') + '<span>' + esc(msg) + '</span>';
    box.appendChild(t);
    setTimeout(() => { t.classList.add('is-out'); setTimeout(() => t.remove(), 300); }, 2600);
  }

  function listBtn(id, kind) {
    const on = inList(id), label = on ? 'Remover da minha lista' : 'Adicionar à minha lista';
    if (kind === 'text') {
      return '<button class="btn btn--outline' + (on ? ' is-on' : '') + '" data-action="list" data-id="' + id + '" data-kind="text" aria-pressed="' + on + '">' + icon(on ? 'check' : 'plus') + '<span>' + (on ? 'Na minha lista' : 'Minha lista') + '</span></button>';
    }
    return '<button class="rbtn' + (kind === 'sm' ? ' rbtn--sm' : '') + (on ? ' is-on' : '') + '" data-action="list" data-id="' + id + '" data-kind="' + (kind || '') + '" aria-pressed="' + on + '" aria-label="' + label + '" title="' + label + '">' + icon(on ? 'check' : 'plus') + '</button>';
  }
  function likeBtn(id, kind) {
    const on = !!S.liked[id];
    return '<button class="rbtn' + (kind === 'sm' ? ' rbtn--sm' : '') + (on ? ' is-on rbtn--solid' : '') + '" data-action="like" data-id="' + id + '" data-kind="' + (kind || '') + '" aria-pressed="' + on + '" aria-label="Gostei" title="' + (on ? 'Você gostou deste conteúdo' : 'Gostei') + '">' + icon('thumb') + '</button>';
  }
  function swap(sel, html) {
    $$(sel).forEach((b) => {
      const tmp = document.createElement('div');
      tmp.innerHTML = html(b);
      b.replaceWith(tmp.firstElementChild);
    });
  }
  function remindBtn(l) {
    const on = !!S.reminders[l.id];
    return '<button class="btn btn--sm btn--outline' + (on ? ' is-on' : '') + '" data-action="remind" data-id="' + l.id + '" aria-pressed="' + on + '">' + icon(on ? 'check' : 'bell') + '<span>' + (on ? 'Lembrete ativo' : 'Lembrar-me') + '</span></button>';
  }
  /* Contador de um evento: "Hoje" no dia; antes disso, "Falta 1 dia" ou "Faltam N dias". */
  function diasAte(d) {
    const a = new Date(), b = new Date(d);
    a.setHours(0, 0, 0, 0); b.setHours(0, 0, 0, 0);
    return Math.round((b - a) / 86400000);
  }
  function contador(d) {
    const n = diasAte(d);
    return n <= 0 ? '<span class="tag tag--live">Hoje</span>' : '<span class="tag">' + (n === 1 ? 'Falta 1 dia' : 'Faltam ' + n + ' dias') + '</span>';
  }
  function dateBox(d) {
    const hoje = sameDay(d, new Date());
    return '<span class="datebox' + (hoje ? ' is-today' : '') + '"><b>' + d.getDate() + '</b><span>' + (hoje ? 'hoje' : MESES[d.getMonth()]) + '</span></span>';
  }

  function card(c) {
    const p = pct(c);
    const badge = p === 100 ? '<span class="card__badge card__badge--done">' + icon('check') + 'Concluído</span>'
      : c.tipo === 'mentoria' ? '<span class="card__badge">Mentoria</span>'
      : c.novo ? '<span class="card__badge">Novo</span>' : '';
    return '<a class="card" href="#/curso/' + c.id + '" data-peek="' + c.id + '" aria-label="' + esc(c.titulo) + '">' + courseCover(c) + badge +
      (started(c) && p < 100 ? '<span class="card__bar"><i style="width:' + Math.max(p, 4) + '%"></i></span>' : '') + '</a>';
  }
  /* curso à venda: capa com selo de conteúdo bloqueado; leva à página do curso, não à janela */
  function saleCard(c) {
    return '<a class="card card--sale" href="#/oferta/' + c.id + '" aria-label="' + esc(c.titulo) + ', curso à venda, conteúdo bloqueado">' + courseCover(c) +
      '<span class="card__badge card__badge--lock">' + icon('lock') + '<span>Bloqueado</span></span></a>';
  }
  /* versão de vitrine: pôster alto, com a área embaixo e chamada "Ver curso" ao passar o mouse.
     Sem preço aqui: o valor aparece só na página do curso. */
  function salePoster(c) {
    return '<a class="card card--sale card--poster" href="#/oferta/' + c.id + '" aria-label="' + esc(c.titulo) + ', curso à venda, conteúdo bloqueado">' +
      '<span class="card__media">' + courseCover(c, { shape: 'poster', kicker: '' }) +
        '<span class="card__badge card__badge--lock">' + icon('lock') + '<span>Bloqueado</span></span>' +
        '<span class="card__cta" aria-hidden="true">Ver curso' + icon('right') + '</span></span>' +
      '<span class="card__caption"><strong>' + esc(areas[c.area].nome) + '</strong></span></a>';
  }
  function gcard(c) {
    return '<div class="gcard">' + card(c) + '<div class="gcard__meta"><strong>' + esc(c.titulo) + '</strong>' + c.aulas.length + ' aulas · ' + fmtMin(c.totalMin) + '</div></div>';
  }
  function continueCard(c) {
    const a = nextAula(c), pos = (P(c.id) && P(c.id).pos[a.id]) || 0, rest = Math.max(1, Math.round(a.min - pos / 60));
    return '<div><a class="card" href="#/aula/' + c.id + '/' + a.id + '" aria-label="Continuar ' + esc(c.titulo) + '">' + courseCover(c) +
      '<span class="card__play"><span>' + icon('play') + '</span></span><span class="card__bar"><i style="width:' + Math.max(pct(c), 4) + '%"></i></span></a>' +
      '<div class="card__caption"><strong>Aula ' + a.n + ' · ' + esc(a.titulo) + '</strong><span>Restam ' + rest + ' min · ' + pct(c) + '% do curso</span></div></div>';
  }
  const WEEK_MOTIFS = ['net', 'rings', 'ecg', 'wave', 'hex', 'clock', 'pill', 'bars'];
  function weekCard(m) {
    const done = m.aulas.filter((a) => isDone(MENTORIA, a)).length, total = m.aulas.length;
    const cv = cover({ h: 350 + m.i * 3, motif: WEEK_MOTIFS[m.i % 8], title: m.titulo, kicker: 'Semana ' + (m.i + 1) });
    if (m.bloqueado) {
      return '<a class="card is-locked" href="#/mentoria" aria-label="Semana ' + (m.i + 1) + ', bloqueada">' + cv + '<span class="card__lock">' + icon('lock') + 'Libera em ' + fmtData(emDias(m.bloqueado)) + '</span></a>';
    }
    return '<a class="card" href="#/mentoria">' + cv +
      (done === total ? '<span class="card__badge card__badge--done">' + icon('check') + 'Concluída</span>' : done ? '<span class="card__badge">Em andamento</span>' : '<span class="card__badge">Liberada</span>') +
      (done && done < total ? '<span class="card__bar"><i style="width:' + (done / total) * 100 + '%"></i></span>' : '') + '</a>';
  }
  function quickCard(c, a) {
    return '<a class="card" href="#/aula/' + c.id + '/' + a.id + '">' + cover({ h: c.h, motif: c.motif, title: a.titulo, kicker: c.titulo }) +
      '<span class="card__play"><span>' + icon('play') + '</span></span><span class="card__pill">' + a.min + ' min</span></a>';
  }
  function top10Card(c, i) {
    return '<a class="top10" href="#/curso/' + c.id + '" data-peek="' + c.id + '" aria-label="' + (i + 1) + 'º: ' + esc(c.titulo) + '"><span class="top10__n' + (i === 9 ? ' top10__n--2' : '') + '" aria-hidden="true">' + (i + 1) + '</span>' + courseCover(c, { shape: 'poster' }) + '</a>';
  }
  function trackStats(t) {
    const cs = t.cursos.map((id) => byId[id]);
    return { cs, min: cs.reduce((s, c) => s + c.totalMin, 0), p: Math.round(cs.reduce((s, c) => s + pct(c), 0) / cs.length) };
  }
  function trackCard(t) {
    const s = trackStats(t);
    return '<a class="tcard" href="#/trilha/' + t.id + '">' + cover({ h: t.h, motif: t.motif, title: t.titulo, kicker: 'Trilha' }) +
      '<div class="tcard__body"><p>' + esc(t.desc) + '</p><div class="tcard__meta"><span>' + s.cs.length + ' cursos · ' + fmtMin(s.min) + '</span><span class="progressbar"><i style="width:' + s.p + '%"></i></span><span>' + s.p + '%</span></div></div></a>';
  }
  function liveCard(l) {
    return '<article class="lcard">' + dateBox(l.quando) + '<div><div class="tagrow"><span class="tag ' + (l.mentoria ? 'tag--red' : 'tag--line') + '">' + esc(l.tipo) + '</span>' + contador(l.quando) + '</div><h3>' + esc(l.titulo) + '</h3><p>' + cap(fmtQuando(l.quando)) + ' · ' + l.min + ' min</p><div class="lcard__foot">' + remindBtn(l) + '</div></div></article>';
  }
  /* Novos conteúdos: curso, aula, gravação ou e-book publicado ou atualizado há até 7 dias */
  const JANELA_NOVOS = 7;
  const TIPO_NOVO = { curso: 'Curso', aula: 'Aula', gravacao: 'Gravação', ebook: 'E-book' };
  const novosConteudos = () => novidades.filter((x) => x.dias <= JANELA_NOVOS).sort((a, b) => a.dias - b.dias);
  function novoCard(x) {
    const c = x.curso ? byId[x.curso] : null, a = c && x.aula ? c.aulas.find((y) => y.id === x.aula) : null;
    const fem = x.tipo === 'aula' || x.tipo === 'gravacao', upd = x.acao === 'atualizado';
    const selo = upd ? (fem ? 'Atualizada' : 'Atualizado') : (fem ? 'Nova' : 'Novo');
    const quando = x.dias === 0 ? 'hoje' : x.dias === 1 ? 'ontem' : 'há ' + x.dias + ' dias';
    const legenda = (upd ? selo : fem ? 'Publicada' : 'Publicado') + ' ' + quando;
    let titulo = x.titulo, sub, href = '', min = x.min;
    if (x.tipo === 'curso') { titulo = c.titulo; sub = areas[c.area].nome; href = '#/curso/' + c.id; }
    else if (x.tipo === 'aula') { titulo = a.titulo; sub = c.titulo; href = '#/aula/' + c.id + '/' + a.id; min = a.min; }
    else if (x.tipo === 'ebook') { titulo = a.titulo; sub = c.titulo + ' · aula ' + a.n; href = c.tipo === 'mentoria' ? EBOOKS : '#/curso/' + c.id + '?ver=ebooks'; }
    else sub = 'Encontro ao vivo';
    const dentro = cover({ h: c ? c.h : x.h, motif: c ? c.motif : x.motif, title: titulo, kicker: TIPO_NOVO[x.tipo] }) +
      '<span class="card__badge' + (upd ? ' card__badge--upd' : '') + '">' + selo + '</span>' +
      (min ? '<span class="card__play"><span>' + icon('play') + '</span></span><span class="card__pill">' + min + ' min</span>' : '');
    const rotulo = TIPO_NOVO[x.tipo] + ': ' + esc(titulo) + ', ' + legenda.toLowerCase();
    return '<div>' + (href
      ? '<a class="card" href="' + href + '" aria-label="' + rotulo + '">' + dentro + '</a>'
      : '<button class="card" data-action="toast" data-msg="Gravação ilustrativa neste protótipo" data-ico="play" style="width:100%;text-align:left" aria-label="' + rotulo + '">' + dentro + '</button>') +
      '<div class="card__caption"><strong>' + esc(sub) + '</strong><span>' + legenda + '</span></div></div>';
  }

  function rail(title, items, o) {
    o = o || {};
    if (!items.length) return '';
    const head = o.href ? '<a href="' + o.href + '">' + esc(title) + '<span class="rail__more">Ver tudo' + icon('right') + '</span></a>' : esc(title);
    return '<section class="rail' + (o.cls ? ' ' + o.cls : '') + '" data-start="1">' +
      '<header class="rail__head">' + (o.head || '<h2 class="rail__title">' + head + (o.note ? ' <span class="rail__sub">' + esc(o.note) + '</span>' : '') + '</h2>') + '<div class="rail__pager" aria-hidden="true"></div></header>' +
      '<div class="rail__viewport"><button class="rail__btn rail__btn--prev" data-rail="-1" aria-label="Anterior">' + icon('left') + '</button>' +
      '<div class="rail__track">' + items.join('') + '</div>' +
      '<button class="rail__btn rail__btn--next" data-rail="1" aria-label="Próximo">' + icon('right') + '</button></div></section>';
  }
  let railUpdaters = [];
  function initRails(root) {
    $$('.rail', root).forEach((r) => {
      const track = $('.rail__track', r), pager = $('.rail__pager', r);
      let pages = 0;
      const update = () => {
        const max = track.scrollWidth - track.clientWidth;
        r.dataset.start = track.scrollLeft < 8 ? '1' : '0';
        r.dataset.end = track.scrollLeft > max - 8 ? '1' : '0';
        const n = max > 8 ? Math.max(2, Math.ceil(track.scrollWidth / track.clientWidth - 0.15)) : 1;
        if (n !== pages) { pages = n; pager.innerHTML = n > 1 ? new Array(n + 1).join('<i></i>') : ''; }
        if (n > 1) {
          const cur = Math.round((track.scrollLeft / max) * (n - 1));
          Array.from(pager.children).forEach((d, i) => d.classList.toggle('is-on', i === cur));
        }
      };
      track.addEventListener('scroll', () => { hidePeek(); update(); }, { passive: true });
      railUpdaters.push(update);
      update();
    });
  }

  function epDesc(a) {
    const t = a.titulo;
    const porTipo = [
      ['Boas-vindas', 'Como o conteúdo está organizado e a melhor forma de aproveitar cada aula.'],
      ['Caso', 'Um caso discutido do início ao fim: pause o vídeo e decida antes de ouvir a conduta.'],
      ['Encontro gravado', 'Gravação do encontro ao vivo da turma, com casos enviados pelos participantes.'],
      ['Simulado', 'Um plantão simulado para você decidir em tempo real e comparar com a conduta comentada.'],
      ['Encerramento', 'O fechamento da turma e os próximos passos depois da mentoria.'],
    ].find((x) => t.indexOf(x[0]) === 0);
    if (porTipo) return porTipo[1];
    const d = [
      'O raciocínio explicado passo a passo, com exemplos tirados do plantão.',
      'Onde costuma dar errado e como evitar quando for a sua vez.',
      'Do conceito à conduta, com o que observar primeiro e o que pode esperar.',
    ];
    return d[a.n % d.length];
  }
  function epList(c, mi, compact) {
    const m = c.modulos[mi], cur = nextAula(c), st = started(c);
    return '<ol class="eps' + (compact ? ' eps--compact' : '') + '">' + m.aulas.map((a) => {
      const done = isDone(c, a), lp = lessonPct(c, a);
      const inner = '<span class="ep__n">' + (a.bloqueada ? icon('lock') : a.n) + '</span>' +
        '<span class="ep__thumb">' + cover({ h: c.h, motif: c.motif, shape: 'thumb' }) + '<span class="card__play"><span>' + icon('play') + '</span></span>' + (lp > 0 && lp < 100 ? '<span class="card__bar"><i style="width:' + lp + '%"></i></span>' : '') + '</span>' +
        '<span class="ep__main"><span class="ep__head"><span class="ep__title">' + esc(a.titulo) + '</span><span class="ep__dur">' + (done ? icon('check') : '') + a.min + ' min</span></span><span class="ep__desc">' + esc(epDesc(a)) + '</span></span>';
      if (a.bloqueada) return '<li class="ep is-locked" title="Libera em ' + fmtData(emDias(m.bloqueado)) + '">' + inner + '</li>';
      return '<li><a class="ep' + (st && a.id === cur.id ? ' is-current' : '') + '" href="#/aula/' + c.id + '/' + a.id + '">' + inner + '</a></li>';
    }).join('') + '</ol>';
  }
  function dlBtn() {
    return '<button class="btn btn--sm btn--outline" aria-label="Baixar" data-action="toast" data-msg="Download ilustrativo neste protótipo" data-ico="download">' + icon('download') + '<span>Baixar</span></button>';
  }
  /* O único material de apoio é o e-book: um para cada aula, na mentoria e nos cursos. */
  const EBOOKS = '#/mentoria?aba=ebooks';
  function ebookFile(a) {
    return '<div class="file"><span class="file__ico">' + icon('book') + '</span><div><strong>' + esc(a.titulo) + '</strong><span>Aula ' + a.n + ' · PDF</span></div>' + dlBtn() + '</div>';
  }
  function ebooksEntry(c, tag, attrs) {
    return '<div class="files"><' + tag + ' class="file file--link" ' + attrs + '><span class="file__ico">' + icon('book') + '</span><div><strong>E-books</strong><span>' + c.aulas.length + ' e-books · um por aula</span></div>' + icon('right', 'file__chev') + '</' + tag + '></div>';
  }
  function empty(ic, title, text, cta) {
    return '<div class="empty">' + icon(ic) + '<h2>' + esc(title) + '</h2><p>' + esc(text) + '</p>' + (cta || '') + '</div>';
  }
  function heroArt() {
    const beat = 'h120l14-22 14 22h24l16-150 22 250 16-100h30q22-50 44 0h100';
    const d = 'M0 230' + beat + beat + beat + beat;
    return '<div class="hero__bg"><div class="hero__grid"></div><svg class="hero__ecg" viewBox="0 0 1600 420" aria-hidden="true"><path class="trace" d="' + d + '"/><path class="beam" pathLength="2060" d="' + d + '"/></svg><div class="hero__fade"></div></div>';
  }

  /* ------------------------------------------------------------------ casca */
  const NAV = [['/', 'Início', 'home'], ['/mentoria', 'Mentoria', 'bolt'], ['/cursos', 'Cursos', 'grid'], ['/trilhas', 'Trilhas', 'route'], ['/ao-vivo', 'Ao vivo', 'live'], ['/minha-lista', 'Minha lista', 'list']];
  function renderShell() {
    const novas = notificacoes.filter((n) => n.nova).length;
    $('#nav').innerHTML =
      '<a class="nav__brand" href="#/">' + esc(marca.nome) + '</a>' +
      '<nav class="nav__links" aria-label="Principal">' + NAV.map((n) => '<a href="#' + n[0] + '" data-nav="' + n[0] + '">' + n[1] + '</a>').join('') + '</nav>' +
      '<div class="nav__tools">' +
        '<form class="search" id="search" role="search"><button type="button" class="nav__icon" data-action="search-open" aria-label="Buscar">' + icon('search') + '</button><input class="search__input" id="q" type="search" placeholder="Cursos, aulas, áreas" aria-label="Buscar" autocomplete="off"></form>' +
        '<div class="dd"><button class="nav__icon" data-action="dd" aria-haspopup="true" aria-expanded="false" aria-label="Notificações">' + icon('bell') + (novas ? '<span class="nav__dot">' + novas + '</span>' : '') + '</button>' +
          '<div class="dd__panel">' + notificacoes.map((n) => '<a class="notif' + (n.nova ? ' is-new' : '') + '" href="' + n.href + '"><span class="notif__ico">' + icon(n.icone) + '</span><span><strong>' + esc(n.titulo) + '</strong><p>' + esc(n.texto) + '</p><time>' + n.quando + '</time></span></a>').join('') + '</div></div>' +
        '<div class="dd"><button class="nav__profile" data-action="dd" aria-haspopup="true" aria-expanded="false" aria-label="Conta de ' + esc(usuario.nome) + '"><span class="avatar">' + usuario.iniciais + '</span><span class="caret"></span></button>' +
          '<div class="dd__panel dd__panel--menu"><div class="dd__head"><span class="avatar">' + usuario.iniciais + '</span><div><strong>' + esc(usuario.nome) + '</strong><span>Mentoria ' + esc(marca.mentoria) + '</span></div></div>' +
          '<a class="dd__item" href="#/progresso">' + icon('target') + 'Meu progresso</a><a class="dd__item" href="#/certificados">' + icon('award') + 'Certificado</a><a class="dd__item" href="#/minha-lista">' + icon('list') + 'Minha lista</a><a class="dd__item" href="#/conta">' + icon('sliders') + 'Conta e preferências</a>' +
          '<div class="dd__sep"></div><a class="dd__item" href="#/ajuda">' + icon('help') + 'Central de ajuda</a><a class="dd__item" href="#/entrar">' + icon('logout') + 'Sair</a></div></div>' +
      '</div>';
    const TAB = [['/', 'Início', 'home'], ['/mentoria', 'Mentoria', 'bolt'], ['/cursos', 'Cursos', 'grid'], ['/ao-vivo', 'Ao vivo', 'live'], ['/progresso', 'Progresso', 'target']];
    $('#tabbar').innerHTML = TAB.map((n) => '<a href="#' + n[0] + '" data-nav="' + n[0] + '">' + icon(n[2]) + '<span>' + n[1] + '</span></a>').join('');
    $('#footer').innerHTML =
      '<div class="footer__links"><a href="#/mentoria">Mentoria ' + esc(marca.mentoria) + '</a><a href="#/cursos">Todos os cursos</a><a href="#/trilhas">Trilhas</a><a href="#/ao-vivo">Agenda ao vivo</a><a href="#/progresso">Meu progresso</a><a href="#/certificados">Certificado</a><a href="#/conta">Conta</a><a href="#/entrar">Tela de entrada</a></div>' +
      '<div class="footer__note"><span>' + esc(marca.nome) + ' · protótipo de interface com conteúdo fictício</span><button data-action="reset">Restaurar dados de exemplo</button></div>';
  }
  function updateNav(path) {
    const key = path.indexOf('/trilha') === 0 ? '/trilhas' : path.indexOf('/aula/' + MENTORIA.id) === 0 ? '/mentoria' : path;
    $$('[data-nav]').forEach((a) => a.classList.toggle('is-active', a.dataset.nav === key));
  }

  /* ---------------------------------------------------------------- páginas */
  let cleanups = [];

  function home(el) {
    const a = nextAula(MENTORIA), p = pct(MENTORIA), prox = lives.find((l) => l.mentoria), mod = MENTORIA.modulos[a.modulo];
    const pos = (P(MENTORIA.id) && P(MENTORIA.id).pos[a.id]) || 0;
    const porArea = (k) => cursos.filter((c) => c.area === k && c.tipo !== 'mentoria');
    const lista = S.list.map((id) => byId[id]).filter(Boolean);

    el.innerHTML =
      '<section class="hero">' + heroArt() +
        '<div class="hero__content"><p class="hero__kicker"><span class="tag tag--red">Mentoria</span><span>' + turmaTxt() + ' · encontros ao vivo</span></p>' +
        '<h1 class="hero__title">Plantão<br>sem GPT</h1><p class="hero__desc">' + esc(MENTORIA.desc) + '</p>' +
        '<div class="hero__actions"><a class="btn btn--light btn--lg" href="#/aula/' + MENTORIA.id + '/' + a.id + '">' + icon('play') + (p ? 'Continuar' : 'Começar') + '</a><a class="btn btn--dim btn--lg" href="#/mentoria">' + icon('info') + 'Mais informações</a></div>' +
        '<div class="hero__resume"><strong>Semana ' + (mod.i + 1) + ' · Aula ' + a.n + '</strong> — ' + esc(a.titulo) + (pos ? ' · restam ' + Math.max(1, Math.round(a.min - pos / 60)) + ' min' : '') + '<span class="progressbar" aria-label="' + p + '% da mentoria concluída"><i style="width:' + p + '%"></i></span></div></div>' +
        (prox ? '<a class="hero__side" href="#/ao-vivo">' + icon('live') + '<span>Próximo encontro ao vivo: <strong>' + fmtQuando(prox.quando) + '</strong></span></a>' : '') +
      '</section>' +
      '<div class="rails rails--overlap">' +
        rail('Continue de onde parou, ' + usuario.tratamento, emAndamento().map(continueCard), { href: '#/progresso' }) +
        rail('Top 10 no plantão esta semana', top10.map((id, i) => top10Card(byId[id], i))) +
        rail('Sua jornada na mentoria ' + marca.mentoria, MENTORIA.modulos.map(weekCard), { href: '#/mentoria' }) +
        rail('Novidades', cursos.filter((c) => c.novo).concat(cursos.filter((c) => c.ano === 2026 && !c.novo && c.tipo !== 'mentoria')).map(card), { href: '#/cursos' }) +
        rail('Trilhas para seguir em ordem', trilhas.map(trackCard), { href: '#/trilhas', cls: 'rail--wide' }) +
        rail('Cardiologia', porArea('cardio').concat(porArea('uti')).map(card), { href: '#/cursos?area=cardio' }) +
        rail('Próximos encontros ao vivo', lives.map(liveCard), { href: '#/ao-vivo', cls: 'rail--mid' }) +
        rail('Via aérea, ventilação e paciente grave', porArea('viaaerea').concat(porArea('infecto'), porArea('emergencia')).map(card), { href: '#/cursos' }) +
        rail('Minha lista', lista.map(card), { href: '#/minha-lista' }) +
        rail('Rotina, comunicação e carreira', porArea('rotina').concat(porArea('neuro'), porArea('trauma')).map(card), { href: '#/cursos?area=rotina' }) +
      '</div>' +
      '<section class="showcase" aria-label="Cursos à venda">' + rail('Cursos à venda', ofertas.map(salePoster), { head:
        '<div class="showcase__head"><p class="hero__kicker"><span class="tag tag--red">À venda</span><span>' + ofertas.length + ' cursos vendidos à parte</span></p>' +
        '<h2 class="showcase__title">Outros cursos da ' + esc(marca.nome) + '</h2>' +
        '<p class="showcase__sub">Escolha um para ver o conteúdo e comprar.</p></div>' }) +
      '</section>';
    initRails(el);
  }

  /* --- mentoria --- */
  let mentoriaTab = 'jornada';
  function mentoria(el, params, query) {
    const c = MENTORIA, a = nextAula(c), p = pct(c), prox = lives.find((l) => l.mentoria);
    const tabs = [['jornada', 'Jornada'], ['encontros', 'Encontros ao vivo'], ['ebooks', 'E-books'], ['comunidade', 'Comunidade']];
    const aba = query && query.get('aba');
    mentoriaTab = tabs.some((t) => t[0] === aba) ? aba : 'jornada';
    el.innerHTML =
      '<section class="hero hero--page">' + heroArt() +
        '<div class="hero__content"><p class="hero__kicker"><span class="tag tag--red">Mentoria</span><span>' + turmaTxt() + ' · encontros ao vivo</span></p>' +
        '<h1 class="hero__title">Plantão<br>sem GPT</h1><p class="hero__desc">' + esc(c.desc) + '</p>' +
        '<div class="hero__actions"><a class="btn btn--light btn--lg" href="#/aula/' + c.id + '/' + a.id + '">' + icon('play') + 'Continuar: aula ' + a.n + '</a>' + listBtn(c.id, 'text') + '</div>' +
        '<ul class="facts"><li>' + icon('calendar') + '8 semanas</li><li>' + icon('play') + c.aulas.length + ' aulas · ' + fmtMin(c.totalMin) + '</li><li>' + icon('live') + 'Encontros ao vivo às quintas, 20h</li><li>' + icon('users') + c.alunos.toLocaleString('pt-BR') + ' participantes</li><li>' + icon('award') + 'Certificado ao final</li></ul></div>' +
      '</section>' +
      '<div class="subnav"><div class="tabs" role="tablist">' + tabs.map((t) => '<button class="tab' + (t[0] === mentoriaTab ? ' is-on' : '') + '" role="tab" aria-selected="' + (t[0] === mentoriaTab) + '" data-mtab="' + t[0] + '">' + t[1] + '</button>').join('') + '</div></div>' +
      '<div class="page" style="padding-top:28px;min-height:50vh" id="mpanel"></div>';

    const panel = $('#mpanel', el);
    function weeks() {
      return '<div class="weeks">' + c.modulos.map((m) => {
        const d = m.aulas.filter((x) => isDone(c, x)).length, tot = m.aulas.length, min = m.aulas.reduce((s, x) => s + x.min, 0);
        const st = m.bloqueado ? 'locked' : d === tot ? 'done' : m.i === a.modulo ? 'now' : 'open';
        const meta = m.bloqueado ? 'Libera em ' + fmtData(emDias(m.bloqueado)) : d === tot ? 'Concluída' : d ? d + ' de ' + tot + ' aulas concluídas' : 'Liberada';
        return '<details class="week is-' + st + '"' + (st === 'now' ? ' open' : '') + '><summary><span class="week__n">' + (st === 'done' ? icon('check') : st === 'locked' ? icon('lock') : m.i + 1) + '</span>' +
          '<div><p class="eyebrow">Semana ' + (m.i + 1) + '</p><h3>' + esc(m.titulo) + '</h3><p class="week__meta">' + tot + ' aulas · ' + fmtMin(min) + ' · ' + meta + '</p></div>' +
          (m.bloqueado ? '<span></span>' : ring(Math.round((d / tot) * 100), 40, 4)) + icon('down', 'week__chev') + '</summary>' + epList(c, m.i, true) + '</details>';
      }).join('') + '</div>';
    }
    function paint() {
      if (mentoriaTab === 'jornada') {
        panel.innerHTML = '<div class="mgrid"><div><h2 class="section-title">Oito semanas, uma por vez</h2>' + weeks() + '</div>' +
          '<aside class="aside-stack">' +
            '<div class="panel"><div class="goal">' + ring(p, 84, 8) + '<div><strong>' + p + '%</strong><p>' + doneCount(c) + ' de ' + c.aulas.length + ' aulas concluídas</p></div></div><a class="btn btn--red btn--block" style="margin-top:18px" href="#/aula/' + c.id + '/' + a.id + '">' + icon('play') + 'Continuar de onde parei</a></div>' +
            (prox ? '<div class="panel"><div class="panel__head"><h3>Próximo encontro</h3>' + contador(prox.quando) + '</div><p style="font-weight:600;line-height:1.35">' + esc(prox.titulo) + '</p><p class="muted" style="font-size:14px;margin:6px 0 14px">' + cap(fmtQuando(prox.quando)) + ' · ' + prox.min + ' min</p>' + remindBtn(prox) + '</div>' : '') +
            '<div class="panel"><div class="panel__head"><h3>Materiais da mentoria</h3></div>' + ebooksEntry(c, 'button', 'type="button" data-mtab="ebooks"') + '</div>' +
          '</aside></div>';
      } else if (mentoriaTab === 'ebooks') {
        const abertas = c.modulos.filter((m) => !m.bloqueado), fechadas = c.modulos.filter((m) => m.bloqueado);
        panel.innerHTML = '<div class="ebooks"><h2 class="section-title">Um e-book para cada aula</h2>' +
          '<p class="ebooks__lead">' + c.aulas.filter((x) => !x.bloqueada).length + ' de ' + c.aulas.length + ' e-books liberados. Os próximos chegam junto com as aulas de cada semana.</p>' +
          abertas.map((m) => '<section class="ebooks__week"><p class="eyebrow">Semana ' + (m.i + 1) + '</p><h3>' + esc(m.titulo) + '</h3><div class="files files--cols">' + m.aulas.map(ebookFile).join('') + '</div></section>').join('') +
          (fechadas.length ? '<section class="ebooks__week"><p class="eyebrow">Em breve</p><h3>Próximas semanas</h3><div class="files files--cols">' + fechadas.map((m) =>
            '<div class="file is-locked"><span class="file__ico">' + icon('lock') + '</span><div><strong>Semana ' + (m.i + 1) + ' · ' + esc(m.titulo) + '</strong><span>' + m.aulas.length + ' e-books · libera em ' + fmtData(emDias(m.bloqueado)) + '</span></div></div>').join('') + '</div></section>' : '') +
          '</div>';
      } else if (mentoriaTab === 'encontros') {
        panel.innerHTML = '<h2 class="section-title">Próximos encontros da turma</h2><div class="agenda">' + lives.filter((l) => l.mentoria).map(agendaItem).join('') + '</div>';
      } else {
        panel.innerHTML = '<div class="feed"><form class="composer" id="composer"><label class="sr-only" for="post">Escreva para a turma</label><textarea class="input" id="post" placeholder="Compartilhe um caso, uma dúvida ou uma vitória do plantão…" maxlength="600"></textarea><div class="composer__foot"><span>Visível para a turma ' + marca.turma + ' da mentoria</span><button class="btn btn--red btn--sm" type="submit">Publicar</button></div></form>' +
          todosPosts().map(postHTML).join('') + '</div>';
      }
    }

    /* --- comunidade: as respostas abrem logo abaixo da publicação, na mesma página --- */
    S.posts = S.posts.map((x, i) => (typeof x === 'string' ? { id: 'u' + i + '-' + x.length, texto: x } : x));
    const fios = () => S.replies || (S.replies = {});
    const abertas = new Set(), curtidas = new Set(), novas = new Set();
    const meuPost = (x) => ({ id: x.id, autor: usuario.nome, iniciais: usuario.iniciais, quando: 'agora', curtidas: 0, respostas: [], texto: x.texto, meu: true });
    const todosPosts = () => S.posts.map(meuPost).concat(comunidade);
    const quem = (x) => '<span class="avatar avatar--round' + (x.mentor || x.meu ? '' : ' avatar--gray') + '">' + x.iniciais + '</span>';
    const cabeca = (x, extra) => '<div class="post__head"><strong>' + esc(x.autor) + '</strong>' + (x.mentor ? '<span class="tag tag--red">Mentora</span>' : '') + '<time>' + x.quando + '</time>' + (extra || '') + '</div>';
    function postHTML(po) {
      const rs = po.respostas.concat(fios()[po.id] || []), n = rs.length, aberta = abertas.has(po.id), curti = curtidas.has(po.id);
      return '<article class="post" data-post="' + po.id + '">' + quem(po) + '<div>' + cabeca(po) + '<p>' + esc(po.texto) + '</p>' +
        '<div class="post__foot"><button class="' + (curti ? 'is-on' : '') + '" data-like="' + po.id + '" data-n="' + po.curtidas + '" aria-pressed="' + curti + '" aria-label="Curtir">' + icon('heart') + '<span>' + (po.curtidas + (curti ? 1 : 0)) + '</span></button>' +
        '<button data-thread="' + po.id + '" aria-expanded="' + aberta + '">' + icon('message') + (n ? n + (n === 1 ? ' resposta' : ' respostas') : 'Responder') + icon('down', 'post__chev') + '</button></div>' +
        (aberta ? '<div class="thread">' +
          (n ? '<ol class="thread__list">' + rs.map((r, k) => { const nova = novas.has(po.id + ':' + k); return '<li class="reply' + (nova ? ' is-new' : '') + '">' + quem(r) + '<div>' + cabeca(r, nova ? '<span class="tag tag--line">Nova</span>' : '') + '<p>' + esc(r.texto) + '</p></div></li>'; }).join('') + '</ol>'
             : '<p class="thread__empty">Ainda sem respostas. Elas aparecem aqui, logo abaixo da publicação.</p>') +
          '<form class="thread__form" data-reply="' + po.id + '">' + quem({ iniciais: usuario.iniciais, meu: true }) + '<label class="sr-only" for="r-' + po.id + '">Sua resposta</label><input class="input" id="r-' + po.id + '" placeholder="Escreva uma resposta…" maxlength="400" autocomplete="off"><button class="btn btn--red btn--sm" type="submit">Responder</button></form></div>' : '') +
        '</div></article>';
    }
    /* redesenha só uma publicação, sem perder o que estiver sendo digitado na resposta */
    function refreshPost(id, foco) {
      const art = $('[data-post="' + id + '"]', panel), po = todosPosts().find((x) => x.id === id);
      if (!art || !po) return;
      const campo = $('.thread__form .input', art), rascunho = campo ? campo.value : '', digitando = !!campo && document.activeElement === campo;
      art.outerHTML = postHTML(po);
      const novo = $('[data-post="' + id + '"] .thread__form .input', panel);
      if (novo) novo.value = rascunho;
      const alvo = (foco === 'campo' || digitando) ? novo : foco === 'botao' ? $('[data-post="' + id + '"] [data-thread]', panel) : null;
      if (alvo) alvo.focus({ preventScroll: true });
    }
    /* Protótipo: alguns segundos depois de publicar, simula a chegada de uma resposta da mentora. */
    function simularResposta(id) {
      setTimeout(() => {
        if (!S.posts.some((x) => x.id === id)) return;
        const lista = fios()[id] || (fios()[id] = []), m = instrutores.helena;
        lista.push({ autor: m.nome, iniciais: m.iniciais, mentor: true, quando: 'agora', texto: 'Obrigada por compartilhar! Vou levar esse ponto para o próximo encontro ao vivo, para discutirmos com a turma.' });
        save();
        toast(m.nome + ' respondeu sua publicação (resposta de exemplo)', 'message');
        if (document.contains(panel) && mentoriaTab === 'comunidade') { abertas.add(id); novas.add(id + ':' + (lista.length - 1)); refreshPost(id); }
      }, 4000);
    }

    function agendaItem(l) {
      return '<article class="agenda__item">' + dateBox(l.quando) + '<div><div class="tagrow"><span class="tag ' + (l.mentoria ? 'tag--red' : 'tag--line') + '">' + esc(l.tipo) + '</span>' + contador(l.quando) + '</div><h3>' + esc(l.titulo) + '</h3><p>' + cap(fmtQuando(l.quando)) + ' · ' + l.min + ' min</p></div>' + remindBtn(l) + '</article>';
    }
    mentoria.agendaItem = agendaItem;
    paint();

    el.onclick = (e) => {
      const t = e.target.closest('[data-mtab]');
      if (t) {
        mentoriaTab = t.dataset.mtab;
        /* a aba fica no endereço, para voltar a ela ao fechar a janela de um curso */
        currentRaw = '/mentoria' + (mentoriaTab === 'jornada' ? '' : '?aba=' + mentoriaTab);
        history.replaceState(null, '', '#' + currentRaw);
        const bar = $('.tabs', el);
        $$('.tab[data-mtab]', el).forEach((b) => {
          const on = b.dataset.mtab === mentoriaTab;
          b.classList.toggle('is-on', on); b.setAttribute('aria-selected', on);
          if (on) { const x = b.offsetLeft - bar.offsetLeft; if (x < bar.scrollLeft || x + b.offsetWidth > bar.scrollLeft + bar.clientWidth) bar.scrollLeft = x - 16; }
        });
        paint();
        const topo = panel.getBoundingClientRect().top + window.scrollY - nav.offsetHeight - $('.subnav', el).offsetHeight;
        if (window.scrollY > topo) window.scrollTo(0, topo);
        return;
      }
      const th = e.target.closest('[data-thread]');
      if (th) {
        const id = th.dataset.thread, abrir = !abertas.has(id);
        if (abrir) abertas.add(id); else { abertas.delete(id); Array.from(novas).forEach((k) => { if (k.indexOf(id + ':') === 0) novas.delete(k); }); }
        /* sem respostas ainda, o clique em "Responder" já leva ao campo de texto */
        const total = todosPosts().find((x) => x.id === id).respostas.length + (fios()[id] || []).length;
        refreshPost(id, abrir && !total ? 'campo' : 'botao');
        return;
      }
      const lk = e.target.closest('[data-like]');
      if (lk) {
        const id = lk.dataset.like, on = !curtidas.has(id);
        if (on) curtidas.add(id); else curtidas.delete(id);
        lk.classList.toggle('is-on', on); lk.setAttribute('aria-pressed', on);
        $('span', lk).textContent = Number(lk.dataset.n) + (on ? 1 : 0);
      }
    };
    el.onsubmit = (e) => {
      const f = e.target;
      if (f.id === 'composer') {
        e.preventDefault();
        const campo = $('#post', el), v = campo.value.trim();
        if (!v) return;
        const novo = { id: 'u' + Date.now(), texto: v };
        S.posts.unshift(novo); save();
        campo.value = '';
        abertas.add(novo.id); /* já aberta, mostrando onde as respostas vão aparecer */
        f.insertAdjacentHTML('afterend', postHTML(meuPost(novo)));
        toast('Publicado para a turma');
        simularResposta(novo.id);
      } else if (f.dataset.reply) {
        e.preventDefault();
        const id = f.dataset.reply, campo = $('.input', f), v = campo.value.trim();
        if (!v) return;
        (fios()[id] || (fios()[id] = [])).push({ autor: usuario.nome, iniciais: usuario.iniciais, quando: 'agora', texto: v, meu: true });
        save(); campo.value = '';
        refreshPost(id, 'campo');
      }
    };
    cleanups.push(() => { el.onclick = null; el.onsubmit = null; });
  }

  /* --- catálogo --- */
  /* Um único filtro, "Filtro", por status do conteúdo. Sem status escolhido, mostra tudo. */
  const F = { area: 'todas', status: 'todos' };
  const STATUS = [['novos', 'Novos'], ['andamento', 'Em andamento'], ['concluidos', 'Concluídos'], ['top', 'Mais assistidos']];
  function catalog(el, params, query) {
    if (query.get('area') && areas[query.get('area')]) F.area = query.get('area');
    const base = cursos.filter((c) => c.tipo !== 'mentoria');
    el.innerHTML = '<div class="page"><header class="page__head"><div><h1 class="page__title">Cursos</h1><p class="page__sub">Tudo o que está incluído na sua assinatura, organizado por área. Filtre para achar o que resolve o seu próximo plantão.</p></div></header>' +
      '<div class="chips" id="areas"></div><div class="toolbar"><span class="toolbar__count" id="count" aria-live="polite"></span><div class="toolbar__ctl"><div class="dd dd--filter" id="filtro"></div></div></div>' +
      '<div class="grid" id="grid"></div></div>';
    const passa = {
      todos: () => true,
      novos: (c) => !!c.novo,
      andamento: (c) => started(c) && pct(c) < 100,
      concluidos: (c) => pct(c) === 100,
      top: (c) => top10.indexOf(c.id) >= 0,
    };
    const ordem = {
      andamento: (a, b) => pct(b) - pct(a),
      top: (a, b) => top10.indexOf(a.id) - top10.indexOf(b.id),
    };
    const vazio = {
      todos: 'Não há cursos nesta área.',
      novos: 'Nenhum curso novo nesta seleção.',
      andamento: 'Você não tem cursos em andamento nesta seleção.',
      concluidos: 'Você ainda não concluiu cursos nesta seleção.',
      top: 'Nenhum dos mais assistidos está nesta área.',
    };
    function paintFiltro() {
      const atual = STATUS.find((x) => x[0] === F.status);
      $('#filtro', el).innerHTML =
        '<button class="fbtn' + (atual ? ' is-on' : '') + '" data-action="dd" aria-haspopup="true" aria-expanded="false">' + icon('sliders') + '<span>Filtro' + (atual ? ': <strong>' + atual[1] + '</strong>' : '') + '</span><span class="caret"></span></button>' +
        '<div class="dd__panel dd__panel--menu" role="menu" aria-label="Filtrar por status">' +
          STATUS.map((x) => '<button class="dd__item" role="menuitemradio" aria-checked="' + (x[0] === F.status) + '" data-status="' + x[0] + '">' + icon('check') + x[1] + '</button>').join('') +
          (atual ? '<div class="dd__sep"></div><button class="dd__item" role="menuitem" data-status="todos">' + icon('close') + 'Limpar filtro</button>' : '') +
        '</div>';
    }
    function paint() {
      $('#areas', el).innerHTML = '<button class="chip' + (F.area === 'todas' ? ' is-on' : '') + '" data-area="todas">Todas as áreas</button>' +
        Object.keys(areas).map((k) => '<button class="chip' + (F.area === k ? ' is-on' : '') + '" data-area="' + k + '">' + areas[k].nome + '</button>').join('');
      paintFiltro();
      const r = base.filter((c) => (F.area === 'todas' || c.area === F.area) && passa[F.status](c)).sort(ordem[F.status] || ((a, b) => b.alunos - a.alunos));
      const n = r.length, pl = n === 1 ? '' : 's';
      const sufixo = { todos: '', novos: ' novo' + pl, andamento: ' em andamento', concluidos: ' concluído' + pl, top: ' entre os mais assistidos' }[F.status];
      $('#count', el).textContent = n + ' curso' + pl + sufixo + (F.area !== 'todas' ? ' em ' + areas[F.area].nome : '');
      const grid = $('#grid', el);
      grid.style.display = n ? '' : 'block';
      grid.innerHTML = n ? r.map(gcard).join('') : empty('search', 'Nada por aqui ainda', vazio[F.status], F.area !== 'todas' || F.status !== 'todos' ? '<button class="btn btn--outline" data-clear>Limpar filtros</button>' : '');
    }
    paint();
    el.onclick = (e) => {
      const ch = e.target.closest('[data-area]');
      if (ch) { F.area = ch.dataset.area; paint(); }
      const st = e.target.closest('[data-status]');
      if (st) {
        /* clicar de novo no status ativo também limpa o filtro */
        F.status = st.dataset.status === F.status ? 'todos' : st.dataset.status;
        closeTransient(); paint();
        $('.fbtn', el).focus({ preventScroll: true });
      }
      if (e.target.closest('[data-clear]')) { F.area = 'todas'; F.status = 'todos'; paint(); }
    };
    cleanups.push(() => { el.onclick = null; });
  }

  /* --- trilhas --- */
  function tracks(el) {
    el.innerHTML = '<div class="page"><header class="page__head"><div><h1 class="page__title">Trilhas</h1><p class="page__sub">Sequências de cursos montadas para um objetivo. Siga na ordem e acompanhe o avanço de cada etapa.</p></div></header><div class="tracklist">' + trilhas.map(trackCard).join('') + '</div></div>';
  }
  function track(el, params) {
    const t = trilhas.find((x) => x.id === params[0]);
    if (!t) return notFound(el);
    const s = trackStats(t), now = s.cs.find((c) => pct(c) < 100) || s.cs[0];
    el.innerHTML = '<div class="page"><nav class="crumbs"><a href="#/trilhas">' + icon('left') + 'Trilhas</a></nav>' +
      '<header class="page__head"><div><p class="eyebrow">Trilha · ' + s.cs.length + ' cursos · ' + fmtMin(s.min) + '</p><h1 class="page__title" style="margin-top:8px">' + esc(t.titulo) + '</h1><p class="page__sub">' + esc(t.desc) + '</p></div>' +
      '<div class="goal">' + ring(s.p, 72, 7) + '<div><strong>' + s.p + '%</strong><p>da trilha concluída</p></div></div></header>' +
      '<ol class="steps">' + s.cs.map((c, i) => {
        const p = pct(c), a = nextAula(c), st = p === 100 ? 'done' : c === now ? 'now' : '';
        return '<li><a class="step' + (st ? ' is-' + st : '') + '" href="#/curso/' + c.id + '"><span class="step__n">' + (p === 100 ? icon('check') : i + 1) + '</span>' + courseCover(c) +
          '<div><h3>' + esc(c.titulo) + '</h3><p>' + esc(c.desc) + '</p><div class="step__meta"><span>' + c.aulas.length + ' aulas · ' + fmtMin(c.totalMin) + '</span>' + (p ? '<span class="progressbar"><i style="width:' + p + '%"></i></span><span>' + p + '%</span>' : '') + '</div></div>' +
          '<span class="btn btn--sm ' + (st === 'now' ? 'btn--light' : 'btn--outline') + '">' + (p === 100 ? 'Rever' : p ? 'Continuar · aula ' + a.n : 'Começar') + '</span></a></li>';
      }).join('') + '</ol></div>';
  }

  /* --- ao vivo --- */
  function live(el) {
    const l = lives[0];
    el.innerHTML = '<div class="page"><header class="page__head"><div><h1 class="page__title">Ao vivo</h1><p class="page__sub">Encontros da mentoria, plantões de dúvidas e aulas abertas. Ative o lembrete e a gente avisa quando começar.</p></div></header>' +
      '<section class="livehero"><div>' + contador(l.quando) + '<h2>' + esc(l.titulo) + '</h2><p>' + esc(l.desc) + '</p><p class="muted" style="margin-top:10px;font-size:14px">' + cap(fmtQuando(l.quando)) + ' · ' + l.min + ' min</p>' +
      '<div class="countdown" id="cd" aria-label="Tempo até o início"></div><div class="livehero__actions"><button class="btn btn--red" data-action="toast" data-msg="A sala abre 10 minutos antes do início" data-ico="live">' + icon('live') + 'Entrar na sala</button>' + remindBtn(l) + '</div></div>' +
      cover({ h: l.h, motif: l.motif, title: l.titulo.split(':').pop().trim(), kicker: l.tipo }) + '</section>' +
      '<h2 class="section-title">Agenda</h2><div class="agenda">' + lives.slice(1).map(mentoria.agendaItem || agendaFallback).join('') + '</div>' +
      (novosConteudos().length ? '' : '<h2 class="section-title">Novos conteúdos</h2><p class="muted">Nenhum conteúdo publicado ou atualizado nos últimos ' + JANELA_NOVOS + ' dias.</p>') + '</div>' +
      '<div class="rails" style="margin-top:8px">' + rail('Novos conteúdos', novosConteudos().map(novoCard), { note: 'Nos últimos ' + JANELA_NOVOS + ' dias' }) + '</div>';
    initRails(el);
    const cd = $('#cd', el);
    const tick = () => {
      let s = Math.max(0, Math.floor((l.quando - new Date()) / 1000));
      const d = Math.floor(s / 86400); s -= d * 86400;
      const h = Math.floor(s / 3600); s -= h * 3600;
      const m = Math.floor(s / 60); s -= m * 60;
      const parts = (d ? [[d, 'dias']] : []).concat([[h, 'horas'], [m, 'min'], [s, 'seg']]);
      cd.innerHTML = parts.map((x) => '<div><b>' + String(x[0]).padStart(2, '0') + '</b><span>' + x[1] + '</span></div>').join('');
    };
    tick();
    const iv = setInterval(tick, 1000);
    cleanups.push(() => clearInterval(iv));
  }
  function agendaFallback(l) {
    return '<article class="agenda__item">' + dateBox(l.quando) + '<div><div class="tagrow"><span class="tag ' + (l.mentoria ? 'tag--red' : 'tag--line') + '">' + esc(l.tipo) + '</span>' + contador(l.quando) + '</div><h3>' + esc(l.titulo) + '</h3><p>' + cap(fmtQuando(l.quando)) + ' · ' + l.min + ' min</p></div>' + remindBtn(l) + '</article>';
  }

  /* --- minha lista --- */
  function myList(el) {
    const items = S.list.map((id) => byId[id]).filter(Boolean);
    el.innerHTML = '<div class="page"><header class="page__head"><div><h1 class="page__title">Minha lista</h1><p class="page__sub">Cursos que você guardou para assistir depois.</p></div></header>' +
      (items.length ? '<div class="grid">' + items.map(gcard).join('') + '</div>' : empty('list', 'Sua lista está vazia', 'Toque no “+” de qualquer curso para guardá-lo aqui e encontrar rápido depois.', '<a class="btn btn--light" href="#/cursos">Explorar cursos</a>')) + '</div>';
  }

  /* --- progresso --- */
  function progress(el) {
    const andamento = emAndamento();
    const aulas = cursos.reduce((s, c) => s + doneCount(c), 0);
    const min = cursos.reduce((s, c) => s + c.aulas.filter((a) => isDone(c, a)).reduce((x, a) => x + a.min, 0), 0);
    const valores = estudoSemana.map((v, i) => minutosDoDia(i));
    const semana = valores.reduce((s, v) => s + v, 0), maior = Math.max.apply(null, valores);
    const teto = Math.max(90, Math.ceil(maior / 30) * 30); /* a escala cresce se um dia passar de 90 minutos */
    const dias = valores.map((v, i) => { const d = emDias(i - 6); return { v, curto: d.toLocaleDateString('pt-BR', { weekday: 'short' }).replace('.', ''), longo: d.toLocaleDateString('pt-BR', { weekday: 'long' }), hoje: i === 6 }; });
    el.innerHTML = '<div class="page"><header class="page__head"><div><h1 class="page__title">Meu progresso</h1><p class="page__sub">O que você estudou, o que está em andamento e o que já concluiu.</p></div></header>' +
      '<div class="stats">' +
        '<div class="stat"><p class="stat__label">' + icon('flame') + 'Sequência de estudo</p><p class="stat__value">12<small>dias</small></p><p class="stat__delta">Seu recorde é de 19 dias</p></div>' +
        '<div class="stat"><p class="stat__label">' + icon('clock') + 'Tempo de estudo</p><p class="stat__value">' + Math.floor(min / 60) + '<small>h ' + String(min % 60).padStart(2, '0') + 'min</small></p><p class="stat__delta"><b>+' + fmtMin(semana) + '</b> nos últimos 7 dias</p></div>' +
        '<div class="stat"><p class="stat__label">' + icon('play') + 'Aulas concluídas</p><p class="stat__value">' + aulas + '</p><p class="stat__delta">em ' + cursos.filter(started).length + ' cursos</p></div>' +
      '</div>' +
      '<div class="split split--one"><section class="panel"><div class="panel__head"><div><h2>Minutos de estudo por dia</h2><p>Últimos 7 dias · total de ' + fmtMin(semana) + '</p></div></div>' +
        '<div class="chart" role="img" aria-label="Minutos de estudo por dia nos últimos sete dias; maior valor ' + maior + ' minutos"><div class="chart__grid">' + [0, teto / 3, (teto / 3) * 2, teto].map((t) => '<span style="bottom:' + (t / teto) * 100 + '%"><em>' + t + '</em></span>').join('') + '</div>' +
        '<div class="chart__cols">' + dias.map((d) => '<div class="chart__col' + (d.hoje ? ' is-today' : '') + (d.v ? '' : ' is-zero') + '" tabindex="0" style="--v:' + (d.v / teto) * 100 + '%" aria-label="' + d.longo + ': ' + d.v + ' minutos">' +
          (d.v === maior || d.hoje ? '<span class="chart__val">' + d.v + '</span>' : '') + '<i class="chart__bar" style="height:' + (d.v / teto) * 100 + '%"></i><span class="chart__tip">' + cap(d.longo) + ' · ' + d.v + ' min</span><span class="chart__x">' + (d.hoje ? 'hoje' : d.curto) + '</span></div>').join('') + '</div></div></section>' +
      '</div>' +
      '<h2 class="section-title">Em andamento</h2>' + (andamento.length ? '<div class="rows">' + andamento.map((c) => { const a = nextAula(c); return '<a class="row" href="#/aula/' + c.id + '/' + a.id + '">' + courseCover(c, { shape: 'thumb' }) + '<div><strong>' + esc(c.titulo) + '</strong><span>Próxima: aula ' + a.n + ' · ' + esc(a.titulo) + '</span><span class="progressbar"><i style="width:' + pct(c) + '%"></i></span></div><span class="btn btn--sm btn--outline">' + icon('play') + pct(c) + '%</span></a>'; }).join('') + '</div>' : '<p class="muted">Nenhum curso em andamento.</p>') + '</div>';
  }

  /* --- certificado --- */
  /* Existe um único certificado: o da mentoria, liberado só ao final dela. Cursos e aulas não emitem certificado. */
  function certHTML() {
    return '<div class="cert"><p class="cert__brand">' + esc(marca.nome) + '</p><p class="cert__kind">Certificado de conclusão</p><p class="cert__name">' + esc(usuario.nome) + '</p>' +
      '<p class="cert__text">concluiu a mentoria <b>' + esc(marca.mentoria) + '</b>, turma ' + marca.turma + '.</p>' +
      '<div class="cert__foot"><div class="cert__sign"><b>' + esc(marca.nome) + '</b>Plataforma de cursos</div></div></div>';
  }
  function certificates(el) {
    el.innerHTML = '<div class="page"><header class="page__head"><div><h1 class="page__title">Certificado</h1><p class="page__sub">O certificado é emitido ao final da mentoria ' + esc(marca.mentoria) + ', que dura ' + marca.duracao + '.</p></div></header>' +
      '<section class="certlock"><div class="certlock__preview" aria-hidden="true">' + certHTML() + '<span class="certlock__veil">' + icon('lock') + 'Disponível ao final da mentoria</span></div>' +
      '<div class="certlock__info"><span class="tag">' + icon('lock') + 'Ainda não disponível</span><h2>Certificado da mentoria ' + esc(marca.mentoria) + '</h2>' +
      '<p>Ele é liberado ao final da mentoria, que dura ' + marca.duracao + '. Quando for liberado, aparece nesta página para você baixar.</p>' +
      '<p class="certlock__note">Os cursos e as aulas não emitem certificado próprio.</p>' +
      '<a class="btn btn--light" href="#/mentoria">' + icon('bolt') + 'Ir para a mentoria</a></div></section></div>';
  }

  /* --- conta --- */
  let contaTab = 'perfil';
  function account(el) {
    const tabs = [['perfil', 'Perfil', 'user'], ['assinatura', 'Assinatura', 'award'], ['avisos', 'Notificações', 'bell']];
    if (!tabs.some((t) => t[0] === contaTab)) contaTab = 'perfil';
    const sw = (k, t, d) => '<div class="setrow"><div><strong>' + t + '</strong><span>' + d + '</span></div><button class="switch" role="switch" aria-checked="' + !!S.prefs[k] + '" data-pref="' + k + '" aria-label="' + t + '"></button></div>';
    function body() {
      if (contaTab === 'perfil') return '<div class="panel"><div class="panel__head"><h2>Perfil</h2></div><div class="whoami"><span class="avatar avatar--lg">' + usuario.iniciais + '</span><div><strong>' + esc(usuario.nome) + '</strong><span>Participando da mentoria ' + esc(marca.mentoria) + '</span></div></div>' +
        '<form class="form form--2" id="perfil"><div class="field"><label for="f1">Nome completo</label><input class="input" id="f1" value="' + esc(usuario.nome) + '"></div><div class="field"><label for="f2">Como quer ser chamada</label><input class="input" id="f2" value="' + esc(usuario.tratamento) + '"></div><div class="field"><label for="f3">E-mail</label><input class="input" id="f3" type="email" value="' + esc(usuario.email) + '"></div><div class="field"><label for="f4">Área de atuação</label><input class="input" id="f4" value="Clínica médica · pronto-socorro"></div><div style="grid-column:1/-1"><button class="btn btn--red" type="submit">Salvar alterações</button></div></form></div>';
      if (contaTab === 'assinatura') return '<div class="plan"><div><span class="tag tag--red">Plano ativo</span><h3>Mentoria ' + esc(marca.mentoria) + '</h3><p>Acesso completo à mentoria, com encontros ao vivo e materiais complementares</p></div></div>' +
        '<div class="panel" style="margin-top:14px"><div class="panel__head"><h2>Incluído no seu plano</h2></div><div class="setrow"><div><strong>Aulas gravadas</strong><span>Com e-book em cada aula</span></div>' + icon('check') + '</div><div class="setrow"><div><strong>Acesso completo à mentoria</strong><span>' + esc(marca.mentoria) + ' · ' + turmaTxt() + '</span></div>' + icon('check') + '</div><div class="setrow"><div><strong>Encontros ao vivo semanais</strong><span>Com gravação disponível depois</span></div>' + icon('check') + '</div><div class="setrow"><div><strong>Comunidade da turma</strong><span>Troca direta com mentores e colegas</span></div>' + icon('check') + '</div><div class="setrow"><div><strong>Certificado da mentoria</strong><span>Liberado ao final da mentoria, que dura ' + marca.duracao + '</span></div>' + icon('check') + '</div></div>';
      return '<div class="panel"><div class="panel__head"><h2>Notificações</h2></div>' + sw('emailAulas', 'Novas aulas liberadas', 'E-mail quando uma semana da mentoria ou um curso novo abrir') + sw('emailLives', 'Encontros ao vivo', 'Aviso uma hora antes dos encontros com lembrete ativo') + '</div>';
    }
    el.innerHTML = '<div class="page"><header class="page__head"><div><h1 class="page__title">Conta e preferências</h1></div></header><div class="settings"><nav class="settings__nav" id="cnav"></nav><div id="cbody"></div></div></div>';
    function paint() {
      $('#cnav', el).innerHTML = tabs.map((t) => '<button class="' + (t[0] === contaTab ? 'is-on' : '') + '" data-ctab="' + t[0] + '">' + icon(t[2]) + t[1] + '</button>').join('');
      $('#cbody', el).innerHTML = body();
    }
    paint();
    el.onclick = (e) => {
      const t = e.target.closest('[data-ctab]');
      if (t) { contaTab = t.dataset.ctab; paint(); return; }
      const p = e.target.closest('[data-pref]');
      if (p) { const k = p.dataset.pref; S.prefs[k] = !S.prefs[k]; save(); p.setAttribute('aria-checked', S.prefs[k]); toast('Preferência salva'); }
    };
    el.onsubmit = (e) => { e.preventDefault(); toast('Alterações salvas'); };
    cleanups.push(() => { el.onclick = null; el.onchange = null; el.onsubmit = null; });
  }

  /* --- entrada --- */
  /* Tela de login da plataforma (GoMut): o mesmo desenho para os dois acessos. Quem chama informa
     o título do cartão, a frase logo abaixo e as opções do menu "Entrar". Estilos em assets/css/login.css. */
  function telaLogin(o) {
    const item = (m) => (m.aqui
      ? '<button type="button" class="dd__item" data-action="login-aqui">' + icon(m.ic) + esc(m.rotulo) + '</button>'
      : '<a class="dd__item" href="' + m.href + '">' + icon(m.ic) + esc(m.rotulo) + '</a>');
    return '<div class="auth gm-login">' +
      '<header class="gm-login__barra"><span class="gm-login__logo"><img src="assets/marca/gomut-logo.png" alt="GoMut" width="1568" height="432"></span>' +
        '<div class="dd gm-login__menu"><button type="button" class="gm-login__link" data-action="dd" aria-haspopup="true" aria-expanded="false">Entrar' + icon('down') + '</button>' +
        '<div class="dd__panel dd__panel--menu">' + o.menu.map(item).join('') + '</div></div></header>' +
      '<div class="gm-login__palco">' +
        '<div class="gm-login__texto"><h1><span>Força para fazer</span> avançar.</h1><p>Uma proposta de experiência com clareza, presença e ação.</p></div>' +
        /* "GO" e o mamute na cor do cartão de acesso, translúcidos; arquivo em 4K (3840px de largura) para ficar nítido em qualquer tela */
        '<div class="gm-login__marca"><div class="gm-login__arte" aria-hidden="true"><img src="assets/marca/gomut-go-mamute-vidro-4k.png" alt="" width="3840" height="1965"></div></div>' +
        '<form class="gm-login__cartao form" id="' + o.formId + '"><div><h2>' + esc(o.titulo) + '</h2><p>' + esc(o.frase) + '</p></div>' +
          '<div class="field"><label class="sr-only" for="' + o.formId + '-e">E-mail</label><input class="input" id="' + o.formId + '-e" type="email" placeholder="Seu e-mail" autocomplete="off"></div>' +
          '<div class="field"><label class="sr-only" for="' + o.formId + '-s">Senha</label><input class="input" id="' + o.formId + '-s" type="password" placeholder="Sua senha" autocomplete="off"></div>' +
          '<button class="btn btn--block gm-login__entrar" type="submit">Entrar</button></form>' +
      '</div>' +
      '<p class="auth__foot">GoMut · protótipo de interface · nenhum dado é enviado</p></div>';
  }
  /* Cor que o navegador usa nas próprias bordas (barra do celular, por exemplo): acompanha o fundo da tela aberta. */
  function corDoNavegador(cor) { const m = document.querySelector('meta[name="theme-color"]'); if (m) m.content = cor; }
  const COR_LOGIN = '#142724';
  /* Login da área de membros: "Acessar minhas compras". */
  function login(el) {
    el.innerHTML = telaLogin({ formId: 'loginform', titulo: 'Acessar minhas compras', frase: 'Entre e acesse seus cursos.',
      menu: [{ rotulo: 'Gerenciar meus negócios', ic: 'sliders', href: 'coprodutor.html' }, { rotulo: 'Acessar minhas compras', ic: 'play', aqui: true }] });
    corDoNavegador(COR_LOGIN);
    el.onsubmit = (e) => { e.preventDefault(); location.hash = '#/'; toast('Bem-vinda de volta, ' + usuario.tratamento); };
    cleanups.push(() => { el.onsubmit = null; corDoNavegador('#141414'); });
  }

  /* --- busca --- */
  function search(el, params, query) {
    const q = (query.get('q') || '').trim(), n = norm(q);
    const inp = $('#q');
    if (inp && document.activeElement !== inp) { inp.value = q; $('#search').classList.toggle('is-open', !!q); }
    const hit = (c) => norm([c.titulo, c.sub || '', c.desc, areas[c.area].nome, c.tags.join(' ')].join(' ')).indexOf(n) >= 0;
    const rc = n ? cursos.filter(hit) : [];
    const ra = n ? cursos.reduce((all, c) => all.concat(c.aulas.filter((a) => !a.bloqueada && norm(a.titulo).indexOf(n) >= 0).map((a) => [c, a])), []).slice(0, 12) : [];
    const sugest = ['ECG', 'Sepse', 'Via aérea', 'Prescrição', 'AVC', 'Trauma'];
    const chips = '<div class="chips" style="margin-bottom:26px">' + sugest.map((s) => '<a class="chip" href="#/busca?q=' + encodeURIComponent(s) + '">' + s + '</a>').join('') + '</div>';
    let html;
    if (!n) html = '<header class="page__head"><div><h1 class="page__title">Buscar</h1><p class="page__sub">Procure por curso, aula ou área.</p></div></header>' + chips + '<h2 class="section-title">Mais procurados</h2><div class="grid">' + top10.slice(0, 10).map((id) => gcard(byId[id])).join('') + '</div>';
    else if (!rc.length && !ra.length) html = empty('search', 'Nada encontrado para “' + q + '”', 'Confira a grafia ou tente um termo mais geral, como o nome da área.', chips);
    else html = '<header class="page__head"><div><p class="eyebrow">' + (rc.length + ra.length) + ' resultados</p><h1 class="page__title" style="margin-top:8px">“' + esc(q) + '”</h1></div></header>' +
      (rc.length ? '<h2 class="section-title">Cursos e mentoria</h2><div class="grid">' + rc.map(gcard).join('') + '</div>' : '') +
      (ra.length ? '<h2 class="section-title">Aulas</h2><div class="grid">' + ra.map((x) => '<div class="gcard">' + quickCard(x[0], x[1]) + '<div class="gcard__meta"><strong>' + esc(x[1].titulo) + '</strong>' + esc(x[0].titulo) + ' · aula ' + x[1].n + '</div></div>').join('') + '</div>' : '');
    el.innerHTML = '<div class="page">' + html + '</div>';
  }

  /* --- central de ajuda --- */
  /* O aluno abre um chamado e, ao enviar, a equipe de suporte precisa ser notificada na hora.
     No protótipo o chamado fica salvo só no navegador: o aviso ao suporte (e-mail, painel ou outro
     canal) é uma regra para a programação. Para o aluno, a tela só confirma o recebimento, em tom
     neutro: nada de sininho nem de "notificado", para não parecer um aviso de emergência. */
  function help(el) {
    let recente = null; /* número do chamado recém-enviado */
    const meus = () => S.tickets || (S.tickets = []);
    const ESTADO = { aberto: ['tag tag--line', 'Aberto'], resolvido: ['tag tag--ok', 'Resolvido'] };
    function ticket(t) {
      const e = ESTADO[t.status] || ESTADO.aberto, quando = t.dias != null ? 'há ' + t.dias + ' dias' : fmtQuando(new Date(t.quando));
      return '<details class="ticket"' + (t.n === recente ? ' open' : '') + '><summary><span class="ticket__n">#' + t.n + '</span><span class="ticket__main"><strong>' + esc(t.assunto) + '</strong><span>' + esc(t.texto) + '</span></span>' +
        '<span class="' + e[0] + '">' + (t.status === 'resolvido' ? icon('check') : '') + e[1] + '</span>' + icon('down', 'week__chev') + '</summary>' +
        '<div class="ticket__body"><p>' + esc(t.texto) + '</p><p class="ticket__meta">' + 'Enviado ' + quando + (t.status === 'aberto' ? ' · recebido pela equipe de suporte' : '') + '</p>' +
        (t.resposta ? '<div class="post__reply"><strong>Equipe de suporte</strong>' + esc(t.resposta) + '</div>' : '') + '</div></details>';
    }
    const lista = () => meus().concat([ajuda.exemplo]).map(ticket).join('');
    el.innerHTML = '<div class="page"><header class="page__head"><div><h1 class="page__title">Central de ajuda</h1><p class="page__sub">Teve um problema ou uma dúvida sobre a plataforma? Abra um chamado para a equipe de suporte.</p></div></header>' +
      '<div class="split" style="margin-top:0"><section class="panel"><div class="panel__head"><h2>Abrir um chamado</h2></div><div id="hok"></div>' +
        '<form class="form" id="hform"><div class="field"><label for="hassunto">Assunto</label><span class="select select--block"><select id="hassunto" required><option value="">Selecione o assunto</option>' + ajuda.assuntos.map((a) => '<option>' + esc(a) + '</option>').join('') + '</select></span></div>' +
        '<div class="field"><label for="htexto">O que aconteceu?</label><textarea class="input" id="htexto" rows="6" required minlength="10" maxlength="1500" placeholder="Conte com detalhes: em que página você estava, o que tentou fazer e o que apareceu na tela."></textarea></div>' +
        '<div class="hform__foot"><button class="btn btn--red" type="submit">Enviar chamado</button></div></form></section>' +
      '<section class="panel"><div class="panel__head"><h2>Meus chamados</h2></div><div class="tickets" id="hlist">' + lista() + '</div></section></div></div>';
    el.onsubmit = (e) => {
      if (e.target.id !== 'hform') return;
      e.preventDefault();
      const assunto = $('#hassunto', el).value, texto = $('#htexto', el).value.trim();
      if (!assunto || texto.length < 10) return;
      const n = 1024 + meus().length + 1;
      meus().unshift({ n, assunto, texto, quando: Date.now(), status: 'aberto' });
      save(); recente = n;
      e.target.reset();
      $('#hok', el).innerHTML = '<div class="notice" tabindex="-1" role="status">' + icon('check') + '<div><strong>Chamado #' + n + ' enviado</strong><span>A equipe de suporte recebeu o seu chamado. Você acompanha o andamento em “Meus chamados”.</span></div></div>';
      $('#hlist', el).innerHTML = lista();
      $('.notice', el).focus();
      toast('Chamado #' + n + ' enviado');
    };
    cleanups.push(() => { el.onsubmit = null; });
  }

  /* --- curso à venda: mais informações e acesso ao checkout --- */
  function offer(el, params) {
    const c = ofertaById[params[0]];
    if (!c) { notFound(el); return; }
    const buy = (cls, label) => '<button class="btn btn--red ' + cls + '" data-action="checkout" data-id="' + c.id + '">' + label + icon('right') + '</button>';
    el.innerHTML =
      '<div class="page offer">' +
        '<nav class="crumbs"><a href="#/">' + icon('left') + 'Início</a><span>·</span><span>Cursos à venda</span></nav>' +
        '<section class="offer__hero"><div>' +
          '<p class="hero__kicker"><span class="tag tag--line">' + icon('lock') + 'Curso à venda</span><span>' + esc(areas[c.area].nome) + '</span></p>' +
          '<h1>' + esc(c.titulo) + '</h1><p class="offer__desc">' + esc(c.desc) + '</p>' +
          '<ul class="facts"><li>' + icon('play') + c.aulas.length + ' aulas · ' + fmtMin(c.totalMin) + '</li><li>' + icon('book') + 'E-book em cada aula</li></ul>' +
          '<div class="hero__actions">' + buy('btn--lg', 'Comprar por ' + fmtPreco(c.preco)) + '<button class="btn btn--dim btn--lg" data-action="scrollto" data-target="#offer-conteudo">Ver conteúdo</button></div>' +
        '</div><div class="offer__cover">' + courseCover(c, { title: '', kicker: '' }) + '<span class="offer__locked">' + icon('lock') + 'Conteúdo bloqueado</span></div></section>' +
        '<div class="mgrid"><div>' +
          '<h2 class="section-title">O que você vai aprender</h2><ul class="learn">' + c.aprende.map((t) => '<li>' + icon('check') + '<span>' + esc(t) + '</span></li>').join('') + '</ul>' +
          '<h2 class="section-title" id="offer-conteudo">Conteúdo do curso</h2><p class="offer__note">' + c.modulos.length + ' módulos · ' + c.aulas.length + ' aulas · liberadas logo após a compra</p>' +
          '<div class="weeks">' + c.modulos.map((m) =>
            '<details class="week"' + (m.i === 0 ? ' open' : '') + '><summary><span class="week__n">' + (m.i + 1) + '</span><div><p class="eyebrow">Módulo ' + (m.i + 1) + '</p><h3>' + esc(m.titulo) + '</h3><p class="week__meta">' + m.aulas.length + ' aulas · ' + fmtMin(m.aulas.reduce((t, x) => t + x.min, 0)) + '</p></div><span></span>' + icon('down', 'week__chev') + '</summary>' +
            '<ol class="eps eps--compact">' + m.aulas.map((a) => '<li class="ep ep--static"><span class="ep__n">' + icon('lock') + '</span><span class="ep__main"><span class="ep__head"><span class="ep__title">' + esc(a.titulo) + '</span><span class="ep__dur">' + a.min + ' min</span></span></span></li>').join('') + '</ol></details>').join('') + '</div>' +
        '</div><aside class="aside-stack"><div class="panel buy">' +
          '<p class="eyebrow">Acesso completo ao curso</p><p class="buy__price">' + fmtPreco(c.preco) + '</p><p class="buy__inst">ou ' + c.parcelas + 'x de ' + fmtPreco(c.preco / c.parcelas) + '</p>' +
          buy('btn--block', 'Ir para o checkout') +
          '<ul class="buy__list">' + [c.aulas.length + ' aulas em vídeo', 'E-book em cada aula', '7 dias de garantia'].map((t) => '<li>' + icon('check') + esc(t) + '</li>').join('') + '</ul>' +
          '<p class="buy__note">' + icon('lock') + 'Você conclui a compra na página de pagamento.</p>' +
        '</div></aside></div>' +
      '</div>' +
      '<div class="rails">' + rail('Outros cursos à venda', ofertas.filter((x) => x.id !== c.id).map(saleCard)) + '</div>';
    initRails(el);
  }

  function notFound(el) {
    el.innerHTML = '<div class="page">' + empty('help', 'Página não encontrada', 'O endereço não existe neste protótipo.', '<a class="btn btn--light" href="#/">Voltar ao início</a>') + '</div>';
  }

  /* --- aula (reprodutor simulado) --- */
  function lesson(el, params) {
    const c = byId[params[0]], a = c && c.aulas.find((x) => x.id === params[1]);
    if (!c || !a) return notFound(el);
    if (a.bloqueada) { toast('Esta aula ainda não foi liberada', 'lock'); location.replace('#/mentoria'); return; }
    const p = ensureP(c.id);
    p.last = a.id; touchRecent(c.id); save();
    const idx = c.aulas.indexOf(a), next = c.aulas.slice(idx + 1).find((x) => !x.bloqueada), prev = idx > 0 ? c.aulas[idx - 1] : null;
    const dur = a.min * 60;
    const chaps = capitulos.map((k) => Object.assign({ t: Math.round(k.de * dur) }, k));
    const st = { pos: Math.min(p.pos[a.id] || 0, dur - 2), playing: false, speed: 1, muted: false, cc: false, ended: false, tab: 'visao', chap: -1, ticks: 0, answers: [] };
    if (p.done[a.id] && st.pos > dur * 0.9) st.pos = 0;
    const men = c.tipo === 'mentoria';
    const TABS = [['visao', 'Visão geral'], ['materiais', 'E-book'], ['quiz', 'Quiz']];

    el.innerHTML = '<div class="lesson' + (S.prefs.cinema ? ' is-cinema' : '') + '" id="lesson"><div class="lesson__main">' +
      '<nav class="crumbs"><a href="#/curso/' + c.id + '">' + icon('left') + esc(c.titulo) + '</a><span>·</span><span>' + esc(modLabel(c, c.modulos[a.modulo])) + '</span></nav>' +
      '<div class="player" id="player" style="--h:' + c.h + '" tabindex="0" aria-label="Reprodutor da aula">' +
        '<div class="stage"><div id="slide"></div></div><span class="player__note">Vídeo ilustrativo do protótipo</span>' +
        '<div class="player__cc" id="cc"' + (st.cc ? '' : ' hidden') + '></div>' +
        '<button class="player__big" id="big" aria-label="Reproduzir"><span>' + icon('play') + '</span></button>' +
        '<div class="player__ctl"><div class="scrub"><div class="scrub__track"><div class="scrub__fill" id="fill"></div>' + chaps.slice(1).map((k) => '<i class="scrub__mark" style="left:' + k.de * 100 + '%"></i>').join('') + '</div><input type="range" id="seek" min="0" max="' + dur + '" step="1" value="0" aria-label="Posição na aula"></div>' +
        '<div class="player__row"><button id="pp" aria-label="Reproduzir ou pausar">' + icon('play') + '</button><button id="b10" aria-label="Voltar 10 segundos">' + icon('back10') + '</button><button id="f10" aria-label="Avançar 10 segundos">' + icon('fwd10') + '</button><button id="vol" class="hide-s" aria-label="Som">' + icon('volume') + '</button>' +
        '<span class="player__time" id="time"></span><span class="player__chapter" id="chap"></span>' +
        '<button id="spd" aria-label="Velocidade de reprodução" title="Velocidade"></button><button id="ccb" class="hide-s' + (st.cc ? ' is-on' : '') + '" aria-label="Legendas" title="Legendas">' + icon('captions') + '</button><button id="cin" class="hide-s" aria-label="Modo cinema" title="Modo cinema">' + icon('cinema') + '</button>' + (next ? '<a id="nx" href="#/aula/' + c.id + '/' + next.id + '" aria-label="Próxima aula" title="Próxima aula" style="display:grid;place-items:center;min-width:36px;height:36px">' + icon('next') + '</a>' : '') + '<button id="fs" aria-label="Tela cheia" title="Tela cheia">' + icon('fullscreen') + '</button></div></div>' +
        '<div id="end"></div></div>' +
      '<header class="lesson__head"><div><p class="eyebrow">Aula ' + a.n + ' de ' + c.aulas.length + '</p><h1>' + esc(a.titulo) + '</h1></div>' +
        '<div class="lesson__actions"><span id="donebtn"></span>' + likeBtn(a.id) + listBtn(c.id) + (prev ? '<a class="btn btn--outline btn--sm" href="#/aula/' + c.id + '/' + prev.id + '">' + icon('left') + 'Anterior</a>' : '') + (next ? '<a class="btn btn--outline btn--sm" href="#/aula/' + c.id + '/' + next.id + '">Próxima' + icon('right') + '</a>' : '') + '</div></header>' +
      '<div class="tabs" role="tablist">' + TABS.map((t) => '<button class="tab' + (t[0] === st.tab ? ' is-on' : '') + '" role="tab" data-ltab="' + t[0] + '">' + t[1] + '</button>').join('') + '</div>' +
      '<div class="tabpanel" id="tabpanel"></div></div><aside class="outline" id="outline" aria-label="Aulas e módulos"></aside></div>';

    const player = $('#player', el), fill = $('#fill', el), seek = $('#seek', el), time = $('#time', el), slide = $('#slide', el), chapEl = $('#chap', el), cc = $('#cc', el), pp = $('#pp', el), big = $('#big', el), end = $('#end', el), panel = $('#tabpanel', el), outline = $('#outline', el), spd = $('#spd', el);
    let countdown = null;

    function paint() {
      fill.style.width = (st.pos / dur) * 100 + '%';
      seek.value = Math.round(st.pos);
      time.textContent = fmtClock(st.pos) + ' / ' + fmtClock(dur);
      let ci = 0;
      chaps.forEach((k, i) => { if (st.pos >= k.t) ci = i; });
      if (ci !== st.chap) {
        st.chap = ci;
        const k = chaps[ci];
        slide.innerHTML = '<p class="slide__kicker">Parte ' + (ci + 1) + ' de ' + chaps.length + ' · ' + esc(k.titulo) + '</p><h2 class="slide__title">' + esc(a.titulo) + '</h2><ul class="slide__points">' + k.pontos.map((x) => '<li>' + esc(x) + '</li>').join('') + '</ul>';
        chapEl.textContent = k.titulo;
        cc.textContent = k.legenda;
      }
    }
    function paintDone() {
      const d = !!p.done[a.id];
      $('#donebtn', el).innerHTML = '<button class="btn btn--sm ' + (d ? 'btn--outline is-on' : 'btn--light') + '" data-lact="done" aria-pressed="' + d + '">' + icon('check') + '<span>' + (d ? 'Concluída' : 'Marcar como concluída') + '</span></button>';
    }
    /* "Aulas e módulos": mostra a mentoria inteira (a jornada e todos os temas, com seus módulos e
       aulas), para o aluno navegar por todo o conteúdo a partir de qualquer aula. Vale só para este
       painel da tela da aula; o catálogo continua organizado por temas e módulos como antes. */
    function paintOutline() {
      const antes = {};
      $$('details[data-k]', outline).forEach((d) => { antes[d.dataset.k] = d.open; });
      const primeira = !Object.keys(antes).length;
      const temas = cursos.filter((x) => x.tipo !== 'mentoria');
      const todos = [MENTORIA].concat(temas);
      const item = (t, x) => {
        const cls = 'oitem' + (isDone(t, x) ? ' is-done' : '') + (x.id === a.id ? ' is-current' : '') + (x.bloqueada ? ' is-locked' : '');
        const inner = '<span class="oitem__st">' + icon(x.bloqueada ? 'lock' : x.id === a.id && !isDone(t, x) ? 'play' : 'check') + '</span><span>' + esc(x.titulo) + '</span><time>' + x.min + ' min</time>';
        return x.bloqueada ? '<div class="' + cls + '">' + inner + '</div>' : '<a class="' + cls + '" href="#/aula/' + t.id + '/' + x.id + '"' + (x.id === a.id ? ' aria-current="true"' : '') + '>' + inner + '</a>';
      };
      const tema = (t) => {
        const kt = 't:' + t.id, atual = t.id === c.id;
        return '<details class="otema' + (atual ? ' is-current' : '') + '" data-k="' + kt + '"' + ((primeira ? atual : antes[kt]) ? ' open' : '') + '><summary><div><strong>' + esc(t.tipo === 'mentoria' ? 'Jornada da mentoria' : t.titulo) + '</strong><span>' + doneCount(t) + '/' + t.aulas.length + ' aulas</span></div>' + icon('down') + '</summary>' +
          t.modulos.map((m) => {
            const km = 'm:' + t.id + ':' + m.i, md = m.aulas.filter((x) => isDone(t, x)).length, min = m.aulas.reduce((s, x) => s + x.min, 0);
            return '<details class="omod" data-k="' + km + '"' + ((primeira ? atual && m.i === a.modulo : antes[km]) ? ' open' : '') + '><summary><div><strong>' + esc(modLabel(t, m)) + '</strong><span>' + (m.bloqueado ? 'Libera em ' + fmtData(emDias(m.bloqueado)) : md + '/' + m.aulas.length + ' aulas · ' + fmtMin(min)) + '</span></div>' + icon('down') + '</summary>' +
              m.aulas.map((x) => item(t, x)).join('') + '</details>';
          }).join('') + '</details>';
      };
      /* título de tema: todos têm o mesmo destaque; o da aula aberta leva também a etiqueta "Tema desta aula" */
      const titulo = (nome, daAula) => '<p class="outline__area' + (daAula ? ' is-current' : '') + '"><span>' + esc(nome) + '</span>' + (daAula ? '<span class="tag tag--red">Tema desta aula</span>' : '') + '</p>';
      outline.innerHTML = '<div class="outline__head outline__head--all"><div><strong>Aulas e módulos</strong><span>Mentoria ' + esc(marca.mentoria) + ' · ' + todos.reduce((s, t) => s + t.modulos.length, 0) + ' módulos · ' + todos.reduce((s, t) => s + t.aulas.length, 0) + ' aulas</span></div></div>' +
        /* cada tema fica num grupo próprio: o título acompanha a rolagem só enquanto o grupo está na tela */
        '<div class="ogrupo">' + titulo('Mentoria', c.tipo === 'mentoria') + tema(MENTORIA) + '</div>' +
        Object.keys(areas).map((k) => {
          const ts = temas.filter((t) => t.area === k);
          return ts.length ? '<div class="ogrupo">' + titulo(areas[k].nome, c.tipo !== 'mentoria' && c.area === k) + ts.map(tema).join('') + '</div>' : '';
        }).join('');
      /* os títulos de tema ficam presos logo abaixo do cabeçalho do painel enquanto a lista rola */
      outline.style.setProperty('--oh', $('.outline__head', outline).offsetHeight + 'px');
    }
    function markDone(v, quiet) {
      if (!!p.done[a.id] === v) return;
      if (v) p.done[a.id] = true; else delete p.done[a.id];
      save(); paintDone(); paintOutline();
      if (!quiet) toast(v ? 'Aula marcada como concluída' : 'Aula marcada como não concluída');
      if (v && pct(c) === 100) setTimeout(() => toast('Curso concluído!', 'check'), 500);
    }
    function hideEnd() { end.innerHTML = ''; clearInterval(countdown); countdown = null; }
    function showEnd() {
      let s = 8;
      const auto = !!next; /* a próxima aula sempre começa sozinha; o aluno pode cancelar na hora */
      end.innerHTML = '<div class="endcard">' + (next ? '<p class="eyebrow">A seguir' + (auto ? ' em <span id="cdn">' + s + '</span> s' : '') + '</p><h3>Aula ' + next.n + ' · ' + esc(next.titulo) + '</h3><div class="endcard__actions"><a class="btn btn--light" href="#/aula/' + c.id + '/' + next.id + '">' + icon('play') + 'Assistir agora</a><button class="btn btn--dim" data-lact="stay">' + (auto ? 'Cancelar' : 'Rever esta aula') + '</button></div>'
        : '<p class="eyebrow">Você chegou ao fim</p><h3>' + (pct(c) === 100 ? 'Curso concluído.' : 'Esta era a última aula liberada.') + '</h3><div class="endcard__actions"><a class="btn btn--dim" href="#/curso/' + c.id + '">Voltar ao curso</a></div>') + '</div>';
      if (auto) countdown = setInterval(() => { s -= 1; const n = $('#cdn', el); if (n) n.textContent = s; if (s <= 0) { clearInterval(countdown); location.hash = '#/aula/' + c.id + '/' + next.id; } }, 1000);
    }
    function setPlaying(v) {
      if (v && st.ended) { st.pos = 0; st.ended = false; hideEnd(); }
      st.playing = v;
      player.classList.toggle('is-playing', v);
      pp.innerHTML = icon(v ? 'pause' : 'play');
      big.setAttribute('aria-label', v ? 'Pausar' : 'Reproduzir');
      if (!v) { p.pos[a.id] = Math.round(st.pos); save(); }
    }
    function seekTo(t) {
      st.pos = Math.max(0, Math.min(dur, t));
      if (st.ended && st.pos < dur) { st.ended = false; hideEnd(); }
      paint();
      if (st.pos >= dur) finish();
    }
    function finish() {
      st.pos = dur; st.ended = true; setPlaying(false); markDone(true, true); p.pos[a.id] = 0; save(); paint(); showEnd();
    }
    function paintSpeed() { spd.textContent = String(st.speed).replace('.', ',') + 'x'; }

    /* abas */
    function paintTab() {
      $$('[data-ltab]', el).forEach((b) => b.classList.toggle('is-on', b.dataset.ltab === st.tab));
      if (st.tab === 'visao') {
        panel.innerHTML = '<div class="prose"><h3>Sobre esta aula</h3><p>' + esc(epDesc(a)) + ' Faz parte de <a href="#/curso/' + c.id + '" style="text-decoration:underline">' + esc(c.titulo) + '</a>: ' + esc(c.sobre || c.desc.charAt(0).toLowerCase() + c.desc.slice(1)) + '</p></div>';
      } else if (st.tab === 'materiais') {
        panel.innerHTML = '<div style="max-width:760px"><div class="files">' + ebookFile(a) + '</div>' +
          '<p class="files__more"><a href="' + (men ? EBOOKS : '#/curso/' + c.id + '?ver=ebooks') + '">Ver todos os e-books ' + (men ? 'da mentoria' : 'do curso') + icon('right') + '</a></p></div>';
      } else {
        const all = st.answers.filter((x) => x != null).length === quiz.length, hits = quiz.filter((q, i) => st.answers[i] === q.c).length;
        panel.innerHTML = '<div class="quiz">' + quiz.map((q, i) => {
          const ans = st.answers[i];
          return '<div class="q"><p class="eyebrow">Questão ' + (i + 1) + ' de ' + quiz.length + '</p><h4>' + esc(q.p) + '</h4><div class="q__opts">' + q.o.map((o, j) => '<button class="q__opt' + (ans != null && j === q.c ? ' is-right' : ans === j ? ' is-wrong' : '') + '" data-lact="answer" data-q="' + i + '" data-o="' + j + '"' + (ans != null ? ' disabled' : '') + '><i>' + 'ABCD'[j] + '</i><span>' + esc(o) + '</span></button>').join('') + '</div>' +
            (ans != null ? '<div class="q__why"><b>' + icon(ans === q.c ? 'check' : 'info') + (ans === q.c ? 'Correto' : 'Não foi dessa vez') + '</b>' + esc(q.e) + '</div>' : '') + '</div>';
        }).join('') + (all ? '<div class="quiz__score"><div><strong>Você acertou ' + hits + ' de ' + quiz.length + '</strong><p class="muted" style="font-size:14px">' + (hits === quiz.length ? 'Tudo certo: pode seguir para a próxima aula.' : 'Vale rever os trechos indicados antes de seguir.') + '</p></div><button class="btn btn--outline btn--sm" data-lact="requiz">Refazer quiz</button></div>' : '') + '<p class="dim" style="font-size:13px">Questões de exemplo, apenas para demonstrar o formato.</p></div>';
      }
    }

    paint(); paintDone(); paintOutline(); paintSpeed(); paintTab();
    /* a lista é longa: o painel abre já posicionado no tema e na aula atuais */
    const posicionar = () => {
      if (!document.contains(outline)) return;
      const cur = $('.oitem.is-current', outline), temaAtual = $('.otema.is-current', outline);
      const topo = $('.outline__head', outline).offsetHeight, titulo = $('.outline__area.is-current', outline);
      outline.style.setProperty('--oh', topo + 'px');
      if (!cur || !temaAtual || outline.scrollHeight <= outline.clientHeight) return;
      outline.scrollTop = (titulo || temaAtual).offsetTop - topo;
      if (cur.offsetTop + cur.offsetHeight > outline.scrollTop + outline.clientHeight) outline.scrollTop = cur.offsetTop - topo - 160;
    };
    posicionar();
    /* as fontes podem terminar de carregar depois e mudar a altura das linhas: reposiciona quando chegarem */
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(posicionar);

    /* eventos */
    const toggle = () => setPlaying(!st.playing);
    big.onclick = toggle; pp.onclick = toggle;
    $('#b10', el).onclick = () => seekTo(st.pos - 10);
    $('#f10', el).onclick = () => seekTo(st.pos + 10);
    seek.oninput = () => seekTo(Number(seek.value));
    $('#vol', el).onclick = (e) => { st.muted = !st.muted; e.currentTarget.innerHTML = icon(st.muted ? 'mute' : 'volume'); };
    spd.onclick = () => { const v = [1, 1.25, 1.5, 2, 0.75]; st.speed = v[(v.indexOf(st.speed) + 1) % v.length]; paintSpeed(); };
    $('#ccb', el).onclick = (e) => { st.cc = !st.cc; cc.hidden = !st.cc; e.currentTarget.classList.toggle('is-on', st.cc); };
    $('#cin', el).onclick = () => { S.prefs.cinema = $('#lesson', el).classList.toggle('is-cinema'); save(); };
    $('#fs', el).onclick = () => { if (document.fullscreenElement) document.exitFullscreen(); else if (player.requestFullscreen) player.requestFullscreen().catch(() => {}); };

    el.onclick = (e) => {
      const tab = e.target.closest('[data-ltab]');
      if (tab) { st.tab = tab.dataset.ltab; paintTab(); return; }
      const t = e.target.closest('[data-lact]');
      if (!t) return;
      const act = t.dataset.lact;
      if (act === 'done') markDone(!p.done[a.id]);
      else if (act === 'answer') { st.answers[Number(t.dataset.q)] = Number(t.dataset.o); paintTab(); }
      else if (act === 'requiz') { st.answers = []; paintTab(); }
      else if (act === 'stay') { hideEnd(); st.ended = false; seekTo(0); }
    };
    const onKey = (e) => {
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || document.body.classList.contains('has-modal') || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === ' ' || e.key === 'k') { if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A') return; e.preventDefault(); toggle(); }
      else if (e.key === 'ArrowLeft') seekTo(st.pos - 10);
      else if (e.key === 'ArrowRight') seekTo(st.pos + 10);
      else if (e.key === 'f') $('#fs', el).click();
      else if (e.key === 'c') $('#ccb', el).click();
    };
    document.addEventListener('keydown', onKey);
    const onPause = () => { if (st.playing) setPlaying(false); };
    window.addEventListener('ems:pause', onPause);

    let relogio = Date.now();
    const iv = setInterval(() => {
      const agora = Date.now(), passou = (agora - relogio) / 1000;
      relogio = agora;
      if (!st.playing) return;
      addStudy(Math.min(passou, 2)); /* minutos de estudo: só conta enquanto o vídeo está tocando */
      st.pos += 0.25 * st.speed;
      st.ticks += 1;
      if (st.pos >= dur) { finish(); return; }
      if (!p.done[a.id] && st.pos >= dur * 0.9) markDone(true, true);
      if (st.ticks % 20 === 0) { p.pos[a.id] = Math.round(st.pos); save(); }
      paint();
    }, 250);

    cleanups.push(() => {
      clearInterval(iv); clearInterval(countdown);
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('ems:pause', onPause);
      if (!st.ended) p.pos[a.id] = Math.round(st.pos);
      save();
      el.onclick = null; el.onsubmit = null;
    });
  }

  /* --------------------------------------------------------- janela do curso */
  const modalRoot = $('#modal-root');
  let modalCourse = null, modalModule = 0, modalEbooks = false, lastFocus = null;

  function renderCourse() {
    const c = modalCourse, st = started(c), p = pct(c), a = nextAula(c), men = c.tipo === 'mentoria';
    const similares = cursos.filter((x) => x.id !== c.id && x.tipo !== 'mentoria').sort((x, y) => (y.area === c.area ? 1 : 0) - (x.area === c.area ? 1 : 0) || y.alunos - x.alunos).slice(0, 6);
    modalRoot.innerHTML = '<div class="modal" role="dialog" aria-modal="true" aria-label="' + esc(c.titulo) + '"><div class="modal__backdrop" data-action="close-modal"></div><article class="sheet">' +
      '<div class="sheet__hero">' + courseCover(c, { title: '', kicker: '' }) + '<button class="sheet__close" data-action="close-modal" aria-label="Fechar">' + icon('close') + '</button>' +
        '<div class="sheet__over"><p class="sheet__kicker">' + (men ? 'Mentoria' : esc(areas[c.area].nome)) + (c.sub ? ' · ' + esc(c.sub) : '') + '</p><h2 class="sheet__title">' + esc(c.titulo) + '</h2>' +
        '<div class="sheet__actions"><a class="btn btn--light" href="#/aula/' + c.id + '/' + a.id + '">' + icon('play') + (p === 100 ? 'Rever' : st ? 'Continuar' : 'Assistir') + '</a>' + listBtn(c.id) + likeBtn(c.id) + '</div></div></div>' +
      '<div class="sheet__body"><div class="sheet__intro">' +
        '<div class="sheet__meta"><span class="nota">' + icon('star') + String(c.nota).replace('.', ',') + '</span><span>' + c.aulas.length + ' aulas</span><span>' + fmtMin(c.totalMin) + '</span></div>' +
        (st ? '<div class="sheet__resume">' + (p === 100 ? 'Você concluiu este curso.' : 'Você está na aula ' + a.n + ' de ' + c.aulas.length + ' · ' + p + '% concluído') + '<span class="progressbar"><i style="width:' + p + '%"></i></span></div>' : '') +
        '<p class="sheet__desc">' + esc(c.desc) + '</p></div>' +
        (men ? '<div class="sheet__section" style="margin-top:24px"><a class="btn btn--outline" href="#/mentoria">' + icon('bolt') + 'Abrir a área da mentoria</a></div>' : '') +
        '<section class="sheet__section"><div class="sheet__sechead"><h3>Aulas</h3><label class="select"><span class="sr-only">Módulo</span><select id="modsel">' + c.modulos.map((m) => '<option value="' + m.i + '"' + (m.i === modalModule ? ' selected' : '') + '>' + esc(modLabel(c, m)) + (m.bloqueado ? ' (bloqueada)' : '') + '</option>').join('') + '</select></label></div><div id="eplist">' + epList(c, modalModule) + '</div></section>' +
        '<section class="sheet__section" id="ebsec"><div class="sheet__sechead"><h3>' + (men ? 'Materiais da mentoria' : 'E-books') + '</h3>' + (men ? '' : '<p class="sheet__note">' + c.aulas.length + ' e-books · um por aula</p>') + '</div>' +
          (men ? ebooksEntry(c, 'a', 'href="' + EBOOKS + '"') : '<div id="eblist">' + ebookGrid(c) + '</div>') + '</section>' +
        '<section class="sheet__section"><div class="sheet__sechead"><h3>Mais como este</h3></div><div class="more">' + similares.map((x) => '<div class="morecard"><a href="#/curso/' + x.id + '" aria-label="' + esc(x.titulo) + '">' + courseCover(x) + '</a><div class="morecard__body"><div class="morecard__row"><span class="morecard__meta"><span class="nota">' + icon('star') + String(x.nota).replace('.', ',') + '</span><span>' + fmtMin(x.totalMin) + '</span></span>' + listBtn(x.id, 'sm') + '</div><p>' + esc(x.desc) + '</p></div></div>').join('') + '</div></section>' +
      '</div></article></div>';
    $('#modsel', modalRoot).onchange = (e) => { modalModule = Number(e.target.value); $('#eplist', modalRoot).innerHTML = epList(c, modalModule); };
    const eb = $('#eblist', modalRoot);
    if (eb) eb.onclick = (e) => {
      if (!e.target.closest('#ebmore')) return;
      modalEbooks = !modalEbooks;
      eb.innerHTML = ebookGrid(c);
      $('#ebmore', eb).focus({ preventScroll: true });
    };
  }
  /* e-books do curso: mostra os quatro primeiros e abre o restante sob demanda */
  function ebookGrid(c) {
    const n = c.aulas.length, rotulo = modalEbooks ? 'Mostrar menos e-books' : 'Ver os ' + n + ' e-books';
    return '<div class="files files--cols">' + (modalEbooks ? c.aulas : c.aulas.slice(0, 4)).map(ebookFile).join('') + '</div>' +
      (n > 4 ? '<div class="expander"><button class="rbtn rbtn--sm" id="ebmore" aria-expanded="' + modalEbooks + '" aria-label="' + rotulo + '" title="' + rotulo + '">' + icon('down') + '</button></div>' : '');
  }
  function openCourse(id, ver) {
    const c = byId[id];
    if (!c) { location.replace('#/'); return; }
    hidePeek(); closeTransient();
    window.dispatchEvent(new Event('ems:pause'));
    if (!modalRoot.firstChild) lastFocus = document.activeElement;
    modalCourse = c;
    modalModule = nextAula(c).modulo;
    modalEbooks = ver === 'ebooks';
    renderCourse();
    document.body.classList.add('has-modal');
    const box = modalRoot.firstElementChild;
    let y = 0;
    if (modalEbooks) { for (let n = $('#ebsec', box); n && n !== box; n = n.offsetParent) y += n.offsetTop; y -= 24; }
    box.scrollTop = y;
    $('.sheet__close', modalRoot).focus({ preventScroll: true });
  }
  function openDialog(html, label) {
    if (!modalRoot.firstChild) lastFocus = document.activeElement;
    modalCourse = null;
    modalRoot.innerHTML = '<div class="modal" role="dialog" aria-modal="true" aria-label="' + esc(label) + '"><div class="modal__backdrop" data-action="close-modal"></div><article class="sheet sheet--narrow"><button class="sheet__close" data-action="close-modal" aria-label="Fechar">' + icon('close') + '</button>' + html + '</article></div>';
    document.body.classList.add('has-modal');
    $('.sheet__close', modalRoot).focus({ preventScroll: true });
  }
  function closeModal() {
    if (!modalRoot.firstChild) return false;
    modalRoot.innerHTML = '';
    modalCourse = null;
    document.body.classList.remove('has-modal');
    if (lastFocus && document.contains(lastFocus)) lastFocus.focus({ preventScroll: true });
    return true;
  }

  /* --------------------------------------------------------------- roteador */
  const view = $('#view');
  const ROUTES = [
    [/^\/$/, home, 'inicio'], [/^\/mentoria$/, mentoria, 'mentoria'], [/^\/cursos$/, catalog, 'cursos'], [/^\/trilhas$/, tracks, 'trilhas'], [/^\/trilha\/([\w-]+)$/, track, 'trilha'],
    [/^\/ao-vivo$/, live, 'ao-vivo'], [/^\/minha-lista$/, myList, 'lista'], [/^\/progresso$/, progress, 'progresso'], [/^\/certificados$/, certificates, 'certificados'],
    [/^\/conta$/, account, 'conta'], [/^\/aula\/([\w-]+)\/([\w-]+)$/, lesson, 'aula'], [/^\/entrar$/, login, 'entrar'], [/^\/busca$/, search, 'busca'], [/^\/oferta\/([\w-]+)$/, offer, 'oferta'], [/^\/ajuda$/, help, 'ajuda'],
  ].concat(AREA === 'coprodutor'
    /* área do coprodutor: só existe em coprodutor.html; as telas ficam em assets/js/admin.js.
       Na área de membros esse endereço não existe, então o aluno cai em "Página não encontrada". */
    ? [[/^\/coprodutor(?:\/(.*))?$/, (el, p, query) => window.EMS_ADMIN.render(el, p[0] || '', query), 'coprodutor']]
    : []);
  let currentRaw = null, preSearch = '#/';

  function parse() {
    const raw = location.hash.replace(/^#/, '') || '/';
    const i = raw.indexOf('?');
    return { raw, path: i < 0 ? raw : raw.slice(0, i), query: new URLSearchParams(i < 0 ? '' : raw.slice(i + 1)) };
  }
  function renderBase(r) {
    cleanups.forEach((fn) => fn());
    cleanups = []; railUpdaters = [];
    hidePeek();
    let found = null;
    for (const rt of ROUTES) { const m = r.path.match(rt[0]); if (m) { found = [rt, m.slice(1)]; break; } }
    document.body.dataset.page = found ? found[0][2] : 'erro';
    currentRaw = r.raw;
    if (found) found[0][1](view, found[1], r.query); else notFound(view);
    updateNav(r.path);
    dirty = false;
    onScroll();
  }
  function route() {
    const r = parse();
    closeTransient();
    /* em coprodutor.html não existe nenhuma tela da área de membros */
    if (AREA === 'coprodutor' && r.path.indexOf('/coprodutor') !== 0) { location.replace('#/coprodutor'); return; }
    const m = r.path.match(/^\/curso\/([\w-]+)$/);
    if (m) {
      if (currentRaw == null) renderBase({ raw: '/', path: '/', query: new URLSearchParams() });
      openCourse(m[1], r.query.get('ver'));
      return;
    }
    const hadModal = closeModal();
    if (hadModal && r.raw === currentRaw) {
      if (dirty) { const y = window.scrollY; renderBase(r); window.scrollTo(0, y); }
      return;
    }
    if (r.path !== '/busca') {
      const q = $('#q');
      if (q && q.value) { q.value = ''; $('#search').classList.remove('is-open'); }
    }
    renderBase(r);
    window.scrollTo(0, 0);
  }

  /* ----------------------------------------------------- interações globais */
  const nav = $('#nav'), peek = $('#peek');
  function onScroll() { nav.classList.toggle('is-solid', window.scrollY > 12); }
  function closeTransient() { $$('.dd.is-open').forEach((d) => { d.classList.remove('is-open'); $('[data-action="dd"]', d).setAttribute('aria-expanded', 'false'); }); }

  /* cartão expandido ao passar o mouse (só com mouse e tela larga) */
  const canHover = window.matchMedia('(hover: hover) and (min-width: 900px)');
  let peekTimer = null, peekFor = null;
  function hidePeek() {
    clearTimeout(peekTimer);
    if (!peekFor) return;
    peekFor = null;
    peek.classList.remove('is-on');
    setTimeout(() => { if (!peekFor) peek.hidden = true; }, 220);
  }
  function showPeek(cardEl) {
    const c = byId[cardEl.dataset.peek];
    if (!c || !document.contains(cardEl)) return;
    const r = cardEl.getBoundingClientRect();
    const w = Math.min(Math.max(320, r.width * 1.5), window.innerWidth - 24);
    let left = r.left + r.width / 2 - w / 2;
    left = Math.max(12, Math.min(left, window.innerWidth - w - 12));
    const top = Math.max(window.scrollY + 76, r.top + window.scrollY + r.height / 2 - (w * 9) / 32 - 60);
    const a = nextAula(c), p = pct(c);
    peek.style.left = left + 'px'; peek.style.top = top + 'px'; peek.style.width = w + 'px';
    peek.style.transformOrigin = (((r.left + r.width / 2 - left) / w) * 100) + '% 35%';
    peek.innerHTML = '<a href="#/curso/' + c.id + '" tabindex="-1">' + courseCover(c) + '</a><div class="peek__body">' +
      '<div class="peek__actions"><a class="rbtn rbtn--solid" href="#/aula/' + c.id + '/' + a.id + '" aria-label="' + (started(c) ? 'Continuar' : 'Assistir') + '" title="' + (started(c) ? 'Continuar' : 'Assistir') + '">' + icon('play') + '</a>' + listBtn(c.id) + likeBtn(c.id) + '<a class="rbtn" href="#/curso/' + c.id + '" aria-label="Mais informações" title="Mais informações">' + icon('down') + '</a></div>' +
      '<div class="peek__meta"><span class="nota">' + icon('star') + String(c.nota).replace('.', ',') + '</span><span>' + c.aulas.length + ' aulas · ' + fmtMin(c.totalMin) + '</span></div>' +
      '<p class="peek__tags">' + c.tags.map(esc).join('<i>•</i>') + '</p>' +
      (started(c) && p < 100 ? '<div class="peek__prog"><span class="progressbar"><i style="width:' + p + '%"></i></span><span>Aula ' + a.n + ' de ' + c.aulas.length + '</span></div>' : '') + '</div>';
    peek.hidden = false;
    peekFor = cardEl;
    requestAnimationFrame(() => requestAnimationFrame(() => { if (peekFor === cardEl) peek.classList.add('is-on'); }));
  }
  document.addEventListener('mouseover', (e) => {
    if (!canHover.matches || document.body.classList.contains('has-modal')) return;
    const overPeek = e.target.closest && e.target.closest('#peek');
    const cardEl = e.target.closest && e.target.closest('[data-peek]');
    if (overPeek) { clearTimeout(peekTimer); return; }
    if (cardEl) {
      if (cardEl === peekFor) return;
      clearTimeout(peekTimer);
      peekTimer = setTimeout(() => showPeek(cardEl), 480);
    } else { hidePeek(); }
  });
  document.addEventListener('mouseleave', hidePeek);

  const ACTIONS = {
    list(t) {
      const id = t.dataset.id, on = !inList(id);
      S.list = on ? [id].concat(S.list) : S.list.filter((x) => x !== id);
      save();
      swap('[data-action="list"][data-id="' + id + '"]', (b) => listBtn(id, b.dataset.kind));
      toast(on ? 'Adicionado à Minha lista' : 'Removido da Minha lista', on ? 'check' : 'close');
    },
    like(t) {
      const id = t.dataset.id;
      S.liked[id] = !S.liked[id]; save();
      swap('[data-action="like"][data-id="' + id + '"]', (b) => likeBtn(id, b.dataset.kind));
      if (S.liked[id]) toast('Vamos recomendar mais conteúdos assim', 'thumb');
    },
    remind(t) {
      const id = t.dataset.id, l = lives.find((x) => x.id === id);
      S.reminders[id] = !S.reminders[id]; save();
      swap('[data-action="remind"][data-id="' + id + '"]', () => remindBtn(l));
      toast(S.reminders[id] ? 'Lembrete ativado: avisaremos uma hora antes' : 'Lembrete desativado', S.reminders[id] ? 'bell' : 'close');
    },
    toast(t) { toast(t.dataset.msg, t.dataset.ico); },
    /* sai da visualização como membro e volta para a tela em que o coprodutor estava */
    'voltar-coprodutor'() { sessao.gravar('visualizando', null); location.href = 'coprodutor.html' + (sessao.ler('voltar') || '#/coprodutor'); },
    /* checkout: abre o endereço cadastrado no curso; sem endereço, só avisa (protótipo) */
    checkout(t) {
      const c = ofertaById[t.dataset.id];
      if (c && c.checkout) window.open(c.checkout, '_blank', 'noopener');
      else toast('Checkout ilustrativo: aqui o botão abre a página de pagamento', 'cart');
    },
    scrollto(t) {
      const alvo = $(t.dataset.target);
      if (alvo) window.scrollTo({ top: alvo.getBoundingClientRect().top + window.scrollY - nav.offsetHeight - 16, behavior: 'smooth' });
    },
    switch(t) { t.setAttribute('aria-checked', t.getAttribute('aria-checked') !== 'true'); },
    'close-modal'() { if (modalCourse) location.hash = '#' + (currentRaw || '/'); else closeModal(); },
    /* menu "Entrar" da tela de login: a opção da própria tela fecha o menu e leva ao campo de e-mail */
    'login-aqui'() { closeTransient(); const campo = $('.gm-login__cartao input'); if (campo) campo.focus(); },
    dd(t) {
      const d = t.closest('.dd'), open = !d.classList.contains('is-open');
      closeTransient();
      d.classList.toggle('is-open', open);
      t.setAttribute('aria-expanded', open);
    },
    'search-open'() {
      const s = $('#search'), q = $('#q');
      if (s.classList.contains('is-open') && !q.value) { s.classList.remove('is-open'); q.blur(); return; }
      s.classList.add('is-open'); q.focus();
    },
    reset() { try { localStorage.removeItem(KEY); } catch (e) { /* ignora */ } S = seed(); location.hash = '#/'; renderBase(parse()); window.scrollTo(0, 0); toast('Dados de exemplo restaurados'); },
  };

  document.addEventListener('click', (e) => {
    const rb = e.target.closest('[data-rail]');
    if (rb) {
      const track = $('.rail__track', rb.closest('.rail'));
      const pad = parseFloat(getComputedStyle(track).paddingLeft) || 0;
      track.scrollBy({ left: Number(rb.dataset.rail) * (track.clientWidth - pad * 2), behavior: 'smooth' });
      return;
    }
    const t = e.target.closest('[data-action]');
    if (t && ACTIONS[t.dataset.action]) {
      if (t.tagName === 'A') e.preventDefault();
      ACTIONS[t.dataset.action](t, e);
      return;
    }
    if (!e.target.closest('.dd')) closeTransient();
    else if (e.target.closest('.dd__panel a')) closeTransient();
    const same = e.target.closest('a[href^="#/"]');
    if (same && same.getAttribute('href') === (location.hash || '#/') && !document.body.classList.contains('has-modal')) window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (modalRoot.firstChild) ACTIONS['close-modal']();
      else if ($('.dd.is-open')) closeTransient();
      else { const s = $('#search'), q = $('#q'); if (s.classList.contains('is-open')) { q.value = ''; q.blur(); s.classList.remove('is-open'); if (parse().path === '/busca') location.hash = preSearch; } }
    } else if (e.key === '/' && AREA === 'membros' && !/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) && !modalRoot.firstChild) {
      e.preventDefault(); ACTIONS['search-open']();
    }
  });

  function bindSearch() {
    const q = $('#q'), s = $('#search');
    q.addEventListener('input', () => {
      const v = q.value.trim(), onSearch = parse().path === '/busca';
      if (v) {
        const h = '#/busca?q=' + encodeURIComponent(v);
        if (onSearch) { history.replaceState(null, '', h); renderBase(parse()); }
        else { preSearch = location.hash || '#/'; if (preSearch.indexOf('#/curso/') === 0) preSearch = '#' + (currentRaw || '/'); location.hash = h; }
      } else if (onSearch) { location.hash = preSearch; }
    });
    q.addEventListener('blur', () => { if (!q.value) s.classList.remove('is-open'); });
    s.addEventListener('submit', (e) => e.preventDefault());
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('scrollend', onScroll, { passive: true });
  window.addEventListener('resize', () => { hidePeek(); railUpdaters.forEach((fn) => fn()); });
  window.addEventListener('hashchange', route);

  /* O que a área do coprodutor (assets/js/admin.js) usa daqui: utilitários, capas, datas e os
     dados de exemplo. Ela fica em arquivo próprio e não muda nada na área de membros. */
  window.EMS = {
    $, $$, esc, cap, icon, toast, fmtMin, fmtData, fmtQuando, fmtPreco, emDias, diasAte, contador, dateBox, cover, courseCover, openDialog, closeModal,
    cursos, ofertas, areas, lives, comunidade, ajuda, marca, usuario, quiz, trilhas, instrutores, MENTORIA, pct,
    estado: () => S, salvar: save, aoSair: (fn) => cleanups.push(fn), sessao, ehCoprodutor, telaLogin, corDoNavegador, COR_LOGIN,
  };

  /* "Visualizar como membro": o botão de voltar só existe para quem entrou como coprodutor e pediu
     a visualização. O aluno nunca vê este elemento. */
  if (AREA === 'membros' && ehCoprodutor() && sessao.ler('visualizando') === '1') {
    const barra = document.createElement('div');
    barra.className = 'previa';
    barra.setAttribute('role', 'region');
    barra.setAttribute('aria-label', 'Visualização como membro');
    barra.innerHTML = '<span>' + icon('info') + 'Visualizando como membro</span><button class="btn btn--sm btn--red" data-action="voltar-coprodutor">' + icon('left') + 'Voltar à área do coprodutor</button>';
    document.body.appendChild(barra);
  }

  renderShell();
  bindSearch();
  route();
})();
