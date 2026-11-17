# QA — avisos de prazo concentrados nas notificações

## 1. O que foi feito

Atendidas as duas solicitações do QA: retirar as faixas do Início e retirar “Termina em X dias” dos cartões de cursos. A remoção inclui hero e progresso. A central de notificações recebe um aviso por matrícula nos três últimos dias efetivos de acesso, aos 3, 2 e 1 dias, com curso, data e botão “Ver meu plano”. Minha conta mantém as datas. A tolerância contratual e as datas cadastradas não foram alteradas.

## 2. Arquivos

- `courses/services.py`: cálculo compartilhado da janela curta e último dia efetivo.
- `users/notifications.py`: geração e revalidação dos avisos/e-mails.
- `courses/student_views.py`, `core/urls.py`: retirada da lógica de faixa e da ação de dispensar aviso.
- `templates/courses/dashboard.html` e `templates/partials/gomut/{course_card,course_hero,course_progress,my_plans}.html`.
- `templates/users/notifications.html` e `static/css/gomut/members.css`.
- `users/test_expiry_notifications.py`, `users/test_notifications.py`, `courses/test_plan_lifecycle.py`.
- `docs/{decisoes-produto,manual-operacao,entrega-v1-qa,ajuste-avisos-vencimento}.md`.

## 3. Migrações

Nenhuma. Não houve alteração de dados de plano nem criação de avisos fictícios persistidos para demonstrar a tela.

## 4. Testes

Suíte: **343 testes aprovados**, zero falhas/erros. Nove testes específicos cobrem remoção das faixas/contagens, ausência de aviso antes da janela, 3/2/1 dias sem duplicação, tolerância, encerramento antecipado, independência entre cursos e destinatários, Minha conta, acesso encerrado/irrestrito/inativo/rascunho e retentativa de e-mails antigos/corrigidos. Envio vigente também testado com SMTP simulado, sem mensagem real.

Os cenários novos reproduziram as divergências antes da implementação. A suíte também identificou a necessidade de manter “Encerrado” no progresso e de explicitar a tolerância no fixture do teste de vencimento; ambos foram corrigidos sem relaxar as expectativas de acesso.

Chrome em 390 e 1440 px: Início, Meus cursos, Progresso, Notificações e Minha conta, todos HTTP200, sem overflow horizontal e sem erro JS. O cartão de alerta foi inspecionado nas duas larguras com uma renderização de exemplo, sem gravar notificação ou alterar prazo da demo. Capturas em `.venv/v1-qa/expiry-*`.

## 5. Regras e limites

- Nova solicitação do usuário prevalece sobre a apresentação antiga do plano oficial.
- Três dias são contados até o fim efetivo do acesso: tolerância natural incluída; antecipado sem tolerância.
- Avisos diários por matrícula e prazo, deduplicados; não acumulam nova entrada ao repetir o comando no mesmo dia.
- Datas e contagens de gestão da equipe permanecem no painel; as datas do aluno ficam em Minha conta.
- E-mail existente acompanha o novo prazo. Logs/notificações históricos preservados.
- Agendamento diário em produção continua pendente da configuração operacional; não foi introduzido agendamento novo nem gravação de notificação em GET/prévia.

## 6. Como conferir

1. Entrar como `aluno@gomut.example` e atualizar o Início.
2. Conferir que “Meus cursos” vem após o hero, sem as duas faixas.
3. Conferir os cartões, Meus cursos e Meu progresso: não mostram “Termina em X dias”. Estados “Encerrado” e “Acesso pendente” continuam quando pertinentes.
4. Abrir Minha conta e conferir início e último dia efetivo de acesso.
5. Nos três últimos dias, o comando diário cria a notificação correspondente no sininho. “Ver meu plano” abre Minha conta na seção correta.
6. Os prazos atuais da demo são maiores que três dias; portanto ela não deve receber um alerta novo de vencimento agora. Os testes exercitam a proximidade do término sem mudar esses dados.

## 7. Pendências

Sem pendência desta alteração. Permanecem as entradas externas já documentadas da V1, incluindo agendamento/SMTP de produção e planilha real. Não houve envio real ou mudança de senha nesta alteração.

## 8. Commit

Assunto: `fix: concentrar avisos de prazo nos ultimos tres dias`. Localizar o hash com `git log -1 -- docs/ajuste-avisos-vencimento.md`.
