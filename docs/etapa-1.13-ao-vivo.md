# Etapa 1.13 — ao vivo

## 1. O que foi feito
Agenda por curso e encontros abertos aos alunos com acesso. Lembrete por aluno, gravações e link de sala protegido por horário. Painel cadastra/edita/desativa encontros, preservando lembretes. Próximo encontro entra nos próximos passos, prioridade 7. Demo ilustrativa sem sala clínica inventada.

## 2. Arquivos
courses/{models,live_services,live_selectors,live_views,test_live_v1,selectors}.py; courses/migrations/0019_live_events.py; courses/management/commands/prepare_demo.py; core/urls.py; painel/{urls,live_forms}.py; painel/views/live.py; templates/courses/live_classes.html; templates/painel/live.html; templates/partials/sidebar_admin.html; este relatório.

## 3. Migrações
courses.0019: LiveEvent(course opcional,title,kind,starts_at,duration_minutes,description,room_url,recording_url,is_active); LiveReminder(student,event), unicidade aluno/encontro. Aplicada demo, schema vazio na suíte.

## 4. Testes
260 testes, zero falhas/erros; oito novos, RED→GREEN: curso alheio, limite exato de 10 minutos, evento aberto exige plano, lembrete único, gravação protegida, encerramento revoga acesso, gestão só equipe e preservação de lembretes, próximos passos. Sem migrações pendentes.

## 5. Causas e efeitos
Validação de matrícula/plano em lista, sala, gravação e lembrete. URL da sala não aparece antes da janela; endpoint revalida horário. Link da sala vale de 10 minutos antes até o fim previsto; gravação só abre após a duração prevista. Desativação conserva histórico.

## 6. Como conferir na tela
1. aluno@gomut.example → Ao vivo (/ao-vivo/): encontro ilustrativo, Lembrar-me/Remover e gravação pública demonstrativa do Vimeo.
2. admin@gomut.example → Ao vivo (/painel/ao-vivo/): cadastrar com curso, tipo, horário, duração, sala/gravação; editar ou desativar.
3. Sala real só aparece dentro da janela e se preenchida. Nenhum link de sala fictício foi inventado para simular sucesso.
4. Chrome390/1440: aluno/painel200, sem overflow/erroJS, capturas verificadas.

## 7. Pendências/desvios
Envio dos lembretes na 1.14. Course.live_meet_url/live_calendar_url/live_schedule_embed permanecem em reserva, sem importação automática: faltam título, data e duração para migrar sem inventar. A nova rota Ao vivo usa LiveEvent; cadastrar os encontros no painel. Campo is_active permite remoção lógica, preservando lembretes. Restringir sala ao período do encontro e gravação após término evita divulgar antecipadamente links por URL direta.

## 8. Commit
feat: agenda ao vivo da etapa 1.13; hash na entrega/diário. Sem push/merge.
