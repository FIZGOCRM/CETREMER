# Manual de operação — equipe GoMut

A implantação atual na KVM4 usa **Docker Compose**, sem cadastro na interface do Coolify. Acesso por túnel, comandos, persistência, backup, atualização e reversão estão no [manual da KVM4](operacao-kvm4.md). Produção e homologação têm contas e bases próprias; não usar as credenciais da demo local como referência para o servidor.

Use o painel com uma conta de administração autorizada. Os usuários aluno@gomut.example e admin@gomut.example são exclusivos da demonstração. Nenhum curso, vídeo ou CPF ilustrativo deve ser apresentado como cadastro real.

## Cursos, módulos e aulas

1. No painel, abra Cursos e Criar curso. Informe nome, descrição, capa e duração do plano em meses; salve.
2. Abra o conteúdo do curso e crie um módulo. Escolha Publicado ou Rascunho e o mês do plano em que libera: mês1 desde o início; mês2 um mês depois; assim por diante. A data usa o início original de cada aluno, não a data em que você cadastrou.
3. Cadastre a aula no módulo, com título, descrição, link do Vimeo e duração real. A plataforma incorpora o vídeo; não recebe upload de vídeo.
4. Envie o PDF no material da aula. Para um PDF do curso inteiro, abra Materiais do curso. Só envie PDF de verdade dentro do limite do formulário.
5. Publique quando pronto. Rascunhos somem para o aluno. Um módulo futuro aparece bloqueado até a data. Se mudar a liberação e afetar alunos ativos, confira o impacto antes de confirmar.
6. Conteúdo com progresso/tentativas deve ser despublicado, sem apagar histórico. Trocar vídeo ou duração zera a posição de retomada, conservando conclusões anteriores.

## Quizzes e avaliação final

1. No editor da aula, abra Quiz. Cadastre a pergunta com duas a cinco alternativas, marque a correta e preencha a justificativa de cada alternativa. Ordene e ative as perguntas.
2. O quiz libera após concluir a aula. Não conta para o certificado. A correção aparece por pergunta; refazer cria outra tentativa.
3. Na última seção do conteúdo do curso, abra Avaliação final. É opcional: se ativa, exige pelo menos70% e todas as aulas publicadas concluídas. O resultado usa a melhor nota.
4. Com tentativas, desative perguntas em vez de excluir. Alterações valem para tentativas futuras; resultados antigos conservam sua versão.

Para importar perguntas, prepare CSV UTF-8 com separador vírgula ou ponto e vírgula, cabeçalho:

    curso,tipo,aula,ordem,pergunta,alternativa_a,alternativa_b,alternativa_c,alternativa_d,correta,comentario,alternativa_e,justificativa_a,justificativa_b,justificativa_c,justificativa_d,justificativa_e

Informe o slug do curso e o título exato da aula. Use `aula` ou `final` em `tipo`. Para a avaliação final, deixe a coluna `aula` vazia. Em `correta`, informe uma letra de A a E entre as alternativas preenchidas. Preencha a justificativa de cada alternativa usada. O formato anterior, com as onze colunas até `comentario`, também é aceito e usa esse comentário para a correção. Primeiro rode:

    python manage.py import_quizzes ARQUIVO.csv --dry-run

Confira erros, quantidade de perguntas e quizzes que serão desativados. Nas aulas dos cursos presentes que não estão no CSV, o quiz fica inativo; outros cursos e avaliação final omitida são preservados. Quizzes com tentativas reais não podem ser substituídos. Só após conferir, execute sem --dry-run. O arquivo entra inteiro ou não entra nada. Não importar na base real sem autorização.

## Alunos e planos

1. Em Alunos, adicione/reaproveite o cadastro pelo e-mail e vincule ao curso correto. Um aluno com dois cursos possui uma matrícula/plano por curso.
2. Crie o plano com a data original de entrada. A data final exibida é o último dia com acesso; internamente o sistema guarda o dia seguinte como limite exclusivo. O mês atual e os módulos liberados seguem a data original.
3. Nunca invente data para completar um cadastro. Confirme com a pessoa responsável quando faltar informação.
4. A importação V1 da planilha real está pendente da entrega/validação do arquivo. O importador legado de cadastro não equivale à importação dos novos planos. Não aplique uma importação real pela confirmação antiga.
5. Para primeiro acesso, a equipe entrega um código temporário ou link de definição de senha pelo fluxo disponível no painel. Sem SMTP não declare e-mail enviado: entregue o código pelo canal combinado. Senhas não devem ser escolhidas pelo administrador nem copiadas para documentos.

A implementação final da importação/envio em lote da etapa1.16 só será validada após a planilha. Antes da operação real, pedir prévia com curso/início/fim/mês/liberações e confirmar linhas encerradas.

## Vencimentos e alterações de plano

1. Abra Vencimentos para ver os próximos60dias e o progresso dos alunos. O contador de e-mails mostra pendências vigentes; not_sent/failed não significam entrega.
2. Na matrícula, Criar plano define início e fim. Observação interna fica para a equipe.
3. Encerrar: escolha o primeiro dia SEM acesso e o motivo. Não acrescenta tolerância; progresso e certificado emitido são preservados.
4. Reativar: informe um limite permitido pelo fim contratual. Não é renovação.
5. Corrigir datas: informe datas corretas e motivo obrigatório. Toda alteração fica no histórico com responsável.
6. Aluno encerrado pode ler a Comunidade de seus cursos, abrir suporte e consultar certificado já emitido; aulas/quiz/avaliação e novas respostas ficam bloqueadas.

## Comunidade

1. Abra Novos ou Encaminhados; tópicos esperando equipe há mais24h aparecem destacados.
2. Encaminhar ao mentor inclui observação interna, invisível ao aluno.
3. Escreva a resposta e escolha a assinatura Mentor ou Equipe; o sistema conserva quem publicou de fato.
4. Marque a resposta que resolve a dúvida. O autor também pode marcar a resposta de outra pessoa.
5. Fixe quando útil. Para dados de paciente ou conteúdo impróprio, oculte tópico/resposta: o texto é conservado para auditoria e some para os alunos. Reabrir retira a solução e volta a fila.

## Chamados e FAQ

1. Abra Chamados, leia assunto, aparelho e descrição. Privado só aparece para dono/equipe; não copie dados privados para resposta pública de outro chamado.
2. Marque Em análise. Ao responder e Resolver, preencha uma orientação. Reabrir retorna a Aberto; a linha do tempo conserva alterações.
3. FAQ: criar/editar pergunta, categoria e resposta; alterar ordem e publicação. Revise promessas de prazo e disponibilidade antes de publicar.
4. Assuntos: criar/editar/ordenar e desativar quando não deve mais aparecer. Desativar preserva chamados antigos.

## Ao vivo

1. Abra Ao vivo e crie encontro com curso (ou vazio para todos os alunos ativos), tipo, título, início, duração, descrição e sala.
2. O aluno ativa Lembrar-me. A sala fica disponível de10min antes até o fim previsto. A gravação abre após o fim, se a equipe cadastrar o link.
3. Desative um encontro cancelado sem apagar os lembretes. Campos antigos de sala no Course ficam em reserva; os encontros novos usam LiveEvent com data/duração.
4. Não prometer gravação em24h sem alinhamento operacional: o sistema publica quando a equipe informar o link.

## Certificado

1. Aluno conclui aulas, avaliação final quando houver e preenche nome/CPF durante o acesso permitido. Quiz de aula não conta.
2. Conferir dados antes de emitir. O certificado preserva os dados da emissão; editar o perfil depois não altera o documento emitido.
3. Baixar PDF usa a impressão do navegador: Salvar como PDF, A4 paisagem. Validação pública pelo código.
4. LinkedIn: abrir Adicionar ao perfil e usar Copiar dados para preencher os campos. A plataforma não publica na conta LinkedIn do aluno.

## Quando algo não funciona

Vídeo: conferir link do Vimeo, privacidade do vídeo no domínio final, conexão e duração cadastrada. Sem referência de duração, não inventar percentuais; conclusão manual continua disponível. No chamado, informar curso/aula, aparelho e navegador, sem senha nem dados de paciente.

E-mail: conferir SMTP/remetente no SiteSettings e o recebimento real do teste. EmailLog sent indica aceite pelo backend, não garante caixa de entrada; conferir spam. not_sent indica falta de configuração/destinatário válido; failed indica falha. O comando diário retenta pendências vigentes. Lembretes passados não são disparados atrasados. Se houver queda no momento do envio, investigar antes de reenviar, pois SMTP não confirma envio e commit de banco numa transação única.

Antes de cada entrega a fila confere novamente destinatário, preferência, plano, publicação/liberação da aula ou módulo e, no encontro, situação, horário e lembrete ainda existente. Avisos obsoletos permanecem no histórico, sem envio, e deixam de contar na fila vigente. Não se confunde esse registro com uma entrega confirmada.

O envio automático reserva o registro por até cinco minutos, sem manter uma transação SQLite aberta durante o SMTP (timeout configurado: 15 segundos). Dois agendamentos concorrentes não enviam a mesma reserva. O painel mostra a reserva e seu horário; se o processo cair, outra execução pode retomá-la após cinco minutos. Existe uma janela inevitável de duplicação se o SMTP aceitar a mensagem e o processo cair antes de salvar `sent`; investigar os registros do provedor antes de forçar um reenvio. Os comandos de envio devem rodar fora de transações externas. Links de primeiro acesso e de recuperação não entram nessa retentativa.

### Prazo de acesso — ajuste de QA

Os avisos ao aluno começam somente nos três últimos dias efetivos de acesso, na central de notificações: 3 dias, 2 dias e último dia. O cálculo inclui a tolerância no término natural e não acrescenta tolerância no encerramento antecipado. Cada matrícula tem sua data, e executar o comando diário novamente não duplica o aviso. Os e-mails de vencimento seguem essa mesma janela, quando houver SMTP configurado.

O Início, o hero, os cartões de cursos e o progresso não mostram faixas nem contagem regressiva. As datas permanecem em Minha conta; “Acesso até” informa o último dia efetivo, incluindo tolerância. O link “Ver meu plano” na notificação leva diretamente a essa seção. O painel da equipe mantém os indicadores antecipados de gestão. Notificações antigas permanecem no histórico; e-mails pendentes cuja condição mudou não são enviados.

Na KVM4, o container `gomut-scheduler` já executa avisos, lembretes e backups. Não duplicar essas rotinas em cron ou Coolify. O aluno acessa <https://emergensimples.gomut.com.br> e a equipe <https://painel.emergensimples.gomut.com.br>; cada endereço tem sua sessão. A produção começou sem cursos e alunos reais; as contas fictícias locais não são contas de produção. Outros ambientes precisam de agendamento próprio. Seguir a [operação HTTPS](publicacao-https.md), o [manual da KVM4](operacao-kvm4.md), o [checklist de produção](producao-checklist.md) e a [restauração SQLite](operacao-sqlite.md).
