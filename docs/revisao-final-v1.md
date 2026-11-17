# Revisão final V1 — correções e evidências

## 1. O que foi feito

Revisão independente, somente leitura, do intervalo `bbbf883..72bb954`, contra o plano oficial, o protótipo e as decisões aprovadas. O revisor executou os 315 testes então existentes e não encontrou divergência de migrações. Encontrou seis problemas importantes e nenhum crítico. Os seis foram reproduzidos com regressões antes das correções. O ajuste textual C19 também foi feito por ser requisito explícito do plano. Não houve segunda rodada de revisão delegada.

## 2. Arquivos criados e alterados nesta correção

- `courses/access.py`, `student_views.py`, `selectors.py`, `services.py`, `material_views.py`, `quiz_views.py`.
- `courses/test_content_release.py`, `test_final_assessment.py`, `test_plan_lifecycle.py` e fixtures dos testes de aluno, progresso, materiais, quizzes, acesso e certificados.
- `community/access.py`, `selectors.py`, `test_v1.py`, `tests.py`.
- `support/access.py`, `selectors.py`, `services.py`, `views.py`, `tests.py`.
- `users/models.py`, `notifications.py`, `test_notifications.py`, novo `test_email_concurrency.py` e `migrations/0015_email_delivery_claim.py`.
- Fixtures de publicação em `users/test_member_navigation.py` e `painel/test_member_preview.py`.
- `templates/courses/dashboard.html`, `templates/support/ticket.html`, `templates/painel/settings.html`.
- `docs/manual-operacao.md` e os documentos consolidados de QA, revisão e decisões.

As fixtures de acesso agora criam cursos explicitamente publicados. O padrão do modelo continua sendo rascunho e o formulário de criação continua sendo testado como rascunho; não houve alteração silenciosa do padrão.

## 3. Migração

`users.0015_email_delivery_claim`: `EmailLog.delivery_token` e `delivery_claimed_at`. Reserva condicional de cinco minutos com token próprio por execução. Os estados continuam `sent`, `not_sent`, `failed`. Aplicada à base demo; criação do esquema vazio e recuperação da reserva testadas. Não há rede SMTP dentro da transação de reserva/finalização.

## 4. Resultado dos testes

**334 testes passaram, zero falhas/erros.** Os testes novos desta revisão incluem:

| Problema | Reprodução antes da correção | Evidência após a correção |
|---|---|---|
| Exclusão perdia tópico/material aberto | Dois testes falharam porque a exclusão era aceita | `ContentReleaseTests.test_lesson_with_community_history_cannot_be_deleted` e `test_module_with_material_open_history_cannot_be_deleted` passam; vínculo e material preservados |
| Conta sem acesso lia/votava em chamados alheios | Lista continha chamado público indevido | Teste com conta sem matrícula e conta encerrada: lista sem conteúdo, detalhe/voto 403; chamado próprio e FAQ disponíveis |
| Mudança editorial perdia qualificação histórica | Cinco testes falharam com qualificação vazia | Desativar final/última pergunta, excluir final sem tentativas e despublicar aula/módulo pendente registram elegibilidade real; emissão após término passa; mudança depois do término não retroage |
| Curso rascunho expunha conteúdo | URL do curso retornou 200 | `test_draft_course_is_hidden_and_all_content_boundaries_refuse_access`: curso/aula 404, materiais/mutações recusados, catálogo/busca/biblioteca sem curso |
| Fila enviava aviso cancelado | Quatro regressões falharam | Avisos revalidam plano, disponibilidade/publicação, liberação, evento, horário e existência de lembrete; contagem exclui obsoletos |
| SMTP segurava a trava SQLite | Rede dentro de transação e dois envios na chamada concorrente | `EmailConcurrencyTests`: transação fechada, heartbeat concorrente grava, segundo trabalhador não envia; reserva expirada recuperada. Três testes também passaram com SQLite temporário em disco |
| Interface oferecia voto proibido | Formulário aparecia no chamado próprio sem matrícula | Formulário oculto, servidor continua recusando POST forjado |
| C19 exigia avaliação inexistente | Primeiro o HTML, depois o e-mail falharam no teste | `PlanLifecycleTests.test_no_final_course_expiry_notice_does_not_require_an_assessment` passa |

Suítes intermediárias: 317 após proteção do histórico; 319 após chamados; 325 após certificados; 326 após publicação; 330 após revalidação da fila; 333 após concorrência; 334 com o complemento C19. `makemigrations --check --dry-run` e `git diff --check` sem pendências/erros.

## 5. Causas e efeitos

C6 e regra geral 17 cobrem também histórico sem progresso de vídeo. C14 agora considera as mudanças administrativas de requisitos no momento em que ocorrem, sem inventar elegibilidade passada. C19 não exige uma avaliação ausente. C25 e a audiência dos chamados são checados tanto nas consultas quanto nos comandos. C29/C30 mantêm deduplicação e disponibilidade do SQLite; eventos obsoletos não são entregues.

## 6. Como conferir

Seguir o [roteiro de QA](entrega-v1-qa.md#6-como-conferir-na-tela), especialmente rascunho → acesso direto, planos → chamados próprios/coletivos, histórico → exclusão recusada e prévia → ações bloqueadas. Para concorrência não é necessário configurar SMTP real: o transporte simulado exercita a disputa com o heartbeat sem enviar mensagens.

Última rodada: 72 combinações Chrome/Edge em 390/1440 px e mais oito da prévia sem alterações no aluno. A impressão do certificado, PDF autenticado e exportação CSV foram conferidos nas etapas correspondentes. A reprodução real do Vimeo **não foi confirmada**: o vídeo público recusou autorização de reprodução e a interface C8 apareceu. O QA com vídeo autorizado continua necessário.

## 7. Pendências e desvios

Etapa 1.16 e entradas de produção seguem pendentes nos termos do plano. Nenhum problema importante da revisão ficou sem correção. O achado textual inicialmente classificado como menor foi corrigido porque o requisito explícito C19 do usuário prevalece sobre a orientação genérica da skill de adiar ajustes menores.

O lease SMTP dura cinco minutos, acima do timeout de transporte de 15 segundos; permite recuperar uma execução interrompida. Existe a janela inevitável entre aceite SMTP e gravação de `sent`: uma queda nesse intervalo pode causar duplicação na retentativa. Não se promete exatamente uma entrega nem recebimento na caixa de entrada. Veja o manual operacional.

Não foram executados teste de carga abrangente, certificação Firefox/Opera, importação real ou implantação. A revisão não foi usada para introduzir recursos fora da V1.

## 8. Commits

| Alteração | Hash |
|---|---|
| Proteger histórico | `f89b7da` |
| Restringir audiência de chamados | `d9c6cb0` |
| Atualizar qualificação editorial | `9407801` |
| Aplicar publicação de curso | `dfd1a2d` |
| Revalidar fila | `520695e` |
| Reserva e rede sem trava SQLite | `d4d4470` |
| Interface do voto conforme permissão | `36a534e` |
| Aviso sem avaliação inexistente | `9f00248` |

O commit da documentação pode ser localizado por `git log -1 -- docs/revisao-final-v1.md`.
