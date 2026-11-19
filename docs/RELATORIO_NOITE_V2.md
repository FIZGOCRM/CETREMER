# Plantão sem GPT · Entrega v2 para QA local

19 de novembro de 2026 · Branch `feat/plantao-sem-gpt-v2` · Projeto GoMut / Emergensimples.

**Os 13 itens estão implementados para QA local.** O aluno entra na experiência do curso, retoma uma aula, consulta a trilha e baixa os materiais. O produtor acompanha a reprodução por aula e escolhe os destaques da semana. A validação usou uma cópia do SQLite e uma instalação separada das dependências. A publicação em produção continua sendo uma etapa futura.

## 1. Cobertura dos pedidos do PDF

Referência: `docs/Plantao_Sem_GPT_Solicitacoes_TI.pdf`, 14 páginas. O item 11 ocupa duas páginas. As decisões v2 fornecidas pelo solicitante resolvem as divergências de conteúdo e navegação das imagens. O ajuste de vencimento da v1 continua valendo.

| Item e página | Status | O que conferir |
|---|---|---|
| 1 · p. 1 · Retomada e interesse | Feito | A home prioriza a aula em andamento com atividade mais recente. A fileira pessoal reúne todas as iniciadas, com posição, minutos restantes, percentual e retomada no player. No painel, cada aula tem iniciantes, avanço médio, quatro faixas de alcance, chegadas ao final e marcações manuais. |
| 2 · p. 2 · Top 10 | Feito | No painel do curso, escolha a segunda-feira e atribua posições de 1 a 10. As métricas aparecem na gestão. O aluno vê a seleção mais recente que já entrou em vigor. Há histórico por semana e validação de curso, posição e repetição. |
| 3 · p. 3 · Novidades | Feito | Aulas, PDFs e gravações disponíveis aparecem na home, com selo de novidade e página completa de 14 dias. As publicações também chegam ao sininho e à fila de e-mail, respeitando acesso e preferências. Um PDF preparado antes de publicar a aula passa a ser novidade quando fica disponível. |
| 4 · p. 4 · Encontros | Feito | A home apresenta os encontros do curso e os gerais. O aluno vê o tipo, a data, a hora, a duração e a proximidade. Inscrição e remoção do lembrete atualizam a tela via fetch. Lembretes de véspera e de última hora têm referências separadas. |
| 5 · p. 5 · Minha lista | Feito | O botão de salvar aparece no card e na aula. A lista persiste por aluno e pode ser aberta na home e pelo menu. Remover um item atualiza os cards correspondentes. |
| 6 · p. 6 · Organização e vitrine | Feito | A rolagem reúne hero, retomada, destaques, novidades, encontros, lista pessoal e outros cursos publicados. Só entram na vitrine cursos sem matrícula do aluno. O contato comercial cita o curso. |
| 7 · p. 7 · Ações da aula | Feito | Conclusão, curtida e Minha lista ficam sob o player. O aluno conserva Anterior/Próxima e a numeração global da aula. Repetir o estado de uma reação preserva um único registro. |
| 8 · p. 8 · Abas | Feito | Visão geral, E-book, Quiz e Anotações, nessa ordem. A descrição vem da aula e as anotações continuam privadas e vinculadas ao minuto do vídeo. |
| 9 · p. 9 · Quiz | Feito | Correção ao clicar, dentro da aba. No erro, o aluno vê sua escolha, a correta e as duas justificativas. O editor aceita de duas a cinco alternativas e exige as justificativas. Perguntas antigas usam o comentário geral. O CSV antigo e as tentativas anteriores continuam legíveis. |
| 10 · p. 10 · E-book da aula | Feito | Card do primeiro PDF em ordem, identificação da aula, download, materiais adicionais e link para a biblioteca do curso. |
| 11 · pp. 11–12 · Trilha e temas | Feito | Chips horizontais e acordeões por módulo, com capas, aulas, duração e progresso. Módulos futuros mostram cadeado e data quando há início de plano. O produtor pode criar o módulo dentro do cadastro da aula. |
| 12 · p. 13 · E-books do módulo | Feito | O módulo reúne a lista das aulas e, abaixo, os PDFs disponíveis para baixar diretamente. A mesma referência de material atende aula, Trilha e biblioteca. |
| 13 · p. 14 · Biblioteca | Feito | E-books agrupados por módulo, chamadas do PDF e contador de liberados. Cada item identifica número global, aula, material e download. Os materiais gerais do curso têm uma seção própria. |

## 2. Decisões adicionais e limites do histórico

- A entrada com um curso ativo renderiza sua home em `/dashboard/`. Com vários, a entrada permite escolher. O curso selecionado orienta os links do menu. Na tela pequena, os cinco destinos ficam na navegação inferior. Certificados, progresso, comunidade e suporte permanecem acessíveis.
- O hero usa a primeira aula disponível e incompleta quando o aluno ainda não tem interrupções. Quando não há próxima aula, oferece acesso à Trilha. A fileira de retomada fica oculta quando está vazia.
- A migração recupera somente o ponto mais distante comprovável pela posição antiga. O sistema anterior não registrava a data do primeiro início nem discriminava conclusões manuais e automáticas. Itens históricos sem data de início podem compor o total acumulado. As janelas de 7 e 30 dias usam inícios conhecidos. As colunas de origem exigem evidência registrada. Uma posição conhecida de pelo menos 90% ainda conta como chegada ao final.
- O alcance mede o ponto mais distante do vídeo, inclusive em um avanço do player. O tempo estudado continua medindo segundos efetivamente creditados. Rebobinar conserva a retomada no novo ponto e o maior alcance anterior. A reserva do relógio inclui o ID da aula para que uma aba pausada não receba o crédito de outra.
- As faixas de avanço são [0,25), [25,50), [50,75) e [75,100] por cento. Aulas sem duração aparecem sinalizadas. A marcação manual é registrada mesmo quando o aluno ainda não começou a reprodução. Os destaques preservam o número atribuído pelo produtor, inclusive se outro destaque ficar oculto.
- O contador da biblioteca inclui PDFs principais e extras das aulas publicadas. O total pode incluir PDFs de módulos futuros. Somente os liberados expõem título e link. Os PDFs gerais do curso ficam fora desse contador. Um módulo futuro sem data inicial conhecida informa o mês do plano.
- O link de contato usa o WhatsApp da escola. Com o número em branco, o cartão oferece contato pelo suporte. Avisos de gravação seguem a preferência de e-mail de encontros. Avisos de aula e e-book seguem a preferência de novas aulas.
- Datas antigas de upload e gravação desconhecidas permanecem vazias. Esses materiais continuam disponíveis pela biblioteca ou agenda. O sistema evita apresentar toda a base anterior como publicada no dia da migração.
- O editor e o novo CSV exigem letras consecutivas a partir de A, para que a letra exibida preserve o gabarito cadastrado. O CSV legado conserva sua interpretação anterior. A avaliação final mantém o envio conjunto das respostas e sua regra de aprovação.
- Os testes v1 que exigiam ausência de “Minha lista” ou marcação antiga das abas passaram a verificar o contrato v2. Continuam cobertos o acesso encerrado, a prévia administrativa somente leitura e as operações das rotas anteriores.

## 3. Dados, rotas e interface

| Migração | Alteração e tratamento de dados |
|---|---|
| `courses/0021_experiencia_por_curso` | Cria `LessonLike`, `SavedLesson`, `WeeklySelection` e `WeeklySelectionItem`. Acrescenta `Module.cover`, `Lesson.cover`, `LessonMaterial.created_at`, `LiveEvent.recording_added_at`, `QuizChoice.explanation` e os campos de telemetria de `Progress`. Substitui o limite de ordem 4 pelo limite 5. O único backfill é `max_position_seconds = last_position_seconds`. As datas históricas desconhecidas ficam nulas. |
| `users/0016_vincular_relogio_aula` | Acrescenta a referência opcional `StudentProfile.heartbeat_lesson`, com `SET_NULL`. Depende da migração anterior. Ao retomar após a atualização, um pulso abre o novo intervalo de medição. |

Os arquivos estão em `courses/migrations/` e `users/migrations/`. Reações têm unicidade por aluno e aula. Seleções têm unicidade por curso e semana e seus itens têm posição e aula únicas. Uma aula presente no histórico de destaques fica protegida contra exclusão. O admin Django dispõe de listagem das reações e dos itens semanais dentro da seleção.

| Área | Rotas e arquivos |
|---|---|
| Aluno por curso | `courses/experience_urls.py` define `dashboard/escolher/<section>/` e, sob `dashboard/cursos/<course_slug>/`, os destinos `inicio/`, `trilha/`, `ebooks/`, `novidades/`, `ao-vivo/` e `minha-lista/`. Views e consultas em `courses/experience_views.py`, `experience_selectors.py`, `selectors.py` e `live_selectors.py`. |
| Aula e ações | `courses/lesson/<id>/reaction/like/` e `reaction/saved/` recebem POST com CSRF e o estado desejado. Heartbeat, conclusão, quiz, lembrete e anotações continuam nos endpoints existentes. `materiais/<kind>/<id>/?download=1` retorna anexo para arquivos armazenados, após verificar o acesso. Ver `courses/player_views.py`, `engagement_services.py`, `services.py`, `student_views.py`, `live_views.py` e `material_views.py`. |
| Produtor | `/painel/relatorios/aulas/` e `/painel/cursos/<id>/top-10/`. Métricas em `painel/reporting.py`, formulários em `painel/analytics_forms.py` e `painel/forms.py`, views em `painel/views/{weekly,reports,lessons,quizzes,course_management}.py`. Edição de capas e criação de módulo reutilizam a gestão do curso. |
| Páginas de membros | `templates/courses/{choose_course,course_home,course_news,course_saved,course_trail}.html` e os parciais em `templates/partials/experience/`. Foram ajustados dashboard, e-books, encontro, aula, avaliação final, cabeçalho e aba do quiz. Ver também `templates/base_membros.html`, `static/css/gomut/{experience,members}.css` e `static/js/gomut/{experience,lesson-guide,quiz}.js`. |
| Páginas do produtor | `templates/painel/{lesson_metrics,lesson_metrics_table,weekly_selection}.html` e os templates existentes de relatório, abas, aula, módulos e confirmações. |
| Avisos | `users/notifications.py` utiliza a central e a fila existentes. A rotina de 15 minutos chama `run_live_reminders`, que também processa publicações. O diário repete a varredura como garantia. A criação do aviso e o registro na fila compartilham uma transação. A tentativa de entrega ocorre depois. |

## 4. Verificação

Ambiente Windows, Python 3.13.17 e Django 5.2.19 instalados de `requirements.txt` em `.venv-v2`.

| Execução | Resultado |
|---|---|
| Linha de base após o snapshot | 392 testes em 98,813 s. 391 passaram. Um teste de configuração HTTPS passou um caminho Linux ao verificador de caminhos absolutos do Windows. A fixture passou a usar caminhos absolutos nativos. As verificações de segurança do aplicativo foram preservadas. |
| Suíte completa final | 431 testes aprovados em 151,665 s, sem falhas ou erros. São 39 testes a mais que na linha de base. |
| Consistência | `check` sem problemas, `makemigrations --check --dry-run` sem alterações pendentes e ambas as migrations aplicadas na cópia. `PRAGMA integrity_check` retornou `ok` e `foreign_key_check` não retornou linhas. |
| Chrome local | Login com as duas contas, 19 destinos HTTP 200 em 390 e 1440 px (38 verificações). Sem excesso de largura da página ou exceções JavaScript observadas. Salvar/remover aula e ativar/desativar lembrete persistiram via fetch/CSRF. O aluno recebeu 403 ao tentar o relatório do produtor. Home, Trilha, E-books e Minha lista também foram exercitados em 1024 px. O acordeão respondeu ao teclado. |
| Aula interativa | No Edge, foram exercitados conclusão, curtida e lista persistentes, escolha e correção A–E, revisão da tentativa e avaliação final. Os testes Django exercitaram o crédito, as pausas, a retomada, o limiar de 90% e duas aulas abertas ao mesmo tempo. O QA desta entrega não repetiu streaming real do catálogo privado do Vimeo. |
| Controles de acesso | Testes abrangem visitante, aluno sem matrícula, plano expirado, módulos futuros, rascunhos, prévia do produtor, PDFs e outros cursos. Testes de notificações cobrem as duas janelas de lembrete, troca de arquivo, republicação, revogação de acesso antes da entrega, falha entre sininho e fila, opt-out e prévia local em console. |

Para auditoria nesta máquina: `.venv/v2-baseline.log`, `.venv/v2-suite-entrega.log`, `.venv/v2-browser-final.log` e `.venv/v2-experience-browser.log`. As capturas locais incluem `.venv/v2-aluno-inicio-390.png`, `.venv/v2-aluno-trilha-1440.png` e `.venv/v2-browser-lesson-quiz.png`. As verificações locais usaram dados de demonstração.

## 5. Como testar agora

Abra [o login do aluno](http://127.0.0.1:8026/login/) ou [o login do produtor](http://127.0.0.1:8026/login/?acesso=admin). Use `aluno-v2@gomut.example` para entrar diretamente no Plantão e `produtor-v2@gomut.example` para a gestão. A senha gerada para essas duas contas está somente em `.venv/v2-acessos-local.txt` nesta máquina. O aluno v1 `aluno@gomut.example` continua disponível para conferir a escolha entre cursos com sua senha existente.

O servidor usa a porta **8026**. Para subi-lo novamente após encerrá-lo, no PowerShell e na raiz do projeto:

~~~powershell
.\.venv-v2\Scripts\python.exe .\.venv\run_v2.py runserver 127.0.0.1:8026
~~~

O lançador local aponta para `.venv/gomut-v2.sqlite3` e `.venv/v2-media`. A demo original conserva o SHA-256 `e900571de27ee1e8959cdc4168c807953919c579adfbfc58136d89e064647e61`, conferido antes e depois das operações. O ambiente antigo conserva suas dependências. Para repetir a suíte, troque `runserver 127.0.0.1:8026` por `test`. O comando `prepare_demo` ganhou `--with-course-experience` para popular cenários de QA sem sobrescrever senhas, resultados ou curadoria anterior. A base v2 já está populada.

| Destino na demo preparada | URL relativa a `http://127.0.0.1:8026` |
|---|---|
| Início do curso | `/dashboard/cursos/gomut-demo-plantao/inicio/` |
| Trilha e módulo | `/dashboard/cursos/gomut-demo-plantao/trilha/` e seus chips por tema |
| Biblioteca | `/dashboard/cursos/gomut-demo-plantao/ebooks/` |
| Novidades | `/dashboard/cursos/gomut-demo-plantao/novidades/` |
| Ao vivo | `/dashboard/cursos/gomut-demo-plantao/ao-vivo/` |
| Minha lista | `/dashboard/cursos/gomut-demo-plantao/minha-lista/` |
| Primeira aula, materiais e quiz | `/courses/gomut-demo-plantao/lessons/1/` |
| Relatórios por aula | `/painel/relatorios/aulas/` |
| Top 10, semana e histórico | `/painel/cursos/1/top-10/` |
| Conteúdo e módulos | `/painel/cursos/1/aulas/` |
| Nova aula, seleção/criação de módulo e capas | `/painel/cursos/1/aulas/nova/` |
| Editar aula e quiz | `/painel/aulas/1/editar/` e `/painel/aulas/1/quiz/` |
| Encontros e gravações | `/painel/ao-vivo/` |

Para ver o feedback de erro e acerto, entre como aluno, abra a primeira aula, marque-a como concluída e abra a aba Quiz. Para conferir a curadoria, entre como produtor em outra sessão do navegador, abra o Top 10, escolha uma segunda-feira e confira o resultado na home daquele curso.

## 6. Cuidados para uma publicação posterior

1. Usar o processo Docker Compose já registrado em `docs/operacao-kvm4.md` e `docs/publicacao-https.md`. Preparar e verificar o backup do banco e da mídia antes da atualização. Coordenar a janela com web e scheduler para evitar escrita concorrente durante a reconstrução das tabelas SQLite.
2. Aplicar `python manage.py migrate --noinput` à base persistente pela nova imagem. A ordem é `courses.0021` e depois `users.0016`. O afrouxamento do limite de alternativas e as adições preservam os registros preexistentes. Uma reversão para o código v1 depois de já cadastrar alternativas E ou seleções semanais requer planejar a restauração do snapshot e reconciliar dados novos.
3. Servir os novos estáticos da imagem e manter o volume de mídia. As capas usam `courses/modules/` e `courses/lessons/`, ambos sob o prefixo de imagens que o handler de produção já permite. Os PDFs continuam em um endpoint autenticado com `private, no-store`. O Dockerfile e os arquivos Compose não precisaram de mudança na v2.
4. Manter uma instância do agendador. Conferir o ciclo de 15 minutos, o diário e `EmailLog`. Uma mensagem pendente precisa de configuração válida de SMTP, preferência e direito de acesso ainda válidos. Em DEBUG e sem SMTP a prévia de uma mensagem nova sai no console, sem marcar entrega real.
5. Homologar com os domínios autorizados no Vimeo, uma matrícula válida e outra expirada. Validar mídia, retomada e o primeiro e-mail real somente quando houver autorização operacional.

## 7. Pendências para operação

- Disponibilização da v2 na VPS depende de autorização posterior. Esta execução foi inteiramente local, sem push, merge ou deploy.
- A equipe deve definir as seleções reais, revisar capas e justificativas, cadastrar os PDFs e publicar os encontros. Os dados deste ensaio ficam na cópia local. O checkout e `sales` permaneceram fora da entrega.
- O número da escola atende ao contato comercial. Notificações automáticas por WhatsApp e telefone de aluno ficam para uma decisão futura. O ponto de extensão dos canais é `users/notifications.py`. Entrega de e-mail ao destinatário externo depende do SMTP da escola e não foi testada aqui.
- URLs externas de PDF já cadastradas continuam como redirecionamentos autorizados. Nesses arquivos o servidor externo decide sobre o download. Para garantir o anexo protegido pela GoMut, usar o upload do PDF. A privacidade e a disponibilidade dos vídeos privados continuam dependendo das configurações do Vimeo.
- O histórico anterior à v2 não permite reconstruir quando cada aluno começou nem atribuir com certeza uma origem a cada conclusão. Preservar essa limitação ao interpretar os primeiros relatórios.

## 8. Commits da branch

O snapshot incluiu as alterações locais anteriores de QA, operação e publicação, os testes e o PDF de referência. Não houve arquivo não rastreado suspeito exigindo inclusão manual. Bases SQLite, senhas, chaves, mídia, ambiente virtual e evidências locais ficaram fora dos commits desta entrega.

- `1466531` chore: snapshot do estado anterior à v2
- `0894f25` testes: usar caminhos absolutos nativos na verificação HTTPS
- `f0163e1` feat: registrar alcance do player, reações e seleção semanal por curso
- `2feeaed` Permite criar aulas e módulos juntos e editar suas capas
- `a812cc4` feat: processar publicações a cada quinze minutos e lembrar encontros na véspera
- `9ff364d` feat: reunir retomada, destaques, novidades e lista pessoal na home do curso
- `30381b7` feat: preparar demonstração isolada da experiência por curso
- `53c8f60` feat: integrar ações, e-books e quiz comentado à página da aula
- `11e6194` Adiciona métricas de reprodução por aula e curadoria semanal por curso
- `b61a935` fix: persistir aviso e fila de e-mail na mesma transação
- `2eb9cf0` feat: demonstrar publicação e retomada com aluno identificado
- `bade3b7` Valida curadoria semanal em serviço transacional do curso
- `e9fc5b3` feat: organizar trilha e biblioteca por módulo com liberação e progresso por aula
- `6f9b498` fix: creditar cada intervalo de reprodução à aula que o iniciou
- `7a02d51` fix: manter letras das alternativas consistentes entre cadastro e resultado
- `3f3f4e8` fix: anunciar materiais quando ficam disponíveis para o aluno
- `00360df` feat: mostrar prévia de e-mail em console no desenvolvimento
- `docs: registrar entrega e validação local do Plantão v2` · relatório final.

O commit do próprio relatório pode ser identificado com `git log -1 --oneline -- docs/RELATORIO_NOITE_V2.md`.
