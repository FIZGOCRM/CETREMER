# Etapa 1.3 — player e tempo assistido

## 1. O que foi feito
- Posição salva por pulso e retomada via Vimeo SDK; concluída nos últimos 5% recomeça do início.
- Pulso de 15 s em reprodução/aba visível, envio adicional em pausa e via beacon em ocultação/saída, com CSRF.
- Crédito limitado pelo relógio global do aluno, até 20 s, sem multiplicação por avanço ou velocidade.
- Estado anterior de reprodução impede creditar o intervalo passado em pausa ao retomar.
- StudyDay por data local, incluindo divisão na meia-noite; ActivityEvent de conclusão.
- Conclusão a 90% creditados; ended exige 50% da duração conhecida no servidor.
- Troca de vídeo/duração zera posição sem apagar tempo de estudo nem conclusão.
- Plano encerrado recusa o próximo pulso, pausa o player e encaminha à explicação; falha do Vimeo mostra mensagem e mantém botão manual.

## 2. Arquivos
- `core/urls.py`
- `courses/forms.py`
- `courses/migrations/0014_player_tracking.py`
- `courses/models.py`
- `courses/player_views.py`
- `courses/services.py`
- `courses/student_views.py`
- `courses/test_player_tracking.py`
- `docs/etapa-1.3-player.md`
- `static/js/aluno.js`
- `templates/courses/lesson_detail.html`
- `users/migrations/0008_player_tracking.py`
- `users/migrations/0009_pause_credit_guard.py`
- `users/models.py`

## 3. Migrações
- courses/0014_player_tracking: campos de posição, tempo creditado e último pulso em Progress; StudyDay e unicidade aluno/data; ActivityEvent. completed_at deixa de ser auto_now para não falsificar a data de conclusão a cada pulso; os valores existentes são preservados.
- users/0008_player_tracking: relógio global last_heartbeat_at.
- users/0009_pause_credit_guard: heartbeat_playing, necessário para não creditar pausa na retomada.
Aplicadas na demonstração e schema vazio nos testes. Nenhuma base de produção utilizada.

## 4. Testes
176 testes, zero falhas/erros; 14 novos em courses/test_player_tracking.py. Primeiro ciclo RED: nove falhas por ausência dos serviços/rotas. Um teste adicional reproduziu crédito indevido ao retomar da pausa; corrigido guardando o estado anterior. Incluem CSRF no beacon, rejeição de campos de crédito forjados, posição decimal, meia-noite local, conclusão idempotente e duração obtida no servidor. node --check passou; nenhuma migration pendente.

## 5. Causas e efeitos
C7: mudança reseta posição e preserva conclusão; C8: mensagem de erro e botão manual (implementação/inspeção da tela, sem alegar homologação de todas as indisponibilidades do Vimeo); C9: relógio por aluno em duas aulas/aparelhos, sem dobro; C10: pulso após fim responde access=ended e não altera a posição anterior; C20: desmarcar reduz progresso, preserva tempo estudado e não reconclui no pulso seguinte. Casos de dados cobertos por testes.

## 6. Como conferir na tela
1. aluno@gomut.example → /dashboard/ → Emergências cardiovasculares → aula (ex.: /courses/gomut-demo-cardiologia/lessons/5/).
2. Reproduzir: posição é enviada a cada 15 s; sair e voltar retoma. A duração demo é curta e ilustrativa.
3. Pausar/ocultar a aba não acumula estudo. Avançar a barra não completa por si só.
4. Admin admin@gomut.example → plano do aluno: após encerrar, o próximo pulso recusa; nenhuma matrícula/progresso é apagado.
5. Editar vídeo/duração no painel reseta a posição de todos, mantendo conclusões.
6. Chrome 390/1440: player e demais telas verificadas HTTP200, sem overflow nem pageerror. O Vimeo público da demo carregou na inspeção. Capturas em .venv/v1-qa/ não versionadas. Credenciais locais já entregues.

## 7. Pendências/desvios
Para o caso sem duração cadastrada, a referência dos 50% vem do oEmbed já existente, consultado pelo servidor no ended. Se o Vimeo não fornecer duração, o sistema explica que não pode confirmar automaticamente e mantém a conclusão manual; não confia na duração enviada pelo navegador. Não inventa tempo para progresso antigo: StudyDay só recebe segundos reais dos pulsos. Quiz/etapas/contagem para próxima aula seguem nas fatias 1.5/1.6.

## 8. Commit
Commit único `feat: retomada e tempo assistido da etapa 1.3`; hash informado na entrega e no diário. Sem push/merge.
