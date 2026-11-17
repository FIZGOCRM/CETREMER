# Plano de implementação V1: Emergensimples na GoMut

Você vai implementar a V1 da área de membros da Emergensimples, em etapas, partindo do código atual (veja docs/diagnostico-projeto-gomut.md) e do protótipo navegável (docs/handoff-design/prototipo-v2/index.html).

**Como trabalhar**
- Faça uma etapa por vez, na ordem deste documento.
- Ao fim de cada etapa, pare e me envie o relatório descrito em "Como entregar cada etapa".
- Só comece a próxima etapa depois da minha confirmação.

---

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

## 2. Ordem das etapas

Siga exatamente esta sequência:

- **0** Preparação
- **Fase 1, V1 funcionando de ponta a ponta:**
  - 1.1 Plano do aluno: datas, encerramento e vencimentos
  - 1.2 Publicação e liberação mensal de módulos
  - 1.3 Player: retomada, tempo assistido e conclusão aos 90%
  - 1.4 Meu progresso e resumo no Início
  - 1.5 Página da aula: etapas, indicação do quiz, fim da aula e anotações
  - 1.6 Quiz da aula
  - 1.7 Avaliação final e regra do certificado
  - 1.8 Importação das perguntas
  - 1.9 Certificados
  - 1.10 Materiais e e-books
  - 1.11 Comunidade
  - 1.12 Suporte: FAQ e chamados
  - 1.13 Ao vivo
  - 1.14 Notificações e e-mails automáticos
  - 1.15 Navegação, busca, Minha conta, login e telas antigas
  - 1.16 Importação dos alunos e envio do primeiro acesso (bloqueada até a planilha chegar)
  - 1.17 Preparação para produção e manual de operação
- **Fase 2, painel no visual GoMut:** 2.1 a 2.10, na ordem.

**Regra da fase 1 para o painel.** Toda etapa da fase 1 que cria algo que a equipe precisa operar (plano, liberação, quiz, comunidade, chamados, FAQ, encontros) já entrega a tela de gestão no painel atual, com o layout antigo. A V1 precisa ser operável desde já; o visual GoMut do painel vem na fase 2, sem refazer regras.

Se a 1.16 ainda estiver bloqueada quando chegar a vez dela, faça a 1.17 e volte à 1.16 quando a planilha chegar.

---

## 3. Regras para todo o trabalho

1. **Stack fixa.** Django 4.2, templates, CSS e JS próprios, SQLite. Sem React, Vue, HTMX, DRF, Celery ou build de frontend.
2. **Nenhuma dependência nova** (pip, CDN ou arquivo vendorizado) sem me perguntar antes.
3. **Banco.**
   - Trabalhe só na base de demonstração (DJANGO_DATABASE_PATH apontando para .venv/gomut-demo.sqlite3, com GOMUT_DEMO_MODE).
   - Nunca rode seed.py.
   - Dados de demonstração novos entram no comando prepare_demo, que continua não destrutivo e idempotente.
4. **Protótipo é referência, não código.**
   - O protótipo-v2 mostra layout, textos e comportamento.
   - O estado dele (objetos em memória, localStorage, login simulado, a tela "Escolha o painel", o botão "Roteiro da demo" e os 3 alunos de demonstração) **não** vai para o produto.
   - Todo estado real fica no banco, com as regras no servidor.
5. **Organização do código** (o padrão que já existe): modelos em models.py; regras em services.py; consultas em selectors.py; checagem de acesso em access.py; views finas; forms para entrada de dados.
6. **Acesso sempre no servidor.**
   - Toda view e todo endpoint do aluno validam login, papel, matrícula, access_decision e a liberação do módulo.
   - Nunca confie em dado enviado pelo navegador para conceder progresso, nota ou certificado.
7. **Gabarito nunca no HTML.** A resposta certa só sai do servidor depois que o aluno responde.
8. **Visual.**
   - A área do aluno usa base_gomut.html + base_membros.html e os CSS de static/css/gomut/.
   - Não misture com cetremer.css.
   - Respeite docs/handoff-design/01-regras-inviolaveis.md: fontes e SVG do handoff, nada substituído por algo parecido.
9. **Textos.** Em pt-BR, iguais aos do protótipo-v2, salvo indicação neste documento. Datas e "hoje" sempre no fuso TIME_ZONE do projeto.
10. **Endpoints JSON.** POST com CSRF, respostas idempotentes quando fizer sentido, erros com mensagem clara em português.
11. **Testes.** Cada etapa entra com testes (modelo, serviço, permissão e view). A suíte inteira precisa continuar passando.
12. **Git.**
    - Um commit por etapa na branch feat/area-aluno-handoff, com prefixos feat:, fix: e docs:.
    - Não faça push nem merge sem eu pedir.
13. **Sem suposições.**
    - Este documento é a única fonte de decisão.
    - Se uma informação não está aqui, no diagnóstico ou no protótipo-v2, ela não existe: pare e pergunte.
    - Não preencha lacunas com "o mais comum" nem com o que outro projeto faria.
14. **Conflitos.** Se algo deste plano conflitar com uma regra que já existe no código (por exemplo, a recusa de sobreposição de períodos), pare e me mostre o conflito com as opções. Não escolha sozinho.
15. **Entradas pendentes.**
    - Uma etapa que depende de algo da seção "Entradas pendentes" é feita até onde não depende, usando os dados de demonstração.
    - O relatório diz exatamente o que ficou esperando.
    - Nunca invente o conteúdo que falta.
16. **Ordem linear.** Não adiante partes de etapas futuras, mesmo que pareçam rápidas.
17. **Nunca apagar o que tem histórico.** Aula, quiz, pergunta, matrícula ou período com progresso, tentativa ou histórico ligado a eles não é apagado: é despublicado, desativado ou encerrado. A interface explica isso quando a equipe tenta excluir.

### Definição de pronto (vale para toda etapa)

Uma etapa só está pronta quando:

- Os critérios da etapa foram atendidos e conferidos na tela com um usuário de demonstração.
- As migrações rodam do zero numa base vazia e na base de demonstração.
- A suíte inteira passa, com testes novos para o que a etapa criou.
- Nada que já funcionava quebrou, no aluno ou no painel.
- Os textos estão em pt-BR.
- A tela funciona na largura de celular (390 px) e de computador (1440 px).
- Os casos da seção "Causas e efeitos" que se aplicam à etapa estão cobertos por teste ou conferidos na tela, e o relatório diz quais.
- O relatório foi enviado e o commit foi feito.

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

## 6. Entradas pendentes (chegam depois)

Estas informações ainda não existem. Nada deve ser inventado no lugar delas.

| Entrada | Usada em | Até chegar |
|---|---|---|
| Planilha dos ~36 alunos: dados cadastrais, curso e data de início do plano | 1.16 | A etapa fica bloqueada. As outras usam os alunos de demonstração. |
| Perguntas reais dos quizzes e das avaliações finais (e quais aulas têm quiz) | 1.6, 1.7, 1.8 | Código e importação prontos. A demonstração usa as perguntas ilustrativas do protótipo-v2, marcadas como demonstração. |
| Nome do médico como deve aparecer para os alunos, etiqueta (ex.: "Mentor") e nome da equipe | 1.11 | Use os textos de demonstração "Mentor da Emergensimples", "Mentor" e "Equipe Emergensimples", editáveis no SiteSettings. |
| Release_month de cada módulo dos 2 cursos | 1.2 | Todos os módulos com release_month = 1 na demonstração. |
| Dados de produção: servidor, e-mail (SMTP), domínio liberado no Vimeo, disco, backups | 1.17 | Nada é configurado para produção. Nenhum valor de produção vai para o código. |

### Formatos esperados

Prepare o projeto para receber exatamente estes formatos. Se algum não servir para o código existente, avise na etapa em que perceber, sem trocar o formato por conta própria.

**Planilha de alunos.**
- Parta do modelo static/modelos/importar-alunos.csv.
- Na etapa 0, me envie as colunas atuais e o que cada uma aceita.
- Se o modelo não tiver estas informações, proponha as colunas que faltam para eu aprovar: nome completo, e-mail, CPF (opcional), telefone (opcional), slug do curso, data de início do plano (dd/mm/aaaa) e data de fim (opcional; vazio = início + plan_months).
- Aluno com 2 cursos ocupa 2 linhas, com o mesmo e-mail.

**Perguntas dos quizzes.** CSV em UTF-8 com cabeçalho, uma linha por pergunta:

| Coluna | Conteúdo |
|---|---|
| curso | slug do curso |
| tipo | aula ou final |
| aula | título exato da aula (vazio quando tipo = final) |
| ordem | número da pergunta dentro do quiz |
| pergunta | enunciado |
| alternativa_a … alternativa_d | 4 alternativas (C e D podem ficar vazias, mas no mínimo 2) |
| correta | A, B, C ou D |
| comentario | explicação mostrada depois da resposta |

Aula que não aparece no CSV fica sem quiz.

---

## 7. Como entregar cada etapa

Ao terminar cada etapa, me envie:

1. O que foi feito, em até 10 linhas.
2. A lista de arquivos criados e alterados.
3. As migrações criadas, com os campos e modelos novos.
4. O resultado da suíte de testes: quantos testes, falhas e quais testes novos.
5. Os casos da seção "Causas e efeitos" cobertos, e como.
6. Como eu confiro na tela, passo a passo: com qual usuário de demonstração, no aluno e no painel.
7. Pendências ou desvios do plano, com o motivo.
8. O hash do commit.

---

## Etapa 0. Preparação

1. Faça commit do estado atual (as 93 entradas do git status), separando código, documentos e arquivos que não devem ser versionados. Me mostre a lista antes de commitar qualquer coisa que pareça base de dados, upload ou segredo.
2. Crie docs/handoff-design/prototipo-v2/ e coloque lá o index.html que vou te entregar. Ele substitui o protótipo antigo como referência. Mantenha o antigo, com uma nota no README da pasta.
3. Crie docs/decisoes-produto.md com as seções 1, 4 e 5 deste documento.
4. Rode a suíte e registre a linha de base (hoje são 138 testes).
5. Me envie as colunas atuais do modelo de importação de alunos e o que cada uma aceita, com a proposta das colunas que faltam (ver "Formatos esperados").
6. Confira se as regras atuais de AccessPeriod (fim exclusivo, tolerância, recusa de sobreposição) permitem o que a etapa 1.1 pede: encerrar, reativar e corrigir datas registrando histórico. Me reporte qualquer conflito antes da etapa 1.1.
7. Liste os identificadores de tela do protótipo-v2 que vamos usar como referência:
   - Aluno: viewHome, heroHTML, kpis, weekChart, nextSteps, courseProgress, viewProgress, viewCourse, viewLesson, lessonSteps, quizTab, quizModal, viewQuiz, viewCerts, viewLive, viewEbooks, viewCom, viewTopic, viewNewTopic, viewSupport, viewTicket, viewNewTicket, header, tabbar, searchHTML, viewAccount, viewLogin.
   - Painel: gCursos, gCriar, gCurso, gBasico, gVisao, gConteudo, gModules, gAula, gVivo, gAlunos, gCom, gCerts, gChamados, gRel, gCfg, gModalHTML.

Pare e me reporte.

---

# FASE 1. V1 funcionando de ponta a ponta

## Etapa 1.1. Plano do aluno: datas, encerramento e vencimentos

**Objetivo:** cada matrícula tem um plano com início e fim claros. A equipe controla as datas manualmente, e aluno e equipe veem os vencimentos com antecedência.

**Dados**
- Course.plan_months (inteiro, padrão 12).
- Enrollment.plan_started_on (data): âncora do cronograma e da liberação mensal. Nas matrículas existentes, preencha com o starts_on do período mais antigo.
- O acesso continua definido por AccessPeriod. Na V1, cada matrícula tem um período (início, fim exclusivo, grace_days = 3 no fim natural).
- Novo modelo AccessChange: enrollment, action (created | ended_early | reactivated | corrected), old_starts_on, old_ends_on, new_starts_on, new_ends_on, reason_code, reason_text, actor, created_at.
- Enrollment.admin_note (texto interno).

**Serviços**
- create_plan(enrollment, starts_on, ends_on=None): ends_on vazio = starts_on + plan_months.
- end_plan_early(enrollment, end_date, reason): grace_days = 0.
- reactivate_plan(enrollment, until_date): until_date não pode passar do fim original.
- correct_plan_dates(enrollment, new_start, new_end, reason).
- Todos gravam AccessChange e usam a mesma checagem de acesso que já existe (access_decision). Se algum conflitar com a recusa de sobreposição, siga o que combinamos na etapa 0.
- plan_status(enrollment) devolve: active | ending_soon(dias) | grace(dias) | ended(data, motivo). ending_soon vale a partir de 30 dias do fim natural.

**Área do aluno**
- **Início e card do curso:** selo "Termina em X dias" (a partir de 30 dias) e, depois do fim, "Encerrado".
- **Faixa no Início:** "Seu acesso a [curso] termina em dd/mm/aaaa. Conclua as aulas e a avaliação final para emitir seu certificado." Aparece aos 30, 15 e 7 dias e durante a tolerância. O aluno pode fechar a faixa, mas ela volta no marco seguinte.
- **Minha conta:** card "Meu plano" por curso, com início, fim, mês atual do plano ("Mês 3 de 12") e situação.
- **Tela de plano encerrado:** aparece ao tentar abrir uma aula, quiz ou avaliação. Mostra o motivo (fim do período ou encerramento) e o contato de suporte (e-mail do SiteSettings e botão "Abrir chamado"). Siga a decisão "Aluno com plano encerrado".

**Painel (layout atual)**
- **Tabela de alunos:** colunas de início, fim e situação do plano por curso, destaque visual para quem vence em até 30 dias e filtro "Vence em 30 dias".
- **Página "Vencimentos":** lista dos próximos 60 dias, ordenada por data, com curso, dias restantes e progresso do aluno (para a equipe saber quem precisa de incentivo para concluir).
- **Na matrícula:** Criar plano, Encerrar (data + motivo), Reativar (data limite), Corrigir datas (motivo obrigatório), Observação interna e Histórico de alterações.

**Casos:** C2, C10 (parte do acesso), C11, C12, C13, C15.

## Etapa 1.2. Publicação e liberação mensal de módulos

**Dados**
- Module: status (draft | published, padrão published) e release_month (inteiro ≥ 1, padrão 1).
- Lesson: status (draft | published, padrão published).

**Regras**
- Serviço único module_release_date(enrollment, module) = plan_started_on + (release_month − 1) meses, pela regra de dia descrita em "Cálculo do mês".
- Serviço lesson_availability(enrollment, lesson) devolve: available | draft | scheduled(data) | plan_ended.
- Rascunho nunca aparece para o aluno.
- Contagens de progresso, próxima aula, avaliação final e certificado consideram só aulas publicadas. Aulas de módulos ainda não liberados contam no total (o aluno vê que existem), mas não podem ser abertas nem concluídas.
- "Continuar" e "Próxima aula" nunca apontam para aula não liberada. Se a próxima estiver bloqueada, o botão vira "Próximo módulo libera em dd/mm".

**Área do aluno**
- Na página do curso e na lateral do player, módulo não liberado mostra cadeado, "Libera em dd/mm/aaaa" e as aulas sem link.
- Acesso direto pela URL de uma aula não liberada mostra a mesma explicação, sem o player.

**Painel (layout atual)**
- Campos status e "Libera no mês N do plano" no form de módulo; status no form de aula.
- Ao mudar release_month, mostre antes de salvar quantos alunos ativos serão afetados (caso C5) e peça confirmação.
- Excluir aula ou módulo com progresso é recusado, com a opção de despublicar (C6).

**Casos:** C1, C2, C3, C4 (parte da liberação), C5, C6.

## Etapa 1.3. Player: retomada, tempo assistido e conclusão aos 90%

**Dados**
- Progress ganha: last_position_seconds, watched_seconds (tempo creditado total na aula) e last_heartbeat_at.
- Novo StudyDay: student, date (data local), seconds, com unicidade student + date.
- Novo ActivityEvent: student, kind, lesson e course opcionais, payload JSON pequeno, created_at. Os tipos começam com lesson_completed, quiz_finished, final_passed e certificate_issued; as próximas etapas acrescentam os seus.
- StudentProfile.last_heartbeat_at, para o limite de crédito por aluno (C9).

**Endpoint**
- POST /courses/lesson/<id>/heartbeat/ com {position, playing}.
- O servidor valida o acesso a cada pulso (C10 → responde {access: "ended"}).
- Credita o tempo pelas regras dos "Critérios técnicos" e atualiza a posição, StudyDay e watched_seconds.
- Ao chegar a 90%, conclui a aula pelo serviço de conclusão que já existe, registra ActivityEvent e responde {completed: true, has_quiz: bool}.

**Player (static/js/aluno.js)**
- Pulso de 15 s com getCurrentTime e timeupdate. Envie também no pause e no visibilitychange/pagehide, por navigator.sendBeacon.
- Ao abrir a aula, chame setCurrentTime(last_position_seconds), exceto se a aula estiver concluída e a posição estiver nos últimos 5%.
- Mantenha o ended → complete, com a regra dos 50%.
- O botão manual continua, e desmarcar diminui o progresso (C20).
- Em caso de erro do player, mostre a mensagem do C8.
- Ao trocar o vídeo ou a duração da aula no painel, zere last_position_seconds daquela aula para todos (C7).

**Casos:** C7, C8, C9, C10, C20.

## Etapa 1.4. Meu progresso e resumo no Início

**Referências:** kpis, weekChart, nextSteps, courseProgress e viewProgress.

**Dados:** só selectors novos sobre Progress, StudyDay, ActivityEvent e os planos. Nada é calculado a partir de completed_at ou da duração cadastrada.

**Itens da tela**
- Aulas concluídas: X de Y, com quantas faltam.
- Estudo nos últimos 7 dias, comparado aos 7 dias anteriores.
- Sequência de dias.
- Certificados emitidos e prontos para emitir.
- Gráfico de minutos por dia (7 dias).
- Mapa de constância de 12 semanas.
- Atividade recente (últimos 6 eventos).
- Progresso por curso: anel, chips Aulas / Avaliação / Certificado / Quizzes e "Mês N de 12 · termina em dd/mm".

**Próximos passos (no máximo 4, nesta ordem de prioridade)**
1. Quiz liberado e ainda não feito.
2. Continuar ou próxima aula liberada.
3. Começar curso não iniciado.
4. Fazer a avaliação final.
5. Emitir certificado.
6. Próximo módulo libera em dd/mm (quando não houver aula liberada pendente).
7. Próximo encontro ao vivo (depois da etapa 1.13).

**Estado vazio:** aluno sem nenhuma aula assistida vê "Assista sua primeira aula para ver seu ritmo aqui."

**Desempenho:** evite N+1. As consultas de progresso por curso devem ser agregadas.

## Etapa 1.5. Página da aula: etapas, indicação do quiz, fim da aula e anotações

**Referências:** viewLesson e lessonSteps.

**Indicação do quiz, antes de assistir** (só em aulas com quiz ativo, C18)
- Lista de aulas do curso: "quiz ao concluir".
- Lateral do player: selo "Quiz".
- Ao abrir a aula: um aviso curto acima das etapas, "Esta aula tem um quiz de N perguntas, liberado quando você concluir a aula.", que o aluno pode dispensar.

**Etapas abaixo do vídeo**
- Assistir (percentual ao vivo e "conclui com 90% assistido") → Faça o quiz (cadeado até concluir) → Próxima aula.
- Sem quiz, a etapa do meio some.
- A etapa atual fica destacada e as feitas ganham check.

**Fim da aula**
- Ao concluir, aviso "Aula concluída" (mais "Quiz liberado!" se houver quiz).
- No fim do vídeo:
  - Com quiz liberado e não feito: o vídeo para e mostra "Aula concluída · quiz liberado", com "Fazer o quiz agora" e "Pular para a próxima aula". Sem contagem automática.
  - Sem quiz pendente: contagem de 5 s para a próxima aula liberada, com Cancelar.
  - Se a próxima aula estiver bloqueada: "Próximo módulo libera em dd/mm", sem contagem.

**Abas:** Sobre a aula, Quiz (só em aulas com quiz), Material, Anotações.

**Anotações**
- Novo LessonNote: student, lesson, position_seconds, text, created_at.
- Criar, listar e apagar só as próprias.
- Clicar no minuto leva o vídeo àquele ponto.

**"Tirar dúvida com a turma":** abre o novo tópico já com curso e aula preenchidos. Depende da etapa 1.11; até lá, deixe o link pronto.

## Etapa 1.6. Quiz da aula

**Referências:** quizTab e quizModal (tela de abertura, indicador Pergunta 1…N → Resultado, barra de progresso, correção e comentário por pergunta, resultado com revisão).

**Dados**
- Quiz: kind (lesson | final), lesson (FK única, só para kind=lesson), course (FK), is_active, is_demo.
- QuizQuestion: quiz, order, text, explanation, is_active.
- QuizChoice: question, order, text, is_correct. Exatamente uma correta por pergunta, com validação.
- QuizAttempt: student, quiz, started_at, finished_at, correct, total, score_pct, answers (JSON {question_id: choice_id}).

**Endpoints**
- POST start: só funciona com a aula concluída e o plano ativo.
- POST answer: recebe {question_id, choice_id} e devolve {correct, correct_choice_id, explanation}. Responder de novo a mesma pergunta na mesma tentativa é recusado.
- POST finish: calcula a nota, registra ActivityEvent e devolve o resumo.
- O HTML leva perguntas e alternativas sem is_correct.

**Telas**
- Aba Quiz com três estados: bloqueado (barra "x% do caminho para liberar"), liberado ("Começar quiz") e feito (resultado da última tentativa, melhor nota, Refazer).
- Selos na lateral e na página do curso: "quiz liberado" ou "Q a/b".

**Painel (layout atual)**
- Editor do quiz na edição da aula: adicionar pergunta, de 2 a 4 alternativas, marcar a correta, comentário, ordenar, desativar.
- Excluir pergunta ou quiz com tentativas é recusado (oferece desativar) (C16, C17).

**Demo:** o prepare_demo cria 2 perguntas em algumas aulas (não em todas, para mostrar os dois casos) a partir do banco QB do protótipo-v2, com is_demo = true.

**Casos:** C16, C17, C18.

## Etapa 1.7. Avaliação final e regra do certificado

**Referência:** viewQuiz.

- Usa Quiz com kind=final, um por curso, opcional (C19).
- Libera quando todas as aulas publicadas estão concluídas e o plano está ativo.
- A correção aparece **depois** de enviar todas as respostas: nota, quais acertou e a alternativa certa.
- Tentativas ilimitadas; vale a melhor nota.
- Atualize o serviço de emissão do certificado (courses/services.py) com as regras da seção de decisões, incluindo o caso C14. Certificados já emitidos não são revalidados.
- Status do curso para o aluno: new | progress | waiting_release (tudo liberado já concluído, há módulos futuros) | exam | done | ended. Esse status alimenta o hero, os cards e os próximos passos.

**Painel (layout atual):** editor da avaliação final na página de aulas do curso, igual ao editor do quiz da aula.

**Casos:** C14, C19.

## Etapa 1.8. Importação das perguntas

**Objetivo:** carregar as perguntas reais pelo CSV de "Formatos esperados".

- Management command import_quizzes <arquivo.csv> com --dry-run.
- O --dry-run valida tudo e mostra um resumo por curso e aula (perguntas e erros por linha) sem gravar nada.
- **Erros que recusam o arquivo inteiro:** curso ou aula não encontrados, menos de 2 alternativas, correta fora das alternativas preenchidas, ordem repetida no mesmo quiz.
- Sem erros e sem --dry-run, grava tudo numa transação: ou entra o arquivo inteiro, ou nada.
- Perguntas de demonstração (is_demo) do mesmo quiz são substituídas.
- Um quiz com tentativas de alunos reais não é sobrescrito: o comando para e lista esses quizzes.
- Testes com um CSV de exemplo em courses/tests/fixtures/.
- Documente o uso em docs/manual-operacao.md (criado na 1.17; por enquanto, deixe o texto no relatório).

## Etapa 1.9. Certificados

**Referência:** viewCerts.

- Lista por curso com os requisitos marcados: aulas X/Y, avaliação % (se houver), nome e CPF.
- O formulário de nome e CPF fica na própria página (validação que já existe).
- Visualização do certificado no layout do protótipo, com código de validação e "Copiar código".
- "Baixar PDF" abre a impressão do navegador, com CSS @media print para sair só o certificado em A4 paisagem.
- "Adicionar ao LinkedIn": link público de adicionar certificado ao perfil, com nome do certificado, organização (SiteSettings.school_name), ano e mês de emissão, código e URL de verificação. Confira o formato do link na documentação atual do LinkedIn antes de montar.
- A página privada mostra só os 2 últimos dígitos do CPF.

**Casos:** C14, C15, C20.

## Etapa 1.10. Materiais e e-books

**Referências:** viewEbooks e a aba Material da aula.

**Dados**
- Novo CourseMaterial (course, title, file, order), para material do curso que não é de uma aula.
- Novo MaterialOpen (student, material_kind, material_id, opened_at), para o estado "Já abri".

**Endpoint**
- GET /materiais/<kind>/<id>/ valida matrícula, plano ativo e liberação do módulo, e devolve o arquivo com FileResponse.
- Os templates deixam de apontar direto para /media/.
- Documente como bloquear /media/materials/ na produção.

**Tela /dashboard/ebooks/**
- E-books das aulas e materiais do curso, agrupados por curso.
- Filtros: Todos, Das aulas, Do curso, Já abri, e por curso.
- Busca.
- Capa no estilo do protótipo.
- Atalho "Ir para a aula".
- Material de aula em rascunho ou de módulo não liberado não aparece.

**Painel (layout atual):** upload, troca e remoção de CourseMaterial na edição do curso.

## Etapa 1.11. Comunidade

**Referências:** viewCom, viewTopic, viewNewTopic, a aba "Dúvidas da turma" do curso e o bloco "Na comunidade" do Início.

**Dados**
- CommunityPost ganha:
  - is_pinned.
  - solution (FK opcional para Comment).
  - solution_marked_by (author | team).
  - solved_at.
  - team_status (new | forwarded | answered), team_note e forwarded_at. Só o painel vê esses campos.
- Comment ganha display_as (self | mentor | team). O author continua sendo quem publicou de fato.
- Novo Helpful: user + post ou comment, com unicidade por usuário.
- SiteSettings ganha mentor_display_name, mentor_label e team_display_name (valores de demonstração em "Entradas pendentes").

**Regras**
- O aluno só vê e publica em tópicos de cursos que tem, ou do tema "Geral" (C22).
- Plano encerrado em todos os cursos: só leitura (C23).
- Resposta com display_as = mentor aparece como "[mentor_display_name] · [mentor_label]"; com display_as = team, como "[team_display_name]".
- Ao publicar uma resposta como mentor ou equipe, team_status vira answered.
- O autor marca "Resolveu minha dúvida" numa resposta de outra pessoa.
- A equipe marca e desmarca solução, fixa, oculta (C21) e encaminha.

**Área do aluno**
- **Lista:** filtros Todos, Sem resposta, Resolvidos, Meus tópicos e por curso; busca; fixados primeiro; contagem de respostas e de "útil".
- **Tópico:** solução destacada no topo das respostas, botão "Útil", campo de resposta e lateral "Mais deste curso".
- **Novo tópico:** curso, aula opcional (filtrada pelo curso), título com no mínimo 8 caracteres, texto com no mínimo 15 e o aviso para não publicar dados de paciente.
- **Bloco no Início:** os 4 tópicos mais recentes dos cursos do aluno.

**Painel (layout atual)**
- Lista com filtros Novos, Encaminhados, Respondidos, Resolvidos, Ocultos e por curso, destacando os que esperam há mais de 24 h (C24).
- Em cada tópico:
  - "Encaminhar ao mentor", com observação interna.
  - Responder escolhendo "Assinar como: [mentor] / [equipe]".
  - Marcar solução, fixar, ocultar e reabrir.

**Casos:** C21, C22, C23, C24.

## Etapa 1.12. Suporte: FAQ e chamados

**Referências:** viewSupport, viewTicket e viewNewTicket.

**Dados**
- FaqItem: category, question, answer, order, is_published.
- SupportSubject: name, order, is_active.
- Ticket:
  - number (sequencial, exibido como #1024), student.
  - subject (FK), title, body.
  - device (Computador | Celular | Tablet).
  - is_private.
  - status (open | in_review | resolved), answer.
  - created_at, resolved_at.
- TicketEvent: ticket, status, actor, note, created_at. Toda troca de status grava um evento.
- TicketVote ("também tenho esse problema"), com unicidade por usuário.

**Área do aluno**
- Busca única nas perguntas frequentes e nos chamados.
- Abas: Perguntas frequentes, Chamados da turma, Meus chamados.
- FAQ com "Isso respondeu?" e "Não, abrir chamado".
- Chamado com linha do tempo Aberto → Em análise → Resolvido.
- Exibição pública com nome reduzido; chamado privado fica fora da lista e da busca (C25).
- Aluno com plano encerrado pode abrir chamado.
- Sem anexo na V1.

**Painel (layout atual)**
- Chamados em andamento e resolvidos: marcar em análise, responder e resolver, reabrir.
- CRUD de FaqItem e de SupportSubject.

**Demo:** o prepare_demo cria as perguntas frequentes e os assuntos do protótipo-v2.

**Casos:** C25.

## Etapa 1.13. Ao vivo

**Referência:** viewLive.

- Novo LiveEvent: course (opcional; vazio = aberto a todos os alunos ativos), title, kind (mentoria | aberto | aula_ao_vivo), starts_at, duration_minutes, description, room_url, recording_url.
- Novo LiveReminder: student, event, com unicidade.
- Agenda com os próximos encontros, botão "Lembrar-me" e gravações dos encontros passados.
- O link da sala aparece a partir de 10 minutos antes do início.
- Os campos antigos de Course (live_meet_url etc.) continuam como reserva. Documente a migração.
- **Painel (layout atual):** CRUD de encontros.

## Etapa 1.14. Notificações e e-mails automáticos

**Dados**
- Notification: user, kind, title, body, url, read_at, created_at.
- EmailLog: user, kind, reference (ex.: id da matrícula + marco), status (sent | not_sent | failed), created_at. Unicidade em kind + reference, para nunca enviar o mesmo aviso duas vezes (C30).
- Preferências do aluno (StudentProfile ou modelo próprio): e-mail de novas aulas e de encontros ao vivo. **O e-mail de vencimento não pode ser desligado.**

**Quando cria notificação**
- A equipe responde um tópico do aluno.
- Uma resposta do aluno é marcada como solução.
- Um chamado do aluno muda de status ou é respondido.
- Uma aula nova é publicada num módulo liberado para ele (C4).
- Um módulo é liberado para ele pelo mês do plano.
- Marcos de vencimento: 30, 15 e 7 dias.
- Um encontro com lembrete ativo começa hoje.

**Comando diário** run_daily_notifications:
- Libera os avisos de módulo do dia.
- Envia os e-mails de vencimento de 30, 15 e 7 dias.
- Envia os e-mails de novas aulas para quem quer recebê-los.
- Envia os lembretes de encontro (1 hora antes; por isso, esta parte roda a cada 15 minutos ou como comando separado, como você achar mais simples e me explicar).
- É idempotente.
- Usa o SiteEmailBackend que já existe. Sem SMTP, registra not_sent (C29).

**Interface**
- Sininho no header com contador, lista e "Marcar como lidas". Substitui a tela pendente.
- Painel: contador "E-mails aguardando envio" na página de Vencimentos.

**Casos:** C4, C29, C30.

## Etapa 1.15. Navegação, busca, Minha conta, login e telas antigas

**Header**
- Itens centralizados: Início, Meus cursos, Meu progresso, Comunidade, E-books, Ao vivo.
- O item atual fica numa pílula de vidro, com traço vermelho embaixo.
- À direita: busca, Suporte (?), sininho e avatar.

**Menu do avatar:** Meu progresso, Certificados, Comunidade, E-books, Suporte, Minha conta, Sair.

**Barra inferior no celular:** Início, Cursos, Comunidade, Progresso, Suporte.

**Busca:** procura nas aulas dos cursos do aluno (título e módulo), mostrando o cadeado nas não liberadas.

**Minha conta:** dados pessoais, Meu plano (etapa 1.1), preferências de e-mail e troca de senha.

**Telas antigas:** migre para base_membros as que ainda usam base_aluno (conta, comunidade, certificados, ao vivo). Ao fim desta etapa, nenhuma tela do aluno carrega cetremer.css.

**Marca:** troque "Emergensimples" escrito nos templates por SiteSettings.school_name. O logo novo (símbolo de pulso com check e o nome em dois pesos, igual ao protótipo-v2) fica como SVG em static/gomut/marca/.

**Login do aluno (viewLogin do protótipo-v2)**
- Duas metades, com divisão no meio.
- À esquerda, painel vermelho profundo com quadriculado de ECG, a marca e o bloco de texto.
- À direita, painel carvão com o formulário.
- Topos alinhados.
- Sem a caixa "Primeiro acesso".
- "Esqueci minha senha" usa o fluxo real.
- O link de primeiro acesso continua disponível na própria tela, discreto, para quem recebeu o código.

## Etapa 1.16. Importação dos alunos e envio do primeiro acesso

**Bloqueada até a planilha chegar.**

- Use a importação em lote que já existe (users/importing.py), com prévia, e as colunas aprovadas na etapa 0.
- Para cada linha, cria ou reaproveita o usuário (C26), cria a matrícula e o plano com a data original de início (create_plan da etapa 1.1).
- **A prévia mostra, por linha:**
  - Novo ou existente.
  - Curso.
  - Início, fim e mês atual do plano.
  - Módulos que já entram liberados.
  - CPF ausente ou inválido (C27).
  - Plano já encerrado (C28), que só importa com confirmação.
- Não rode na base de produção sem a minha confirmação explícita. Me entregue o relatório da prévia antes de confirmar.
- **Envio do primeiro acesso**
  - Ação no painel para enviar o link de primeiro acesso por e-mail a um aluno ou a todos os importados que ainda não definiram senha, usando o fluxo que já existe.
  - Registra a data de envio.
  - Sem SMTP, a ação mostra os códigos para entrega por fora, como já acontece hoje.

**Casos:** C1, C26, C27, C28.

## Etapa 1.17. Preparação para produção e manual de operação

**docs/producao-checklist.md**, com campos em branco para eu preencher:

- Servidor, sistema, servidor de aplicação e proxy (o projeto hoje só tem wsgi.py).
- Caminho do disco persistente para o SQLite e para media/.
- Rotina de backup (o comando que já existe) e o agendamento.
- Variáveis de ambiente: só os **nomes**, nunca valores.
- SMTP (configurado no SiteSettings) e remetente.
- Domínio do site e domínio liberado no Vimeo.
- Bloqueio de acesso direto a /media/materials/.
- Agendamentos: run_daily_notifications, lembretes de encontro e backup.
- DEBUG desligado, ALLOWED_HOSTS e CSRF_TRUSTED_ORIGINS.

Rode `python manage.py check --deploy` e liste os avisos no relatório, sem corrigir o que depender de dado de produção.

**docs/manual-operacao.md**, para a equipe Fisgo, em linguagem simples e passo a passo:

- Cadastrar curso, módulo (com o mês de liberação) e aula (com Vimeo e PDF).
- Publicar e despublicar.
- Cadastrar quiz e avaliação final, e importar perguntas.
- Cadastrar aluno, importar a planilha e enviar o primeiro acesso.
- Acompanhar vencimentos; encerrar, reativar e corrigir planos.
- Responder a Comunidade (encaminhar ao mentor, publicar assinando como mentor ou equipe, marcar solução, ocultar).
- Responder chamados e manter a FAQ.
- Cadastrar encontros ao vivo.
- O que fazer quando o vídeo não carrega e quando os e-mails não saem.

---

# FASE 2. Painel no visual GoMut

Comece só depois de eu fechar a fase 1. As regras e os serviços já existem; aqui muda a interface.

**Regras da fase 2**
- Crie uma base nova de painel (base_painel_gomut.html) com o CSS GoMut claro dos tokens do handoff.
- Migre tela por tela, sem mudar regras de negócio.
- As URLs antigas continuam funcionando até a troca de cada tela.
- Nenhuma regra é duplicada no painel: tudo passa pelos serviços da fase 1.

**2.1 Estrutura**
- Base, header com logo GoMut e "Visualizar como membro".
- Barra lateral com contadores: Comunidade = tópicos novos e encaminhados; Chamados = abertos e em análise; Vencimentos = planos que vencem em até 30 dias.
- Menu da conta.

**2.2 Meus cursos e Criar curso** (gCursos, gCriar).

**2.3 Curso: Básico e Visão geral** (gBasico, gVisao)
- Indicadores: alunos ativos, aulas publicadas e em rascunho, tópicos sem resposta, chamados abertos.
- Ferramentas de gestão.
- Próximas liberações por mês do plano.
- Precisa de atenção, com o número real de aulas sem link do Vimeo e de planos vencendo.

**2.4 Conteúdo: módulos e aulas** (gModules)
- Reordenação.
- Mês de liberação e situação do módulo.
- Criar aula rápida como rascunho.
- Avaliação final como última seção, depois do último módulo.

**2.5 Editar aula** (gAula): conteúdo, Vimeo, duração, e-book, editor do quiz, situação, mover de módulo e prévia do vídeo.

**2.6 Alunos e Vencimentos** (gAlunos)
- Tabela e filtros.
- Modal de plano com criar, encerrar, reativar, corrigir, observação e histórico.
- Envio de primeiro acesso.

**2.7 Comunidade e Chamados** (gCom, gChamados), com as ações da fase 1.

**2.8 Ao vivo, Certificados e Configurações** (gVivo, gCerts, gCfg)
- Configurações: escola, nome do mentor, etiqueta, nome da equipe, e-mail de suporte, FAQ e assuntos, avisos.

**2.9 Relatórios** (gRel), só com métricas reais:
- Alunos que acessaram por dia.
- Acessaram nos últimos 7 dias.
- Horas assistidas.
- Progresso médio por curso.
- Aprovação na avaliação final.
- Aulas mais concluídas.
- Alunos sem acesso recente.
- Planos vencendo e progresso de quem vence.
- Exportar CSV.

**2.10 Visualizar como membro**
- Pré-visualização somente leitura da área do aluno, por aluno escolhido, sem usar a senha dele.
- Desenho:
  - "Ver como" na linha do aluno e "Visualizar como membro" no header abrem /painel/visualizar/<aluno_id>/.
  - A sessão guarda o aluno visualizado e o administrador. O administrador continua logado como ele mesmo.
  - Faixa fixa: "Vendo como membro · Nome", com "Voltar ao painel".
  - Um middleware ou decorator recusa qualquer POST da área do aluno nesse modo, com "Modo visualização: ações desativadas". Pulsos do player também são ignorados.
  - Novo MemberPreviewLog: admin, student, started_at, ended_at.
  - Se esse desenho conflitar com o código atual, pare e me reporte antes de implementar.

---

# Fora da V1

Não implemente sem uma nova decisão minha:

- Gateway de pagamento (Asaas), compra pelo site, checkout e matrícula automática.
- Renovação de plano.
- Página de vendas, vitrine, cursos à venda, trilhas, fileiras configuráveis do Início e áreas.
- Papéis de equipe (suporte, editor), controle de acesso e login do médico no painel.
- PDF do certificado gerado no servidor.
- Leitor de PDF página a página (PDF.js).
- Liberação por aula ou por data fixa.
- Anexos em chamados.
- "Minha lista" e favoritos.
- Multi-tenant.
