# Decisões durante a execução da V1

Este registro acompanha a [entrega para QA](entrega-v1-qa.md). A autoridade é o plano oficial, complementado pelas confirmações do usuário. Não substitui decisões de negócio pendentes. Lista completa das decisões registradas durante a execução e dos limites da revisão, na ordem em que foram adotados.

## Confirmações e critérios adotados antes da revisão

| # | Decisão e motivo | Consequência / custo se estiver errada |
|---|---|---|
| 1 | Trabalhar na branch existente `feat/area-aluno-handoff`, no checkout autorizado; sem nova worktree. | A integração continua manual; nenhum merge ou push foi feito. |
| 2 | Período corrente editável com `AccessChange`, em vez de criar períodos sobrepostos para cada correção. Aprovado pelo usuário. | Uma nova política de múltiplos períodos exigirá outra decisão; a auditoria preserva os valores anteriores. |
| 3 | Limite de reativação acompanha o fim contratual corrigido. Aprovado. | Alterar o contrato passa por correção justificada, não pela reativação. |
| 4 | Data final exibida é inclusiva; armazenamento exclusivo. Encerramento antecipado identifica explicitamente o primeiro dia sem acesso. Aprovado. | Integrações futuras precisam converter datas; confundir as duas representações altera o acesso em um dia. |
| 5 | Contato de suporte próprio em `SiteSettings.support_email`. Aprovado. | Precisa ser preenchido na operação; não foi inventado endereço do cliente. |
| 6 | Permitir intervalo vazio somente no encerramento antecipado, com `ended_early` e tolerância zero. Aprovado após reportar conflito com a constraint anterior. | Criação normal mantém fim posterior ao início; a exceção não serve para planos novos. |
| 7 | Preservar períodos e âncoras demonstrativas existentes; não inventar início de matrícula histórica ausente. | Cadastros antigos sem âncora precisam de revisão antes de operar liberação mensal. |
| 8 | Sem duração cadastrada, consultar metadados do Vimeo no servidor para a regra de `ended`; se não confirmar a duração, manter conclusão manual. | Falha externa impede a conclusão automática nesse caso; o navegador não decide a duração confiável. |
| 9 | Ligar indicadores de quiz/final/encontro apenas quando os modelos correspondentes existirem, na ordem do plano. | Estados intermediários da implementação não anteciparam funcionalidades; a entrega final já reúne essas etapas. |
| 10 | Congelar perguntas, alternativas e correção por tentativa. | Alterar gabarito não recalcula notas antigas; uma política diferente precisaria preservar evidência histórica equivalente. |
| 11 | Registrar a qualificação C14 quando todos os requisitos, inclusive nome e CPF, estiverem completos durante o acesso. Sem inferência retroativa. | Quem só informa dados depois do término, sem qualificação prévia, não ganha emissão retroativa; certificados emitidos continuam válidos. |
| 12 | Importação de perguntas usa o título exato e recusa aulas homônimas; cursos presentes no CSV têm quizzes de aulas omitidas desativados. Final omitida e outros cursos ficam preservados. Tentativas reais bloqueiam substituição. | O arquivo precisa refletir a seleção desejada e resolver ambiguidades; não há escolha silenciosa entre aulas com mesmo título. |
| 13 | LinkedIn: link público estático e “Copiar dados para o LinkedIn”, aprovado após consulta à documentação oficial. | O aluno preenche o formulário; não há promessa de preenchimento automático. |
| 14 | Preservar links externos legados de material por redirecionamento autenticado; novos PDFs de curso ficam privados. | A plataforma autoriza a saída, mas a privacidade do destino externo depende desse destino. O proxy deve negar `/media/materials/`. |
| 15 | Comunidade só permite escrita com algum curso publicado e acesso ativo; antes do primeiro plano ou depois do término é somente leitura. | Não basta criar conta para publicar. Matrículas continuam limitando os tópicos de curso que podem ser lidos. |
| 16 | FAQ da demo descreve capacidades reais, sem prometer SMTP recebido, gravação em 24h ou alteração de snapshot de certificado. | O cliente precisa ajustar o conteúdo às políticas e prazos que assumir; não se inventaram compromissos operacionais. |
| 17 | Sala de encontro abre dez minutos antes e fecha ao fim da duração prevista; gravação após o fim. Links antigos do curso não viram agenda por inferência. | Um encontro que ultrapasse a duração exige correção pela equipe; não há liberação indefinida do link. |
| 18 | Fila guarda assunto/corpo e prazo; não reenvia avisos temporais vencidos nem fabrica publicação antiga. | Histórico de e-mail não equivale a entrega nem a backfill de eventos; SMTP e banco não oferecem confirmação atômica conjunta. |
| 19 | Catálogo/vendas antigos encaminham para login/membros/painel; dados preservados. Cadastro legado permanece sem link e sem conceder matrícula. | A rota direta de cadastro ainda existe; não substitui a operação manual da V1. As autorizações não dependem de esconder o link. |
| 20 | Autorização para todas as fatias removeu confirmações rotineiras e o gate entre fases, preservando o bloqueio externo da 1.16. | A autorização não permite inventar planilha, importar produção, enviar mensagens reais, instalar dependências ou implantar. |
| 21 | `Ticket` não tem curso; o indicador do curso conta chamados dos alunos matriculados e usa esse rótulo. | Um chamado técnico pode aparecer em ambos os cursos do mesmo aluno; não é métrica de chamado vinculado exclusivamente a um curso. |
| 22 | Editor aceita duração precisa; um novo PDF substitui o primeiro material preservando seu ID, mantém os extras e não apaga arquivo antigo do disco. | Pode acumular arquivos sem referência no armazenamento; limpeza exige política e confirmação próprias. Histórico de abertura mantém o ID. |
| 23 | Cadastro manual exige âncora do plano; importador legado fica sem link e não representa a migração V1. | A importação dos alunos continua pendente. Não usar o fluxo legado para simular datas originais. |
| 24 | E-mails de primeiro acesso/recuperação não guardam link/token no `EmailLog` nem entram em retentativa automática. Registro após a tentativa; janela de plano autenticada somente na mesma origem. | Reenviar acesso requer nova solicitação; protege credenciais e evita reaproveitar links expirados. |
| 25 | Configurações de avisos apresentam fila, logs e políticas existentes; sem controle global novo de silenciamento. Vencimento continua obrigatório. | Novos controles exigem especificação; preferências de aulas/encontros continuam por aluno. |
| 26 | Registrar visitas diárias reais a partir de agora, sem backfill por `last_login` ou duração do curso. | Relatórios não oferecem uma história que a base nunca coletou. Ausência de registro antigo não prova inatividade. |
| 27 | Relatório distingue acessos/horas na janela de tempo da situação acadêmica atual. | Não tratar o percentual atual como ganho de progresso dentro da janela escolhida. |
| 28 | Prévia permite contas ativas de aluno. Troca/saída encerra auditoria; aba abandonada mantém `ended_at` vazio até evento verificável. | Duração de uma prévia abandonada não é tempo confiável de uso. A prévia não muda dados do aluno. |

## Decisões da revisão final

| # | Decisão e motivo | Consequência / custo se estiver errada |
|---|---|---|
| 29 | Manter os seis achados importantes como correções obrigatórias; nenhum crítico. Excluir conteúdo considera também tópicos e abertura de material. | Para conteúdo usado, a operação é despublicar; não apagar vínculos históricos. |
| 30 | Chamados coletivos exigem pelo menos um acesso ativo, conforme a audiência expressa do plano. Próprios chamados e FAQ permanecem acessíveis sem matrícula ou após término. | Encerrados não leem chamados de terceiros nem votam. Se o cliente desejar outra audiência, precisa de decisão explícita de privacidade. |
| 31 | Mudança editorial de requisitos atualiza a qualificação no momento real da mudança, sem retroagir para acesso já encerrado. | Não resolve por adivinhação uma qualificação antiga que nunca foi registrada. |
| 32 | `Course.is_published` passa a controlar publicação efetiva dos conteúdos. Não publicar automaticamente cursos históricos. Planos e certificados continuam independentes. | Cursos antigos com flag falsa precisam de revisão editorial; dados e certificados não são apagados. |
| 33 | Fila revalida destinatário, preferência, plano, publicação/liberação e lembrete/evento antes de enviar. Avisos obsoletos ficam no histórico e saem da contagem vigente. | Uma mudança legítima pode suspender o envio antigo; novo evento precisa de referência própria. |
| 34 | Reserva de e-mail em atualização condicional curta; rede fora da transação. Lease de cinco minutos para recuperação após queda, timeout SMTP de 15s. | Uma queda após aceite e antes de `sent` pode duplicar na retentativa. SMTP não oferece exatamente uma entrega; investigar provedor antes de forçar envio. |
| 35 | Ocultar o voto na interface quando o servidor o recusa; a autorização continua no servidor. | Interface não é controle de segurança; POST direto também é validado. |
| 36 | Corrigir o achado C19, inicialmente textual, por exigência explícita do plano: não mandar fazer avaliação inexistente. | Nenhum ajuste menor conhecido desta revisão ficou adiado; o texto passa a acompanhar a presença da avaliação. |

## Itens que o revisor deixou fora de julgamento — limites mantidos

| # | Decisão | Consequência / custo se ignorada |
|---|---|---|
| 37 | Importação real e primeiro acesso em lote aguardam a planilha; não declarar a 1.16 implementada. | Prévia, duplicatas, datas originais e confirmação precisam ser tratadas na etapa pendente. |
| 38 | Infraestrutura, SMTP, domínio Vimeo, backups operacionais e avisos de implantação continuam externos. | QA local não significa produção pronta. O backup precisa de restauração operacional conferida. |
| 39 | Manter LinkedIn estático aprovado, sem tratar ausência de autofill como defeito. | Preenchimento manual segue necessário. |
| 40 | Conteúdo clínico, assinatura real e cronograma não foram inventados. | O médico/equipe precisam fornecer e validar esses dados. |
| 41 | Sem backfill de métricas inexistentes. | Estatística antiga não pode ser reconstruída por suposição. |
| 42 | Fidelidade visual conferida nos fluxos e larguras descritos, sem afirmar certificação completa. Reprodução Vimeo real recusada por direitos; C8 observado. | Falta reconferir reprodução/retomada/eventos com vídeo e domínio autorizados; Firefox e Opera não foram aprovados. |
| 43 | Concorrência SMTP/heartbeat reproduzida e testada em disco; sem alegar teste de carga abrangente. | Carga e infraestrutura reais podem revelar outros limites do SQLite que exigem medição. |
| 44 | Não ampliar escopo para pagamentos, renovação, rotas legadas não vinculadas ou funcionalidades fora da V1. | A base antiga não representa ativação de Asaas nem migração real pronta. |

Não há minor conhecido desta revisão deixado para depois. Permanecem as dependências externas explicitadas, especialmente 1.16 e reprodução com vídeo autorizado.
