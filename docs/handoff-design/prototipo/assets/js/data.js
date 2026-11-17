/* ==========================================================================
   Emergensimples — conteúdo de exemplo do protótipo
   Tudo aqui é FICTÍCIO (cursos, instrutores, números) e serve só para dar
   corpo ao design. Troque por dados reais na integração.
   ========================================================================== */
(function () {
  'use strict';

  /* turma: ano da turma da mentoria. É sempre o ano atual, lido do relógio na hora de exibir:
     na virada do ano, todo "Turma AAAA" do portal muda sozinho, sem ninguém editar nada.
     duracao: duração da mentoria. O certificado só é liberado ao final dela. */
  const marca = { nome: 'Emergensimples', mentoria: 'Plantão sem GPT', get turma() { return new Date().getFullYear(); }, duracao: '12 meses' };

  const usuario = { nome: 'Marina Souza', tratamento: 'Dra. Marina', iniciais: 'MS', email: 'marina@exemplo.com' };

  /* Áreas — o matiz (h) colore as capas geradas; a interface em si fica na paleta base. */
  const areas = {
    emergencia: { nome: 'Emergência', h: 2 },
    cardio:     { nome: 'Cardiologia', h: 338 },
    viaaerea:   { nome: 'Via aérea e ventilação', h: 198 },
    uti:        { nome: 'Terapia intensiva', h: 172 },
    neuro:      { nome: 'Neurologia', h: 262 },
    infecto:    { nome: 'Infectologia', h: 96 },
    pediatria:  { nome: 'Pediatria', h: 40 },
    trauma:     { nome: 'Trauma e procedimentos', h: 22 },
    imagem:     { nome: 'Imagem e exames', h: 222 },
    rotina:     { nome: 'Rotina e carreira', h: 300 },
  };

  const instrutores = {
    helena: { nome: 'Dra. Helena Prado', iniciais: 'HP', titulo: 'Emergencista · mentora principal',
      bio: 'Coordena pronto-socorro há mais de dez anos e criou a mentoria para ensinar o raciocínio que usa todos os dias na sala vermelha.' },
    rafael: { nome: 'Dr. Rafael Monteiro', iniciais: 'RM', titulo: 'Cardiologista',
      bio: 'Plantonista de unidade coronariana. Ensina ECG e dor torácica com foco em decisão rápida.' },
    bianca: { nome: 'Dra. Bianca Azevedo', iniciais: 'BA', titulo: 'Intensivista',
      bio: 'Atua em UTI adulto e leva para as aulas o que realmente muda conduta à beira-leito.' },
    tiago:  { nome: 'Dr. Tiago Nakamura', iniciais: 'TN', titulo: 'Neurologista',
      bio: 'Trabalha em unidade de AVC e é obcecado por encurtar o tempo entre a porta e a decisão.' },
    livia:  { nome: 'Dra. Lívia Carvalho', iniciais: 'LC', titulo: 'Pediatra emergencista',
      bio: 'Ensina a atender criança no pronto-socorro sem medo e sem exagero.' },
    andre:  { nome: 'Dr. André Bastos', iniciais: 'AB', titulo: 'Cirurgião do trauma',
      bio: 'Instrutor de atendimento ao trauma e de procedimentos de emergência.' },
    camila: { nome: 'Dra. Camila Rezende', iniciais: 'CR', titulo: 'Infectologista',
      bio: 'Especialista em uso racional de antibióticos no pronto atendimento.' },
  };

  /* ---------------------------------------------------------------- cursos */

  const defs = [
    { id: 'plantao-sem-gpt', tipo: 'mentoria', titulo: 'Plantão sem GPT', area: 'emergencia', h: 357, motif: 'ecg',
      instrutor: 'helena', ano: marca.turma, nota: 4.9, alunos: 1240,
      /* frase fixa da mentoria, definida pela equipe: não reescrever */
      desc: 'Bem-vindo(a) ao Plantão Sem GPT. Raciocínio clínico passo a passo, casos reais e encontros ao vivo toda semana, sem depender de ChatGPT.',
      sobre: 'raciocínio clínico passo a passo, casos reais e encontros ao vivo toda semana, sem depender de ChatGPT.',
      tags: ['Mentoria em grupo', 'Encontros ao vivo', 'Casos reais'],
      modulos: [
        { titulo: 'Mentalidade de plantonista', aulas: [['Boas-vindas à mentoria', 6], ['Por que “sem GPT”? Pensar antes de consultar', 12], ['O mapa mental do plantão', 14], ['Como estudar durante as oito semanas', 8]] },
        { titulo: 'Os primeiros 10 minutos', aulas: [['Paciente grave: reconhecer em 30 segundos', 11], ['ABCDE na vida real', 16], ['Monitorização e acessos: o básico bem feito', 13], ['Encontro gravado: simulando a sala vermelha', 58]] },
        { titulo: 'Dor torácica', aulas: [['As causas que não podem passar', 15], ['ECG em quatro perguntas', 18], ['Estratificar e decidir', 14], ['Encontro gravado: casos de dor torácica', 62]] },
        { titulo: 'Falta de ar', aulas: [['Dispneia: por onde começar', 12], ['Oxigênio, VNI ou tubo?', 17], ['Sequência rápida sem pânico', 19], ['Encontro gravado: casos de dispneia', 60]] },
        { titulo: 'Sepse e choque', bloqueado: 7, aulas: [['Reconhecer sepse cedo', 13], ['A primeira hora', 15], ['Choque: tipos e condutas iniciais', 18], ['Encontro gravado: sepse na madrugada', 57]] },
        { titulo: 'Neuro no plantão', bloqueado: 14, aulas: [['Rebaixamento do nível de consciência', 14], ['AVC: tempo é cérebro', 16], ['Crise convulsiva', 12], ['Encontro gravado: casos neurológicos', 61]] },
        { titulo: 'Prescrição e passagem de plantão', bloqueado: 21, aulas: [['Prescrição segura', 15], ['Passagem de plantão estruturada', 10], ['Documentar para se proteger', 11], ['Encontro gravado: revisão de prescrições', 55]] },
        { titulo: 'Plantão simulado', bloqueado: 28, aulas: [['Simulado 1: plantão de enfermaria', 25], ['Simulado 2: pronto-socorro cheio', 27], ['Feedback e próximos passos', 9], ['Encerramento da turma', 45]] },
      ] },

    { id: 'ecg-no-plantao', titulo: 'ECG no Plantão', area: 'cardio', motif: 'ecg', tema: 'ECG', instrutor: 'rafael', ano: 2026, nota: 4.9, alunos: 3180,
      desc: 'Um método em quatro perguntas para ler qualquer eletrocardiograma sem travar — do traçado normal às alterações que não podem esperar.',
      tags: ['Método prático', 'Traçados comentados'] },
    { id: 'dor-toracica', titulo: 'Dor Torácica', sub: 'Da triagem à conduta', area: 'cardio', motif: 'rings', tema: 'dor torácica', instrutor: 'rafael', ano: 2025, nota: 4.8, alunos: 2410,
      desc: 'Como separar o que é grave do que pode esperar, organizar a investigação e decidir o destino do paciente com segurança.',
      tags: ['Casos comentados', 'Fluxo de decisão', 'Direto ao ponto'] },
    { id: 'arritmias', titulo: 'Arritmias na Emergência', area: 'cardio', motif: 'bars', tema: 'arritmias', instrutor: 'rafael', ano: 2026, novo: true, nota: 4.7, alunos: 890,
      desc: 'Taqui e bradiarritmias do reconhecimento à conduta inicial, com traçados reais e raciocínio em voz alta.',
      tags: ['Traçados reais', 'Passo a passo'] },
    { id: 'via-aerea', titulo: 'Via Aérea sem Medo', area: 'viaaerea', motif: 'wave', tema: 'via aérea', instrutor: 'helena', ano: 2025, nota: 4.9, alunos: 2760,
      desc: 'Preparação, decisão e plano B. O que fazer antes, durante e depois de abordar uma via aérea no plantão.',
      tags: ['Simulações', 'Plano B'] },
    { id: 'ventilacao', titulo: 'Ventilação Mecânica Descomplicada', area: 'viaaerea', motif: 'wave', h: 186, tema: 'ventilação mecânica', instrutor: 'bianca', ano: 2025, nota: 4.8, alunos: 1930,
      desc: 'Os ajustes iniciais, as curvas que importam e como reagir quando o alarme toca — sem fórmulas decoradas.',
      tags: ['Sem decoreba', 'Curvas comentadas', 'À beira-leito'] },
    { id: 'gasometria', titulo: 'Gasometria em 10 Passos', area: 'uti', motif: 'drop', tema: 'gasometria', instrutor: 'bianca', ano: 2024, nota: 4.7, alunos: 3540,
      desc: 'Um roteiro fixo para interpretar qualquer gasometria e transformar números em hipótese e conduta.',
      tags: ['Roteiro fixo', 'Exercícios'] },
    { id: 'choque', titulo: 'Choque: Reconhecer e Tratar', area: 'uti', motif: 'rings', h: 160, tema: 'choque', instrutor: 'bianca', ano: 2026, novo: true, nota: 4.8, alunos: 720,
      desc: 'Identificar o paciente em choque antes da hipotensão e iniciar o tratamento certo para cada cenário.',
      tags: ['Paciente grave', 'Casos reais'] },
    { id: 'eletrolitos', titulo: 'Distúrbios Hidroeletrolíticos', area: 'uti', motif: 'hex', tema: 'distúrbios hidroeletrolíticos', instrutor: 'bianca', ano: 2025, nota: 4.6, alunos: 1480,
      desc: 'Sódio, potássio e companhia: quando corrigir, com que pressa e como não piorar o paciente.',
      tags: ['Tabelas práticas', 'Casos comentados', 'Revisão'] },
    { id: 'glicemia', titulo: 'Emergências Glicêmicas', area: 'uti', motif: 'drop', h: 150, tema: 'emergências glicêmicas', instrutor: 'bianca', ano: 2024, nota: 4.6, alunos: 1320,
      desc: 'Hipo e hiperglicemias graves no pronto-socorro, da suspeita ao acompanhamento nas primeiras horas.',
      tags: ['Fluxo de decisão', 'Direto ao ponto'] },
    { id: 'sepse', titulo: 'Sepse: a Primeira Hora', area: 'infecto', motif: 'hex', tema: 'sepse', instrutor: 'camila', ano: 2025, nota: 4.9, alunos: 2980,
      desc: 'Reconhecer cedo, agir rápido e reavaliar. Tudo o que precisa acontecer na primeira hora — e em que ordem.',
      tags: ['Tempo-dependente', 'Casos reais'] },
    { id: 'antibioticos', titulo: 'Antibióticos no PS', area: 'infecto', motif: 'pill', tema: 'antibióticos', instrutor: 'camila', ano: 2026, novo: true, nota: 4.7, alunos: 640,
      desc: 'Como escolher, quando começar e quando não prescrever. Uso racional explicado por síndromes.',
      tags: ['Por síndromes', 'Uso racional'] },
    { id: 'avc', titulo: 'AVC: Janela de Ação', area: 'neuro', motif: 'clock', tema: 'AVC', instrutor: 'tiago', ano: 2025, nota: 4.8, alunos: 2100,
      desc: 'Do primeiro contato à decisão terapêutica: o que perguntar, o que examinar e o que não pode atrasar.',
      tags: ['Tempo-dependente', 'Protocolo comentado', 'Casos reais'] },
    { id: 'crise-convulsiva', titulo: 'Crise Convulsiva', area: 'neuro', motif: 'net', tema: 'crise convulsiva', instrutor: 'tiago', ano: 2024, nota: 4.6, alunos: 1760,
      desc: 'O atendimento da crise em andamento e a investigação depois que ela passa, sem exageros e sem omissões.',
      tags: ['Passo a passo', 'Casos comentados'] },
    { id: 'emergencias-psiquiatricas', titulo: 'Emergências Psiquiátricas', area: 'neuro', motif: 'net', h: 280, tema: 'emergências psiquiátricas', instrutor: 'tiago', ano: 2025, nota: 4.5, alunos: 980,
      desc: 'Agitação, risco e acolhimento: como conduzir com segurança para o paciente e para a equipe.',
      tags: ['Comunicação', 'Segurança', 'Casos reais'] },
    { id: 'pediatria-ps', titulo: 'Pediatria no Pronto-Socorro', area: 'pediatria', motif: 'rings', tema: 'pediatria', instrutor: 'livia', ano: 2025, nota: 4.8, alunos: 1650,
      desc: 'As queixas mais comuns da criança no PS e os sinais que diferenciam o quadro simples do grave.',
      tags: ['Sinais de alarme', 'Doses comentadas', 'Casos reais'] },
    { id: 'trauma', titulo: 'Trauma: Atendimento Inicial', area: 'trauma', motif: 'cross', tema: 'trauma', instrutor: 'andre', ano: 2024, nota: 4.7, alunos: 2240,
      desc: 'A sequência do atendimento inicial ao politraumatizado, com as prioridades que salvam vidas.',
      tags: ['Sequência prática', 'Simulações', 'Trabalho em equipe'] },
    { id: 'suturas', titulo: 'Suturas e Pequenos Procedimentos', area: 'trauma', motif: 'stitch', h: 30, tema: 'pequenos procedimentos', instrutor: 'andre', ano: 2025, nota: 4.8, alunos: 3020,
      desc: 'Técnica demonstrada de perto: materiais, anestesia local, pontos mais usados e cuidados depois.',
      tags: ['Mão na massa', 'Vídeos em close'] },
    { id: 'intoxicacoes', titulo: 'Intoxicações Exógenas', area: 'emergencia', motif: 'drop', h: 14, tema: 'intoxicações', instrutor: 'helena', ano: 2024, nota: 4.5, alunos: 1110,
      desc: 'Abordagem inicial do paciente intoxicado: o que perguntar, o que reconhecer e a quem recorrer.',
      tags: ['Abordagem geral', 'Casos reais', 'Fluxo de decisão'] },
    { id: 'intercorrencias-enfermaria', titulo: 'Intercorrências na Enfermaria', area: 'emergencia', motif: 'bars', tema: 'intercorrências', instrutor: 'helena', ano: 2025, nota: 4.8, alunos: 2630,
      desc: 'Febre, dor, queda de saturação, agitação: como responder aos chamados mais frequentes da madrugada.',
      tags: ['Plantão noturno', 'Direto ao ponto'] },
    { id: 'raio-x-torax', titulo: 'Raio-X de Tórax na Prática', area: 'imagem', motif: 'xray', tema: 'raio-X de tórax', instrutor: 'bianca', ano: 2024, nota: 4.7, alunos: 2890,
      desc: 'Uma leitura sistemática para não deixar passar o que importa, com dezenas de imagens comentadas.',
      tags: ['Leitura sistemática', 'Imagens comentadas'] },
    { id: 'pocus', titulo: 'POCUS à Beira-Leito', area: 'imagem', motif: 'scan', tema: 'ultrassom à beira-leito', instrutor: 'bianca', ano: 2026, novo: true, nota: 4.9, alunos: 760,
      desc: 'O ultrassom como extensão do exame físico: janelas essenciais e como integrar o achado à decisão.',
      tags: ['Janelas essenciais', 'Vídeos reais'] },
    { id: 'primeiro-plantao', titulo: 'Primeiro Plantão', sub: 'Guia de sobrevivência', area: 'rotina', motif: 'cross', tema: 'primeiro plantão', instrutor: 'helena', ano: 2025, nota: 4.9, alunos: 4120,
      desc: 'O que levar, como se organizar, a quem pedir ajuda e como chegar inteiro ao fim das doze horas.',
      tags: ['Para começar', 'Organização'] },
    { id: 'prescricao-segura', titulo: 'Prescrição Segura', area: 'rotina', motif: 'pill', h: 312, tema: 'prescrição', instrutor: 'camila', ano: 2025, nota: 4.8, alunos: 3350,
      desc: 'Estrutura, clareza e dupla checagem: como prescrever de um jeito que protege o paciente e você.',
      tags: ['Segurança do paciente', 'Modelos prontos'] },
    { id: 'passagem-de-plantao', titulo: 'Passagem de Plantão', area: 'rotina', motif: 'chat', tema: 'passagem de plantão', instrutor: 'helena', ano: 2026, novo: true, nota: 4.7, alunos: 540,
      desc: 'Um roteiro simples para passar e receber o plantão sem perder informação crítica.',
      tags: ['Comunicação', 'Roteiro pronto', 'Curso rápido'] },
    { id: 'mas-noticias', titulo: 'Comunicação de Más Notícias', area: 'rotina', motif: 'chat', h: 288, tema: 'comunicação difícil', instrutor: 'livia', ano: 2024, nota: 4.8, alunos: 1870,
      desc: 'Como conduzir conversas difíceis com pacientes e famílias, com estrutura e humanidade.',
      tags: ['Comunicação', 'Simulações'] },
  ];

  /* Estrutura padrão de módulos para os cursos (a mentoria tem estrutura própria). */
  function modulosPadrao(c, seed) {
    const v = (base, i) => base + ((seed * 3 + i * 5) % 4);
    return [
      { titulo: 'Abordagem passo a passo', aulas: [['Avaliação inicial em cinco minutos', v(10, 3)], ['Sinais de alarme que não podem passar', v(8, 4)], ['Do primeiro atendimento à reavaliação', v(13, 5)], ['Quando pedir ajuda — e para quem', v(6, 6)]] },
      { titulo: 'Casos comentados', aulas: [['Caso 1: o plantão começa cheio', v(12, 7)], ['Caso 2: o paciente que piora', v(13, 8)], ['Caso 3: a decisão difícil', v(11, 9)]] },
    ];
  }

  function montar(d, i) {
    const c = Object.assign({ tipo: 'curso' }, d);
    c.h = d.h != null ? d.h : areas[d.area].h;
    const mods = d.modulos || modulosPadrao(d, i);
    let n = 0;
    c.modulos = mods.map(function (m, mi) {
      return {
        i: mi,
        titulo: m.titulo,
        bloqueado: m.bloqueado || 0, // dias até liberar (mentoria libera por semana)
        aulas: m.aulas.map(function (a, ai) {
          n += 1;
          return { id: c.id + '-m' + (mi + 1) + 'a' + (ai + 1), n: n, titulo: a[0], min: a[1], modulo: mi, bloqueada: !!m.bloqueado };
        }),
      };
    });
    c.aulas = c.modulos.reduce(function (all, m) { return all.concat(m.aulas); }, []);
    c.totalMin = c.aulas.reduce(function (s, a) { return s + a.min; }, 0);
    return c;
  }
  const cursos = defs.map(montar);

  /* ------------------------------------------------- cursos à venda (ofertas) */
  /* Cursos fora do plano do aluno, vendidos à parte. Exemplos fictícios: nomes, preços e
     condições são só para dar corpo ao design.
     checkout: endereço da página de pagamento real. Vazio = aviso ilustrativo no protótipo. */
  const defsVenda = [
    { id: 'pcr-sem-panico', titulo: 'PCR sem Pânico', area: 'emergencia', h: 6, motif: 'ecg', tema: 'parada cardiorrespiratória', instrutor: 'helena',
      preco: 497, parcelas: 12, checkout: '',
      desc: 'Do reconhecimento ao pós-parada: como liderar o atendimento, organizar a equipe e tomar as decisões que mudam o desfecho.',
      aprende: ['Reconhecer a parada e iniciar o atendimento sem perder tempo', 'Distribuir funções e liderar a equipe com clareza', 'Escolher a conduta certa para cada ritmo', 'Conduzir os cuidados logo após o retorno da circulação'] },
    { id: 'uti-para-plantonistas', titulo: 'UTI para Plantonistas', area: 'uti', motif: 'hex', tema: 'terapia intensiva', instrutor: 'bianca',
      preco: 597, parcelas: 12, checkout: '',
      desc: 'O essencial para assumir um plantão de terapia intensiva com segurança, da admissão à passagem do caso.',
      aprende: ['Organizar a visita e priorizar os pacientes do plantão', 'Ajustar drogas vasoativas e sedação à beira-leito', 'Interpretar a monitorização sem se perder nos números', 'Reconhecer quando o paciente está piorando'] },
    { id: 'tomografia-no-plantao', titulo: 'Tomografia no Plantão', area: 'imagem', motif: 'scan', tema: 'tomografia', instrutor: 'tiago',
      preco: 397, parcelas: 12, checkout: '',
      desc: 'Um roteiro para olhar tomografias de crânio, tórax e abdome e achar o que muda a conduta antes do laudo chegar.',
      aprende: ['Seguir um roteiro de leitura para cada região', 'Identificar os achados que não podem esperar', 'Saber quando pedir contraste e quando ele atrapalha', 'Conversar com a radiologia fazendo a pergunta certa'] },
    { id: 'sedacao-e-analgesia', titulo: 'Sedação e Analgesia', area: 'viaaerea', motif: 'drop', tema: 'sedação e analgesia', instrutor: 'bianca',
      preco: 397, parcelas: 12, checkout: '',
      desc: 'Como escolher, preparar e titular as drogas mais usadas no pronto-socorro, com doses e cuidados para cada situação.',
      aprende: ['Escolher a droga pelo paciente, e não pelo hábito', 'Preparar e titular com segurança', 'Sedar para procedimentos sem perder a via aérea', 'Prevenir e tratar as complicações mais comuns'] },
    { id: 'emergencias-obstetricas', titulo: 'Emergências Obstétricas', area: 'emergencia', h: 320, motif: 'rings', tema: 'emergências obstétricas', instrutor: 'livia',
      preco: 497, parcelas: 12, checkout: '',
      desc: 'O que todo plantonista precisa saber para estabilizar a gestante até a chegada da equipe especializada.',
      aprende: ['Avaliar a gestante que chega ao pronto-socorro', 'Conduzir as síndromes hipertensivas na urgência', 'Agir rápido nos sangramentos da gestação', 'Saber o que muda na reanimação da gestante'] },
    { id: 'procedimentos-no-plantao', titulo: 'Procedimentos no Plantão', area: 'trauma', motif: 'stitch', tema: 'procedimentos', instrutor: 'andre',
      preco: 597, parcelas: 12, checkout: '',
      desc: 'Acesso central, drenagem de tórax, paracentese e punção lombar, demonstrados passo a passo e de perto.',
      aprende: ['Indicar e contraindicar cada procedimento', 'Preparar o material e posicionar o paciente', 'Executar a técnica passo a passo', 'Reconhecer e manejar as complicações'] },
    { id: 'ecg-avancado', titulo: 'ECG Avançado', area: 'cardio', motif: 'bars', tema: 'ECG avançado', instrutor: 'rafael',
      preco: 397, parcelas: 12, checkout: '',
      desc: 'Para quem já lê o básico: bloqueios, taquicardias de QRS largo e os padrões de alto risco que passam despercebidos.',
      aprende: ['Diferenciar as taquicardias de QRS largo', 'Reconhecer padrões de alto risco sem supra clássico', 'Interpretar bloqueios e marca-passo', 'Decidir a conduta a partir do traçado'] },
    { id: 'idoso-no-pronto-socorro', titulo: 'Idoso no Pronto-Socorro', area: 'rotina', h: 34, motif: 'clock', tema: 'atendimento ao idoso', instrutor: 'helena',
      preco: 297, parcelas: 12, checkout: '',
      desc: 'Apresentações atípicas, polifarmácia e delirium: como atender o paciente idoso sem cair nas armadilhas mais comuns.',
      aprende: ['Desconfiar das apresentações atípicas', 'Revisar a prescrição e evitar interações', 'Prevenir, reconhecer e tratar delirium', 'Conversar com a família e planejar a alta'] },
  ];
  const ofertas = defsVenda.map(function (d, i) {
    const c = montar(Object.assign({ tipo: 'oferta', tags: [] }, d), i + 2);
    c.aulas.forEach(function (a) { a.bloqueada = true; }); // só libera depois da compra
    return c;
  });

  /* ---------------------------------------------------------------- trilhas */

  const trilhas = [
    { id: 'do-zero', titulo: 'Do zero ao primeiro plantão', h: 300, motif: 'cross',
      desc: 'Para quem vai começar a dar plantão: organização, prescrição, comunicação e as intercorrências que mais aparecem.',
      cursos: ['primeiro-plantao', 'prescricao-segura', 'passagem-de-plantao', 'intercorrencias-enfermaria', 'mas-noticias'] },
    { id: 'sala-vermelha', titulo: 'Sala vermelha', h: 357, motif: 'ecg',
      desc: 'O paciente grave, do reconhecimento à estabilização. A trilha mais procurada por quem já está no pronto-socorro.',
      cursos: ['via-aerea', 'choque', 'sepse', 'ventilacao', 'gasometria'] },
    { id: 'coracao', titulo: 'Coração na emergência', h: 338, motif: 'rings',
      desc: 'ECG, dor torácica e arritmias em sequência, para ganhar segurança nas queixas cardiológicas.',
      cursos: ['ecg-no-plantao', 'dor-toracica', 'arritmias'] },
    { id: 'neuro', titulo: 'Neuro no pronto-socorro', h: 262, motif: 'net',
      desc: 'AVC, crises convulsivas e emergências psiquiátricas, com foco no que é tempo-dependente.',
      cursos: ['avc', 'crise-convulsiva', 'emergencias-psiquiatricas'] },
    { id: 'imagem', titulo: 'Imagem à beira-leito', h: 222, motif: 'scan',
      desc: 'Raio-X e ultrassom como extensão do exame físico, do básico ao uso avançado.',
      cursos: ['raio-x-torax', 'pocus'] },
  ];

  /* ---------------------------------------------------------------- ao vivo */

  function proximo(diaSemana, h, m, semanas) {
    const agora = new Date();
    const d = new Date(agora);
    d.setHours(h, m, 0, 0);
    let diff = (diaSemana - d.getDay() + 7) % 7;
    if (diff === 0 && d <= agora) diff = 7;
    d.setDate(d.getDate() + diff + (semanas || 0) * 7);
    return d;
  }

  const lives = [
    { id: 'l-mentoria-1', titulo: 'Encontro da mentoria: casos de dor torácica', tipo: 'Mentoria', mentoria: true, instrutor: 'helena', quando: proximo(4, 20, 0), min: 90, h: 357, motif: 'ecg',
      desc: 'Discussão ao vivo de três casos enviados pela turma, com raciocínio em voz alta e espaço para perguntas.' },
    { id: 'l-duvidas', titulo: 'Plantão de dúvidas', tipo: 'Aberto a todos', instrutor: 'bianca', quando: proximo(2, 19, 30), min: 60, h: 172, motif: 'chat',
      desc: 'Traga a dúvida do seu último plantão. Perguntas respondidas ao vivo, sem roteiro.' },
    { id: 'l-ecg', titulo: 'ECG comentado: dez traçados em sessenta minutos', tipo: 'Aula ao vivo', instrutor: 'rafael', quando: proximo(6, 10, 0), min: 60, h: 338, motif: 'bars',
      desc: 'Dez eletrocardiogramas lidos do zero com o método das quatro perguntas.' },
    { id: 'l-mentoria-2', titulo: 'Encontro da mentoria: casos de dispneia', tipo: 'Mentoria', mentoria: true, instrutor: 'helena', quando: proximo(4, 20, 0, 1), min: 90, h: 357, motif: 'wave',
      desc: 'Oxigênio, ventilação não invasiva ou tubo? Casos discutidos passo a passo.' },
    { id: 'l-primeiro', titulo: 'Aula aberta: como se preparar para o primeiro plantão', tipo: 'Aberto a todos', instrutor: 'helena', quando: proximo(1, 20, 0, 1), min: 75, h: 300, motif: 'cross',
      desc: 'O que ninguém conta antes das primeiras doze horas — e como chegar pronto.' },
    { id: 'l-sepse', titulo: 'Discussão de caso: sepse na madrugada', tipo: 'Aula ao vivo', instrutor: 'camila', quando: proximo(3, 19, 0, 1), min: 60, h: 96, motif: 'hex',
      desc: 'Um caso real, do primeiro chamado à reavaliação, com as decisões comentadas.' },
  ].sort(function (a, b) { return a.quando - b.quando; });

  /* Novos conteúdos (página Ao vivo): tudo o que foi publicado ou atualizado, com a idade em dias.
     A seção mostra só os últimos 7 dias. Os itens mais antigos ficam na lista de propósito,
     para a regra poder ser conferida: eles não aparecem. */
  const novidades = [
    { tipo: 'curso', acao: 'publicado', dias: 0, curso: 'passagem-de-plantao' },
    { tipo: 'aula', acao: 'publicado', dias: 1, curso: 'plantao-sem-gpt', aula: 'plantao-sem-gpt-m4a3' },
    { tipo: 'gravacao', acao: 'publicado', dias: 2, titulo: 'Casos da sala vermelha', min: 58, h: 357, motif: 'ecg' },
    { tipo: 'curso', acao: 'publicado', dias: 3, curso: 'pocus' },
    { tipo: 'curso', acao: 'atualizado', dias: 4, curso: 'sepse' },
    { tipo: 'gravacao', acao: 'publicado', dias: 5, titulo: 'Plantão de dúvidas #12', min: 61, h: 172, motif: 'chat' },
    { tipo: 'ebook', acao: 'atualizado', dias: 6, curso: 'plantao-sem-gpt', aula: 'plantao-sem-gpt-m3a2' },
    { tipo: 'curso', acao: 'atualizado', dias: 7, curso: 'antibioticos' },
    /* mais de 7 dias: ficam fora da seção */
    { tipo: 'gravacao', acao: 'publicado', dias: 14, titulo: 'Gasometrias difíceis', min: 54, h: 160, motif: 'drop' },
    { tipo: 'gravacao', acao: 'publicado', dias: 21, titulo: 'AVC: três casos, três decisões', min: 63, h: 262, motif: 'clock' },
    { tipo: 'gravacao', acao: 'publicado', dias: 21, titulo: 'Criança com febre no PS', min: 49, h: 40, motif: 'rings' },
    { tipo: 'gravacao', acao: 'publicado', dias: 30, titulo: 'Raio-X: o que você deixou passar', min: 52, h: 222, motif: 'xray' },
    { tipo: 'gravacao', acao: 'publicado', dias: 30, titulo: 'Antibiótico: começar ou esperar?', min: 56, h: 96, motif: 'pill' },
  ];

  /* ---------------------------------------------------------------- diversos */

  const top10 = ['ecg-no-plantao', 'primeiro-plantao', 'via-aerea', 'sepse', 'prescricao-segura', 'gasometria', 'suturas', 'raio-x-torax', 'intercorrencias-enfermaria', 'dor-toracica'];

  /* Avisos do sininho. O aluno só é notificado em quatro situações, e em nenhuma outra:
     1) uma nova aula foi liberada; 2) há um encontro da mentoria;
     3) um comentário que ele publicou na comunidade foi respondido (a comunidade centraliza os
        comentários dos alunos e as respostas dos mentores; não há mais dúvidas dentro da aula);
     4) um chamado de suporte que ele abriu foi respondido. */
  const notificacoes = [
    { icone: 'live', titulo: 'Encontro da mentoria hoje, às 20h', texto: 'Discussão de casos de dor torácica enviados pela turma.', href: '#/ao-vivo', quando: 'agora', nova: true },
    { icone: 'play', titulo: 'Nova aula liberada', texto: 'Semana 4 da mentoria: “Sequência rápida sem pânico”.', href: '#/mentoria', quando: 'há 2 h', nova: true },
    { icone: 'message', titulo: 'Seu comentário foi respondido', texto: 'Uma mentora respondeu à sua publicação na comunidade.', href: '#/mentoria?aba=comunidade', quando: 'ontem' },
    { icone: 'help', titulo: 'Seu chamado foi respondido', texto: 'A equipe de suporte respondeu ao chamado #1018, sobre e-books.', href: '#/ajuda', quando: 'há 3 dias' },
  ];

  /* Publicações da comunidade. As respostas abrem logo abaixo de cada publicação. */
  const comunidade = [
    { id: 'c1', autor: 'Lucas Ferraz', iniciais: 'LF', quando: 'há 35 min', curtidas: 18,
      texto: 'Primeiro plantão sozinho ontem. Usei o mapa mental da semana 1 do começo ao fim e, pela primeira vez, não travei na passagem. Obrigado, turma!',
      respostas: [
        { autor: 'Paula Antunes', iniciais: 'PA', quando: 'há 30 min', texto: 'Que notícia boa! O primeiro plantão sozinho a gente nunca esquece.' },
        { autor: 'Dra. Helena Prado', iniciais: 'HP', mentor: true, quando: 'há 22 min', texto: 'É isso, Lucas. Passagem bem feita é metade de um plantão tranquilo. Conta mais no encontro de quinta.' },
        { autor: 'Rodrigo Leal', iniciais: 'RL', quando: 'há 10 min', texto: 'Também uso o mapa mental. Imprimi e deixo no bolso do jaleco.' },
      ] },
    { id: 'c2', autor: 'Dra. Helena Prado', iniciais: 'HP', mentor: true, quando: 'há 2 h', curtidas: 42,
      texto: 'Para o encontro de hoje: enviem até as 18h os casos de dor torácica que quiserem discutir. Vale caso que deu certo e caso que deu errado — aprendemos mais com o segundo.',
      respostas: [
        { autor: 'Lucas Ferraz', iniciais: 'LF', quando: 'há 1 h', texto: 'Vou enviar um de ontem, que me deixou em dúvida até o fim do plantão.' },
        { autor: 'Paula Antunes', iniciais: 'PA', quando: 'há 50 min', texto: 'Pode ser caso de enfermaria ou só de pronto-socorro?' },
        { autor: 'Dra. Helena Prado', iniciais: 'HP', mentor: true, quando: 'há 45 min', texto: 'Pode ser dos dois, Paula. O que importa é o raciocínio.' },
        { autor: 'Rodrigo Leal', iniciais: 'RL', quando: 'há 20 min', texto: 'Enviado. Até mais tarde!' },
      ] },
    { id: 'c3', autor: 'Paula Antunes', iniciais: 'PA', quando: 'há 5 h', curtidas: 9,
      texto: 'Alguém tem um bom jeito de organizar as pendências no meio do plantão? Papel, celular, prancheta? Estou testando um modelo e posso compartilhar.',
      respostas: [
        { autor: 'Rodrigo Leal', iniciais: 'RL', quando: 'há 4 h', texto: 'Uso uma folha dobrada em quatro, um quadrante por paciente. Simples e funciona.' },
        { autor: 'Lucas Ferraz', iniciais: 'LF', quando: 'há 3 h', texto: 'Compartilha o modelo, por favor! Sempre perco alguma pendência na troca de turno.' },
      ] },
    { id: 'c4', autor: 'Rodrigo Leal', iniciais: 'RL', quando: 'ontem', curtidas: 23,
      texto: 'Revi a aula “ABCDE na vida real” antes de entrar e fez diferença. Recomendo assistir de novo depois de alguns plantões: a gente escuta outra coisa.',
      respostas: [
        { autor: 'Paula Antunes', iniciais: 'PA', quando: 'ontem', texto: 'Concordo. Na segunda vez reparei em detalhes que tinham passado batido.' },
        { autor: 'Dra. Helena Prado', iniciais: 'HP', mentor: true, quando: 'ontem', texto: 'Essa é a ideia: a aula é a mesma, quem muda é você.' },
        { autor: 'Lucas Ferraz', iniciais: 'LF', quando: 'ontem', texto: 'Boa dica, vou rever antes do plantão de sábado.' },
      ] },
  ];

  const capitulos = [
    { titulo: 'Introdução', de: 0, pontos: ['O que você vai conseguir fazer ao final desta aula', 'Por que esse tema derruba tanto plantonista', 'Como esta aula se liga às anteriores'], legenda: 'Antes de qualquer conduta, vamos organizar o raciocínio.' },
    { titulo: 'Conceito central', de: 0.18, pontos: ['A ideia que organiza todo o raciocínio', 'O que observar primeiro no paciente', 'O que pode esperar — e o que não pode'], legenda: 'Guarde esta ideia: ela vale para quase todo paciente que chega.' },
    { titulo: 'Aplicação no plantão', de: 0.52, pontos: ['Passo a passo comentado em um caso', 'Onde a maioria erra e como evitar', 'Como registrar e comunicar a conduta'], legenda: 'Agora um caso: pause e pense no que você faria antes de continuar.' },
    { titulo: 'Resumo', de: 0.86, pontos: ['Três pontos para levar no bolso', 'Checklist rápido para o próximo plantão', 'O que estudar em seguida'], legenda: 'Para fechar: três pontos que você leva para o próximo plantão.' },
  ];

  const quiz = [
    { p: 'Na avaliação inicial do paciente grave, qual é a ordem da abordagem ABCDE?',
      o: ['Circulação, via aérea, respiração, exposição, neurológico', 'Via aérea, respiração, circulação, neurológico, exposição', 'Respiração, via aérea, circulação, exposição, neurológico', 'Via aérea, circulação, respiração, neurológico, exposição'], c: 1,
      e: 'A sequência prioriza o que mata primeiro: via aérea (A), respiração (B), circulação (C), avaliação neurológica (D) e exposição (E).' },
    { p: 'Qual ferramenta estrutura a comunicação na passagem de plantão?',
      o: ['SBAR', 'APGAR', 'ABCDE', 'SOAP'], c: 0,
      e: 'SBAR organiza a mensagem em Situação, Breve histórico, Avaliação e Recomendação.' },
    { p: 'Qual é a faixa de frequência cardíaca habitualmente considerada normal para um adulto em repouso?',
      o: ['40 a 60 bpm', '60 a 100 bpm', '100 a 120 bpm', '80 a 140 bpm'], c: 1,
      e: 'Entre 60 e 100 batimentos por minuto. Abaixo disso fala-se em bradicardia; acima, em taquicardia.' },
  ];

  /* Central de ajuda: assuntos do formulário e um chamado antigo, só de exemplo */
  const ajuda = {
    assuntos: ['Acesso à plataforma', 'Aulas e vídeos', 'E-books', 'Encontros ao vivo', 'Certificado', 'Plano', 'Outro assunto'],
    exemplo: { n: 1018, assunto: 'E-books', status: 'resolvido', dias: 4,
      texto: 'Não consegui baixar o e-book da aula 3. O botão abre uma página em branco.',
      resposta: 'O arquivo foi reenviado e já está disponível na aba E-books. Obrigado por avisar!' },
  };

  const estudoSemana = [35, 50, 0, 62, 45, 80, 28]; // minutos por dia, do mais antigo para hoje

  window.DB = { marca, usuario, areas, instrutores, cursos, ofertas, trilhas, lives, novidades, top10, notificacoes, comunidade, capitulos, quiz, estudoSemana, ajuda };
})();
