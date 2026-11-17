# Decisões de produto — V1

Fonte normativa: `docs/handoff v1 oficial/prompt-implementacao-gomut_3.md`.
Seções 1, 4 e 5 reproduzidas integralmente, sem alterações de regra. Prevalecem sobre os handoffs antigos. Nenhuma etapa futura foi implementada neste registro.

## 1. O que é a V1

**Objetivo.** O médico cliente da Fisgo publica seus cursos e aulas na plataforma. Os alunos assistem, têm o progresso salvo e são guiados em todas as telas, sem ficar com dúvida sobre o que fazer em seguida.

**Quem usa**

| Pessoa | O que faz |
|---|---|
| Aluno | Entra, vê no Início onde parou, um resumo do progresso e os cursos que tem. Assiste às aulas (retoma de onde parou), faz os quizzes, a avaliação final e emite o certificado. Usa a Comunidade para dúvidas sobre o curso e o Suporte para problemas técnicos. |
| Equipe Fisgo | Uma integrante da Fisgo opera o painel em nome do médico, como se fosse da equipe dele: cadastra cursos, módulos, aulas, quizzes e alunos; controla as datas de plano; encaminha as dúvidas da Comunidade ao médico e publica as respostas; responde os chamados. |
| Médico | **Não acessa o painel na V1.** Responde às dúvidas fora da plataforma, e a equipe Fisgo publica a resposta em nome dele. |

**O fluxo do aluno, de ponta a ponta**
1. Login.
2. Início: o hero mostra o curso e o ponto onde ele parou, junto com um resumo do progresso, os cursos dele e a comunidade.
3. Entra no curso: começa na primeira aula ou continua na aula em que estava.
4. Assiste. O progresso fica salvo no ponto exato do vídeo.
5. Se a aula tem quiz: antes de começar ele já sabe que o quiz existe. Ao terminar a aula fica claro que ela acabou e que o quiz está liberado.
6. Próxima aula, e assim por diante.
7. Fim do curso: avaliação final e certificado.
8. Em qualquer momento: Comunidade para dúvidas sobre o conteúdo e Suporte para problemas técnicos.

**Fora da V1:** gateway de pagamento, compra pelo site e matrícula automática. Os alunos são controlados manualmente pela equipe Fisgo. Veja a lista completa em "Fora da V1", no fim.

**Detalhes visuais.** Pequenas diferenças de acabamento em relação ao protótipo podem ser corrigidas depois. O que não pode faltar é o comportamento: regras, dados salvos e as indicações ao aluno em cada passo.

---

## 4. Decisões de produto

Registre esta seção em docs/decisoes-produto.md na etapa 0. Ela vale acima de qualquer documento antigo do handoff, inclusive docs/handoff-design/06-comportamentos-e-regras.md.

### Operação

| Tema | Decisão |
|---|---|
| Clientes | Instalação dedicada à Emergensimples. Sem multi-tenant. Marca, nome do mentor e textos da escola vêm da configuração global (SiteSettings). |
| Quem opera | Só a equipe Fisgo. Um único perfil de administrador (os papéis ADMIN e CREATOR atuais), com acesso a tudo. Sem papéis de suporte ou editor na V1. O médico não tem login no painel. |
| Pagamento | Fora da V1. O checkout continua desativado. Sem página de venda nem vitrine. |

### Plano e acesso do aluno

| Tema | Decisão |
|---|---|
| Plano | Cada matrícula (aluno + curso) tem um **período único**: data de início e data de fim. A duração padrão é a do curso (campo novo Course.plan_months, padrão 12). O fim padrão é o início + plan_months. |
| Alunos atuais | Entram com a **data original de início** do plano (vem na planilha). Quem está no 3º mês segue exatamente o mesmo cronograma, sem recomeçar. |
| Dois cursos | Cada curso tem o seu próprio plano, com datas independentes. |
| Fim do plano | O curso **termina** ao fim do período. Não existe renovação na V1. |
| Tolerância | Vale a tolerância que já existe no projeto (3 dias, grace_days) só para o fim natural do plano. Durante a tolerância, o aluno vê "Seu acesso termina em X dias". Depois disso, as aulas bloqueiam. |
| Encerramento antecipado | A equipe pode encerrar o acesso numa data escolhida (hoje ou outra), informando o motivo (Desistência, Inadimplência, Pedido do aluno, Outro, com texto livre). Sem tolerância. O histórico fica guardado e é possível reativar depois. |
| Correção de datas | A equipe pode corrigir o início ou o fim de um plano registrado errado, com motivo obrigatório. Toda mudança fica registrada. |
| Avisos de vencimento | Aos 30, 15 e 7 dias do fim natural do plano: no painel (lista de vencimentos e destaque na tabela de alunos), na área do aluno (faixa no Início e em Minha conta) e por e-mail ao aluno. |
| Aluno com plano encerrado | As aulas, quizzes e avaliação ficam bloqueados, com uma tela que explica o motivo e mostra o contato de suporte. Continuam disponíveis: Início (com o curso como "Encerrado"), Meu progresso, Certificados, Minha conta, Suporte (pode abrir chamado) e a Comunidade apenas para leitura (não pode publicar nem responder). |
| Certificado depois do fim | Se o aluno cumpriu todos os requisitos antes do fim do plano, pode emitir o certificado depois. Se não cumpriu, não pode. |

### Conteúdo e liberação

| Tema | Decisão |
|---|---|
| Estrutura | Curso → Módulo → Aula. "Mentoria" no protótipo é a configuração da escola, não um modelo novo. |
| Publicação | Módulo e aula podem estar em rascunho ou publicados. Rascunho nunca aparece para o aluno. |
| Liberação | **Por módulo, configurável:** cada módulo tem "Libera no mês N do plano" (campo release_month, padrão 1 = já no início). A equipe define ao cadastrar. Não há liberação por aula nem por data fixa na V1. |
| Cálculo do mês | O mês N libera na data de início do plano + (N − 1) meses de calendário, no mesmo dia do mês. Se o dia não existir no mês (ex.: 31), vale o último dia daquele mês. |
| Módulo ainda não liberado | Aparece para o aluno com cadeado e "Libera em dd/mm/aaaa", com as aulas listadas, mas sem abrir. |

### Aula, quiz e avaliação

| Tema | Decisão |
|---|---|
| Progresso | Salvo no ponto exato do vídeo. Ao voltar, o vídeo continua de onde parou. |
| Conclusão | Automática com 90% da duração efetivamente assistida, além do botão manual "Marcar como concluída". |
| Quiz da aula | **Opcional por aula.** Só algumas aulas terão quiz (o conteúdo real define quais). Aulas sem quiz não mostram nada sobre quiz. |
| Indicação do quiz | Antes e durante a aula, o aluno vê que aquela aula tem quiz: na lista de aulas do curso, na lateral do player, num aviso no início da aula e nas etapas abaixo do vídeo. |
| Liberação do quiz | Abre quando a aula é concluída. O quiz é orientação, não bloqueio: o aluno pode pular e seguir para a próxima aula. |
| Nota do quiz | Não conta para o certificado. Tentativas ilimitadas, guarda a melhor nota e a última tentativa. |
| Fim da aula | Indicação clara de "Aula concluída". Se houver quiz, também "Quiz liberado", com "Fazer o quiz agora" e "Pular para a próxima aula". |
| Avaliação final | Opcional por curso (só existe se o curso tiver perguntas cadastradas). Libera quando todas as aulas publicadas do curso estão concluídas. Tentativas ilimitadas, sem intervalo, vale a melhor nota. Aprovação com 70% ou mais. |
| Certificado | Exige todas as aulas publicadas concluídas + avaliação final ≥ 70% (se o curso tiver avaliação final) + nome completo + CPF válido. Os certificados já emitidos continuam válidos. O PDF segue pela impressão do navegador, com layout novo. O botão "Adicionar ao LinkedIn" usa o link público de "adicionar ao perfil". |
| Anotações | Sempre privadas do aluno. |

### Comunidade e suporte

| Tema | Decisão |
|---|---|
| Comunidade | Para dúvidas sobre o conteúdo do curso. O aluno publica tópicos; os outros alunos respondem; a equipe Fisgo publica a resposta do médico. |
| Fluxo da equipe | Tópico novo → a equipe marca "Encaminhado ao mentor" (com observação interna) → recebe a resposta do médico fora da plataforma → publica. Esse status é interno: só o painel vê. |
| Em nome de quem | Ao publicar, a equipe escolhe a assinatura: "[nome do mentor] · [etiqueta]" ou "[nome da equipe]". O sistema guarda internamente quem publicou de fato. Nome do mentor, etiqueta e nome da equipe ficam no SiteSettings. |
| Solução | O autor do tópico pode marcar "Resolveu minha dúvida" numa resposta. A equipe pode marcar ou desmarcar a solução, fixar e ocultar. |
| Suporte | Para problemas técnicos e de uso da plataforma. Tem FAQ e chamados com status Aberto → Em análise → Resolvido. |
| Chamados públicos | Visíveis para todos os alunos ativos, mostrando só o primeiro nome e a inicial do sobrenome. O aluno pode marcar o chamado como privado; aí só ele e a equipe veem. |

### Critérios técnicos

- **Tempo de estudo.**
  - O player envia um "pulso" a cada 15 s enquanto o vídeo está tocando e a aba está visível.
  - O servidor credita no máximo o tempo real decorrido desde o último pulso **daquele aluno** (em qualquer aula ou aparelho), até 20 s por pulso. Assim, dois aparelhos ao mesmo tempo não contam em dobro.
  - A velocidade de reprodução não multiplica o crédito.
  - Vídeo pausado ou aba oculta não credita nada.
- **Sequência de dias.** Um dia conta quando o aluno tem pelo menos 60 s creditados nesse dia, no fuso do projeto.
- **Regra dos 90%.**
  - A aula conclui sozinha quando o tempo creditado nela chega a 90% de duration_seconds.
  - Sem duração cadastrada, vale o evento ended do Vimeo.
  - O evento ended conclui a aula só se houver pelo menos 50% de tempo creditado.
- **E-books.** A biblioteca abre o PDF no visualizador do próprio navegador, por um endpoint autenticado, e marca o arquivo como "aberto". O leitor página a página do protótipo fica fora da V1.

---

## 5. Causas e efeitos (comportamento esperado em situações-limite)

Cada linha vira teste ou conferência na etapa indicada.

| # | Situação | Comportamento esperado | Etapa |
|---|---|---|---|
| C1 | Aluno importado com início há 2 meses e 10 dias | Está no mês 3. Módulos com release_month 1, 2 e 3 abertos; o 4 mostra "Libera em" + a data certa. | 1.2, 1.16 |
| C2 | Aluno com os 2 cursos e inícios diferentes | Cada curso calcula mês, liberação, avisos e fim pelo próprio plano. | 1.1, 1.2 |
| C3 | Plano começa dia 31 | O mês 2 libera no último dia do mês seguinte (ex.: 28 ou 29/02). | 1.2 |
| C4 | Equipe publica uma aula num módulo já liberado | A aula aparece na hora para quem tem o módulo liberado. O aluno recebe a notificação "Nova aula liberada". | 1.2, 1.14 |
| C5 | Equipe muda o release_month de um módulo para mais tarde | Alunos que ainda não chegaram ao mês veem a nova data. Aulas já concluídas continuam concluídas e contam no progresso. Quem já tinha acesso **perde** o acesso às aulas não concluídas até a nova data: o painel avisa antes de salvar quantos alunos serão afetados e pede confirmação. | 1.2 |
| C6 | Equipe tenta excluir uma aula com progresso de alunos | Não exclui. Oferece despublicar. | 1.2 |
| C7 | Equipe troca o vídeo ou a duração de uma aula já concluída por alunos | Quem concluiu continua com a aula concluída. A posição salva é zerada para todos naquela aula. | 1.3 |
| C8 | Vídeo não carrega (Vimeo fora ou domínio não liberado) | O player mostra "Não foi possível carregar o vídeo. Tente novamente ou abra um chamado no Suporte." O botão "Marcar como concluída" continua disponível. | 1.3 |
| C9 | Aluno assiste em dois aparelhos ao mesmo tempo | O crédito de tempo não dobra (limite por aluno). A posição salva é a do último pulso recebido. | 1.3 |
| C10 | Plano vence com o aluno no meio de uma aula | O próximo pulso responde "acesso encerrado". O player pausa e mostra a tela de plano encerrado. O tempo assistido até ali fica salvo. | 1.1, 1.3 |
| C11 | Aluno no período de tolerância | Assiste normalmente e vê a faixa "Seu acesso termina em X dias". | 1.1 |
| C12 | Encerramento antecipado com data de hoje | Bloqueia hoje, sem tolerância. Fica registrado com motivo e responsável. | 1.1 |
| C13 | Reativação depois de um encerramento antecipado | Volta a ter acesso até a data escolhida pela equipe, que não pode passar do fim original do plano. O progresso anterior continua. | 1.1 |
| C14 | Aluno cumpriu os requisitos do certificado e o plano acabou antes de ele emitir | Pode emitir o certificado depois do fim. | 1.9 |
| C15 | Plano acaba com o aluno sem ter concluído | Não emite. Vê o progresso, mas não as aulas. | 1.1, 1.9 |
| C16 | Equipe edita uma pergunta de quiz que já tem tentativas | A edição vale para as próximas tentativas. Notas antigas não são recalculadas. | 1.6 |
| C17 | Equipe tenta excluir um quiz ou pergunta com tentativas | Não exclui. Oferece desativar; quiz desativado some para o aluno. | 1.6 |
| C18 | Aula sem quiz | Nenhuma indicação de quiz em nenhuma tela. As etapas abaixo do vídeo mostram só Assistir → Próxima aula. | 1.5 |
| C19 | Curso sem avaliação final | O certificado exige só aulas, nome e CPF. Nenhuma tela fala em avaliação final para esse curso. | 1.7 |
| C20 | Aluno desmarca uma aula concluída | O progresso diminui. O quiz já feito continua com a nota. Se ele já tinha certificado emitido, o certificado continua válido. | 1.3, 1.9 |
| C21 | Aluno publica dado de paciente na Comunidade | A equipe oculta o tópico ou a resposta. O texto fica guardado para auditoria e some para os alunos. | 1.11 |
| C22 | Tópico de um curso que o aluno não tem | Não aparece para ele. Um link direto responde "sem acesso". | 1.11 |
| C23 | Aluno com plano encerrado abre a Comunidade | Lê, mas não publica nem responde. A tela explica o motivo. | 1.11 |
| C24 | Tópico sem resposta da equipe há mais de 24 h | Aparece destacado no painel. | 1.11 |
| C25 | Chamado privado | Não aparece na lista pública nem na busca de outros alunos. | 1.12 |
| C26 | Planilha com e-mail que já existe na base | A prévia mostra a linha como "aluno existente": acrescenta a matrícula, não cria outro usuário. | 1.16 |
| C27 | Planilha com CPF inválido ou vazio | Importa sem CPF e avisa na prévia. O aluno informa o CPF ao emitir o certificado. | 1.16 |
| C28 | Planilha com plano já terminado | A prévia destaca a linha como "plano encerrado". Importa só se a equipe confirmar essas linhas. | 1.16 |
| C29 | E-mail automático sem SMTP configurado | Não quebra nada. Fica registrado como "não enviado", e o painel mostra quantos e-mails aguardam envio. | 1.14 |
| C30 | O comando diário de avisos roda duas vezes no mesmo dia | Não envia o mesmo aviso duas vezes (cada envio fica registrado). | 1.14 |

---
