/* GoMut — área do coprodutor (protótipo das telas e dos fluxos).

   A GoMut é a plataforma; a mentoria gerenciada aqui é a do cliente (Emergensimples · Plantão sem GPT).
   A referência de design é a área de membros: mesmos componentes, formatos e tipografia.
   Só as cores mudam, para a paleta da GoMut (creme, grafite, Verde GO e âmbar), e entra o
   logotipo da GoMut na barra do topo e na entrada (ver assets/css/admin.css e assets/marca/).
   A organização do conteúdo segue a da Eduzz Membros: temas > módulos > aulas, com
   "Configurações de publicação" e data de liberação por módulo e por aula.

   Os dados ficam só no navegador (localStorage). Ligar esta área à área de membros é tarefa da
   programação. Duas pontes já funcionam no protótipo, porque usam dados que o aluno cria:
   responder a um chamado e responder na comunidade. */
(function () {
  'use strict';

  const KEY = 'emergensimples:coprodutor:v1';
  let E = null;       /* API da área de membros (window.EMS): ícones, capas, datas, avisos */
  let A = null;       /* dados da área do coprodutor */
  let tela = null;    /* tela atual, para redesenhar depois de salvar */
  let abertos = null; /* módulos abertos na tela de um tema */
  let cfgAba = 'mentoria', chAba = 'aberto', alFiltro = 'todos';

  /* ------------------------------------------------------------ utilitários */
  const esc = (s) => E.esc(s == null ? '' : String(s));
  const icon = (n, c) => E.icon(n, c);
  const iso = (d) => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  const deIso = (s) => new Date(s + 'T00:00');
  const dataBR = (s) => (s ? s.slice(8, 10) + '/' + s.slice(5, 7) + '/' + s.slice(0, 4) : '');
  const uid = (p) => p + Date.now().toString(36) + Math.floor(Math.random() * 1296).toString(36);
  const slug = (t) => String(t).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40);
  const plural = (n, um, varios) => n + ' ' + (n === 1 ? um : varios);
  const ir = (sub) => { location.hash = '#/coprodutor' + (sub ? '/' + sub : ''); };
  const norm = (s) => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const iniciais = (nome) => { const p = String(nome).trim().split(/\s+/); return ((p[0] || '').charAt(0) + (p.length > 1 ? p[p.length - 1].charAt(0) : '')).toUpperCase(); };


  /* Link do Vimeo -> endereço de incorporação. Aceita vimeo.com/ID, vimeo.com/ID/CHAVE e player.vimeo.com/video/ID. */
  function vimeoSrc(url) {
    const m = String(url || '').trim().match(/^(?:https?:\/\/)?(?:www\.|player\.)?vimeo\.com\/(?:video\/)?(\d{6,12})(?:(?:\/|\?h=)([0-9a-f]{6,}))?/i);
    return m ? 'https://player.vimeo.com/video/' + m[1] + (m[2] ? '?h=' + m[2] : '') : '';
  }

  /* ------------------------------------------------------------------ dados */
  function semente() {
    const lib = (dias) => (dias ? { tipo: 'data', data: iso(E.emDias(dias)) } : { tipo: 'imediata' });
    const mesesAtras = (n) => { const d = new Date(); d.setMonth(d.getMonth() - n); return iso(d); };
    const maisMeses = (s, n) => { const d = deIso(s); d.setMonth(d.getMonth() + n); return iso(d); };
    /* módulos e aulas de um tema ou de um curso à venda */
    const modsDe = (c) => c.modulos.map((m) => ({
      id: c.id + '-m' + (m.i + 1), titulo: m.titulo, lib: lib(m.bloqueado),
      aulas: m.aulas.map((a) => ({ id: a.id, titulo: a.titulo, desc: '', vimeo: '', min: a.min, lib: { tipo: 'imediata' }, status: 'publicada', ebook: 'ebook-' + slug(a.titulo) + '.pdf', quiz: null })),
    }));
    const temas = E.cursos.map((c) => ({
      id: c.id, jornada: c.tipo === 'mentoria', titulo: c.tipo === 'mentoria' ? 'Jornada da mentoria' : c.titulo,
      area: c.tipo === 'mentoria' ? '' : c.area, desc: c.tipo === 'mentoria' ? 'As semanas da mentoria, liberadas uma por vez.' : c.desc, h: c.h, motif: c.motif,
      /* o que o aluno vê no cartão e na janela do tema: subtítulo, etiquetas, selo "Novo" e capa */
      sub: c.sub || '', tags: (c.tags || []).slice(), novo: !!c.novo, capa: '',
      modulos: modsDe(c),
    }));
    const areas = {};
    Object.keys(E.areas).forEach((k) => { areas[k] = { nome: E.areas[k].nome, h: E.areas[k].h }; });
    /* fileiras do Início: as "fixas" são montadas pela plataforma; as "por área" mostram os temas das áreas marcadas */
    const fixa = (nome) => ({ id: slug(nome), nome, visivel: true, tipo: 'fixa' });
    const porArea = (nome, lista) => ({ id: slug(nome), nome, visivel: true, tipo: 'areas', areas: lista });
    const aluno = (nome, email, meses, plano, progresso, ultimo) => ({ id: slug(nome), nome, email, entrada: mesesAtras(meses), ate: maisMeses(mesesAtras(meses), 12), plano, progresso, ultimo, obs: '' });
    return {
      temas,
      areas,
      trilhas: E.trilhas.map((t) => ({ id: t.id, titulo: t.titulo, desc: t.desc, temas: t.cursos.slice(), capa: '' })),
      encontros: E.lives.map((l) => ({ id: l.id, titulo: l.titulo, tipo: l.tipo, data: iso(l.quando), hora: String(l.quando.getHours()).padStart(2, '0') + ':' + String(l.quando.getMinutes()).padStart(2, '0'), min: l.min, desc: l.desc, link: 'https://sala.exemplo.com/' + l.id, gravacao: '', capa: '' })),
      ofertas: E.ofertas.map((o) => ({ id: o.id, titulo: o.titulo, area: o.area, desc: o.desc, preco: o.preco, parcelas: o.parcelas, checkout: '', visivel: true, h: o.h, motif: o.motif,
        aprende: (o.aprende || []).slice(), garantia: 7, capa: '', modulos: modsDe(o) })),
      inicio: {
        frase: E.MENTORIA.desc, vitrineTitulo: 'Outros cursos da ' + E.marca.nome, vitrineTexto: 'Escolha um para ver o conteúdo e comprar.',
        fileiras: [fixa('Continue de onde parou'), fixa('Top 10 no plantão esta semana'), fixa('Sua jornada na mentoria'), fixa('Novidades'), fixa('Trilhas para seguir em ordem'),
          porArea('Cardiologia', ['cardio', 'uti']), fixa('Próximos encontros ao vivo'), porArea('Via aérea, ventilação e paciente grave', ['viaaerea', 'infecto', 'emergencia']),
          fixa('Minha lista'), porArea('Rotina, comunicação e carreira', ['rotina', 'neuro', 'trauma']), fixa('Vitrine de cursos à venda')],
      },
      alunos: [
        aluno(E.usuario.nome, E.usuario.email, 3, 'ativo', E.pct(E.MENTORIA), 'hoje'),
        aluno('Lucas Ferraz', 'lucas@exemplo.com', 3, 'ativo', 44, 'hoje'),
        aluno('Paula Antunes', 'paula@exemplo.com', 3, 'ativo', 38, 'ontem'),
        aluno('Rodrigo Leal', 'rodrigo@exemplo.com', 5, 'ativo', 61, 'há 2 dias'),
        aluno('Beatriz Nogueira', 'beatriz@exemplo.com', 8, 'ativo', 79, 'há 4 dias'),
        aluno('Caio Teixeira', 'caio@exemplo.com', 1, 'ativo', 9, 'hoje'),
        aluno('Fernanda Lopes', 'fernanda@exemplo.com', 10, 'ativo', 92, 'há 1 semana'),
        aluno('Gustavo Prates', 'gustavo@exemplo.com', 6, 'cancelado', 17, 'há 2 meses'),
      ],
      chamados: [
        { n: 1022, aluno: 'Lucas Ferraz', assunto: 'Aulas e vídeos', texto: 'O vídeo da aula “Oxigênio, VNI ou tubo?” não carrega no celular. No computador funciona.', dias: 1, status: 'aberto', resposta: '' },
        { n: 1021, aluno: 'Paula Antunes', assunto: 'Acesso à plataforma', texto: 'Pedi para redefinir a senha e o e-mail não chegou. Já olhei a caixa de spam.', dias: 2, status: 'aberto', resposta: '' },
        { n: 1016, aluno: 'Rodrigo Leal', assunto: 'Certificado', texto: 'Quando o certificado fica disponível?', dias: 9, status: 'resolvido', resposta: 'O certificado é liberado ao final da mentoria, 12 meses depois da sua entrada. Ele aparece na página Certificado.' },
      ],
      ocultas: {},
      cert: { texto: 'concluiu a mentoria {mentoria}, turma {ano}.', assinatura: E.marca.nome, cargo: 'Plataforma de cursos' },
      avisos: { aula: true, encontro: true, comentario: true, chamado: true },
      /* e-mails enviados ao aluno (ele pode desligar cada um em Conta e preferências) */
      emails: { aulas: true, encontros: true },
      /* encontros: frase do topo da página da mentoria; mentor e mentorTag: quem responde na comunidade */
      mentoria: { nome: E.marca.mentoria, duracao: 12, suporte: 'suporte@exemplo.com', encontros: 'Encontros ao vivo às quintas, 20h', mentor: E.instrutores.helena.nome, mentorTag: 'Mentora',
        /* aba Básico do curso: autor (tutor), situação de publicação e capa (nome do arquivo e imagem reduzida) */
        tutor: E.instrutores.helena.nome, status: 'publicado', capa: '', capaImg: '' },
      /* nome mostrado na barra do topo, no rodapé e no certificado da área de membros */
      marca: { nome: E.marca.nome },
      /* Conta e preferências > Assinatura, na área de membros */
      plano: {
        desc: 'Acesso completo à mentoria, com encontros ao vivo e materiais complementares',
        itens: [
          { t: 'Aulas gravadas', d: 'Com e-book em cada aula' },
          { t: 'Acesso completo à mentoria', d: '{mentoria} · Turma {ano}' },
          { t: 'Encontros ao vivo semanais', d: 'Com gravação disponível depois' },
          { t: 'Comunidade da turma', d: 'Troca direta com mentores e colegas' },
          { t: 'Certificado da mentoria', d: 'Liberado ao final da mentoria, que dura {duracao}' },
        ],
      },
      /* Central de ajuda: opções do campo "Assunto" do chamado */
      ajuda: { assuntos: E.ajuda.assuntos.slice() },
      /* atalhos mostrados na página de busca do aluno */
      busca: ['ECG', 'Sepse', 'Via aérea', 'Prescrição', 'AVC', 'Trauma'],
      cursosNovos: [],   /* cursos criados em "Meus cursos" > "Criar curso" */
    };
  }
  /* Dados salvos antes de uma configuração existir ganham o valor de exemplo dela, sem perder o que já foi alterado. */
  function completar(s) {
    const b = semente();
    ['areas', 'emails', 'marca', 'plano', 'ajuda', 'busca', 'cursosNovos'].forEach((k) => { if (s[k] == null) s[k] = b[k]; });
    ['encontros', 'mentor', 'mentorTag', 'tutor', 'status', 'capa', 'capaImg'].forEach((k) => { if (s.mentoria[k] == null) s.mentoria[k] = b.mentoria[k]; });
    s.temas.forEach((t) => { if (t.tags == null) { const r = b.temas.find((x) => x.id === t.id) || {}; t.sub = r.sub || ''; t.tags = r.tags || []; t.novo = !!r.novo; t.capa = ''; } });
    s.ofertas.forEach((o) => { if (o.aprende == null) { const r = b.ofertas.find((x) => x.id === o.id) || {}; o.aprende = r.aprende || []; o.garantia = 7; o.capa = ''; o.modulos = r.modulos || []; } });
    s.trilhas.forEach((t) => { if (t.capa == null) t.capa = ''; });
    s.encontros.forEach((e) => { if (e.capa == null) e.capa = ''; });
    if (s.inicio.fileiras.some((f) => !f.tipo)) s.inicio.fileiras = b.inicio.fileiras.map((f) => { const antiga = s.inicio.fileiras.find((x) => x.nome === f.nome); return antiga ? Object.assign({}, f, { visivel: antiga.visivel }) : f; });
    return s;
  }
  function carregar() {
    try { const s = JSON.parse(localStorage.getItem(KEY)); if (s && s.temas && s.alunos && s.mentoria) return completar(s); } catch (e) { /* segue com o exemplo */ }
    return semente();
  }
  function salvar() { try { localStorage.setItem(KEY, JSON.stringify(A)); } catch (e) { /* ignora */ } }

  /* tema do catálogo ou curso à venda: os dois têm módulos e aulas e usam a mesma tela de conteúdo */
  const achaTema = (id) => A.temas.find((t) => t.id === id) || A.ofertas.find((o) => o.id === id);
  const ehVenda = (t) => A.ofertas.indexOf(t) >= 0;
  function achaAula(t, id) { for (const m of t.modulos) { const a = m.aulas.find((x) => x.id === id); if (a) return { m, a }; } return null; }
  const areaNome = (k) => (k && A.areas[k] ? A.areas[k].nome : 'Mentoria');
  const areasOp = () => [['', 'Mentoria']].concat(Object.keys(A.areas).map((k) => [k, A.areas[k].nome]));
  function todasAulas() { const r = []; A.temas.forEach((t) => t.modulos.forEach((m) => m.aulas.forEach((a) => r.push({ t, m, a })))); return r; }
  const quando = (e) => new Date(e.data + 'T' + (e.hora || '00:00'));

  /* Chamados: os do aluno do protótipo (criados na Central de ajuda), os de outros alunos e o de exemplo. */
  function chamados() {
    const S = E.estado(), u = E.usuario.nome, ex = E.ajuda.exemplo;
    const doAluno = (S.tickets || []).map((t) => ({ n: t.n, aluno: u, assunto: t.assunto, texto: t.texto, quando: E.fmtQuando(new Date(t.quando)), status: t.status, resposta: t.resposta || '', ref: t, origem: 'aluno' }));
    const outros = A.chamados.map((t) => ({ n: t.n, aluno: t.aluno, assunto: t.assunto, texto: t.texto, quando: 'há ' + plural(t.dias, 'dia', 'dias'), status: t.status, resposta: t.resposta || '', ref: t, origem: 'outro' }));
    return doAluno.concat(outros, [{ n: ex.n, aluno: u, assunto: ex.assunto, texto: ex.texto, quando: 'há ' + ex.dias + ' dias', status: ex.status, resposta: ex.resposta, origem: 'fixo' }]).sort((a, b) => b.n - a.n);
  }
  /* Publicações da comunidade, com as respostas que o aluno e a mentora já deram. */
  function publicacoes() {
    const S = E.estado(), extra = S.replies || {};
    const meus = (S.posts || []).map((p, i) => (typeof p === 'string' ? { id: 'u' + i + '-' + p.length, texto: p } : p)).map((p) => ({ id: p.id, autor: E.usuario.nome, iniciais: E.usuario.iniciais, quando: 'agora', texto: p.texto, respostas: [] }));
    return meus.concat(E.comunidade).map((p) => Object.assign({}, p, { respostas: (p.respostas || []).concat(extra[p.id] || []) }));
  }
  const semResposta = (p) => !p.mentor && !p.respostas.some((r) => r.mentor);

  /* ------------------------------------------------------------- liberação */
  function libTag(l) {
    if (!l || l.tipo === 'imediata') return '<span class="tag tag--ok">Liberado</span>';
    if (l.tipo === 'dias') return '<span class="tag tag--line">' + l.dias + ' dias após a entrada</span>';
    return E.diasAte(deIso(l.data)) > 0 ? '<span class="tag tag--line">' + icon('lock') + 'Libera em ' + dataBR(l.data) + '</span>' : '<span class="tag tag--ok">Liberado em ' + dataBR(l.data) + '</span>';
  }
  function libCampos(l) {
    l = l || { tipo: 'imediata' };
    const op = (v, t, extra) => '<label class="opt"><input type="radio" name="lib" value="' + v + '"' + (l.tipo === v ? ' checked' : '') + '><span>' + t + '</span>' + (extra || '') + '</label>';
    return '<div class="opts">' + op('imediata', 'Imediata') +
      op('data', 'Em uma data', '<input class="input input--sm" type="date" name="libData" value="' + (l.data || '') + '" aria-label="Data de liberação">') +
      op('dias', 'Dias após a entrada do aluno', '<input class="input input--sm" type="number" min="1" max="365" name="libDias" value="' + (l.dias || 7) + '" aria-label="Quantidade de dias">') + '</div>';
  }
  const libLer = (d) => (d.lib === 'data' && d.libData ? { tipo: 'data', data: d.libData } : d.lib === 'dias' ? { tipo: 'dias', dias: Math.max(1, Number(d.libDias) || 1) } : { tipo: 'imediata' });

  /* --------------------------------------------------- peças de formulário */
  const campo = (rotulo, controle, dica, id) => '<div class="field">' + (rotulo ? '<label' + (id ? ' for="f-' + id + '"' : '') + '>' + rotulo + '</label>' : '') + controle + (dica ? '<p class="hint">' + dica + '</p>' : '') + '</div>';
  const entrada = (nome, valor, extra) => '<input class="input" id="f-' + nome + '" name="' + nome + '" value="' + esc(valor) + '"' + (extra ? ' ' + extra : '') + '>';
  const areaTexto = (nome, valor, linhas, extra) => '<textarea class="input" id="f-' + nome + '" name="' + nome + '" rows="' + (linhas || 4) + '"' + (extra ? ' ' + extra : '') + '>' + esc(valor) + '</textarea>';
  const selecao = (nome, opcoes, atual) => '<span class="select select--block"><select id="f-' + nome + '" name="' + nome + '">' + opcoes.map((o) => '<option value="' + esc(o[0]) + '"' + (String(o[0]) === String(atual) ? ' selected' : '') + '>' + esc(o[1]) + '</option>').join('') + '</select></span>';
  const chave = (caminho, ligado, rotulo) => '<button type="button" class="switch" role="switch" aria-checked="' + !!ligado + '" data-sw="' + caminho + '" aria-label="' + esc(rotulo) + '"></button>';

  /* Imagem de capa: o arquivo é escolhido no computador. No protótipo guarda-se só o nome dele;
     sem imagem, a capa continua sendo gerada com o título, como hoje. */
  const capaCampo = (atual) => campo('Imagem de capa', '<input class="input cop-arquivo" type="file" accept="image/*" name="capa" id="f-capa">',
    (atual ? 'Capa atual: ' + esc(atual) + '. Escolha outro arquivo para trocar. ' : 'Sem imagem, a capa é gerada com o título. ') + 'Tamanho recomendado: 1280 × 720 px, em JPG ou PNG.', 'capa');
  const capaLer = (f, atual) => { const i = f.querySelector('[name="capa"]'); return i && i.files && i.files[0] ? i.files[0].name : (atual || ''); };
  const lerLista = (txt, sep, max) => String(txt || '').split(sep).map((x) => x.trim()).filter(Boolean).slice(0, max || 99);
  /* setas de ordem (subir e descer um item de lista) */
  const setas = (cop, i, n) => '<button type="button" class="ibtn ibtn--up" data-cop="' + cop + '" data-i="' + i + '" data-d="-1" aria-label="Mover para cima"' + (i === 0 ? ' disabled' : '') + '>' + icon('down') + '</button>' +
    '<button type="button" class="ibtn" data-cop="' + cop + '" data-i="' + i + '" data-d="1" aria-label="Mover para baixo"' + (i === n - 1 ? ' disabled' : '') + '>' + icon('down') + '</button>';
  const mover = (lista, b) => { const i = Number(b.dataset.i), j = i + Number(b.dataset.d); if (j < 0 || j >= lista.length) return false; lista.splice(j, 0, lista.splice(i, 1)[0]); return true; };

  function dialogo(titulo, corpo, aoSalvar, rotulo, perigo) {
    E.openDialog('<div class="sheet__body cop-dialog"><h2>' + esc(titulo) + '</h2><form class="form" id="cop-form">' + corpo +
      '<div class="cop-dialog__foot"><button type="button" class="btn btn--outline" data-action="close-modal">Cancelar</button><button class="btn ' + (perigo ? 'btn--perigo' : 'btn--go') + '" type="submit">' + (rotulo || 'Salvar') + '</button></div></form></div>', titulo);
    const f = document.querySelector('#cop-form');
    f.onsubmit = (e) => {
      e.preventDefault();
      if (aoSalvar(Object.fromEntries(new FormData(f)), f) === false) return;
      salvar(); E.closeModal(); repintar();
    };
    const primeiro = f.querySelector('input:not([type="radio"]):not([type="checkbox"]), textarea, select');
    if (primeiro) primeiro.focus();
  }
  /* confirmações são sempre de ações que tiram algo do ar (excluir, cancelar, restaurar): botão em vermelho de perigo */
  const confirmar = (titulo, texto, rotulo, aoConfirmar) => dialogo(titulo, '<p class="cop-dialog__txt">' + texto + '</p>', () => { aoConfirmar(); }, rotulo, true);

  /* ----------------------------------------------------------- estrutura */
  /* A primeira tela do painel é "Meus cursos" (endereço #/coprodutor).
     A navegação fica no painel lateral, presente em todas as telas. LADO é a lista das opções, na
     ordem em que aparecem; cada linha tem [chave, endereço, nome, ícone]. As telas de dentro de um
     curso (Visão geral, Conteúdo, Ao vivo) são abertas a partir de "Meus cursos" e mantêm essa
     opção marcada. */
  const link = (sec) => '#/coprodutor' + (sec ? '/' + sec : '');
  /* ícones que só o painel usa, no mesmo traço dos ícones da área de membros */
  const traco = (d) => '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">' + d + '</svg>';
  const IC = {
    menu: traco('<path d="M4 7h16M4 12h16M4 17h16"/>'),
    grafico: traco('<path d="M4 20h16M7.5 20v-6M12 20V6M16.5 20v-9"/>'),
    escudo: traco('<path d="M12 3.5l7 2.6v5.2c0 4.2-2.8 7.7-7 9.2-4.2-1.5-7-5-7-9.2V6.1z"/><path d="M9 12l2.2 2.2 3.8-4"/>'),
  };
  const LADO = [
    ['criar', 'cursos/novo', 'Criar curso', () => icon('plus')],
    ['meus', '', 'Meus cursos', () => icon('grid')],
    ['relatorios', 'relatorios', 'Relatórios', () => IC.grafico],
    ['comunidade', 'comunidade', 'Comunidade', () => icon('message')],
    ['alunos', 'alunos', 'Alunos', () => icon('users')],
    ['certificados', 'certificados', 'Certificados', () => icon('award')],
    ['acesso', 'acesso', 'Controle de acesso', () => IC.escudo],
    ['chamados', 'chamados', 'Chamados', () => icon('help')],
    ['config', 'config', 'Configurações', () => icon('sliders')],
  ];
  /* qual opção do painel lateral fica marcada em cada tela */
  const opcaoAtiva = (sec, partes) => {
    if (sec === 'cursos' && partes[1] === 'novo') return 'criar';
    if (sec === '' || sec === 'cursos' || sec === 'visao' || sec === 'conteudo' || sec === 'ao-vivo') return 'meus';
    return sec;
  };
  /* Logotipo da GoMut: a arte original, sem redesenho, sempre sobre fundo claro (manual da marca). */
  const LOGO = '<img src="assets/marca/gomut-logo.png" alt="GoMut" width="1568" height="432">';
  function navHTML(sec, partes) {
    const ativa = opcaoAtiva(sec, partes);
    /* barra do topo: logotipo e conta. O botão de menu só aparece no celular, onde o painel lateral fica recolhido. */
    return '<header class="nav is-solid cop-nav"><button class="cop-nav__menu" type="button" data-lado aria-label="Abrir o menu" aria-expanded="false" aria-controls="cop-lado">' + IC.menu + '</button>' +
      '<a class="cop-brand" href="#/coprodutor" aria-label="GoMut: meus cursos">' + LOGO + '</a><span class="tag tag--go cop-nav__tag">Coprodutor</span>' +
      '<div class="nav__tools"><button class="btn btn--sm btn--outline cop-nav__aluno" data-ver="#/" aria-label="Visualizar como membro">' + icon('play') + '<span>Visualizar como membro</span></button>' +
      '<div class="dd"><button class="nav__profile" data-action="dd" aria-haspopup="true" aria-expanded="false" aria-label="Conta do coprodutor"><span class="avatar">CP</span><span class="caret"></span></button>' +
      '<div class="dd__panel dd__panel--menu"><div class="dd__head"><span class="avatar">CP</span><div><strong>Coprodutor</strong><span>Mentoria ' + esc(A.mentoria.nome) + '</span></div></div>' +
      '<a class="dd__item" href="' + link('') + '">' + icon('grid') + 'Meus cursos</a><a class="dd__item" href="' + link('config') + '">' + icon('sliders') + 'Configurações</a><button class="dd__item" data-ver="#/">' + icon('play') + 'Visualizar como membro</button>' +
      '<div class="dd__sep"></div><button class="dd__item" data-sair>' + icon('logout') + 'Sair</button></div></div></div></header>' +
      /* painel lateral: o menu do produtor */
      '<aside class="cop-lado" id="cop-lado"><nav class="cop-lado__menu" aria-label="Menu do painel">' +
      LADO.map((m) => '<a href="' + link(m[1]) + '"' + (m[0] === ativa ? ' class="is-on" aria-current="page"' : '') + '>' + m[3]() + '<span>' + m[2] + '</span></a>').join('') +
      '</nav></aside><button class="cop-lado__veu" type="button" data-lado tabindex="-1" aria-label="Fechar o menu"></button>';
  }
  /* Painel lateral no celular: abre e fecha pelo botão da barra do topo. */
  function alternarLado(el, abrir) {
    const lado = el.querySelector('.cop-lado'), botao = el.querySelector('.cop-nav__menu');
    if (!lado || !botao) return;
    const aberto = abrir === undefined ? !lado.classList.contains('is-aberto') : abrir;
    lado.classList.toggle('is-aberto', aberto);
    botao.setAttribute('aria-expanded', aberto);
    botao.setAttribute('aria-label', aberto ? 'Fechar o menu' : 'Abrir o menu');
  }
  /* caminho das telas de dentro do curso do cliente: Meus cursos · nome do curso · tela */
  const noCurso = (nome) => '<a href="' + link('') + '">' + icon('left') + 'Meus cursos</a><span>·</span><a href="' + link('cursos/mentoria') + '">' + esc(A.mentoria.nome) + '</a><span>·</span><span>' + nome + '</span>';
  const pagina = (o) => '<div class="page cop">' + (o.crumbs ? '<nav class="crumbs">' + o.crumbs + '</nav>' : '') +
    '<header class="page__head"><div><h1 class="page__title">' + esc(o.titulo) + '</h1>' + (o.sub ? '<p class="page__sub">' + o.sub + '</p>' : '') + '</div>' + (o.acoes ? '<div class="cop-acoes">' + o.acoes + '</div>' : '') + '</header>' +
    (o.abas || '') + o.corpo + '<p class="cop-foot">GoMut · área do coprodutor · protótipo: as alterações ficam salvas só neste navegador.</p></div>';
  const naoAchou = () => ({ html: pagina({ titulo: 'Página não encontrada', sub: 'Este endereço não existe na área do coprodutor.', corpo: '<a class="btn btn--light" href="#/coprodutor">Voltar a Meus cursos</a>' }) });

  function alternar(b) {
    const p = b.dataset.sw.split('.');
    let o = A;
    for (let i = 0; i < p.length - 1; i++) o = o[p[i]];
    o[p[p.length - 1]] = !o[p[p.length - 1]];
    salvar();
    b.setAttribute('aria-checked', o[p[p.length - 1]]);
    E.toast('Alteração salva');
  }

  function pintar(el, sub, query, manter) {
    const partes = sub.split('/').filter(Boolean), sec = partes[0] || '';
    if (el.querySelector('details[data-mod]')) abertos = new Set(Array.from(el.querySelectorAll('details[data-mod][open]')).map((d) => d.dataset.mod));
    const T = (TELAS[sec] || naoAchou)(partes.slice(1), query);
    const y = window.scrollY;
    tela = { el, sub, query };
    el.innerHTML = navHTML(sec, partes) + T.html;
    el.onclick = (e) => {
      /* painel lateral no celular: o botão da barra abre e fecha; tocar fora ou numa opção fecha */
      if (e.target.closest('[data-lado]')) { alternarLado(el); return; }
      if (e.target.closest('.cop-lado a')) alternarLado(el, false);
      const ver = e.target.closest('[data-ver]');
      if (ver) { visualizar(ver.dataset.ver); return; }
      if (e.target.closest('[data-sair]')) { sair(el); return; }
      const sw = e.target.closest('[data-sw]');
      if (sw) { alternar(sw); return; }
      const t = e.target.closest('[data-cop]');
      if (t && T.on && T.on[t.dataset.cop]) T.on[t.dataset.cop](t, e);
    };
    el.onsubmit = (e) => {
      const f = e.target, k = f.dataset.form;
      if (k && T.submit && T.submit[k]) { e.preventDefault(); T.submit[k](Object.fromEntries(new FormData(f)), f); }
    };
    el.oninput = (e) => { if (T.input) T.input(e.target, el); };
    el.onkeydown = (e) => { if (e.key === 'Escape') alternarLado(el, false); };
    if (!manter) E.aoSair(() => { el.onclick = null; el.onsubmit = null; el.oninput = null; el.onkeydown = null; });
    else window.scrollTo(0, y);
  }
  function repintar() { if (tela && document.contains(tela.el)) pintar(tela.el, tela.sub, tela.query, true); }

  /* --------------------------------------------- permissão e visualização */
  /* "Visualizar como membro": abre a área de membros (index.html) na tela pedida. A marca gravada
     na sessão é o que faz aparecer, lá, o botão "Voltar à área do coprodutor". Só chega aqui quem
     entrou como coprodutor; o aluno não tem nem a opção nem o botão. */
  function visualizar(destino) {
    E.sessao.gravar('visualizando', '1');
    E.sessao.gravar('voltar', location.hash || '#/coprodutor');
    location.href = 'index.html' + (destino || '#/');
  }
  function sair(el) {
    E.sessao.gravar('papel', null); E.sessao.gravar('visualizando', null); E.sessao.gravar('voltar', null);
    E.closeModal();
    history.replaceState(null, '', '#/coprodutor');
    entrarTela(el);
  }
  /* Entrada da área do coprodutor. No protótipo, qualquer preenchimento entra: o que importa é
     mostrar que esta área tem acesso próprio, separado do acesso do aluno. */
  function entrarTela(el) {
    tela = null;
    /* Tela de login da plataforma, a mesma da área de membros (E.telaLogin, em app.js).
       Aqui o cartão é "Gerenciar meus negócios". */
    el.innerHTML = E.telaLogin({ formId: 'cop-entrar', titulo: 'Gerenciar meus negócios', frase: 'Entre e gerencie seu negócio.',
      menu: [{ rotulo: 'Gerenciar meus negócios', ic: 'sliders', aqui: true }, { rotulo: 'Acessar minhas compras', ic: 'play', href: 'index.html#/entrar' }] });
    E.corDoNavegador(E.COR_LOGIN);
    el.onclick = null; el.oninput = null; el.onkeydown = null;
    el.onsubmit = (e) => {
      e.preventDefault();
      E.corDoNavegador('#ffffff');
      E.sessao.gravar('papel', 'coprodutor');
      E.toast('Você entrou como coprodutor');
      if (!A) A = carregar();
      pintar(el, '', new URLSearchParams(), false);
      window.scrollTo(0, 0);
    };
  }

  /* ============================================================ visão geral */
  function visao() {
    const aulas = todasAulas(), publicadas = aulas.filter((x) => x.a.status === 'publicada').length, semVideo = aulas.filter((x) => !vimeoSrc(x.a.vimeo)).length;
    const abertosCh = chamados().filter((c) => c.status === 'aberto').length, semResp = publicacoes().filter(semResposta).length;
    const ativos = A.alunos.filter((a) => a.plano === 'ativo').length;
    /* número de destaque: o mesmo cartão de "Meu progresso" da área de membros, com link para a tela do assunto */
    const bloco = (href, ic, rotulo, valor, apoio) => '<a class="stat" href="' + href + '"><p class="stat__label">' + icon(ic) + rotulo + '</p><p class="stat__value">' + valor + '</p><p class="stat__delta">' + apoio + '</p></a>';
    /* ferramenta de gestão: a mesma linha usada nas listas de materiais da área de membros
       (ícone, nome e uma frase), com etiqueta quando há pendência */
    const ferramenta = (href, ic, nome, texto, pendencia) => '<a class="file file--link" href="' + href + '"><span class="file__ico">' + icon(ic) + '</span><div><strong>' + nome + '</strong><span>' + texto + '</span></div>' +
      (pendencia ? '<span class="tag tag--alerta">' + pendencia + '</span>' : '') + icon('right', 'file__chev') + '</a>';
    const grupo = (titulo, itens) => '<div><p class="eyebrow cop-grupo">' + titulo + '</p><div class="files">' + itens.join('') + '</div></div>';
    const linha =(href, titulo, apoio, direita) => '<a class="setrow" href="' + href + '"><div><strong>' + titulo + '</strong><span>' + apoio + '</span></div>' + direita + '</a>';
    const libs = [];
    A.temas.forEach((t) => t.modulos.forEach((m, mi) => {
      if (m.lib.tipo === 'data' && E.diasAte(deIso(m.lib.data)) > 0) libs.push({ d: m.lib.data, titulo: (t.jornada ? 'Semana ' : 'Módulo ') + (mi + 1) + ' · ' + m.titulo, apoio: t.titulo + ' · ' + plural(m.aulas.length, 'aula', 'aulas'), href: link('conteudo/' + t.id) });
      m.aulas.forEach((a) => { if (a.lib.tipo === 'data' && E.diasAte(deIso(a.lib.data)) > 0) libs.push({ d: a.lib.data, titulo: a.titulo, apoio: t.titulo + ' · aula', href: link('conteudo/' + t.id + '/' + a.id) }); });
    }));
    libs.sort((a, b) => (a.d < b.d ? -1 : 1));
    const enc = A.encontros.filter((e) => E.diasAte(quando(e)) >= 0).sort((a, b) => quando(a) - quando(b)).slice(0, 3);
    const rascunhos = aulas.length - publicadas;
    const semCheckout = A.ofertas.filter((o) => !o.checkout).length;
    const curso = cursoDe('mentoria');
    return { on: acoesCurso(curso), html: pagina(Object.assign(cabecaCurso(curso, 'visao'), {
      corpo:
        '<div class="toolbar cop-resumo-topo"><span class="toolbar__count">O que está no ar na mentoria ' + esc(A.mentoria.nome) + ' e o que precisa da sua atenção.</span><a class="btn btn--go" href="' + link('conteudo') + '">' + icon('plus') + 'Cadastrar aula</a></div>' +
        '<div class="stats">' +
          bloco(link('alunos'), 'users', 'Alunos ativos', ativos, plural(A.alunos.length - ativos, 'plano cancelado', 'planos cancelados')) +
          bloco(link('conteudo'), 'play', 'Aulas publicadas', publicadas, plural(rascunhos, 'aula em rascunho', 'aulas em rascunho')) +
          bloco(link('chamados'), 'help', 'Chamados abertos', abertosCh, 'aguardando resposta do suporte') +
          bloco(link('comunidade'), 'message', 'Comentários sem resposta', semResp, 'na comunidade da mentoria') + '</div>' +
        /* ferramentas de gestão: tudo o que o coprodutor configura, em três grupos */
        '<div class="cop-sec"><h2 class="section-title">Ferramentas de gestão</h2><p>Tudo o que você configura para a área de membros</p></div>' +
        '<div class="cop-grupos">' +
        grupo('Conteúdo', [
          ferramenta(link('conteudo'), 'play', 'Aulas e módulos', 'Aulas, vídeos e liberação', rascunhos ? plural(rascunhos, 'rascunho', 'rascunhos') : ''),
          ferramenta(link('conteudo/trilhas'), 'route', 'Trilhas', 'Sequências de temas para o estudo'),
          ferramenta(link('conteudo/venda'), 'cart', 'Cursos à venda', 'Vitrine e checkout', semCheckout ? semCheckout + ' sem link' : ''),
          ferramenta(link('conteudo/inicio'), 'home', 'Página inicial', 'Destaque, fileiras e vitrine do Início'),
          ferramenta(link('conteudo/areas'), 'grid', 'Áreas', 'Filtros do catálogo de cursos'),
        ]) +
        grupo('Alunos e relacionamento', [
          ferramenta(link('alunos'), 'users', 'Alunos', 'Cadastro e planos dos alunos'),
          ferramenta(link('ao-vivo'), 'calendar', 'Ao vivo', 'Encontros e aulas abertas'),
          ferramenta(link('comunidade'), 'message', 'Comunidade', 'Comentários e respostas', semResp ? plural(semResp, 'pendente', 'pendentes') : ''),
          ferramenta(link('chamados'), 'help', 'Chamados', 'Pedidos da Central de ajuda', abertosCh ? plural(abertosCh, 'aberto', 'abertos') : ''),
        ]) +
        grupo('Configurações', [
          ferramenta(link('config'), 'bolt', 'Mentoria', 'Nome, duração e suporte'),
          ferramenta(link('config') + '?aba=membros', 'user', 'Área de membros', 'Nome da marca e busca'),
          ferramenta(link('config') + '?aba=plano', 'list', 'Plano do aluno', 'O que está incluído no plano'),
          ferramenta(link('config') + '?aba=ajuda', 'help', 'Central de ajuda', 'Assuntos dos chamados'),
          ferramenta(link('certificados'), 'award', 'Certificado', 'Texto e assinatura'),
          ferramenta(link('config') + '?aba=avisos', 'bell', 'Avisos', 'Sininho e e-mails ao aluno'),
        ]) + '</div>' +
        '<div class="split" style="margin-top:clamp(32px, 4vw, 52px)"><section class="panel"><div class="panel__head"><div><h2>Próximas liberações</h2><p>Módulos e aulas com data marcada</p></div><a class="btn btn--sm btn--outline" href="' + link('conteudo') + '">Ver conteúdo</a></div>' +
          (libs.length ? libs.slice(0, 6).map((x) => linha(x.href, esc(x.titulo), esc(x.apoio), '<span class="tag tag--line">' + icon('lock') + dataBR(x.d) + '</span>')).join('') : '<p class="muted">Nenhuma liberação programada.</p>') + '</section>' +
        '<section class="panel"><div class="panel__head"><h2>Precisa de atenção</h2></div>' +
          linha(link('chamados'), plural(abertosCh, 'chamado aberto', 'chamados abertos'), 'Central de ajuda', icon('right')) +
          linha(link('comunidade'), plural(semResp, 'comentário sem resposta', 'comentários sem resposta'), 'Comunidade', icon('right')) +
          linha(link('conteudo'), plural(semVideo, 'aula sem link do Vimeo', 'aulas sem link do Vimeo'), 'Conteúdo', icon('right')) + '</section></div>' +
        '<h2 class="section-title">Próximos encontros ao vivo</h2><div class="agenda">' + (enc.length ? enc.map((e) => encontroHTML(e, true)).join('') : '<p class="muted">Nenhum encontro marcado.</p>') + '</div>',
    })) };
  }

  /* =============================================================== conteúdo */
  const abasConteudo = (atual) => '<div class="tabs cop-tabs">' + [['', 'Aulas e módulos'], ['trilhas', 'Trilhas'], ['venda', 'Cursos à venda'], ['inicio', 'Página inicial'], ['areas', 'Áreas']].map((a) => '<a class="tab' + (a[0] === atual ? ' is-on' : '') + '" href="' + link('conteudo' + (a[0] ? '/' + a[0] : '')) + '">' + a[1] + '</a>').join('') + '</div>';

  function conteudo(p, query) {
    if (p[0] === 'trilhas') return trilhas();
    if (p[0] === 'venda') return venda();
    if (p[0] === 'inicio') return inicio();
    if (p[0] === 'areas') return areasTela();
    if (p[0] && p[1]) return aulaTela(p[0], p[1]);
    if (p[0]) return temaTela(p[0]);
    const area = query.get('area') || 'todas';
    const lista = A.temas.filter((t) => area === 'todas' || (t.area || 'mentoria') === area);
    const chipA = (k, nome) => '<a class="chip' + (area === k ? ' is-on' : '') + '" href="' + link('conteudo') + (k === 'todas' ? '' : '?area=' + k) + '">' + nome + '</a>';
    return {
      html: pagina({
        crumbs: noCurso('Conteúdo'), titulo: 'Conteúdo', sub: 'Tudo o que o aluno assiste na mentoria. Cada tema tem módulos, e cada módulo tem aulas.',
        acoes: '<button class="btn btn--go" data-cop="novo-tema">' + icon('plus') + 'Novo tema</button>', abas: abasConteudo(''),
        corpo: '<div class="chips cop-chips">' + chipA('todas', 'Todas as áreas') + chipA('mentoria', 'Mentoria') + Object.keys(A.areas).map((k) => chipA(k, A.areas[k].nome)).join('') + '</div>' +
          '<div class="toolbar"><span class="toolbar__count">' + plural(lista.length, 'tema', 'temas') + '</span></div>' +
          '<div class="grid">' + lista.map((t) => {
            const as = t.modulos.reduce((s, m) => s.concat(m.aulas), []), comVideo = as.filter((a) => vimeoSrc(a.vimeo)).length;
            return '<div class="gcard"><a class="card" href="' + link('conteudo/' + t.id) + '" aria-label="Gerenciar ' + esc(t.titulo) + '">' + E.cover({ h: t.h, motif: t.motif, title: t.titulo, kicker: areaNome(t.area) }) + '</a>' +
              '<div class="gcard__meta"><strong>' + esc(t.titulo) + '</strong>' + plural(t.modulos.length, 'módulo', 'módulos') + ' · ' + plural(as.length, 'aula', 'aulas') + '<br>' + comVideo + ' de ' + as.length + ' com vídeo</div></div>';
          }).join('') + '</div>',
      }),
      on: {
        'novo-tema'() {
          dialogo('Novo tema', campo('Título do tema', entrada('titulo', '', 'required maxlength="80"'), '', 'titulo') + campo('Área', selecao('area', areasOp(), area === 'todas' || area === 'mentoria' ? 'emergencia' : area), '', 'area') + campo('Descrição', areaTexto('desc', '', 3), 'Aparece na janela do tema, na área do aluno.', 'desc'), (d) => {
            const k = d.area && A.areas[d.area] ? d.area : '';
            const t = { id: uid('tema-'), jornada: false, titulo: d.titulo.trim(), area: k, desc: d.desc.trim(), h: k ? A.areas[k].h : 357, motif: 'rings', sub: '', tags: [], novo: false, capa: '', modulos: [] };
            if (!t.titulo) return false;
            A.temas.push(t); E.toast('Tema criado'); setTimeout(() => ir('conteudo/' + t.id), 0);
          }, 'Criar tema');
        },
      },
    };
  }

  /* --- tema: módulos e aulas --- */
  function linhaAula(t, m, a, ai) {
    const video = !!vimeoSrc(a.vimeo), href = link('conteudo/' + t.id + '/' + a.id);
    return '<li class="ep ep--static cop-aula"><span class="ep__n">' + (ai + 1) + '</span><span class="ep__main"><span class="ep__head"><a class="ep__title" href="' + href + '">' + esc(a.titulo) + '</a><span class="ep__dur">' + (a.min ? a.min + ' min' : 'sem duração') + '</span></span>' +
      '<span class="cop-aula__tags">' + (a.status === 'rascunho' ? '<span class="tag tag--alerta">Rascunho</span>' : '<span class="tag tag--ok">Publicada</span>') +
        '<span class="tag' + (video ? ' tag--line' : '') + '">' + icon('play') + (video ? 'Vimeo' : 'Sem link do Vimeo') + '</span>' +
        '<span class="tag' + (a.ebook ? ' tag--line' : '') + '">' + icon('book') + (a.ebook ? 'E-book' : 'Sem e-book') + '</span>' + (a.lib.tipo !== 'imediata' ? libTag(a.lib) : '') + '</span></span>' +
      '<span class="cop-aula__acoes"><button class="ibtn ibtn--up" data-cop="aula-mover" data-m="' + m.id + '" data-a="' + a.id + '" data-d="-1" aria-label="Mover para cima"' + (ai === 0 ? ' disabled' : '') + '>' + icon('down') + '</button>' +
        '<button class="ibtn" data-cop="aula-mover" data-m="' + m.id + '" data-a="' + a.id + '" data-d="1" aria-label="Mover para baixo"' + (ai === m.aulas.length - 1 ? ' disabled' : '') + '>' + icon('down') + '</button>' +
        '<a class="btn btn--sm btn--outline" href="' + href + '">' + icon('pencil') + '<span>Editar</span></a></span></li>';
  }
  function temaTela(id) {
    const t = achaTema(id);
    if (!t) return naoAchou();
    const rot = t.jornada ? 'Semana ' : 'Módulo ', venda = ehVenda(t);
    if (!abertos || !t.modulos.some((m) => abertos.has(m.id))) abertos = new Set(t.modulos.length ? [t.modulos[0].id] : []);
    const noAluno = venda ? E.ofertas.some((c) => c.id === t.id) : E.cursos.some((c) => c.id === t.id);
    /* resumo do que o aluno vê no cartão e na janela: selo, subtítulo, etiquetas e capa */
    const etq = (txt, cls) => '<span class="tag' + (cls ? ' ' + cls : '') + '">' + txt + '</span>';
    const resumo = '<p class="cop-aula__tags cop-resumo">' + (venda
      ? etq(E.fmtPreco(t.preco) + ' · até ' + t.parcelas + 'x', 'tag--line') + etq(t.garantia ? plural(t.garantia, 'dia', 'dias') + ' de garantia' : 'Sem garantia') + etq(plural((t.aprende || []).length, 'item', 'itens') + ' em “O que você vai aprender”') + (t.checkout ? etq('Checkout cadastrado', 'tag--ok') : etq('Sem link de checkout', 'tag--alerta'))
      : (t.novo ? etq('Novo', 'tag--go') : '') + (t.sub ? etq(esc(t.sub), 'tag--line') : '') + (t.tags || []).map((x) => etq(esc(x))).join('')) +
      etq(t.capa ? 'Capa: ' + esc(t.capa) : 'Capa gerada com o título', t.capa ? 'tag--line' : '') + '</p>';
    const mods = t.modulos.map((m, mi) => '<details class="week" data-mod="' + m.id + '"' + (abertos.has(m.id) ? ' open' : '') + '><summary><span class="week__n">' + (mi + 1) + '</span><div><p class="eyebrow">' + rot + (mi + 1) + '</p><h3>' + esc(m.titulo) + '</h3><p class="week__meta">' + plural(m.aulas.length, 'aula', 'aulas') + ' · ' + E.fmtMin(m.aulas.reduce((s, a) => s + (a.min || 0), 0)) + '</p><p class="cop-lib">' + libTag(m.lib) + '</p></div>' + icon('down', 'week__chev') + '</summary>' +
      '<div class="cop-mod"><div class="cop-mod__bar"><button class="btn btn--sm btn--outline" data-cop="mod-editar" data-m="' + m.id + '">' + icon('pencil') + '<span>Editar módulo</span></button><button class="btn btn--sm btn--outline" data-cop="mod-excluir" data-m="' + m.id + '">' + icon('trash') + '<span>Excluir</span></button></div>' +
      (m.aulas.length ? '<ol class="eps eps--compact">' + m.aulas.map((a, ai) => linhaAula(t, m, a, ai)).join('') + '</ol>' : '<p class="muted cop-vazio">Este módulo ainda não tem aulas.</p>') +
      '<form class="cop-novo" data-form="nova-aula" data-m="' + m.id + '"><input class="input" name="titulo" placeholder="Nome da nova aula" required maxlength="120" aria-label="Nome da nova aula"><button class="btn btn--go" type="submit">' + icon('plus') + 'Criar aula</button></form></div></details>').join('');
    const mod = (el) => t.modulos.find((m) => m.id === el.dataset.m);
    const formMod = (m) => campo('Título do módulo', entrada('titulo', m ? m.titulo : '', 'required maxlength="80"'), '', 'titulo') + campo('Data de liberação', libCampos(m && m.lib), 'Se uma aula deste módulo também tiver data, vale a maior das duas.');
    return {
      html: pagina({
        crumbs: '<a href="' + link(venda ? 'conteudo/venda' : 'conteudo') + '">' + icon('left') + (venda ? 'Cursos à venda' : 'Conteúdo') + '</a><span>·</span><span>' + esc(areaNome(t.area)) + '</span>',
        titulo: t.titulo, sub: esc(t.desc) || 'Sem descrição.',
        acoes: (noAluno ? '<button class="btn btn--outline" data-ver="' + (venda ? '#/oferta/' + t.id : t.jornada ? '#/mentoria' : '#/curso/' + t.id) + '">' + icon('play') + 'Visualizar como membro</button>' : '') + '<button class="btn btn--light" data-cop="tema-editar">' + icon('pencil') + (venda ? 'Editar curso' : 'Editar tema') + '</button>',
        corpo: resumo + '<h2 class="section-title">' + (t.jornada ? 'Semanas e aulas' : 'Módulos e aulas') + '</h2>' +
          (venda ? '<p class="hint cop-nota">Na página do curso, o aluno vê os módulos e as aulas bloqueados. Eles são liberados depois da compra.</p>' : '') + (mods ? '<div class="weeks">' + mods + '</div>' : '<p class="muted">Este tema ainda não tem módulos. Crie o primeiro abaixo.</p>') +
          '<form class="cop-novo cop-novo--mod" data-form="novo-modulo"><input class="input" name="titulo" placeholder="Título do novo módulo" required maxlength="80" aria-label="Título do novo módulo"><button class="btn btn--light" type="submit">' + icon('plus') + 'Criar módulo</button></form>' +
          (t.jornada || venda ? '' : '<div class="cop-perigo"><button class="btn btn--sm btn--outline" data-cop="tema-excluir">' + icon('trash') + '<span>Excluir tema</span></button></div>'),
      }),
      on: {
        'tema-editar'() {
          if (venda) { ofertaDialogo(t); return; }
          dialogo('Editar tema',
            campo('Título do tema', entrada('titulo', t.titulo, 'required maxlength="80"'), '', 'titulo') +
            (t.jornada ? '' : campo('Subtítulo', entrada('sub', t.sub || '', 'maxlength="60" placeholder="Ex.: Da triagem à conduta"'), 'Opcional. Aparece ao lado da área, na janela do tema.', 'sub') + campo('Área', selecao('area', areasOp(), t.area), '', 'area')) +
            campo('Descrição', areaTexto('desc', t.desc, 3), 'Aparece na janela do tema, na área do aluno.', 'desc') +
            campo('Etiquetas', entrada('tags', (t.tags || []).join(', '), 'maxlength="90" placeholder="Ex.: Casos reais, Passo a passo"'), 'Até três, separadas por vírgula. Aparecem na prévia do tema e ajudam o aluno a achá-lo na busca.', 'tags') +
            capaCampo(t.capa) +
            (t.jornada ? '' : campo('Selo “Novo”', '<label class="opt"><input type="checkbox" name="novo"' + (t.novo ? ' checked' : '') + '><span>Mostrar o selo “Novo” na capa deste tema</span></label>', 'Com o selo, o tema entra na fileira “Novidades” do Início e no filtro “Novos” da página Cursos.')),
            (d, f) => {
              if (!d.titulo.trim()) return false;
              t.titulo = d.titulo.trim(); t.desc = d.desc.trim(); t.tags = lerLista(d.tags, ',', 3); t.capa = capaLer(f, t.capa);
              if (!t.jornada) { t.sub = (d.sub || '').trim(); t.novo = !!d.novo; t.area = d.area && A.areas[d.area] ? d.area : ''; if (t.area) t.h = A.areas[t.area].h; }
              E.toast('Tema salvo');
            });
        },
        'tema-excluir'() {
          if (venda) return;
          confirmar('Excluir tema', 'O tema “' + esc(t.titulo) + '” e todas as suas aulas saem da área do aluno. Esta ação não pode ser desfeita.', 'Excluir tema', () => {
            A.temas.splice(A.temas.indexOf(t), 1); A.trilhas.forEach((tr) => { tr.temas = tr.temas.filter((x) => x !== t.id); });
            E.toast('Tema excluído'); setTimeout(() => ir('conteudo'), 0);
          });
        },
        'mod-editar'(b) {
          const m = mod(b);
          dialogo('Editar ' + rot.trim().toLowerCase(), formMod(m), (d) => { if (!d.titulo.trim()) return false; m.titulo = d.titulo.trim(); m.lib = libLer(d); E.toast('Módulo salvo'); });
        },
        'mod-excluir'(b) {
          const m = mod(b);
          confirmar('Excluir módulo', 'O módulo “' + esc(m.titulo) + '”' + (m.aulas.length ? ' e ' + (m.aulas.length === 1 ? 'a aula dele' : 'as ' + m.aulas.length + ' aulas dele') + ' saem' : ' sai') + ' da área do aluno. Esta ação não pode ser desfeita.', 'Excluir módulo', () => { t.modulos.splice(t.modulos.indexOf(m), 1); E.toast('Módulo excluído'); });
        },
        'aula-mover'(b) {
          const m = mod(b), i = m.aulas.findIndex((a) => a.id === b.dataset.a), j = i + Number(b.dataset.d);
          if (i < 0 || j < 0 || j >= m.aulas.length) return;
          m.aulas.splice(j, 0, m.aulas.splice(i, 1)[0]); salvar(); repintar();
        },
      },
      submit: {
        'nova-aula'(d, f) {
          const m = t.modulos.find((x) => x.id === f.dataset.m), titulo = d.titulo.trim();
          if (!m || !titulo) return;
          const a = { id: uid('aula-'), titulo, desc: '', vimeo: '', min: 0, lib: { tipo: 'imediata' }, status: 'rascunho', ebook: '', quiz: [] };
          m.aulas.push(a); salvar(); E.toast('Aula criada como rascunho'); ir('conteudo/' + t.id + '/' + a.id);
        },
        'novo-modulo'(d) {
          const titulo = d.titulo.trim();
          if (!titulo) return;
          const m = { id: uid('mod-'), titulo, lib: { tipo: 'imediata' }, aulas: [] };
          t.modulos.push(m); abertos = new Set([m.id]); salvar(); E.toast('Módulo criado'); repintar();
        },
      },
    };
  }

  /* --- cadastro de aula --- */
  function questaoHTML(q) {
    q = q || { p: '', o: ['', '', '', ''], c: 0, e: '' };
    const k = uid('q');
    return '<div class="cop-q"><div class="cop-q__top"><strong>Questão</strong><button type="button" class="btn btn--sm btn--outline" data-cop="quiz-del">' + icon('trash') + '<span>Remover</span></button></div>' +
      '<textarea class="input" rows="2" data-q="p" placeholder="Pergunta" aria-label="Pergunta">' + esc(q.p) + '</textarea>' +
      [0, 1, 2, 3].map((j) => '<label class="cop-q__op"><input type="radio" name="' + k + '" value="' + j + '"' + (q.c === j ? ' checked' : '') + ' aria-label="Alternativa ' + 'ABCD'[j] + ' é a correta"><input class="input input--sm" data-q="o" value="' + esc(q.o[j]) + '" placeholder="Alternativa ' + 'ABCD'[j] + '" aria-label="Alternativa ' + 'ABCD'[j] + '"></label>').join('') +
      '<input class="input input--sm cop-q__e" data-q="e" value="' + esc(q.e || '') + '" maxlength="300" placeholder="Comentário da resposta (opcional)" aria-label="Comentário da resposta"></div>';
  }
  const ebookBox = (nome) => '<input type="hidden" name="ebook" value="' + esc(nome) + '">' + (nome
    ? '<div class="file"><span class="file__ico">' + icon('book') + '</span><div><strong>' + esc(nome) + '</strong><span>PDF · o aluno baixa na aba E-book da aula</span></div><button type="button" class="btn btn--sm btn--outline" data-cop="ebook-enviar">Substituir</button><button type="button" class="btn btn--sm btn--outline" data-cop="ebook-tirar" aria-label="Remover e-book">' + icon('trash') + '</button></div>'
    : '<div class="cop-envio"><p>Nenhum e-book enviado para esta aula.</p><button type="button" class="btn btn--light" data-cop="ebook-enviar">' + icon('download', 'cop-up') + 'Enviar PDF</button></div>');
  const videoBox = (src) => (src ? '<iframe src="' + src + '" title="Prévia do vídeo" allow="fullscreen; picture-in-picture" allowfullscreen loading="lazy"></iframe>' : '<div class="cop-video__vazio">' + icon('play') + '<p>Cole o link do Vimeo para ver o vídeo aqui.</p></div>');

  function aulaTela(tid, aid) {
    const t = achaTema(tid), r = t && achaAula(t, aid);
    if (!r) return naoAchou();
    const a = r.a, m = r.m, src = vimeoSrc(a.vimeo), questoes = a.quiz || E.quiz;
    const noAluno = E.cursos.some((c) => c.id === t.id && c.aulas.some((x) => x.id === a.id && !x.bloqueada));
    return {
      html: pagina({
        crumbs: '<a href="' + link(ehVenda(t) ? 'conteudo/venda' : 'conteudo') + '">' + icon('left') + (ehVenda(t) ? 'Cursos à venda' : 'Conteúdo') + '</a><span>·</span><a href="' + link('conteudo/' + t.id) + '">' + esc(t.titulo) + '</a><span>·</span><span>' + esc(m.titulo) + '</span>',
        titulo: a.titulo, sub: a.status === 'rascunho' ? 'Rascunho: o aluno só vê a aula depois de publicada.' : 'Aula publicada.',
        acoes: noAluno ? '<button class="btn btn--outline" data-ver="#/aula/' + t.id + '/' + a.id + '">' + icon('play') + 'Visualizar como membro</button>' : '',
        corpo: '<form class="mgrid cop-aulaform" data-form="aula" novalidate><div class="cop-col">' +
          '<section class="panel"><div class="panel__head"><h2>Conteúdo da aula</h2></div><div class="form">' +
            campo('Título', entrada('titulo', a.titulo, 'required maxlength="120"'), '', 'titulo') +
            campo('Descrição', areaTexto('desc', a.desc, 5, 'maxlength="1200"'), 'Aparece para o aluno em “Sobre esta aula”.', 'desc') +
            campo('Link do vídeo no Vimeo', entrada('vimeo', a.vimeo, 'type="url" inputmode="url" placeholder="https://vimeo.com/123456789" autocomplete="off"') + '<p class="cop-msg" id="vmsg" role="status"></p>', 'O vídeo fica hospedado no Vimeo e é incorporado à página da aula: o aluno assiste sem sair da área de membros.', 'vimeo') +
            campo('Duração, em minutos', entrada('min', a.min || '', 'type="number" min="0" max="600" inputmode="numeric"'), 'Mostrada ao lado do nome da aula.', 'min') + '</div></section>' +
          '<section class="panel"><div class="panel__head"><div><h2>E-book da aula</h2><p>Um PDF por aula</p></div></div><div id="ebook">' + ebookBox(a.ebook) + '</div></section>' +
          '<section class="panel"><div class="panel__head"><div><h2>Quiz da aula</h2><p>Aparece na aba Quiz</p></div><button type="button" class="btn btn--sm btn--outline" data-cop="quiz-add">' + icon('plus') + '<span>Adicionar questão</span></button></div><div id="quiz">' + questoes.map(questaoHTML).join('') + '</div><p class="hint">Em cada questão, marque a alternativa correta. O comentário aparece para o aluno logo depois que ele responde. Aula sem questões fica sem a aba Quiz.</p></section></div>' +
          '<aside class="aside-stack"><section class="panel"><div class="panel__head"><h2>Configurações de publicação</h2></div><div class="form">' +
            campo('Situação', selecao('status', [['rascunho', 'Rascunho'], ['publicada', 'Publicada']], a.status), '', 'status') +
            campo('Data de liberação', libCampos(a.lib), 'Se o módulo também tiver data, vale a maior das duas.') +
            campo('Módulo', selecao('modulo', t.modulos.map((x, i) => [x.id, (t.jornada ? 'Semana ' : 'Módulo ') + (i + 1) + ' · ' + x.titulo]), m.id), '', 'modulo') +
            '<button class="btn btn--go btn--block" type="submit">Salvar aula</button><button type="button" class="btn btn--outline btn--block" data-cop="aula-excluir">' + icon('trash') + 'Excluir aula</button></div></section>' +
          '<section class="panel"><div class="panel__head"><h2>Prévia do vídeo</h2></div><div class="cop-video" id="vprev">' + videoBox(src) + '</div></section></aside></form>',
      }),
      input(alvo, el) {
        if (alvo.name !== 'vimeo') return;
        const v = alvo.value.trim(), s = vimeoSrc(v), msg = el.querySelector('#vmsg'), prev = el.querySelector('#vprev');
        msg.className = 'cop-msg' + (v ? (s ? ' is-ok' : ' is-erro') : '');
        msg.textContent = !v ? '' : s ? 'Link do Vimeo reconhecido.' : 'Este link não parece ser de um vídeo do Vimeo.';
        if (prev.dataset.src !== s) { prev.dataset.src = s; prev.innerHTML = videoBox(s); }
      },
      on: {
        'quiz-add'(b, e) { e.preventDefault(); document.querySelector('#quiz').insertAdjacentHTML('beforeend', questaoHTML()); const q = document.querySelectorAll('#quiz .cop-q'); q[q.length - 1].querySelector('textarea').focus(); },
        'quiz-del'(b) { b.closest('.cop-q').remove(); },
        'ebook-enviar'() {
          const titulo = document.querySelector('#f-titulo').value.trim() || a.titulo;
          document.querySelector('#ebook').innerHTML = ebookBox('ebook-' + slug(titulo) + '.pdf');
          E.toast('Envio ilustrativo: aqui o coprodutor escolhe o PDF no computador', 'info');
        },
        'ebook-tirar'() { document.querySelector('#ebook').innerHTML = ebookBox(''); },
        'aula-excluir'() {
          confirmar('Excluir aula', 'A aula “' + esc(a.titulo) + '” sai da área do aluno, junto com o e-book e o quiz. Esta ação não pode ser desfeita.', 'Excluir aula', () => {
            m.aulas.splice(m.aulas.indexOf(a), 1); E.toast('Aula excluída'); setTimeout(() => ir('conteudo/' + t.id), 0);
          });
        },
      },
      submit: {
        aula(d, f) {
          const titulo = d.titulo.trim(), campoTitulo = f.querySelector('[name="titulo"]'), campoVideo = f.querySelector('[name="vimeo"]');
          if (!titulo) { campoTitulo.focus(); E.toast('Dê um título à aula', 'info'); return; }
          if (d.vimeo.trim() && !vimeoSrc(d.vimeo)) { campoVideo.focus(); E.toast('Confira o link do Vimeo', 'info'); return; }
          if (d.status === 'publicada' && !vimeoSrc(d.vimeo)) E.toast('Aula publicada sem vídeo: cole o link do Vimeo quando tiver', 'info');
          else E.toast('Aula salva');
          const quiz = Array.from(f.querySelectorAll('.cop-q')).map((b) => ({ p: b.querySelector('[data-q="p"]').value.trim(), o: Array.from(b.querySelectorAll('[data-q="o"]')).map((i) => i.value.trim()), c: Number((b.querySelector('input[type="radio"]:checked') || { value: 0 }).value), e: b.querySelector('[data-q="e"]').value.trim() })).filter((q) => q.p);
          Object.assign(a, { titulo, desc: d.desc.trim(), vimeo: d.vimeo.trim(), min: Math.max(0, Math.round(Number(d.min) || 0)), status: d.status, lib: libLer(d), ebook: d.ebook || '', quiz });
          const destino = t.modulos.find((x) => x.id === d.modulo);
          if (destino && destino !== m) { m.aulas.splice(m.aulas.indexOf(a), 1); destino.aulas.push(a); }
          salvar(); repintar();
        },
      },
    };
  }

  /* --- trilhas --- */
  /* Janela de trilha: título, descrição, capa e os temas na ordem em que o aluno vai seguir. */
  function trilhaDialogo(tr) {
    const temasOp = A.temas.filter((t) => !t.jornada);
    const lista = tr ? tr.temas.filter((id) => temasOp.some((t) => t.id === id)) : [];
    dialogo(tr ? 'Editar trilha' : 'Nova trilha',
      campo('Título da trilha', entrada('titulo', tr ? tr.titulo : '', 'required maxlength="80"'), '', 'titulo') + campo('Descrição', areaTexto('desc', tr ? tr.desc : '', 3), 'Aparece no cartão e no topo da página da trilha.', 'desc') +
      capaCampo(tr && tr.capa) + campo('Temas da trilha', '<div id="tr-temas"></div>', 'O aluno segue os temas nesta ordem. Use as setas para mudar a posição.'),
      (d, f) => {
        const x = { titulo: d.titulo.trim(), desc: d.desc.trim(), temas: lista.slice(), capa: capaLer(f, tr && tr.capa) };
        if (!x.titulo) return false;
        if (tr) { Object.assign(tr, x); E.toast('Trilha salva'); } else { A.trilhas.push(Object.assign({ id: uid('trilha-') }, x)); E.toast('Trilha criada'); }
      }, tr ? 'Salvar' : 'Criar trilha');
    const caixa = document.querySelector('#tr-temas');
    const desenhar = () => {
      const fora = temasOp.filter((t) => lista.indexOf(t.id) < 0);
      caixa.innerHTML = (lista.length ? lista.map((id, i) => '<div class="setrow cop-ordem"><div><strong>' + (i + 1) + '. ' + esc(achaTema(id).titulo) + '</strong></div><div class="cop-item__acoes">' + setas('ordem', i, lista.length) +
          '<button type="button" class="ibtn" data-i="' + i + '" data-d="x" aria-label="Tirar da trilha">' + icon('close') + '</button></div></div>').join('') : '<p class="muted cop-vazio">Nenhum tema na trilha ainda.</p>') +
        (fora.length ? '<span class="select select--block"><select aria-label="Adicionar tema à trilha"><option value="">Adicionar tema…</option>' + fora.map((t) => '<option value="' + t.id + '">' + esc(t.titulo) + '</option>').join('') + '</select></span>' : '');
    };
    desenhar();
    caixa.onclick = (e) => {
      const b = e.target.closest('button[data-i]');
      if (!b) return;
      if (b.dataset.d === 'x') lista.splice(Number(b.dataset.i), 1); else mover(lista, b);
      desenhar();
    };
    caixa.onchange = (e) => { if (e.target.tagName === 'SELECT' && e.target.value) { lista.push(e.target.value); desenhar(); } };
  }
  function trilhas() {
    return {
      html: pagina({
        crumbs: noCurso('Conteúdo'), titulo: 'Conteúdo', sub: 'Trilhas são sequências de temas que o aluno segue em ordem.',
        acoes: '<button class="btn btn--go" data-cop="nova">' + icon('plus') + 'Nova trilha</button>', abas: abasConteudo('trilhas'),
        corpo: '<div class="agenda cop-lista">' + (A.trilhas.length ? A.trilhas.map((tr, i) => '<article class="agenda__item cop-item"><span class="cop-num">' + (i + 1) + '</span><div><h3>' + esc(tr.titulo) + '</h3><p>' + esc(tr.desc) + '</p><p class="cop-item__meta">' + plural(tr.temas.length, 'tema', 'temas') + (tr.temas.length ? ': ' + tr.temas.map((id) => { const t = achaTema(id); return t ? esc(t.titulo) : ''; }).filter(Boolean).join(', ') : '') + (tr.capa ? ' · capa: ' + esc(tr.capa) : '') + '</p></div>' +
          '<div class="cop-item__acoes"><button class="btn btn--sm btn--outline" data-cop="editar" data-id="' + tr.id + '">' + icon('pencil') + '<span>Editar</span></button><button class="btn btn--sm btn--outline" data-cop="excluir" data-id="' + tr.id + '" aria-label="Excluir trilha">' + icon('trash') + '</button></div></article>').join('') : '<p class="muted">Nenhuma trilha cadastrada.</p>') + '</div>',
      }),
      on: {
        nova() { trilhaDialogo(null); },
        editar(b) { trilhaDialogo(A.trilhas.find((x) => x.id === b.dataset.id)); },
        excluir(b) { const tr = A.trilhas.find((x) => x.id === b.dataset.id); confirmar('Excluir trilha', 'A trilha “' + esc(tr.titulo) + '” sai da área do aluno. Os temas dela continuam no catálogo.', 'Excluir trilha', () => { A.trilhas.splice(A.trilhas.indexOf(tr), 1); E.toast('Trilha excluída'); }); },
      },
    };
  }

  /* --- cursos à venda --- */
  /* Tudo o que a página do curso à venda mostra ao aluno: título, área, descrição, "O que você vai
     aprender", preço, parcelas, garantia, capa e o link do checkout. Os módulos e as aulas ficam na
     tela de conteúdo do curso (a mesma dos temas). */
  const primeiraArea = () => Object.keys(A.areas)[0] || '';
  const formOferta = (o) => campo('Título do curso', entrada('titulo', o ? o.titulo : '', 'required maxlength="80"'), '', 'titulo') + campo('Área', selecao('area', areasOp().slice(1), o ? o.area : primeiraArea()), '', 'area') +
    campo('Descrição', areaTexto('desc', o ? o.desc : '', 3), 'Aparece no topo da página do curso.', 'desc') +
    campo('O que você vai aprender', areaTexto('aprende', o ? (o.aprende || []).join('\n') : '', 4), 'Um item por linha. Aparece na página do curso, antes do conteúdo.', 'aprende') +
    '<div class="form form--3">' + campo('Preço (R$)', entrada('preco', o ? o.preco : '', 'type="number" min="0" step="0.01" required'), '', 'preco') + campo('Parcelas', entrada('parcelas', o ? o.parcelas : 12, 'type="number" min="1" max="24"'), '', 'parcelas') +
      campo('Garantia (dias)', entrada('garantia', o ? o.garantia : 7, 'type="number" min="0" max="90"'), '', 'garantia') + '</div>' +
    campo('Link do checkout', entrada('checkout', o ? o.checkout : '', 'type="url" placeholder="https://"'), 'Os botões “Comprar” e “Ir para o checkout” abrem este endereço.', 'checkout') + capaCampo(o && o.capa);
  const lerOferta = (d, f, o) => ({ titulo: d.titulo.trim(), area: A.areas[d.area] ? d.area : primeiraArea(), desc: d.desc.trim(), aprende: lerLista(d.aprende, '\n', 8), preco: Math.max(0, Number(d.preco) || 0), parcelas: Math.max(1, Math.round(Number(d.parcelas) || 1)),
    garantia: Math.max(0, Math.round(Number(d.garantia) || 0)), checkout: d.checkout.trim(), capa: capaLer(f, o && o.capa) });
  const corArea = (k) => (A.areas[k] ? A.areas[k].h : 357);
  function ofertaDialogo(o) {
    dialogo(o ? 'Editar curso à venda' : 'Novo curso à venda', formOferta(o), (d, f) => {
      const x = lerOferta(d, f, o);
      if (!x.titulo) return false;
      if (o) { Object.assign(o, x, { h: corArea(x.area) }); E.toast('Curso salvo'); }
      else { A.ofertas.push(Object.assign({ id: uid('oferta-'), visivel: true, h: corArea(x.area), motif: 'rings', modulos: [] }, x)); E.toast('Curso criado'); }
    }, o ? 'Salvar' : 'Criar curso');
  }
  function venda() {
    const aulasDe = (o) => (o.modulos || []).reduce((n, m) => n + m.aulas.length, 0);
    return {
      html: pagina({
        crumbs: noCurso('Conteúdo'), titulo: 'Conteúdo', sub: 'Cursos vendidos à parte. Aparecem bloqueados na vitrine do Início e levam à página do curso, com o botão de checkout.',
        acoes: '<button class="btn btn--go" data-cop="novo">' + icon('plus') + 'Novo curso à venda</button>', abas: abasConteudo('venda'),
        corpo: '<div class="rows cop-rows">' + A.ofertas.map((o, i) => '<div class="row cop-row">' + E.cover({ h: o.h, motif: o.motif, shape: 'thumb' }) + '<div><strong>' + esc(o.titulo) + '</strong><span>' + esc(areaNome(o.area)) + ' · ' + E.fmtPreco(o.preco) + ' · até ' + o.parcelas + 'x · ' + plural(aulasDe(o), 'aula', 'aulas') + '</span>' +
          '<span class="cop-aula__tags">' + (o.checkout ? '<span class="tag tag--ok">Checkout cadastrado</span>' : '<span class="tag tag--alerta">Sem link de checkout</span>') + (o.visivel ? '' : '<span class="tag">Fora da vitrine</span>') + '</span></div>' +
          '<div class="cop-item__acoes"><label class="cop-sw"><span>Na vitrine</span>' + chave('ofertas.' + i + '.visivel', o.visivel, 'Mostrar ' + o.titulo + ' na vitrine') + '</label>' +
          '<a class="btn btn--sm btn--outline" href="' + link('conteudo/' + o.id) + '">' + icon('play') + '<span>Aulas e módulos</span></a><button class="btn btn--sm btn--outline" data-cop="editar" data-id="' + o.id + '">' + icon('pencil') + '<span>Editar</span></button></div></div>').join('') + '</div>',
      }),
      on: {
        novo() { ofertaDialogo(null); },
        editar(b) { ofertaDialogo(A.ofertas.find((x) => x.id === b.dataset.id)); },
      },
    };
  }

  /* --- página inicial do aluno --- */
  /* como cada fileira fixa é montada (o aluno vê só o título e os cartões) */
  const FILA_INFO = {
    'continue-de-onde-parou': 'O que o aluno começou a assistir. Montada sozinha, para cada aluno.',
    'top-10-no-plantao-esta-semana': 'Os dez temas mais assistidos na semana. Montada sozinha.',
    'sua-jornada-na-mentoria': 'As semanas da mentoria, na ordem de liberação.',
    novidades: 'Os temas marcados com o selo “Novo”.',
    'trilhas-para-seguir-em-ordem': 'As trilhas cadastradas na aba Trilhas.',
    'proximos-encontros-ao-vivo': 'Os encontros cadastrados em Ao vivo.',
    'minha-lista': 'O que o aluno guardou para assistir depois.',
    'vitrine-de-cursos-a-venda': 'Os cursos da aba Cursos à venda marcados “Na vitrine”.',
  };
  function inicio() {
    const F = A.inicio.fileiras;
    /* antes de redesenhar a tela, guarda o que foi digitado nos campos de texto */
    const guardar = () => { const f = document.querySelector('form[data-form="inicio"]'); if (!f) return; const d = Object.fromEntries(new FormData(f)); A.inicio.vitrineTitulo = d.vitrineTitulo.trim(); A.inicio.vitrineTexto = d.vitrineTexto.trim(); };
    const formFila = (x) => campo('Título da fileira', entrada('nome', x ? x.nome : '', 'required maxlength="60"'), '', 'nome') +
      campo('Áreas mostradas', '<div class="cop-checks">' + Object.keys(A.areas).map((k) => '<label class="opt"><input type="checkbox" name="areas" value="' + k + '"' + (x && x.areas.indexOf(k) >= 0 ? ' checked' : '') + '><span>' + esc(A.areas[k].nome) + '</span></label>').join('') + '</div>', 'A fileira mostra os temas das áreas marcadas.');
    const lerFila = (d, f) => ({ nome: d.nome.trim(), areas: Array.from(f.querySelectorAll('[name="areas"]:checked')).map((i) => i.value) });
    const valida = (x) => { if (x.nome && x.areas.length) return true; E.toast('Dê um título e marque ao menos uma área', 'info'); return false; };
    const linha = (f, i) => '<div class="setrow"><div><strong>' + esc(f.nome) + '</strong><span>' + (f.tipo === 'areas' ? 'Temas de: ' + (f.areas.filter((k) => A.areas[k]).map((k) => esc(A.areas[k].nome)).join(', ') || 'nenhuma área marcada') : FILA_INFO[f.id] || 'Montada sozinha pela plataforma.') + '</span></div>' +
      '<div class="cop-item__acoes">' + setas('fila-mover', i, F.length) +
      (f.tipo === 'areas' ? '<button type="button" class="ibtn" data-cop="fila-editar" data-i="' + i + '" aria-label="Editar a fileira ' + esc(f.nome) + '">' + icon('pencil') + '</button><button type="button" class="ibtn" data-cop="fila-excluir" data-i="' + i + '" aria-label="Excluir a fileira ' + esc(f.nome) + '">' + icon('trash') + '</button>' : '') +
      chave('inicio.fileiras.' + i + '.visivel', f.visivel, 'Mostrar a fileira ' + f.nome) + '</div></div>';
    return {
      html: pagina({
        crumbs: noCurso('Conteúdo'), titulo: 'Conteúdo', sub: 'O que aparece na página inicial do aluno.', abas: abasConteudo('inicio'),
        corpo: '<form class="cop-estreito" data-form="inicio"><section class="panel"><div class="panel__head"><h2>Destaque da mentoria</h2></div><div class="form">' +
            '<div class="setrow"><div><strong>Frase de boas-vindas</strong><span>É a descrição do curso. Aparece embaixo do título, no topo do Início e da página da mentoria.</span></div><a class="btn btn--sm btn--outline" href="' + link('cursos/mentoria') + '">Alterar</a></div>' +
            '<div class="setrow"><div><strong>Título do destaque</strong><span>É o título do curso: ' + esc(A.mentoria.nome) + '.</span></div><a class="btn btn--sm btn--outline" href="' + link('cursos/mentoria') + '">Alterar</a></div>' +
            '<div class="setrow"><div><strong>Turma</strong><span>Mostra sempre o ano atual e muda sozinha na virada do ano.</span></div><span class="tag tag--line">Turma ' + new Date().getFullYear() + '</span></div></div></section>' +
          '<section class="panel"><div class="panel__head"><h2>Vitrine de cursos à venda</h2></div><div class="form">' + campo('Título', entrada('vitrineTitulo', A.inicio.vitrineTitulo, 'required maxlength="60"'), '', 'vitrineTitulo') + campo('Texto de apoio', entrada('vitrineTexto', A.inicio.vitrineTexto, 'maxlength="120"'), '', 'vitrineTexto') + '</div></section>' +
          '<section class="panel"><div class="panel__head"><div><h2>Fileiras do Início</h2><p>Mude a ordem com as setas e desligue as que não quer mostrar</p></div><button type="button" class="btn btn--sm btn--outline" data-cop="fila-nova">' + icon('plus') + '<span>Nova fileira</span></button></div>' + F.map(linha).join('') + '</section>' +
          '<button class="btn btn--go" type="submit">Salvar página inicial</button></form>',
      }),
      on: {
        'fila-mover'(b) { guardar(); if (mover(F, b)) { salvar(); repintar(); } },
        'fila-nova'() { guardar(); dialogo('Nova fileira', formFila(null), (d, f) => { const x = lerFila(d, f); if (!valida(x)) return false; F.push(Object.assign({ id: uid('fila-'), visivel: true, tipo: 'areas' }, x)); E.toast('Fileira criada'); }, 'Criar fileira'); },
        'fila-editar'(b) { guardar(); const x = F[Number(b.dataset.i)]; dialogo('Editar fileira', formFila(x), (d, f) => { const y = lerFila(d, f); if (!valida(y)) return false; Object.assign(x, y); E.toast('Fileira salva'); }); },
        'fila-excluir'(b) { guardar(); const x = F[Number(b.dataset.i)]; confirmar('Excluir fileira', 'A fileira “' + esc(x.nome) + '” sai da página inicial do aluno. Os temas dela continuam no catálogo.', 'Excluir fileira', () => { F.splice(F.indexOf(x), 1); E.toast('Fileira excluída'); }); },
      },
      submit: { inicio() { guardar(); salvar(); E.toast('Página inicial salva'); } },
    };
  }

  /* --- áreas do catálogo --- */
  /* As áreas são os filtros da página Cursos do aluno e a base das fileiras por área do Início. */
  function areasTela() {
    const chaves = Object.keys(A.areas);
    const nomeCampo = (v) => campo('Nome da área', entrada('nome', v, 'required maxlength="40"'), 'Aparece como filtro na página Cursos e na capa dos temas.', 'nome');
    return {
      html: pagina({
        crumbs: noCurso('Conteúdo'), titulo: 'Conteúdo', sub: 'As áreas organizam o catálogo do aluno: são os filtros da página Cursos e a base das fileiras do Início.',
        acoes: '<button class="btn btn--go" data-cop="nova">' + icon('plus') + 'Nova área</button>', abas: abasConteudo('areas'),
        corpo: '<div class="cop-estreito"><section class="panel">' + (chaves.length ? chaves.map((k) => {
          const n = A.temas.filter((t) => t.area === k).length, v = A.ofertas.filter((o) => o.area === k).length;
          return '<div class="setrow"><div><strong>' + esc(A.areas[k].nome) + '</strong><span>' + plural(n, 'tema', 'temas') + (v ? ' · ' + plural(v, 'curso à venda', 'cursos à venda') : '') + '</span></div>' +
            '<div class="cop-item__acoes"><button class="btn btn--sm btn--outline" data-cop="editar" data-k="' + k + '">' + icon('pencil') + '<span>Renomear</span></button>' +
            '<button class="btn btn--sm btn--outline" data-cop="excluir" data-k="' + k + '" aria-label="Excluir a área ' + esc(A.areas[k].nome) + '"' + (n + v ? ' disabled title="Só dá para excluir uma área que não tem temas nem cursos"' : '') + '>' + icon('trash') + '</button></div></div>';
        }).join('') : '<p class="muted">Nenhuma área cadastrada.</p>') + '</section></div>',
      }),
      on: {
        nova() {
          dialogo('Nova área', nomeCampo(''), (d) => {
            const nome = d.nome.trim();
            if (!nome) return false;
            let k = slug(nome).replace(/-/g, '');
            if (!k || A.areas[k]) k = uid('area');
            A.areas[k] = { nome, h: (Object.keys(A.areas).length * 47 + 120) % 360 };
            E.toast('Área criada');
          }, 'Criar área');
        },
        editar(b) { const a = A.areas[b.dataset.k]; dialogo('Renomear área', nomeCampo(a.nome), (d) => { if (!d.nome.trim()) return false; a.nome = d.nome.trim(); E.toast('Área salva'); }); },
        excluir(b) {
          const k = b.dataset.k;
          confirmar('Excluir área', 'A área “' + esc(A.areas[k].nome) + '” sai dos filtros da página Cursos e das fileiras do Início.', 'Excluir área', () => {
            delete A.areas[k];
            A.inicio.fileiras.forEach((f) => { if (f.areas) f.areas = f.areas.filter((x) => x !== k); });
            E.toast('Área excluída');
          });
        },
      },
    };
  }

  /* ================================================================ ao vivo */
  function encontroHTML(e, resumo) {
    const d = quando(e), passou = E.diasAte(d) < 0;
    return '<article class="agenda__item">' + E.dateBox(d) + '<div><div class="tagrow"><span class="tag ' + (e.tipo === 'Mentoria' ? 'tag--go' : 'tag--line') + '">' + esc(e.tipo) + '</span>' + (passou ? '<span class="tag">Realizado</span>' : E.contador(d)) + '</div><h3>' + esc(e.titulo) + '</h3><p>' + E.cap(E.fmtQuando(d)) + ' · ' + e.min + ' min' + (resumo ? '' : ' · ' + (e.link ? 'sala cadastrada' : 'sem link da sala') + (e.gravacao ? ' · gravação publicada' : '')) + '</p></div>' +
      (resumo ? '<a class="btn btn--sm btn--outline" href="' + link('ao-vivo') + '">Abrir</a>' : '<div class="cop-item__acoes"><button class="btn btn--sm btn--outline" data-cop="editar" data-id="' + e.id + '">' + icon('pencil') + '<span>Editar</span></button><button class="btn btn--sm btn--outline" data-cop="excluir" data-id="' + e.id + '" aria-label="Excluir encontro">' + icon('trash') + '</button></div>') + '</article>';
  }
  function aoVivo() {
    const TIPOS = [['Mentoria', 'Encontro da mentoria'], ['Aberto a todos', 'Aberto a todos'], ['Aula ao vivo', 'Aula ao vivo']];
    const form = (e) => campo('Título', entrada('titulo', e ? e.titulo : '', 'required maxlength="100"'), '', 'titulo') + campo('Tipo', selecao('tipo', TIPOS, e ? e.tipo : 'Mentoria'), '', 'tipo') +
      '<div class="form form--3">' + campo('Data', entrada('data', e ? e.data : iso(E.emDias(7)), 'type="date" required'), '', 'data') + campo('Hora', entrada('hora', e ? e.hora : '20:00', 'type="time" required'), '', 'hora') + campo('Duração (min)', entrada('min', e ? e.min : 60, 'type="number" min="10" max="300" required'), '', 'min') + '</div>' +
      campo('Descrição', areaTexto('desc', e ? e.desc : '', 3), 'Aparece no destaque da página Ao vivo.', 'desc') +
      campo('Link da sala', entrada('link', e ? e.link : '', 'type="url" placeholder="https://"'), 'O botão “Entrar na sala” abre este endereço. Para o aluno, a sala abre 10 minutos antes do início.', 'link') +
      campo('Link da gravação no Vimeo', entrada('gravacao', e ? e.gravacao : '', 'type="url" placeholder="https://vimeo.com/123456789"'), 'Depois do encontro. A gravação entra em “Novos conteúdos”.', 'gravacao') + capaCampo(e && e.capa);
    const ler = (d, f, e) => ({ titulo: d.titulo.trim(), tipo: d.tipo, data: d.data, hora: d.hora, min: Math.max(10, Math.round(Number(d.min) || 60)), desc: d.desc.trim(), link: d.link.trim(), gravacao: d.gravacao.trim(), capa: capaLer(f, e && e.capa) });
    const ordem = A.encontros.slice().sort((a, b) => quando(a) - quando(b));
    const futuros = ordem.filter((e) => E.diasAte(quando(e)) >= 0), passados = ordem.filter((e) => E.diasAte(quando(e)) < 0).reverse();
    return {
      html: pagina({
        crumbs: noCurso('Ao vivo'), titulo: 'Ao vivo', sub: 'Encontros da mentoria, plantões de dúvidas e aulas abertas. O aluno vê a agenda e pode ativar o lembrete.',
        acoes: '<button class="btn btn--go" data-cop="novo">' + icon('plus') + 'Novo encontro</button>',
        corpo: '<h2 class="section-title">Agenda</h2><div class="agenda">' + (futuros.length ? futuros.map((e) => encontroHTML(e)).join('') : '<p class="muted">Nenhum encontro marcado.</p>') + '</div>' +
          (passados.length ? '<h2 class="section-title">Realizados</h2><div class="agenda">' + passados.map((e) => encontroHTML(e)).join('') + '</div>' : ''),
      }),
      on: {
        novo() { dialogo('Novo encontro', form(null), (d, f) => { const x = ler(d, f, null); if (!x.titulo || !x.data) return false; if (x.gravacao && !vimeoSrc(x.gravacao)) { E.toast('Confira o link da gravação', 'info'); return false; } A.encontros.push(Object.assign({ id: uid('enc-') }, x)); E.toast('Encontro criado'); }, 'Criar encontro'); },
        editar(b) { const e = A.encontros.find((x) => x.id === b.dataset.id); dialogo('Editar encontro', form(e), (d, f) => { const x = ler(d, f, e); if (!x.titulo || !x.data) return false; if (x.gravacao && !vimeoSrc(x.gravacao)) { E.toast('Confira o link da gravação', 'info'); return false; } Object.assign(e, x); E.toast('Encontro salvo'); }); },
        excluir(b) { const e = A.encontros.find((x) => x.id === b.dataset.id); confirmar('Excluir encontro', 'O encontro “' + esc(e.titulo) + '” sai da agenda do aluno.', 'Excluir encontro', () => { A.encontros.splice(A.encontros.indexOf(e), 1); E.toast('Encontro excluído'); }); },
      },
    };
  }

  /* ================================================================= alunos */
  function alunos() {
    const lista = A.alunos.filter((a) => alFiltro === 'todos' || a.plano === alFiltro);
    const chipF = (k, nome) => '<button class="chip' + (alFiltro === k ? ' is-on' : '') + '" data-cop="filtro" data-k="' + k + '">' + nome + '</button>';
    const form = (a) => campo('Situação do plano', selecao('plano', [['ativo', 'Ativo'], ['cancelado', 'Cancelado']], a.plano), '', 'plano') + campo('Acesso até', entrada('ate', a.ate, 'type="date" required'), 'A mentoria dura ' + A.mentoria.duracao + ' meses a partir da entrada (' + dataBR(a.entrada) + ').', 'ate') + campo('Observação interna', areaTexto('obs', a.obs, 2), 'Só a equipe vê.', 'obs');
    return {
      html: pagina({
        titulo: 'Alunos', sub: 'Quem está na mentoria. Só o coprodutor configura ou cancela o plano; o aluno não cancela por conta própria.',
        acoes: '<button class="btn btn--go" data-cop="novo">' + icon('plus') + 'Adicionar aluno</button>',
        corpo: '<div class="chips cop-chips">' + chipF('todos', 'Todos') + chipF('ativo', 'Ativos') + chipF('cancelado', 'Cancelados') + '</div><div class="toolbar"><label class="cop-busca">' + icon('search') + '<input class="input input--sm" type="search" placeholder="Buscar por nome ou e-mail" aria-label="Buscar aluno por nome ou e-mail" data-busca></label><span class="toolbar__count" data-conta>' + plural(lista.length, 'aluno', 'alunos') + '</span></div>' +
          '<div class="cop-tabela"><table><thead><tr><th>Aluno</th><th>Entrada</th><th>Acesso até</th><th>Progresso</th><th>Plano</th><th><span class="sr-only">Ações</span></th></tr></thead><tbody>' + lista.map((a) =>
            '<tr data-q="' + esc(norm(a.nome + ' ' + a.email)) + '"><td><div class="cop-quem"><span class="avatar avatar--round avatar--gray">' + esc(iniciais(a.nome)) + '</span><div><strong>' + esc(a.nome) + '</strong><span>' + esc(a.email) + ' · último acesso ' + esc(a.ultimo) + '</span></div></div></td><td>' + dataBR(a.entrada) + '</td><td>' + dataBR(a.ate) + '</td><td><span class="cop-prog"><span class="progressbar"><i style="width:' + a.progresso + '%"></i></span>' + a.progresso + '%</span></td>' +
            '<td>' + (a.plano === 'ativo' ? '<span class="tag tag--ok">Ativo</span>' : '<span class="tag">Cancelado</span>') + '</td>' +
            '<td><div class="cop-item__acoes"><button class="btn btn--sm btn--outline" data-cop="plano" data-id="' + a.id + '" aria-label="Configurar plano" title="Configurar plano">' + icon('sliders') + '<span>Configurar plano</span></button>' + (a.plano === 'ativo' ? '<button class="btn btn--sm btn--outline" data-cop="cancelar" data-id="' + a.id + '">Cancelar plano</button>' : '<button class="btn btn--sm btn--outline" data-cop="reativar" data-id="' + a.id + '">Reativar</button>') + '</div></td></tr>').join('') + '<tr data-vazia hidden><td colspan="6" class="cop-vazia">Nenhum aluno encontrado com essa busca.</td></tr></tbody></table></div>',
      }),
      /* busca: filtra as linhas da tabela enquanto o coprodutor digita */
      input(alvo, el) {
        if (!alvo.matches('[data-busca]')) return;
        const q = norm(alvo.value.trim());
        let n = 0;
        el.querySelectorAll('tbody tr[data-q]').forEach((tr) => { const ok = tr.dataset.q.indexOf(q) >= 0; tr.hidden = !ok; if (ok) n++; });
        el.querySelector('[data-conta]').textContent = plural(n, 'aluno', 'alunos');
        el.querySelector('[data-vazia]').hidden = n > 0;
      },
      on: {
        filtro(b) { alFiltro = b.dataset.k; repintar(); },
        novo() {
          dialogo('Adicionar aluno', campo('Nome completo', entrada('nome', '', 'required maxlength="80"'), '', 'nome') + campo('E-mail', entrada('email', '', 'type="email" required'), 'O aluno recebe o acesso neste e-mail.', 'email') + campo('Data de entrada', entrada('entrada', iso(new Date()), 'type="date" required'), 'O acesso vale por ' + A.mentoria.duracao + ' meses a partir desta data.', 'entrada'), (d) => {
            if (!d.nome.trim() || !d.email.trim() || !d.entrada) return false;
            const fim = deIso(d.entrada); fim.setMonth(fim.getMonth() + A.mentoria.duracao);
            A.alunos.unshift({ id: uid('aluno-'), nome: d.nome.trim(), email: d.email.trim(), entrada: d.entrada, ate: iso(fim), plano: 'ativo', progresso: 0, ultimo: 'ainda não acessou', obs: '' });
            alFiltro = 'todos'; E.toast('Aluno adicionado');
          }, 'Adicionar aluno');
        },
        plano(b) { const a = A.alunos.find((x) => x.id === b.dataset.id); dialogo('Plano de ' + a.nome, form(a), (d) => { a.plano = d.plano; a.ate = d.ate || a.ate; a.obs = d.obs.trim(); E.toast('Plano salvo'); }); },
        cancelar(b) { const a = A.alunos.find((x) => x.id === b.dataset.id); confirmar('Cancelar plano', esc(a.nome) + ' perde o acesso à mentoria assim que você confirmar. O progresso fica guardado, caso o plano seja reativado.', 'Cancelar plano', () => { a.plano = 'cancelado'; E.toast('Plano cancelado'); }); },
        reativar(b) { const a = A.alunos.find((x) => x.id === b.dataset.id); a.plano = 'ativo'; salvar(); E.toast('Plano reativado'); repintar(); },
      },
    };
  }

  /* ============================================================= comunidade */
  function comunidadeTela() {
    /* quem responde pela mentoria e a etiqueta ao lado do nome vêm de Configurações > Mentoria */
    const semTitulo = A.mentoria.mentor.replace(/^(dra?|profa?)\.?\s+/i, '');
    const posts = publicacoes(), mentora = { nome: A.mentoria.mentor, iniciais: iniciais(semTitulo) }, etiqueta = esc(A.mentoria.mentorTag);
    const quem = (x) => '<span class="avatar avatar--round' + (x.mentor ? '' : ' avatar--gray') + '">' + esc(x.iniciais) + '</span>';
    const cabeca = (x, extra) => '<div class="post__head"><strong>' + esc(x.autor) + '</strong>' + (x.mentor ? '<span class="tag tag--go">' + etiqueta + '</span>' : '') + '<time>' + esc(x.quando) + '</time>' + (extra || '') + '</div>';
    return {
      html: pagina({
        titulo: 'Comunidade', sub: 'Os comentários dos alunos e as respostas dos mentores ficam centralizados aqui. Ao responder, o aluno recebe o aviso “Seu comentário foi respondido”.',
        corpo: '<div class="toolbar"><span class="toolbar__count">' + plural(posts.length, 'publicação', 'publicações') + ' · ' + posts.filter(semResposta).length + ' sem resposta da mentoria</span></div><div class="feed">' + posts.map((p) => {
          const oculta = !!A.ocultas[p.id];
          return '<article class="post' + (oculta ? ' is-oculta' : '') + '">' + quem(p) + '<div>' + cabeca(p, (semResposta(p) ? '<span class="tag tag--alerta">Sem resposta</span>' : '') + (oculta ? '<span class="tag">Oculta para os alunos</span>' : '')) + '<p>' + esc(p.texto) + '</p>' +
            '<div class="thread">' + (p.respostas.length ? '<ol class="thread__list">' + p.respostas.map((r) => '<li class="reply">' + quem(r) + '<div>' + cabeca(r) + '<p>' + esc(r.texto) + '</p></div></li>').join('') + '</ol>' : '<p class="thread__empty">Ainda sem respostas.</p>') +
            '<form class="thread__form" data-form="responder" data-post="' + esc(p.id) + '">' + quem({ iniciais: mentora.iniciais, mentor: true }) + '<input class="input" name="texto" placeholder="Responder como ' + esc(A.mentoria.mentor) + '…" maxlength="400" required autocomplete="off" aria-label="Resposta da mentoria"><button class="btn btn--go btn--sm" type="submit">Responder</button></form>' +
            '<div class="cop-mod__bar"><button class="btn btn--sm btn--outline" data-cop="ocultar" data-id="' + esc(p.id) + '">' + (oculta ? 'Mostrar de novo' : 'Ocultar publicação') + '</button></div></div></div></article>';
        }).join('') + '</div>',
      }),
      on: { ocultar(b) { A.ocultas[b.dataset.id] = !A.ocultas[b.dataset.id]; salvar(); E.toast(A.ocultas[b.dataset.id] ? 'Publicação ocultada' : 'Publicação visível de novo'); repintar(); } },
      submit: {
        responder(d, f) {
          const texto = d.texto.trim(), S = E.estado();
          if (!texto) return;
          const fios = S.replies || (S.replies = {});
          (fios[f.dataset.post] || (fios[f.dataset.post] = [])).push({ autor: mentora.nome, iniciais: mentora.iniciais, mentor: true, quando: 'agora', texto });
          E.salvar(); E.toast('Resposta publicada na comunidade'); repintar();
        },
      },
    };
  }

  /* =============================================================== chamados */
  function chamadosTela() {
    const todos = chamados(), lista = todos.filter((c) => c.status === chAba);
    const aba = (k, nome) => '<button class="tab' + (chAba === k ? ' is-on' : '') + '" data-cop="aba" data-k="' + k + '">' + nome + ' (' + todos.filter((c) => c.status === k).length + ')</button>';
    return {
      html: pagina({
        titulo: 'Chamados', sub: 'Pedidos abertos pelos alunos na Central de ajuda. A equipe de suporte é avisada em ' + esc(A.mentoria.suporte) + ' a cada chamado novo.',
        abas: '<div class="tabs cop-tabs" role="tablist">' + aba('aberto', 'Abertos') + aba('resolvido', 'Resolvidos') + '</div>',
        corpo: '<div class="tickets cop-estreito">' + (lista.length ? lista.map((c, i) => '<details class="ticket"' + (i === 0 && chAba === 'aberto' ? ' open' : '') + '><summary><span class="ticket__n">#' + c.n + '</span><span class="ticket__main"><strong>' + esc(c.assunto) + ' · ' + esc(c.aluno) + '</strong><span>' + esc(c.texto) + '</span></span>' +
          (c.status === 'aberto' ? '<span class="tag tag--alerta">Aberto</span>' : '<span class="tag tag--ok">' + icon('check') + 'Resolvido</span>') + icon('down', 'week__chev') + '</summary><div class="ticket__body"><p>' + esc(c.texto) + '</p><p class="ticket__meta">' + esc(c.aluno) + ' · recebido ' + esc(c.quando) + '</p>' +
          (c.resposta ? '<div class="post__reply"><strong>Equipe de suporte</strong>' + esc(c.resposta) + '</div>' : '<form class="cop-resposta" data-form="responder" data-n="' + c.n + '"><textarea class="input" name="texto" rows="3" required minlength="5" placeholder="Escreva a resposta para o aluno…" aria-label="Resposta para o aluno"></textarea><div class="cop-resposta__foot"><span class="hint">O aluno vê a resposta no próprio chamado e recebe o aviso “Seu chamado foi respondido”.</span><button class="btn btn--go" type="submit">Responder e resolver</button></div></form>') + '</div></details>').join('') : '<p class="muted">' + (chAba === 'aberto' ? 'Nenhum chamado aberto.' : 'Nenhum chamado resolvido.') + '</p>') + '</div>',
      }),
      on: { aba(b) { chAba = b.dataset.k; repintar(); } },
      submit: {
        responder(d, f) {
          const c = todos.find((x) => String(x.n) === f.dataset.n), texto = d.texto.trim();
          if (!c || !c.ref || !texto) return;
          c.ref.resposta = texto; c.ref.status = 'resolvido';
          if (c.origem === 'aluno') E.salvar(); else salvar();
          E.toast('Resposta enviada ao aluno'); repintar();
        },
      },
    };
  }

  /* ========================================================== configurações */
  function config(p, query) {
    /* "Certificados" tem tela própria, aberta pelo painel lateral */
    const abas = [['mentoria', 'Mentoria'], ['membros', 'Área de membros'], ['plano', 'Plano do aluno'], ['ajuda', 'Central de ajuda'], ['avisos', 'Avisos']];
    /* a aba aberta vem do endereço (?aba=...), para os atalhos da Visão geral abrirem direto nela */
    const pedida = query ? query.get('aba') : '';
    cfgAba = abas.some((a) => a[0] === pedida) ? pedida : 'mentoria';
    const ano = new Date().getFullYear();
    const P = A.plano.itens, S = A.ajuda.assuntos;
    /* antes de redesenhar a aba do plano, guarda a descrição que estiver sendo digitada */
    const guardarPlano = () => { const c = document.querySelector('form[data-form="plano"] [name="desc"]'); if (c) A.plano.desc = c.value.trim(); };
    const formItem = (x) => campo('Título', entrada('t', x ? x.t : '', 'required maxlength="50"'), '', 't') + campo('Texto de apoio', entrada('d', x ? x.d : '', 'maxlength="90"'), 'Você pode usar {mentoria}, {ano} e {duracao}: o aluno vê o nome da mentoria, o ano da turma e a duração.', 'd');
    const comDados = (txt) => esc(txt).replace('{mentoria}', esc(A.mentoria.nome)).replace('{ano}', ano).replace('{duracao}', A.mentoria.duracao + ' meses');
    let corpo;
    if (cfgAba === 'avisos') {
      const linha = (k, titulo, quandoTxt, exemplo) => '<div class="setrow"><div><strong>' + titulo + '</strong><span>' + quandoTxt + '</span><span class="cop-exemplo">Exemplo: “' + exemplo + '”</span></div>' + chave('avisos.' + k, A.avisos[k], titulo) + '</div>';
      const email = (k, titulo, texto) => '<div class="setrow"><div><strong>' + titulo + '</strong><span>' + texto + '</span></div>' + chave('emails.' + k, A.emails[k], 'E-mail: ' + titulo) + '</div>';
      corpo = '<div class="panel"><div class="panel__head"><div><h2>Avisos ao aluno</h2><p>O sininho só avisa nestas quatro situações</p></div></div>' +
        linha('aula', 'Nova aula liberada', 'Quando uma aula é publicada ou chega a data de liberação.', 'Nova aula liberada') +
        linha('encontro', 'Encontro da mentoria', 'No dia de um encontro ao vivo.', 'Encontro da mentoria hoje, às 20h') +
        linha('comentario', 'Comentário respondido', 'Quando um mentor responde a uma publicação do aluno na comunidade.', 'Seu comentário foi respondido') +
        linha('chamado', 'Chamado respondido', 'Quando o suporte responde a um chamado aberto pelo aluno.', 'Seu chamado foi respondido') + '</div>' +
        '<div class="panel cop-mt"><div class="panel__head"><div><h2>E-mails ao aluno</h2><p>O aluno pode desligar cada um em Conta e preferências</p></div></div>' +
        email('aulas', 'Novas aulas liberadas', 'E-mail quando uma semana da mentoria ou um tema novo abrir.') +
        email('encontros', 'Encontros ao vivo', 'Aviso uma hora antes dos encontros em que o aluno ativou o lembrete.') + '</div>';
    } else if (cfgAba === 'membros') {
      corpo = '<form class="cop-estreito" data-form="membros"><section class="panel"><div class="panel__head"><h2>Marca</h2></div><div class="form">' +
        campo('Nome da marca', entrada('marca', A.marca.nome, 'required maxlength="40"'), 'Aparece na barra do topo e no rodapé da área de membros e no cabeçalho do certificado.', 'marca') + '</div></section>' +
        '<section class="panel"><div class="panel__head"><h2>Busca</h2></div><div class="form">' +
        campo('Sugestões de busca', entrada('busca', A.busca.join(', '), 'maxlength="120"'), 'Até seis termos, separados por vírgula. Aparecem como atalhos na página de busca do aluno.', 'busca') +
        '<div class="setrow"><div><strong>Mais procurados</strong><span>Lista montada sozinha, com os temas mais assistidos.</span></div><span class="tag tag--line">Automático</span></div></div></section>' +
        '<div><button class="btn btn--go" type="submit">Salvar</button></div></form>';
    } else if (cfgAba === 'plano') {
      corpo = '<form class="panel" data-form="plano"><div class="panel__head"><div><h2>Plano do aluno</h2><p>O que o aluno vê em Conta e preferências, na aba Assinatura</p></div></div><div class="form">' +
        '<div class="setrow"><div><strong>Nome do plano</strong><span>É o título do curso: Mentoria ' + esc(A.mentoria.nome) + '.</span></div><a class="btn btn--sm btn--outline" href="' + link('cursos/mentoria') + '">Alterar</a></div>' +
        campo('Descrição do plano', areaTexto('desc', A.plano.desc, 2, 'maxlength="160" required'), 'Aparece abaixo do nome, no cartão “Plano ativo”.', 'desc') +
        '<div><button class="btn btn--go" type="submit">Salvar descrição</button></div></div></form>' +
        '<section class="panel cop-mt"><div class="panel__head"><div><h2>Incluído no plano</h2><p>Lista mostrada ao aluno, nesta ordem</p></div><button class="btn btn--sm btn--outline" data-cop="item-novo">' + icon('plus') + '<span>Adicionar item</span></button></div>' +
        (P.length ? P.map((x, i) => '<div class="setrow"><div><strong>' + esc(x.t) + '</strong><span>' + comDados(x.d) + '</span></div><div class="cop-item__acoes">' + setas('item-mover', i, P.length) +
          '<button class="ibtn" data-cop="item-editar" data-i="' + i + '" aria-label="Editar o item ' + esc(x.t) + '">' + icon('pencil') + '</button><button class="ibtn" data-cop="item-excluir" data-i="' + i + '" aria-label="Excluir o item ' + esc(x.t) + '">' + icon('trash') + '</button></div></div>').join('') : '<p class="muted">Nenhum item cadastrado.</p>') + '</section>' +
        '<div class="panel cop-mt"><div class="setrow"><div><strong>Situação e validade de cada plano</strong><span>Só o coprodutor configura e cancela, na página Alunos.</span></div><a class="btn btn--sm btn--outline" href="' + link('alunos') + '">Abrir alunos</a></div></div>';
    } else if (cfgAba === 'ajuda') {
      corpo = '<section class="panel"><div class="panel__head"><div><h2>Assuntos do chamado</h2><p>Opções do campo “Assunto”, na Central de ajuda do aluno</p></div></div>' +
        (S.length ? S.map((x, i) => '<div class="setrow"><div><strong>' + esc(x) + '</strong></div><div class="cop-item__acoes">' + setas('assunto-mover', i, S.length) +
          '<button class="ibtn" data-cop="assunto-excluir" data-i="' + i + '" aria-label="Excluir o assunto ' + esc(x) + '">' + icon('trash') + '</button></div></div>').join('') : '<p class="muted">Nenhum assunto cadastrado.</p>') +
        '<form class="cop-novo cop-novo--mod" data-form="assunto"><input class="input" name="assunto" placeholder="Novo assunto" required maxlength="40" aria-label="Novo assunto"><button class="btn btn--light" type="submit">' + icon('plus') + 'Adicionar assunto</button></form></section>' +
        '<div class="panel cop-mt"><div class="setrow"><div><strong>E-mail da equipe de suporte</strong><span>' + esc(A.mentoria.suporte) + ' recebe um aviso a cada chamado novo.</span></div><a class="btn btn--sm btn--outline" href="' + link('config') + '">Alterar</a></div>' +
        '<div class="setrow"><div><strong>Respostas aos chamados</strong><span>A equipe responde na página Chamados, e o aluno vê a resposta em “Meus chamados”.</span></div><a class="btn btn--sm btn--outline" href="' + link('chamados') + '">Abrir chamados</a></div></div>';
    } else {
      corpo = '<form class="panel" data-form="mentoria"><div class="panel__head"><h2>Mentoria</h2></div><div class="form">' +
        '<div class="setrow"><div><strong>Nome da mentoria</strong><span>É o título do curso: ' + esc(A.mentoria.nome) + '. Aparece no destaque do Início e na página da mentoria.</span></div><a class="btn btn--sm btn--outline" href="' + link('cursos/mentoria') + '">Alterar</a></div>' +
        campo('Duração', selecao('duracao', [[6, '6 meses'], [12, '12 meses'], [18, '18 meses'], [24, '24 meses']], A.mentoria.duracao), 'Define até quando o aluno tem acesso e quando o certificado é liberado.', 'duracao') +
        campo('Frase dos encontros ao vivo', entrada('encontros', A.mentoria.encontros, 'maxlength="60"'), 'Aparece no topo da página da mentoria, ao lado do número de aulas.', 'encontros') +
        '<div class="form form--2">' + campo('Quem responde na comunidade', entrada('mentor', A.mentoria.mentor, 'required maxlength="60"'), 'Nome mostrado nas respostas da mentoria.', 'mentor') +
          campo('Etiqueta ao lado do nome', entrada('mentorTag', A.mentoria.mentorTag, 'required maxlength="20"'), 'Ex.: Mentora, Mentor, Equipe.', 'mentorTag') + '</div>' +
        campo('E-mail da equipe de suporte', entrada('suporte', A.mentoria.suporte, 'type="email" required'), 'Recebe um aviso a cada chamado aberto na Central de ajuda.', 'suporte') +
        '<div class="setrow"><div><strong>Turma</strong><span>Mostra sempre o ano atual e muda sozinha na virada do ano.</span></div><span class="tag tag--line">Turma ' + ano + '</span></div>' +
        '<div class="setrow"><div><strong>Semanas, aulas e participantes</strong><span>Os números do topo da página da mentoria são contados sozinhos, a partir do conteúdo e dos alunos.</span></div><span class="tag tag--line">Automático</span></div>' +
        '<div><button class="btn btn--go" type="submit">Salvar mentoria</button></div></div></form>' +
        '<div class="panel cop-mt"><div class="setrow"><div><strong>Dados de exemplo</strong><span>Desfaz tudo o que foi alterado nesta área do protótipo.</span></div><button class="btn btn--sm btn--outline" data-cop="restaurar">Restaurar exemplo</button></div></div>';
    }
    return {
      html: pagina({ titulo: 'Configurações',
        abas: '<div class="tabs cop-tabs">' + abas.map((a) => '<a class="tab' + (a[0] === cfgAba ? ' is-on' : '') + '" href="' + link('config') + (a[0] === 'mentoria' ? '' : '?aba=' + a[0]) + '">' + a[1] + '</a>').join('') + '</div>',
        corpo: '<div class="cop-coluna">' + corpo + '</div>' }),
      on: {
        restaurar() { confirmar('Restaurar exemplo', 'Tudo o que foi criado ou alterado na área do coprodutor volta ao estado inicial.', 'Restaurar', () => { A = semente(); abertos = null; E.toast('Exemplo restaurado'); }); },
        'item-novo'() { guardarPlano(); dialogo('Novo item do plano', formItem(null), (d) => { if (!d.t.trim()) return false; P.push({ t: d.t.trim(), d: d.d.trim() }); E.toast('Item adicionado'); }, 'Adicionar item'); },
        'item-editar'(b) { guardarPlano(); const x = P[Number(b.dataset.i)]; dialogo('Editar item do plano', formItem(x), (d) => { if (!d.t.trim()) return false; x.t = d.t.trim(); x.d = d.d.trim(); E.toast('Item salvo'); }); },
        'item-excluir'(b) { guardarPlano(); const x = P[Number(b.dataset.i)]; confirmar('Excluir item', 'O item “' + esc(x.t) + '” sai da lista “Incluído no seu plano”, na conta do aluno.', 'Excluir item', () => { P.splice(P.indexOf(x), 1); E.toast('Item excluído'); }); },
        'item-mover'(b) { guardarPlano(); if (mover(P, b)) { salvar(); repintar(); } },
        'assunto-mover'(b) { if (mover(S, b)) { salvar(); repintar(); } },
        'assunto-excluir'(b) { const x = S[Number(b.dataset.i)]; confirmar('Excluir assunto', 'O assunto “' + esc(x) + '” sai do formulário da Central de ajuda. Os chamados já abertos com ele continuam na lista.', 'Excluir assunto', () => { S.splice(S.indexOf(x), 1); E.toast('Assunto excluído'); }); },
      },
      submit: {
        mentoria(d) {
          Object.assign(A.mentoria, { duracao: Number(d.duracao) || 12, suporte: d.suporte.trim(), encontros: d.encontros.trim(), mentor: d.mentor.trim() || A.mentoria.mentor, mentorTag: d.mentorTag.trim() || A.mentoria.mentorTag });
          salvar(); E.toast('Mentoria salva'); repintar();
        },
        membros(d) { A.marca.nome = d.marca.trim() || A.marca.nome; A.busca = lerLista(d.busca, ',', 6); salvar(); E.toast('Área de membros salva'); repintar(); },
        plano() { guardarPlano(); salvar(); E.toast('Descrição do plano salva'); },
        assunto(d) { const x = d.assunto.trim(); if (!x) return; if (S.some((y) => norm(y) === norm(x))) { E.toast('Esse assunto já está na lista', 'info'); return; } S.push(x); salvar(); E.toast('Assunto adicionado'); repintar(); },
      },
    };
  }

  /* ============================================================ certificados */
  function certificados() {
    const ano = new Date().getFullYear();
    const texto = A.cert.texto.replace('{mentoria}', A.mentoria.nome).replace('{ano}', ano);
    return {
      html: pagina({
        titulo: 'Certificados', sub: 'O certificado de conclusão que o aluno recebe ao final da mentoria ' + esc(A.mentoria.nome) + '.',
        corpo: '<div class="cop-coluna">' +
          '<form class="panel" data-form="cert"><div class="panel__head"><h2>Certificado</h2></div><div class="form">' +
        '<div class="setrow"><div><strong>Quando é liberado</strong><span>Só ao final da mentoria, ' + A.mentoria.duracao + ' meses depois da entrada do aluno. Temas e aulas não emitem certificado.</span></div><span class="tag tag--line">' + icon('lock') + 'Ao final</span></div>' +
        campo('Texto do certificado', entrada('texto', A.cert.texto, 'required maxlength="160"'), 'Use {mentoria} para o nome da mentoria e {ano} para o ano da turma.', 'texto') +
        '<div class="form form--2">' + campo('Assinatura', entrada('assinatura', A.cert.assinatura, 'required maxlength="60"'), '', 'assinatura') + campo('Linha abaixo da assinatura', entrada('cargo', A.cert.cargo, 'maxlength="60"'), '', 'cargo') + '</div>' +
        '<div><button class="btn btn--go" type="submit">Salvar certificado</button></div></div></form>' +
        '<h2 class="section-title">Como o aluno vai ver</h2><div class="cop-cert"><div class="cert"><p class="cert__brand">' + esc(A.marca.nome) + '</p><p class="cert__kind">Certificado de conclusão</p><p class="cert__name">Nome do aluno</p><p class="cert__text">' + esc(texto) + '</p><div class="cert__foot"><div class="cert__sign"><b>' + esc(A.cert.assinatura) + '</b>' + esc(A.cert.cargo) + '</div></div></div></div>' + '</div>',
      }),
      submit: {
        cert(d) { A.cert.texto = d.texto.trim(); A.cert.assinatura = d.assinatura.trim(); A.cert.cargo = d.cargo.trim(); salvar(); E.toast('Certificado salvo'); repintar(); },
      },
    };
  }

  /* ============================================== telas das próximas etapas */
  /* "Relatórios" e "Controle de acesso" já estão no painel lateral, mas o conteúdo delas ainda não
     foi definido: por ora mostram só o título e um aviso. */
  const emBreve = (titulo, ic) => () => ({ html: pagina({ titulo, corpo: '<div class="empty">' + ic + '<h2>Tela em construção</h2><p>O conteúdo de “' + titulo + '” será definido em uma próxima etapa do painel.</p></div>' }) });

  /* ============================================================ meus cursos */
  /* Primeira tela do painel. Lista os cursos a que o produtor ou coprodutor tem acesso: o curso do
     cliente, que já está cadastrado (a mentoria), e os que forem criados aqui. Cada cartão mostra a
     capa, o nome, a situação de publicação e a quantidade de aulas e de alunos. Ao clicar num curso,
     abre a página dele, na aba "Básico". A organização segue a da Eduzz, em versão simples. */
  const publicado = (c) => c.status === 'publicado';
  const situacao = (c) => (publicado(c) ? '<span class="tag tag--ok">Publicado</span>' : '<span class="tag tag--alerta">Despublicado</span>');
  /* quem pode ser o autor do curso: a marca e as pessoas da equipe */
  const tutores = () => { const l = [A.marca.nome].concat(Object.keys(E.instrutores).map((k) => E.instrutores[k].nome)); [A.mentoria.mentor, A.mentoria.tutor].forEach((n) => { if (n && l.indexOf(n) < 0) l.push(n); }); return l; };
  /* O curso do cliente (id "mentoria") e os cursos criados aqui, vistos do mesmo jeito. */
  function cursoDe(id) {
    if (id === 'mentoria') {
      const j = A.temas.find((t) => t.jornada) || A.temas[0] || {}, m = A.mentoria;
      return { id: 'mentoria', cliente: true, nome: m.nome, desc: A.inicio.frase, tutor: m.tutor, status: m.status, capa: m.capa, capaImg: m.capaImg, h: j.h, motif: j.motif,
        aulas: todasAulas().length, alunos: A.alunos.filter((a) => a.plano === 'ativo').length };
    }
    const c = A.cursosNovos.find((x) => x.id === id);
    return c ? Object.assign({ aulas: 0, alunos: 0, h: 168, motif: 'rings', tutor: '', capa: '', capaImg: '' }, c) : null;
  }
  function gravarCurso(id, d) {
    if (id === 'mentoria') {
      if (d.nome != null) A.mentoria.nome = d.nome;
      if (d.desc != null) A.inicio.frase = d.desc;
      ['tutor', 'status', 'capa', 'capaImg'].forEach((k) => { if (d[k] != null) A.mentoria[k] = d[k]; });
    } else Object.assign(A.cursosNovos.find((x) => x.id === id), d);
    salvar();
  }
  const listaCursos = () => ['mentoria'].concat(A.cursosNovos.map((c) => c.id)).map(cursoDe);
  /* capa do curso: a imagem enviada ou, sem ela, a capa gerada com o título */
  const capaCurso = (c) => (c.capaImg ? '<span class="cover cop-capa-img"><img src="' + c.capaImg + '" alt=""></span>' : E.cover({ h: c.h, motif: c.motif, title: c.nome, kicker: c.cliente ? 'Mentoria' : 'Curso' }));

  function cursosLista() {
    const cursos = listaCursos();
    const cartao = (c) => '<div class="gcard" data-q="' + esc(norm(c.nome)) + '"><a class="card" href="' + link('cursos/' + c.id) + '" aria-label="Abrir o curso ' + esc(c.nome) + '">' + capaCurso(c) + '</a>' +
      '<div class="gcard__meta"><span class="tagrow cop-curso__tags">' + situacao(c) + '</span><strong>' + esc(c.nome) + '</strong>' + plural(c.aulas, 'aula', 'aulas') + ' · ' + plural(c.alunos, 'aluno', 'alunos') + '</div></div>';
    return {
      html: pagina({
        titulo: 'Meus cursos', sub: 'Gerencie e personalize seus cursos e conteúdos.',
        acoes: '<a class="btn btn--go" href="' + link('cursos/novo') + '">' + icon('plus') + 'Criar curso</a>',
        corpo: '<div class="toolbar"><label class="cop-busca">' + icon('search') + '<input class="input input--sm" type="search" placeholder="Buscar curso pelo nome" aria-label="Buscar curso pelo nome" data-busca></label><span class="toolbar__count" data-conta>' + plural(cursos.length, 'curso', 'cursos') + '</span></div>' +
          '<div class="grid cop-cursos">' + cursos.map(cartao).join('') + '</div>' +
          '<p class="muted cop-vazia" data-vazia hidden>Nenhum curso encontrado com esse nome.</p>',
      }),
      /* busca: mostra só os cursos cujo nome contém o que foi digitado */
      input(alvo, el) {
        if (!alvo.matches('[data-busca]')) return;
        const q = norm(alvo.value.trim());
        let n = 0;
        el.querySelectorAll('.cop-cursos .gcard').forEach((g) => { const ok = g.dataset.q.indexOf(q) >= 0; g.hidden = !ok; if (ok) n++; });
        el.querySelector('[data-conta]').textContent = plural(n, 'curso', 'cursos');
        el.querySelector('[data-vazia]').hidden = n > 0;
      },
    };
  }

  /* ============================================================ página do curso */
  /* Cabeçalho da página de um curso: o nome, o autor, a situação de publicação, as ações
     (visualizar, publicar ou despublicar, excluir) e as abas. "Básico" é a primeira aba. */
  function cabecaCurso(c, aba) {
    const abas = [['basico', 'Básico', 'cursos/' + c.id]].concat(c.cliente ? [['visao', 'Visão geral', 'visao'], ['conteudo', 'Conteúdo', 'conteudo'], ['ao-vivo', 'Ao vivo', 'ao-vivo']] : []);
    return {
      crumbs: '<a href="' + link('') + '">' + icon('left') + 'Meus cursos</a>',
      titulo: c.nome, sub: c.tutor ? 'Por ' + esc(c.tutor) : '',
      acoes: situacao(c) + '<button class="btn btn--sm btn--outline" data-cop="curso-ver">' + icon('play') + '<span>Visualizar curso</span></button>' +
        /* o botão de publicação muda conforme a situação do curso */
        (publicado(c) ? '<button class="btn btn--sm btn--outline" data-cop="curso-despublicar">Despublicar curso</button>' : '<button class="btn btn--sm btn--go" data-cop="curso-publicar">Publicar curso</button>') +
        '<button class="btn btn--sm btn--outline" data-cop="curso-excluir">' + icon('trash') + '<span>Excluir curso</span></button>',
      abas: '<div class="tabs cop-tabs">' + abas.map((a) => '<a class="tab' + (a[0] === aba ? ' is-on' : '') + '" href="' + link(a[2]) + '">' + a[1] + '</a>').join('') + '</div>',
    };
  }
  function acoesCurso(c) {
    return {
      'curso-ver'() {
        if (c.cliente) visualizar('#/mentoria');
        else E.toast('Neste protótipo, só o curso ' + A.mentoria.nome + ' abre na área de membros', 'info');
      },
      'curso-publicar'() { gravarCurso(c.id, { status: 'publicado' }); E.toast('Curso publicado'); repintar(); },
      'curso-despublicar'() {
        confirmar('Despublicar curso', 'O curso “' + esc(c.nome) + '” deixa de aparecer para os alunos até ser publicado de novo. O conteúdo e o progresso dos alunos ficam guardados.', 'Despublicar curso', () => { gravarCurso(c.id, { status: 'despublicado' }); E.toast('Curso despublicado'); });
      },
      'curso-excluir'() {
        confirmar('Excluir curso', 'O curso “' + esc(c.nome) + '” sai da sua lista de cursos' + (c.cliente ? ' e da área de membros, com todas as aulas' : '') + '. Esta ação não pode ser desfeita.', 'Excluir curso', () => {
          /* o curso de exemplo fica: sem ele, o protótipo perde o conteúdo que as outras telas mostram */
          if (c.cliente) { E.toast('Exclusão ilustrativa: o curso de exemplo continua no protótipo', 'info'); return; }
          A.cursosNovos.splice(A.cursosNovos.findIndex((x) => x.id === c.id), 1); E.toast('Curso excluído'); setTimeout(() => ir(''), 0);
        });
      },
    };
  }

  /* Reduz a imagem escolhida para caber no navegador (o protótipo guarda os dados no próprio navegador). */
  function reduzirImagem(arq, pronto) {
    if (!/^image\/(png|jpe?g)$/.test(arq.type)) { E.toast('Escolha uma imagem em JPEG, JPG ou PNG', 'info'); return; }
    const leitor = new FileReader();
    leitor.onload = () => {
      const im = new Image();
      im.onload = () => {
        const L = 960, H = 540, tela = document.createElement('canvas'), k = Math.max(L / im.width, H / im.height), w = im.width * k, h = im.height * k;
        tela.width = L; tela.height = H;
        tela.getContext('2d').drawImage(im, (L - w) / 2, (H - h) / 2, w, h);
        pronto(tela.toDataURL('image/jpeg', 0.82));
      };
      im.onerror = () => E.toast('Não foi possível ler essa imagem', 'info');
      im.src = leitor.result;
    };
    leitor.readAsDataURL(arq);
  }
  /* Campos da aba "Básico": título, descrição, autor e capa do curso. Os mesmos campos, em branco,
     formam a tela "Criar curso". o.form: nome do formulário; o.rotulo: texto do botão principal;
     o.travado: o botão principal começa desligado e liga quando algo é alterado. */
  function formBasico(c, o) {
    let nova = null; /* capa escolhida e ainda não salva: { nome, img } */
    const img = () => (nova ? nova.img : c.capaImg || '');
    const miolo = () => (img() ? '<img src="' + img() + '" alt="Capa do curso">' : c.nome ? E.cover({ h: c.h, motif: c.motif, title: c.nome, kicker: c.cliente ? 'Mentoria' : 'Curso' }) : '<span class="cop-capa__vazia">' + icon('download', 'cop-up') + 'Enviar imagem</span>');
    const acoesCapa = () => '<label class="linkbtn" for="f-capa">' + icon('download', 'cop-up') + (img() ? 'Trocar imagem' : 'Enviar imagem') + '</label>' + (img() ? '<button type="button" class="linkbtn" data-cop="capa-tirar">' + icon('trash') + 'Remover imagem</button>' : '');
    const pintarCapa = (el) => { el.querySelector('#capa-caixa').innerHTML = miolo(); el.querySelector('#capa-acoes').innerHTML = acoesCapa(); };
    const destravar = (el) => { el.querySelector('form[data-form="' + o.form + '"] [type="submit"]').disabled = false; };
    /* campo com a explicação embaixo, à esquerda, e o contador de caracteres à direita */
    const contado = (rotulo, nome, controle, max, valor, dica) => '<div class="field"><label for="f-' + nome + '">' + rotulo + '</label>' + controle + '<div class="cop-campo-pe"><p class="hint">' + dica + '</p><p class="cop-conta" data-conta="' + nome + '">' + String(valor || '').length + ' / ' + max + '</p></div></div>';
    return {
      html: '<form class="panel cop-basico" data-form="' + o.form + '" novalidate><div class="cop-basico__grade">' +
        '<div class="field"><span>Capa do curso</span><input class="sr-only" type="file" accept="image/png, image/jpeg" name="capa" id="f-capa" aria-label="Capa do curso">' +
          '<label class="cop-capa" for="f-capa" id="capa-caixa">' + miolo() + '</label><div class="cop-capa__acoes" id="capa-acoes">' + acoesCapa() + '</div>' +
          '<p class="hint">A imagem aparece na tela “Meus cursos”, para identificar o curso. Tamanho recomendado: 1920 × 1080 px. Formatos: JPEG, JPG ou PNG.</p></div>' +
        '<div class="form">' +
          /* título e descrição são os textos do destaque da área de membros; lá, a fonte e o estilo não mudam */
          contado('Título do curso', 'nome', entrada('nome', c.nome || '', 'required maxlength="60"'), 60, c.nome, 'É o nome do curso na área de membros.') +
          contado('Descrição do curso', 'desc', areaTexto('desc', c.desc || '', 5, 'maxlength="220"'), 220, c.desc, 'Aparece logo abaixo do título, na área de membros.') +
          /* o autor fica só no painel do produtor: a área de membros não mostra esse dado */
          campo('Autor do curso', selecao('tutor', (c.tutor ? [] : [['', 'Selecione']]).concat(tutores().map((n) => [n, n])), c.tutor || ''), 'Fica só no painel do produtor. Não aparece na área de membros.', 'tutor') +
        '</div></div>' +
        '<div class="cop-basico__pe"><a class="btn btn--outline" href="' + link('') + '">Cancelar</a><button class="btn btn--go" type="submit"' + (o.travado ? ' disabled' : '') + '>' + o.rotulo + '</button></div></form>',
      input(alvo, el) {
        const f = el.querySelector('form[data-form="' + o.form + '"]');
        if (!f || !f.contains(alvo)) return;
        if (alvo.name === 'capa') { const arq = alvo.files && alvo.files[0]; if (arq) reduzirImagem(arq, (dados) => { nova = { nome: arq.name, img: dados }; pintarCapa(el); destravar(el); }); return; }
        const conta = f.querySelector('[data-conta="' + alvo.name + '"]');
        if (conta) conta.textContent = alvo.value.length + ' / ' + alvo.maxLength;
        destravar(el);
      },
      tirarCapa(el) { nova = { nome: '', img: '' }; el.querySelector('#f-capa').value = ''; pintarCapa(el); destravar(el); },
      ler(d) { return { nome: d.nome.trim(), desc: d.desc.trim(), tutor: d.tutor || '', capa: nova ? nova.nome : c.capa || '', capaImg: nova ? nova.img : c.capaImg || '' }; },
    };
  }
  const pedirTitulo = (f) => { f.querySelector('[name="nome"]').focus(); E.toast('Dê um título ao curso', 'info'); };

  /* "Criar curso": os campos da aba Básico em branco, para criar um curso do zero. */
  function cursoNovo() {
    const B = formBasico({ h: 168, motif: 'rings' }, { form: 'criar', rotulo: 'Criar curso' });
    return {
      html: pagina({
        crumbs: '<a href="' + link('') + '">' + icon('left') + 'Meus cursos</a>',
        titulo: 'Criar curso', sub: 'Preencha os dados básicos do novo curso. Você pode alterá-los depois, na página do curso.',
        corpo: B.html,
      }),
      input: B.input,
      on: { 'capa-tirar'() { B.tirarCapa(tela.el); } },
      submit: {
        criar(d, f) {
          const c = B.ler(d);
          if (!c.nome) { pedirTitulo(f); return; }
          c.id = uid('curso-'); c.status = 'despublicado'; /* o curso nasce despublicado; "Publicar curso" fica na página dele */
          A.cursosNovos.unshift(c); salvar();
          E.toast('Curso criado'); ir('cursos/' + c.id);
        },
      },
    };
  }
  /* Aba "Básico" da página do curso: título, descrição, autor e capa. */
  function cursoBasico(id) {
    const c = cursoDe(id);
    if (!c) return naoAchou();
    const B = formBasico(c, { form: 'basico', rotulo: 'Salvar alterações', travado: true });
    return {
      html: pagina(Object.assign(cabecaCurso(c, 'basico'), {
        corpo: B.html + (c.cliente ? '' : '<section class="panel cop-mt"><div class="panel__head"><div><h2>Aulas e módulos</h2><p>Este curso ainda não tem aulas</p></div></div>' +
          '<p class="hint">O cadastro de módulos e aulas segue o mesmo fluxo do curso ' + esc(A.mentoria.nome) + ', na aba Conteúdo. Neste protótipo, esse fluxo está demonstrado só naquele curso.</p></section>'),
      })),
      input: B.input,
      on: Object.assign({ 'capa-tirar'() { B.tirarCapa(tela.el); } }, acoesCurso(c)),
      submit: {
        basico(d, f) {
          const n = B.ler(d);
          if (!n.nome) { pedirTitulo(f); return; }
          gravarCurso(c.id, n); E.toast('Alterações salvas'); repintar();
        },
      },
    };
  }
  const cursosTela = (p) => (p[0] === 'novo' ? cursoNovo() : p[0] ? cursoBasico(p[0]) : cursosLista());

  const TELAS = { '': cursosLista, cursos: cursosTela, visao, conteudo, 'ao-vivo': aoVivo, relatorios: emBreve('Relatórios', IC.grafico), comunidade: comunidadeTela, alunos, certificados,
    acesso: emBreve('Controle de acesso', IC.escudo), chamados: chamadosTela, config };

  window.EMS_ADMIN = {
    render(el, sub, query) {
      E = window.EMS;
      /* sem permissão de coprodutor, nenhuma tela desta área abre: aparece a entrada */
      if (!E.ehCoprodutor()) { entrarTela(el); return; }
      if (!A) A = carregar();
      E.sessao.gravar('voltar', location.hash || '#/coprodutor');
      pintar(el, sub || '', query || new URLSearchParams(), false);
    },
  };
})();
