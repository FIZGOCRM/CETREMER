# Etapa 1.12 — suporte, FAQ e chamados

## 1. O que foi feito
Central de ajuda com busca única em FAQ/chamados, abas público/meus e abertura sem exigir plano ativo. Chamados privados só para dono/equipe; nome público reduzido. Voto Também tenho esse problema. Histórico em toda transição/resposta; painel analisa, responde, resolve e reabre. Gestão de FAQ e assuntos com desativação. Dados ilustrativos pelo prepare_demo.

## 2. Arquivos
Novo app support: __init__.py, models.py, access.py, services.py, selectors.py, forms.py, views.py, tests.py, demo.py e migrations/0001_support_v1.py; core/{settings,urls}.py; painel/urls.py e views/support.py; courses/management/commands/prepare_demo.py; templates/support/{hub,new_ticket,ticket}.html; templates/painel/{tickets,support_settings}.html; templates/{base_membros,partials/sidebar_admin,partials/gomut/member_header,courses/access_pending}.html; este relatório.

## 3. Migrações
support.0001: FaqItem, SupportSubject, Ticket, TicketEvent, TicketVote; unicidade usuário/chamado. Numeração deriva da PK alocada pelo SQLite (1023+PK), dentro da transação, evitando SELECT MAX concorrente. Relações de histórico protegidas contra exclusão. Aplicada somente demo; schema vazio pela suíte.

## 4. Testes
252 testes, zero falhas/erros. Nove novos em support/tests.py, oito primeiros RED→GREEN: privacidade em busca/lista/URL, abertura sem plano, sequência numérica, linha do tempo, resolução com resposta, privilégio equipe, voto único/privado, nome reduzido e FAQ rascunho, assunto/aparelho inválido. Nono cobre criação HTTP e gestão FAQ/assuntos. Corrigido nome de perfil nulo detectado no teste.

## 5. Causas e efeitos
C25: chamado privado não aparece em lista/busca de outro aluno, nem abre por URL. Encerramento de plano não bloqueia suporte. Histórico conserva status, ator e texto de cada alteração; chamado não é apagado.

## 6. Como conferir na tela
1. aluno@gomut.example → Central de ajuda (/suporte/): abrir FAQ, Sim/Não, buscar e trocar abas.
2. Abrir chamado: assunto, aparelho, título e descrição; opcional Privado. Ver número e linha do tempo; público permite voto.
3. admin@gomut.example → Chamados (/painel/chamados/): Em análise, responder/Resolver e Reabrir. Links FAQ/Assuntos permitem criar, editar, ordenar e despublicar/desativar.
4. Chrome 390/1440 em seis páginas de aluno/painel, HTTP200, sem overflow/erro JS; captura visual revisada.

## 7. Pendências/desvios
FAQ do protótipo foi ajustada para não prometer SMTP imediato, prazo fixo de gravação ou reemissão de certificado (fora da V1 e contrária ao snapshot imutável). Datas e requisito de avaliação correspondem ao cadastro real. Nenhum dado clínico ou pessoa real foi criado. Notificações na 1.14; layout final do painel na Fase 2. Sem anexos nesta versão. Assuntos com histórico são desativados e FAQ despublicada, preservando dados.

## 8. Commit
feat: suporte e chamados da etapa 1.12; hash na entrega/diário. Sem push/merge.
