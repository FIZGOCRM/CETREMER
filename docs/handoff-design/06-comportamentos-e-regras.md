# Comportamentos e regras

Regras de funcionamento que o design pressupõe. Onde o protótipo simula, a regra real está descrita aqui.

## 1. Acessos e permissões

1. Existem dois acessos separados, cada um com a sua tela de login (mesmo desenho): **produtor/coprodutor** (painel) e **membro** (área de membros).
2. O membro entra só na área de membros. Ele nunca vê link, botão ou tela do painel.
3. O produtor ou coprodutor tem, no painel, **Visualizar como membro** (barra do topo e menu da conta) e **Visualizar curso** (página do curso). Os dois abrem a área de membros com a faixa **Voltar à área do coprodutor**, que leva de volta à tela do painel em que ele estava.
4. A faixa e os dois botões existem só para quem tem permissão de produtor ou coprodutor.
5. No protótipo qualquer preenchimento entra. A autenticação e a regra de permissão reais são da programação.
6. A tela "Controle de acesso" do painel ainda não tem conteúdo definido (ver `08-pendencias-e-perguntas.md`).

## 2. Cursos e publicação

1. **Situação do curso**: Publicado ou Despublicado. Curso novo nasce despublicado.
2. Despublicar tira o curso da vista dos alunos, sem apagar conteúdo nem progresso. Pede confirmação.
3. Excluir curso pede confirmação e não pode ser desfeito.
4. O **título** e a **descrição** do curso, editados na aba Básico, são os textos do destaque da área de membros.
5. O **autor** do curso aparece só no painel.
6. A **capa** enviada aparece em "Meus cursos". Sem imagem, a capa é gerada com o título.
7. A busca de "Meus cursos" é pelo nome do curso, ignorando acentos e maiúsculas.

## 3. Temas, módulos e aulas

1. Hierarquia: **tema → módulo → aula**. Na jornada da mentoria o módulo se chama **Semana**.
2. **Situação da aula**: Rascunho (o aluno não vê) ou Publicada. Aula nova nasce em rascunho.
3. **Liberação**, definida no módulo e, se quiser, também na aula. Três opções: Imediata; Em uma data; Dias após a entrada do aluno. Quando módulo e aula têm data, **vale a maior das duas**.
4. Para o aluno, módulo ou aula ainda não liberados aparecem com cadeado e "Libera em DD/MM".
5. O vídeo fica no **Vimeo**. O produtor cola o link e o vídeo é incorporado na página da aula; o aluno assiste sem sair da área de membros. Formatos de link aceitos: `vimeo.com/ID`, `vimeo.com/ID/CHAVE` e `player.vimeo.com/video/ID`.
6. Cada aula tem **um e-book** (PDF), o único material de apoio.
7. O **quiz** é opcional. Cada questão tem quatro alternativas, uma correta, e um comentário mostrado depois que o aluno responde. Aula sem questões fica sem a aba Quiz.
8. A ordem das aulas dentro do módulo é definida no painel, pelas setas.
9. Excluir tema, módulo ou aula pede confirmação.
10. Um tema marcado com o selo **Novo** mostra o selo na capa, entra na fileira "Novidades" e no filtro "Novos".

## 4. Tela da aula (área de membros)

1. A aula é marcada como concluída quando o aluno chega a 90% do vídeo, ou pelo botão "Marcar como concluída". O botão também desmarca.
2. A posição em que o aluno parou é guardada, e a aula retoma dali.
3. Ao terminar, aparece "A seguir em 8 s" e a próxima aula liberada começa sozinha. O aluno pode cancelar.
4. O painel "Aulas e módulos" mostra toda a mentoria (jornada e todos os temas).
5. Os minutos de estudo só contam enquanto o vídeo está tocando.
6. Atalhos de teclado do reprodutor do protótipo (espaço ou K, setas, F, C) valem para o reprodutor simulado; com o Vimeo valem os do próprio Vimeo.

## 5. Encontros ao vivo

1. Tipos: Encontro da mentoria; Aberto a todos; Aula ao vivo.
2. O botão "Entrar na sala" abre o link cadastrado. Para o aluno, a sala abre 10 minutos antes do início.
3. O aluno pode ativar um lembrete em cada encontro ("Lembrar-me" vira "Lembrete ativo").
4. Contador: no dia mostra "Hoje"; antes, "Falta 1 dia" ou "Faltam N dias".
5. Depois do encontro, o produtor cola o link da gravação no Vimeo; a gravação entra em "Novos conteúdos".

## 6. Comunidade

1. Centraliza as publicações dos alunos e as respostas de quem responde pela mentoria. Não há perguntas dentro da aula.
2. As respostas abrem logo abaixo de cada publicação.
3. Quem responde pela mentoria aparece com o nome e a etiqueta configurados em Configurações › Mentoria.
4. O produtor pode **ocultar** uma publicação (ela some para os alunos) e mostrá-la de novo.
5. No painel, publicação de aluno sem resposta da mentoria leva a etiqueta "Sem resposta".

## 7. Central de ajuda e chamados

1. O aluno abre um chamado escolhendo um **assunto** (lista configurada no painel) e descrevendo o problema.
2. Ao enviar, a **equipe de suporte é avisada por e-mail** (endereço em Configurações › Mentoria). Para o aluno, a tela só confirma o recebimento, em tom neutro.
3. No painel, responder um chamado o marca como **Resolvido**. O aluno vê a resposta em "Meus chamados".
4. Situações do chamado: Aberto e Resolvido.

## 8. Avisos ao aluno

O sininho avisa em **quatro situações e em nenhuma outra**. Cada uma pode ser desligada no painel:

1. **Nova aula liberada** — quando uma aula é publicada ou chega a data de liberação.
2. **Encontro da mentoria** — no dia de um encontro ao vivo.
3. **Comentário respondido** — quando quem responde pela mentoria responde a uma publicação do aluno.
4. **Chamado respondido** — quando o suporte responde a um chamado do aluno.

E-mails ao aluno (dois, que o produtor liga ou desliga e o aluno também pode desligar): novas aulas liberadas; lembrete uma hora antes dos encontros com lembrete ativo.

## 9. Certificado

1. Existe **um único certificado**: o da mentoria.
2. É liberado só ao final da mentoria (duração configurada: 6, 12, 18 ou 24 meses a partir da entrada do aluno).
3. Temas e aulas não emitem certificado.
4. O texto aceita `{mentoria}` (nome da mentoria) e `{ano}` (ano da turma).

## 10. Alunos e plano

1. **Só o produtor ou coprodutor** configura e cancela o plano. O aluno não cancela por conta própria.
2. Situações do plano: Ativo e Cancelado. Cancelar pede confirmação; o progresso fica guardado para o caso de reativação.
3. "Acesso até" é calculado pela data de entrada mais a duração da mentoria, e pode ser alterado.
4. A observação interna do plano só a equipe vê.

## 11. O que é automático (sem configuração)

- **Turma AAAA**: sempre o ano atual, lido do relógio.
- **Continue de onde parou** e **Minha lista**: de cada aluno.
- **Top 10 no plantão esta semana** e **Mais procurados**: os temas mais assistidos.
- **Novos conteúdos** (página Ao vivo): o que foi publicado ou atualizado nos **últimos 7 dias**.
- **Nota** dos temas, número de aulas, duração total e número de participantes.
- **Progresso**, sequência de estudo e minutos de estudo.
- Capítulos e legendas do vídeo: vêm do Vimeo.

## 12. Formulários

1. Campos obrigatórios bloqueiam o salvamento e levam o cursor ao campo, com um aviso curto.
2. "Salvar alterações" da aba Básico fica desligado até haver alteração.
3. Ações que tiram algo do ar sempre pedem confirmação, com o botão em vermelho de perigo.
4. Depois de salvar, um aviso rápido confirma por alguns segundos.
5. Imagens de capa: JPEG, JPG ou PNG. Curso: 1920 × 1080 px. Tema, trilha, encontro e curso à venda: 1280 × 720 px.
