# Painel do produtor — tela por tela

Identidade da GoMut. **Fundo branco, um tema só**, Verde GO `#04736b` nas ações, texto grafite `#202221`. Usa os mesmos componentes da área de membros, com as cores da GoMut.

- Protótipo: `prototipo/coprodutor.html` (telas em `prototipo/assets/js/admin.js`).
- Estilos: `tokens.css` e `app.css` (base comum) mais `admin.css` (cores e peças do painel).
- Imagens: `telas/painel/computador-1440/` e `telas/painel/celular-390/`.
- Os endereços abaixo são os do protótipo (depois de `coprodutor.html#/coprodutor`).

O painel é construído **por etapas**. O que ainda não foi definido está em `08-pendencias-e-perguntas.md` e não deve ser inventado.

## Estrutura comum

Três regiões fixas (imagem `02-meus-cursos.png`):

1. **Barra do topo** (altura `68px`, fundo branco, linha de `1px` embaixo): logotipo da GoMut (leva a "Meus cursos"), etiqueta verde **Coprodutor**; à direita, o botão pequeno de contorno **Visualizar como membro** (ícone `play`) e o menu da conta (avatar "CP" e seta).
   - Menu da conta (`36-menu-da-conta.png`): cabeçalho "Coprodutor / Mentoria Plantão sem GPT"; **Meus cursos**, **Configurações**, **Visualizar como membro**; separador; **Sair**.
2. **Painel lateral** (largura `248px`): as nove opções, nesta ordem — Criar curso, Meus cursos, Relatórios, Comunidade, Alunos, Certificados, Controle de acesso, Chamados, Configurações. Medidas e estados em `03-componentes/componentes.md`, seção 11.
   - A opção **Meus cursos** fica marcada em "Meus cursos" e em todas as telas de dentro de um curso (Básico, Visão geral, Conteúdo, Ao vivo). **Criar curso** fica marcada só na tela de criação.
3. **Conteúdo**: começa depois do painel lateral. Cada tela tem, de cima para baixo: caminho de volta (quando existe), cabeçalho (título em Archivo, frase de apoio e ações à direita), abas (quando existem) e o corpo.

Até 899 px o painel lateral fica recolhido e abre por um botão de menu na barra do topo (`telas/painel/celular-390/03-menu-lateral-aberto.png`).

No rodapé de cada tela do protótipo há a linha "GoMut · área do coprodutor · protótipo: as alterações ficam salvas só neste navegador." É texto do protótipo.

### Padrões que se repetem

- **Uma ação principal por tela**, em botão verde (`.btn--go`), no cabeçalho à direita. As demais ações em contorno.
- **Editar** abre uma janela com o formulário, "Cancelar" e "Salvar".
- **Excluir, despublicar, cancelar plano e restaurar** pedem confirmação numa janela com o botão em vermelho de perigo.
- Depois de salvar, um aviso rápido confirma ("Tema salvo", "Curso publicado", etc.).
- **Chave** (liga/desliga) salva na hora e mostra "Alteração salva".
- **Setas de ordem** (para cima e para baixo) mudam a posição do item na lista; a primeira seta de cima e a última de baixo ficam desligadas.

## Telas

### 1. Meus cursos — `/coprodutor` — `02-meus-cursos.png`

**É a primeira tela depois de entrar.**

- Título **Meus cursos**; frase "Gerencie e personalize seus cursos e conteúdos."; ação **Criar curso** (verde, ícone `plus`).
- Busca ("Buscar curso pelo nome") à esquerda e a contagem ("N cursos") à direita. A busca filtra enquanto se digita, ignorando acentos e maiúsculas. Sem resultado: "Nenhum curso encontrado com esse nome."
- Grade de cursos: 4 por linha (3 até 1439 px, 2 até 1099 px, 1 até 599 px). Cada cartão mostra, de cima para baixo: **capa** (a imagem enviada ou, sem ela, a capa gerada com o título), **situação** (etiqueta "Publicado" ou "Despublicado"), **nome do curso** e **"N aulas · N alunos"**.
- Clicar no cartão abre a página do curso, na aba Básico.
- **Não há** "Ordenar por" nem "Filtrar por".

### 2. Página do curso — cabeçalho e abas

Vale para as abas Básico e Visão geral (`03-curso-aba-basico.png`, `04-curso-visao-geral.png`).

- Caminho: "‹ Meus cursos".
- Título: o nome do curso. Embaixo: "Por [autor do curso]".
- À direita, nesta ordem: etiqueta de **situação**; **Visualizar curso** (contorno, ícone `play`); o **botão de publicação**; **Excluir curso** (contorno, ícone `trash`). Todos em tamanho pequeno.
- O botão de publicação muda com a situação:
  - Curso publicado → **Despublicar curso** (contorno). Pede confirmação: "O curso "X" deixa de aparecer para os alunos até ser publicado de novo. O conteúdo e o progresso dos alunos ficam guardados."
  - Curso despublicado → **Publicar curso** (verde). Publica na hora.
- **Visualizar curso** abre o curso na área de membros, com a faixa "Voltar à área do coprodutor".
- **Excluir curso** pede confirmação: "O curso "X" sai da sua lista de cursos e da área de membros, com todas as aulas. Esta ação não pode ser desfeita."
- Abas do curso: **Básico**, **Visão geral**, **Conteúdo**, **Ao vivo**. Um curso recém-criado tem só a aba Básico.

### 3. Aba Básico — `/coprodutor/cursos/ID` — `03-curso-aba-basico.png`

Um painel com duas colunas: a capa à esquerda e os campos à direita. Até 1099 px, uma coluna, na ordem título, descrição, autor, capa.

| Campo | Controle | Explicação mostrada embaixo | O que é |
|---|---|---|---|
| **Capa do curso** | Caixa tracejada com a capa; "Enviar imagem" / "Trocar imagem" e "Remover imagem" | "A imagem aparece na tela "Meus cursos", para identificar o curso. Tamanho recomendado: 1920 × 1080 px. Formatos: JPEG, JPG ou PNG." | Aparece no cartão do curso em "Meus cursos" |
| **Título do curso** | Campo de texto, até 60 caracteres, com contador | "É o nome do curso na área de membros." | É o título do destaque da área de membros. Lá a fonte e o estilo não mudam: o painel só altera o texto |
| **Descrição do curso** | Área de texto, até 220 caracteres, com contador | "Aparece logo abaixo do título, na área de membros." | É o texto abaixo do título no destaque |
| **Autor do curso** | Seleção | "Fica só no painel do produtor. Não aparece na área de membros." | Aparece só no painel ("Por …") |

Rodapé do painel, à direita: **Cancelar** (contorno; volta a "Meus cursos" sem salvar) e **Salvar alterações** (verde; **desligado até algo ser alterado**). Sem título, não salva: o cursor vai para o campo e aparece "Dê um título ao curso".

### 4. Criar curso — `/coprodutor/cursos/novo` — `14-criar-curso.png`

Título **Criar curso**; frase "Preencha os dados básicos do novo curso. Você pode alterá-los depois, na página do curso." Os **mesmos campos da aba Básico, em branco**, com a caixa da capa mostrando "Enviar imagem". Botões: **Cancelar** e **Criar curso**. O curso nasce **despublicado** e, ao ser criado, abre a página dele.

### 5. Aba Visão geral — `/coprodutor/visao` — `04-curso-visao-geral.png`

1. Frase "O que está no ar na mentoria X e o que precisa da sua atenção." e o botão **Cadastrar aula**.
2. Quatro cartões de número, cada um levando à sua tela: Alunos ativos, Aulas publicadas, Chamados abertos, Comentários sem resposta. 4 por linha; 2 por linha até 1279 px.
3. **Ferramentas de gestão** ("Tudo o que você configura para a área de membros"): três grupos de linhas de atalho, com ícone verde, nome, frase e seta; pendências aparecem como etiqueta pêssego.
   - **Conteúdo**: Aulas e módulos · Trilhas · Cursos à venda · Página inicial · Áreas
   - **Alunos e relacionamento**: Alunos · Ao vivo · Comunidade · Chamados
   - **Configurações**: Mentoria · Área de membros · Plano do aluno · Central de ajuda · Certificado · Avisos
4. Dois painéis: **Próximas liberações** (módulos e aulas com data marcada) e **Precisa de atenção** (chamados abertos, comentários sem resposta, aulas sem link do Vimeo).
5. **Próximos encontros ao vivo**.

### 6. Aba Conteúdo — `/coprodutor/conteudo…` — `05` a `12`

Caminho "‹ Meus cursos · nome do curso · Conteúdo". Título **Conteúdo**. Cinco abas internas:

**a) Aulas e módulos** (`05`): filtros em pílula por área ("Todas as áreas", "Mentoria" e as áreas), contagem e a grade de temas (capa, nome, "N módulos · N aulas", "N de N com vídeo"). Ação: **Novo tema**.

**b) Tela do tema** (`06`; janela de edição em `30`): caminho "‹ Conteúdo · área". Título do tema e descrição. Ações: **Visualizar como membro** e **Editar tema**. Uma linha de etiquetas resume o que o aluno vê (selo Novo, subtítulo, etiquetas, capa). Depois, os módulos que abrem e fecham (na jornada da mentoria chamam-se **Semana**):
- Cabeçalho do módulo: número, título, "N aulas · duração" e a etiqueta de liberação.
- Dentro: **Editar módulo**, **Excluir**; a lista de aulas (número, título, duração, etiquetas "Publicada/Rascunho", "Vimeo/Sem link do Vimeo", "E-book/Sem e-book", liberação; setas de ordem e **Editar**); e o campo "Nome da nova aula" com **Criar aula**.
- No fim: campo "Título do novo módulo" com **Criar módulo**, e **Excluir tema**.

Janela **Editar tema**: Título do tema · Subtítulo ("Opcional. Aparece ao lado da área, na janela do tema.") · Área · Descrição · Etiquetas ("Até três, separadas por vírgula…") · Imagem de capa · Selo "Novo" (caixa de marcar).

Janela **Editar módulo**: Título do módulo · Data de liberação (três opções: Imediata; Em uma data; Dias após a entrada do aluno).

**c) Cadastro da aula** (`07`): caminho "‹ Conteúdo · tema · módulo". Título da aula; frase "Rascunho: o aluno só vê a aula depois de publicada." ou "Aula publicada." Duas colunas (uma até 1279 px):
- Esquerda, três painéis: **Conteúdo da aula** (Título; Descrição, que aparece em "Sobre esta aula"; Link do vídeo no Vimeo, com mensagem "Link do Vimeo reconhecido." ou "Este link não parece ser de um vídeo do Vimeo."; Duração em minutos) · **E-book da aula** (um PDF por aula: enviar, substituir, remover) · **Quiz da aula** (cada questão: pergunta, quatro alternativas com a marcação da correta e o comentário da resposta; "Adicionar questão", "Remover").
- Direita: **Configurações de publicação** (Situação: Rascunho ou Publicada; Data de liberação; Módulo; **Salvar aula**; **Excluir aula**) e **Prévia do vídeo**.

**d) Trilhas** (`08`; janela em `31`): lista numerada (título, descrição, temas) com **Editar** e excluir. Ação: **Nova trilha**. Janela: Título · Descrição · Imagem de capa · **Temas da trilha, em ordem**, com setas de ordem, botão de tirar e a seleção "Adicionar tema…".

**e) Cursos à venda** (`09`; conteúdo em `10`; janela em `32`): cada linha tem miniatura, título, "área · preço · até Nx · N aulas", etiquetas ("Checkout cadastrado" ou "Sem link de checkout"; "Fora da vitrine"), a chave **Na vitrine**, **Aulas e módulos** e **Editar**. Ação: **Novo curso à venda**. Janela: Título do curso · Área · Descrição · O que você vai aprender (um item por linha) · Preço (R$) · Parcelas · Garantia (dias) · Link do checkout · Imagem de capa. Os módulos e as aulas do curso à venda usam a mesma tela dos temas.

**f) Página inicial** (`11`): três painéis e o botão **Salvar página inicial**.
- **Destaque da mentoria**: três linhas informativas (Frase de boas-vindas, Título do destaque, Turma). As duas primeiras apontam para a aba Básico.
- **Vitrine de cursos à venda**: Título e Texto de apoio.
- **Fileiras do Início**: uma linha por fileira, com nome, explicação, setas de ordem e a chave de mostrar. As fileiras "por área" têm também editar e excluir. Botão **Nova fileira** (Título da fileira; Áreas mostradas).

**g) Áreas** (`12`): lista das áreas do catálogo, com "N temas · N cursos à venda", **Renomear** e excluir (desligado enquanto a área tiver temas ou cursos). Ação: **Nova área**.

### 7. Aba Ao vivo — `/coprodutor/ao-vivo` — `13`; janela em `33`

Caminho "‹ Meus cursos · nome do curso · Ao vivo". Seções **Agenda** e **Realizados**. Cada encontro: caixa de data, tipo, contador ou "Realizado", título, "data · duração · sala cadastrada / sem link da sala · gravação publicada", **Editar** e excluir. Ação: **Novo encontro**. Janela: Título · Tipo (Encontro da mentoria; Aberto a todos; Aula ao vivo) · Data · Hora · Duração (min) · Descrição · Link da sala · Link da gravação no Vimeo · Imagem de capa.

### 8. Relatórios — `/coprodutor/relatorios` — `15`

**Tela provisória.** Mostra só o título e o estado vazio "Tela em construção". O conteúdo **ainda não foi definido**: não implementar nada além disso.

### 9. Comunidade — `/coprodutor/comunidade` — `16`

Contagem ("N publicações · N sem resposta da mentoria") e as publicações. Cada uma mostra autor, etiquetas ("Sem resposta", "Oculta para os alunos"), texto, as respostas, o campo "Responder como [nome]…" com **Responder**, e **Ocultar publicação** / **Mostrar de novo**. Ao responder, o aluno recebe o aviso "Seu comentário foi respondido".

### 10. Alunos — `/coprodutor/alunos` — `17`; janela em `35`

Filtros em pílula (Todos, Ativos, Cancelados), busca ("Buscar por nome ou e-mail") e a tabela: **Aluno** (avatar, nome, e-mail e último acesso) · **Entrada** · **Acesso até** · **Progresso** (barra e porcentagem) · **Plano** (etiqueta "Ativo" ou "Cancelado") · ações (**Configurar plano**; **Cancelar plano** ou **Reativar**). Ação: **Adicionar aluno** (Nome completo, E-mail, Data de entrada).

Janela **Plano de [nome]**: Situação do plano · Acesso até · Observação interna.

### 11. Certificados — `/coprodutor/certificados` — `18`

Painel **Certificado**: linha "Quando é liberado" (só ao final), Texto do certificado (aceita `{mentoria}` e `{ano}`), Assinatura, Linha abaixo da assinatura e **Salvar certificado**. Embaixo, **Como o aluno vai ver**, com a prévia do certificado nas cores da área de membros.

### 12. Controle de acesso — `/coprodutor/acesso` — `19`

**Tela provisória**, igual à de Relatórios. Conteúdo ainda não definido.

### 13. Chamados — `/coprodutor/chamados` — `20`

Abas **Abertos (N)** e **Resolvidos (N)**. Cada chamado abre e fecha: número, "assunto · aluno", resumo, etiqueta e, dentro, o texto, quando foi recebido e o campo de resposta com **Responder e resolver**. Chamado resolvido mostra a resposta dada.

### 14. Configurações — `/coprodutor/config` — `21` a `25`

Título **Configurações** e cinco abas:

1. **Mentoria** (`21`): linha "Nome da mentoria" (aponta para a aba Básico) · Duração (6, 12, 18 ou 24 meses) · Frase dos encontros ao vivo · Quem responde na comunidade · Etiqueta ao lado do nome · E-mail da equipe de suporte · linhas informativas "Turma" e "Semanas, aulas e participantes" (automáticos) · **Salvar mentoria**. Embaixo, "Dados de exemplo" com **Restaurar exemplo** (só do protótipo).
2. **Área de membros** (`22`): **Marca** (Nome da marca) e **Busca** (Sugestões de busca, até seis; "Mais procurados" é automático) · **Salvar**.
3. **Plano do aluno** (`23`): linha "Nome do plano" · Descrição do plano · **Salvar descrição** · painel **Incluído no plano** (itens com setas de ordem, editar e excluir; **Adicionar item**) · atalho para Alunos.
4. **Central de ajuda** (`24`): **Assuntos do chamado** (lista com setas de ordem e excluir; campo "Novo assunto" com **Adicionar assunto**) e atalhos para o e-mail do suporte e para Chamados.
5. **Avisos** (`25`): **Avisos ao aluno** (quatro chaves, cada uma com quando acontece e um exemplo) e **E-mails ao aluno** (duas chaves).

## Janelas de edição e de confirmação

Imagens `30` a `35`. Estrutura fixa: título em Archivo, formulário, rodapé com os botões à direita. O primeiro campo recebe o foco ao abrir. Fecham pelo "X", por "Cancelar" ou clicando fora.

- Edição: **Cancelar** (contorno) e **Salvar** / **Criar …** (verde).
- Confirmação de ação que tira algo do ar (`34-janela-confirmar-exclusao.png`): texto explicando a consequência e o botão da ação em vermelho de perigo, com o nome da ação ("Excluir curso", "Despublicar curso", "Cancelar plano").

## Textos dos avisos rápidos

"Você entrou como coprodutor" · "Alterações salvas" · "Alteração salva" · "Curso criado" · "Curso publicado" · "Curso despublicado" · "Curso excluído" · "Tema criado" · "Tema salvo" · "Tema excluído" · "Módulo criado" · "Módulo salvo" · "Módulo excluído" · "Aula criada como rascunho" · "Aula salva" · "Aula excluída" · "Trilha criada" · "Trilha salva" · "Trilha excluída" · "Encontro criado" · "Encontro salvo" · "Encontro excluído" · "Aluno adicionado" · "Plano salvo" · "Plano cancelado" · "Plano reativado" · "Resposta publicada na comunidade" · "Publicação ocultada" · "Publicação visível de novo" · "Resposta enviada ao aluno" · "Certificado salvo" · "Mentoria salva" · "Página inicial salva".
