# Área de membros — tela por tela

Identidade do cliente (Emergensimples), mentoria **Plantão sem GPT**. Fundo `#141414`, vermelho `#e50914`. **Está aprovada: implementar exatamente como está.**

- Protótipo: `prototipo/index.html` (telas em `prototipo/assets/js/app.js`, dados de exemplo em `prototipo/assets/js/data.js`).
- Estilos: `prototipo/assets/css/tokens.css` e `app.css`.
- Imagens: `telas/membros/computador-1440/` e `telas/membros/celular-390/`.
- Os endereços abaixo são os do protótipo (depois de `index.html#`). No produto real os endereços seguem o padrão do projeto.

Conteúdo fictício (vem do banco de dados no produto real): nomes de temas, pessoas, números, datas e textos de exemplo. Rótulos, títulos de tela, botões e mensagens são definitivos.

## Estrutura comum

### Barra do topo

Fixa, `68px` de altura. No alto da página é transparente com um degradê escuro; ao rolar mais de 12 px fica sólida em `#141414`.

- Marca em texto: **Emergensimples** (vem de Configurações › Área de membros do painel). Sem logotipo.
- Links: **Início**, **Mentoria**, **Cursos**, **Trilhas**, **Ao vivo**, **Minha lista**. `14px`, cor `#e5e5e5`; o da tela aberta fica branco em peso `700`.
- Busca: lupa que abre um campo ("Cursos, aulas, áreas").
- Sininho, com contador vermelho das novidades. Abre uma lista com os avisos (imagem `25-notificacoes.png`).
- Perfil: avatar com as iniciais e seta. Menu (imagem `26-menu-do-perfil.png`): cabeçalho com nome e "Mentoria Plantão sem GPT"; **Meu progresso**, **Certificado**, **Minha lista**, **Conta e preferências**; separador; **Central de ajuda**, **Sair**.

Até 899 px: os links somem e aparece uma **barra inferior** fixa com 5 itens (ícone em cima, rótulo de 10 px embaixo): Início, Mentoria, Cursos, Ao vivo, Progresso.

### Rodapé

Lista de links em colunas e uma linha final. No protótipo a linha final diz "Emergensimples · protótipo de interface com conteúdo fictício" e traz "Restaurar dados de exemplo": **isso é do protótipo e não vai para o produto**.

### Faixa "Visualizando como membro"

Só aparece para quem entrou como produtor ou coprodutor e clicou em "Visualizar como membro" (ou "Visualizar curso") no painel. Fica fixa embaixo, à esquerda: fundo branco, texto "Visualizando como membro" e o botão **Voltar à área do coprodutor**. O aluno nunca vê essa faixa.

## Telas

### 1. Início — `/` — `02-inicio.png`

1. **Destaque** (ocupa o topo, altura `max(520px, min(56.25vw, 90vh))`): fundo com grade e traçado de ECG animado em vermelho.
   - Linha de cima: etiqueta vermelha **Mentoria** e o texto "Turma AAAA · encontros ao vivo" (o ano é sempre o ano atual).
   - Título: nome da mentoria, em duas linhas, **PLANTÃO / SEM GPT** (Archivo 900, largura 64%, maiúsculas, `clamp(56px, 9.4vw, 156px)`).
   - Descrição do curso logo abaixo: "Bem-vindo(a) ao Plantão Sem GPT. Raciocínio clínico passo a passo, casos reais e encontros ao vivo toda semana, sem depender de ChatGPT."
   - Botões: **Continuar** (ou **Começar**, se o aluno ainda não assistiu nada), claro, com ícone de reproduzir; **Mais informações**, suave, com ícone de informação.
   - Linha de retomada: "Semana N · Aula N — título da aula · restam N min" e a barra de progresso da mentoria.
   - À direita, embaixo: atalho "Próximo encontro ao vivo: dia e hora".
2. **Fileiras de cartões**, nesta ordem padrão (o produtor muda a ordem e liga/desliga cada uma no painel):
   1. "Continue de onde parou, [tratamento do aluno]"
   2. "Top 10 no plantão esta semana" (cartões em formato de pôster com o número grande ao lado)
   3. "Sua jornada na mentoria Plantão sem GPT" (uma capa por semana; as bloqueadas mostram cadeado e "Libera em DD/MM")
   4. "Novidades"
   5. "Trilhas para seguir em ordem"
   6. "Cardiologia" (fileira por área)
   7. "Próximos encontros ao vivo"
   8. "Via aérea, ventilação e paciente grave" (fileira por área)
   9. "Minha lista"
   10. "Rotina, comunicação e carreira" (fileira por área)

   Cada fileira rola na horizontal, com setas nas laterais em telas largas, e pode ter um link "ver tudo". Fileira sem itens não aparece.
3. **Vitrine "Cursos à venda"**: etiqueta "À venda", "N cursos vendidos à parte", título "Outros cursos da Emergensimples", frase "Escolha um para ver o conteúdo e comprar." e os cursos em pôster, com selo de cadeado "Bloqueado" e a área embaixo. Sem preço na vitrine.

Passar o mouse sobre um cartão de tema abre uma **prévia ampliada** com nota, número de aulas, duração e as etiquetas do tema.

### 2. Mentoria — `/mentoria` — `03` a `06`

Destaque menor, com os mesmos elementos do Início e:

- Botões: **Continuar: aula N** e **Minha lista**.
- Linha de fatos, com ícones: "8 semanas" · "N aulas · duração total" · "Encontros ao vivo às quintas, 20h" (frase configurável no painel) · "N participantes" · "Certificado ao final".

Abas (ficam presas abaixo da barra do topo ao rolar):

1. **Jornada** (`03-mentoria-jornada.png`): título "Oito semanas, uma por vez". À esquerda, a lista de semanas que abrem e fecham: número em círculo (visto verde quando concluída, cadeado quando bloqueada), "Semana N", título, "N aulas · duração · situação", anel de progresso e seta. Dentro, as aulas (número, título, duração; a aula atual destacada; aula bloqueada com cadeado). À direita: painel de progresso (anel, "N de N aulas concluídas", botão vermelho **Continuar de onde parei**), painel **Próximo encontro** (contador, título, data, botão de lembrete) e painel **Materiais da mentoria** (atalho para E-books).
2. **Encontros ao vivo** (`04`): "Próximos encontros da turma", em lista de agenda (caixa de data, tipo, contador, título, data e duração, botão de lembrete).
3. **E-books** (`05`): "Um e-book para cada aula", "N de N e-books liberados…", agrupados por semana, cada um com botão **Baixar**. Semanas bloqueadas aparecem em "Em breve".
4. **Comunidade** (`06`): campo para publicar ("Compartilhe um caso, uma dúvida ou uma vitória do plantão…", "Visível para a turma AAAA da mentoria", botão **Publicar**) e as publicações. Cada publicação tem avatar, autor, etiqueta de quem responde pela mentoria (ex.: "Mentora"), tempo, texto, curtir e "N respostas". As respostas abrem **logo abaixo da publicação**, com um campo para responder.

### 3. Cursos — `/cursos` — `07-cursos.png`

Título "Cursos" e a frase "Tudo o que está incluído na sua assinatura, organizado por área. Filtre para achar o que resolve o seu próximo plantão."

- Filtros em pílula por área: "Todas as áreas" e uma por área cadastrada.
- À direita, o botão **Filtro**, que abre um menu com um único grupo de opções: Novos, Em andamento, Concluídos, Mais assistidos. Com um filtro ativo, o botão mostra "Filtro: nome" e o menu ganha "Limpar filtro".
- Contagem ("N cursos…") e a grade de cartões (capa, nome, "N aulas · duração").
- Sem resultado: estado vazio "Nada por aqui ainda" e o botão "Limpar filtros".

### 4. Janela do tema — `/curso/ID` — `08-janela-do-curso.png`

Abre por cima da tela em que o aluno estava.

- Capa larga no topo com degradê para o fundo; sobre ela, área e subtítulo, título e os botões **Assistir** / **Continuar** / **Rever**, adicionar à lista e curtir.
- Nota (estrela), número de aulas e duração; linha de retomada com barra de progresso; descrição.
- **Aulas**: seletor de módulo e a lista de aulas com miniatura, título, duração e descrição curta.
- **E-books**: os quatro primeiros e um botão para mostrar todos.
- **Mais como este**: seis temas parecidos.

### 5. Trilhas — `/trilhas` e `/trilha/ID` — `09` e `10`

Lista de trilhas em cartões largos (capa, descrição, "N cursos · duração", barra de progresso e porcentagem). A página da trilha mostra o caminho de volta, sobretítulo "Trilha · N cursos · duração", título, descrição, anel de progresso e os temas **em ordem numerada**, cada um com capa, texto, progresso e botão (Começar, Continuar · aula N, Rever).

### 6. Ao vivo — `/ao-vivo` — `11-ao-vivo.png`

- Destaque do próximo encontro: contador, título, descrição, data e duração, contagem regressiva (dias, horas, min, seg), botão vermelho **Entrar na sala** e o botão de lembrete; à direita, a capa.
- **Agenda**: os demais encontros.
- **Novos conteúdos** ("Nos últimos 7 dias"): fileira com o que foi publicado ou atualizado (curso, aula, gravação, e-book), com selo "Novo/Nova" ou "Atualizado/Atualizada".

### 7. Minha lista — `/minha-lista` — `12`

Grade com o que o aluno guardou. Vazia: "Sua lista está vazia" e o botão "Explorar cursos".

### 8. Meu progresso — `/progresso` — `13`

Três cartões de número (Sequência de estudo, Tempo de estudo, Aulas concluídas), o gráfico "Minutos de estudo por dia" dos últimos 7 dias (o dia de hoje destacado) e a lista "Em andamento".

### 9. Certificado — `/certificados` — `14`

Existe **um único certificado**: o da mentoria, liberado só ao final dela. A tela mostra a prévia do certificado coberta por um véu com cadeado ("Disponível ao final da mentoria"), a etiqueta "Ainda não disponível", o texto explicativo e o botão "Ir para a mentoria". Temas e aulas não emitem certificado.

Certificado: papel branco, proporção `1.414 / 1`; nome da marca, "Certificado de conclusão", nome do aluno (Archivo), texto ("concluiu a mentoria **Plantão sem GPT**, turma AAAA.") e assinatura.

### 10. Conta e preferências — `/conta` — `15` a `17`

Menu lateral com três itens e o conteúdo ao lado:

1. **Perfil**: avatar grande, nome, e o formulário (Nome completo, Como quer ser chamada, E-mail, Área de atuação) com o botão vermelho **Salvar alterações**.
2. **Assinatura**: cartão "Plano ativo" com o nome da mentoria e a descrição do plano, e o painel **Incluído no seu plano**, com uma linha por item e um visto. **Não há botão de cancelar.**
3. **Notificações**: duas chaves de e-mail (Novas aulas liberadas, Encontros ao vivo).

### 11. Busca — `/busca` — `18` e `19`

Sem termo: título "Buscar", atalhos em pílula (as sugestões configuradas no painel) e "Mais procurados". Com termo: "N resultados", o termo entre aspas e duas seções, "Cursos e mentoria" e "Aulas". Sem resultado: "Nada encontrado para…".

### 12. Central de ajuda — `/ajuda` — `20`

Dois painéis lado a lado: **Abrir um chamado** (Assunto, "O que aconteceu?", botão vermelho **Enviar chamado**) e **Meus chamados** (cada chamado abre e fecha: número, assunto, resumo, etiqueta "Aberto" ou "Resolvido" e, dentro, a resposta da equipe). Ao enviar, aparece um aviso verde de confirmação, em tom neutro: "Chamado #N enviado".

### 13. Curso à venda — `/oferta/ID` — `21`

Caminho "‹ Início · Cursos à venda". Topo com etiqueta "Curso à venda" e a área, título, descrição, fatos, botão vermelho **Comprar por R$ …** e "Ver conteúdo"; à direita a capa com o selo "Conteúdo bloqueado". Depois: **O que você vai aprender** (lista com vistos), **Conteúdo do curso** (módulos que abrem e fecham, com as aulas bloqueadas) e, na lateral, o painel de compra (preço, "ou Nx de R$ …", **Ir para o checkout**, lista com "N aulas em vídeo", "E-book em cada aula", "N dias de garantia"). No fim, a fileira "Outros cursos à venda".

Os botões de compra abrem, em nova aba, o endereço de checkout cadastrado no painel.

### 14. Aula — `/aula/TEMA/AULA` — `22` a `24`

Duas colunas: à esquerda o conteúdo, à direita o painel **Aulas e módulos** (380 px; 320 px até 1199 px; embaixo do conteúdo até 1023 px).

- Caminho: "‹ nome do tema · módulo".
- **Vídeo** em 16:9. No protótipo é um reprodutor simulado; no produto é o vídeo do Vimeo incorporado.
- Cabeçalho: "Aula N de N", título e as ações: **Marcar como concluída** (vira "Concluída"), curtir, adicionar à lista, **Anterior** e **Próxima**.
- Abas: **Visão geral** ("Sobre esta aula"), **E-book** (o e-book da aula com **Baixar** e o link para todos) e **Quiz** (questões com quatro alternativas; depois de responder aparece certo ou errado e o comentário da resposta; ao final, "Você acertou N de N" e "Refazer quiz").
- Painel **Aulas e módulos**: mostra **a mentoria inteira**, agrupada por área, com a jornada e todos os temas, seus módulos e aulas, para navegar por tudo a partir de qualquer aula. Abre posicionado no tema e na aula atuais. O tema da aula aberta leva a etiqueta "Tema desta aula".
- Ao terminar o vídeo: cartão "A seguir em 8 s" com **Assistir agora** e **Cancelar**.

### 15. Página não encontrada

Estado vazio "Página não encontrada" e o botão "Voltar ao início".

## Regras de exibição que a implementação precisa manter

1. "Turma AAAA" mostra sempre o ano atual, lido do relógio.
2. O sininho só avisa em quatro situações (ver `06-comportamentos-e-regras.md`).
3. Selo "Novo" só nos temas marcados no painel.
4. Aula e semana bloqueadas mostram cadeado e a data de liberação.
5. Nenhuma tela da área de membros leva ao painel do produtor.
