# Etapa 1.14 — notificações e e-mails

## 1. O que foi feito
Notificações pessoais com contador, lista e marcar lidas. Gatilhos para equipe na comunidade, solução, chamado, aula publicada/liberada, módulo e encontro com lembrete. Avisos obrigatórios de vencimento 30/15/7. Preferências para aulas/encontros no perfil. Comandos diário e lembretes15min, deduplicação, log de envio, tentativas pendentes e contador no painel. Sem SMTP, não simula entrega.

## 2. Arquivos
users/{models,notifications,notification_views,test_notifications}.py; users/migrations/{0011_notifications,0012_email_deadline}.py; users/management/commands/{run_daily_notifications,run_live_reminders}.py e __init__.py; courses/{models,services}.py; courses/migrations/0020_notifications.py; courses/management/commands/prepare_demo.py; community/services.py; support/services.py; core/{settings,context_processors,urls}.py; painel/views/plans.py; templates/users/notifications.html; templates/painel/expirations.html; templates/partials/gomut/member_header.html; static/css/gomut/members.css; este relatório.

## 3. Migrações
users.0011: Notification com referência única por usuário/tipo/evento; EmailLog com referência única por tipo (inclui usuário), assunto/corpo congelados para retentar; preferências no StudentProfile. users.0012: EmailLog.send_before, para não enviar aviso temporal vencido. courses.0020: Lesson.published_at; sem inventar histórico para aulas antigas. Publicação pelo serviço registra a data; publicar módulo marca suas aulas publicadas. Aplicadas demo/schema vazio.

## 4. Testes
271 testes, zero falhas/erros. Onze novos em users/test_notifications.py, RED→GREEN: marcos obrigatórios/deduplicação, DEBUG sem SMTP, envio/falha, retentativa, aula futura, módulo, comunidade/solução/chamado, lembrete, leitura isolada, prazo do e-mail e publicação de módulo. Comandos reais na demo sem SMTP: duas execuções diárias criaram zero avisos adicionais; lembretes zero. makemigrations sem alterações.

## 5. Causas e efeitos
C4: publicação e liberação avaliadas no servidor, sem avisar aula inacessível. C29: console DEBUG não conta como entrega; status not_sent. C30: referências únicas e verificação sent sob reserva de escrita SQLite evitam reenvio em execuções normais/concomitantes. Vencimento não possui preferência de desligamento. Avisos de conversa não copiam títulos potencialmente sensíveis para outras telas.

## 6. Como conferir na tela
1. aluno@gomut.example → sininho (/notificacoes/): aviso ilustrativo, contador, detalhes e Marcar como lidas.
2. Responder como equipe a um tópico, marcar uma resposta como solução ou atualizar chamado no painel gera aviso para o destinatário.
3. admin@gomut.example → Vencimentos: contador de e-mails aguardando envio.
4. Executar python manage.py run_daily_notifications diariamente; python manage.py run_live_reminders a cada15min. O segundo avisa na próxima hora.
5. Chrome390/1440: notificações/painel200, sem overflow/erroJS; telas inspecionadas. Preferências entram na Minha conta na próxima etapa.

## 7. Pendências/desvios
Agendamento e SMTP reais dependem da infraestrutura1.17. Fila retenta após SMTP disponível, respeitando preferência atual e prazo: vencimento até o fim do dia do marco; encontro até o início. Pendências vencidas ficam no histórico, fora do contador vigente. Histórico anterior de publicação sem timestamp não gera uma enxurrada inicial.
O projeto mantém o SiteEmailBackend, sem Celery/dependências. Reserva SQLite serializa entregas por log. Há uma limitação operacional de SMTP: se o processo morrer após o servidor aceitar o e-mail e antes do commit, o protocolo não fornece confirmação transacional idempotente; investigar esse caso antes de retentar manualmente. Não se promete exactly-once perante uma queda nesse intervalo. Nenhum e-mail real foi enviado no QA.

## 8. Commit
feat: notificacoes e emails da etapa 1.14; hash na entrega/diário. Sem push/merge.
