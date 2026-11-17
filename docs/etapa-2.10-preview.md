# Etapa 2.10 — Visualizar como membro

## 1. O que foi feito
Escolha de aluno e Ver como na tabela. Sessão conserva o administrador; middleware apresenta o aluno apenas nas rotas de membros. Faixa com retorno ao painel. Toda requisição de gravação bloqueada, incluindo heartbeat/logout. Player permite assistir/retomar sem registrar tempo/conclusão. Formulários e botões de mutação desativados. Auditoria de início, troca e saída. GET não atualiza visitas, último acesso ou abertura de PDF.

## 2. Arquivos
users/{models,member_preview,preview_middleware,views}.py; users/migrations/0014_member_preview_audit.py; core/settings.py; painel/{urls,test_member_preview}.py; painel/views/preview.py; courses/student_views.py; templates/{base_membros,base_painel_gomut,painel/students,painel/preview_choose,users/preview_blocked,courses/lesson_detail}.html; static/{css/gomut/members.css,js/gomut/member-preview.js,js/aluno.js}; este relatório.

## 3. Migrações
users.0014: MemberPreviewLog(admin,student,started_at,ended_at), relações protegidas. Aplicada demo/schema vazio. Nenhum login como aluno, senha ou token é usado na troca.

## 4. Testes
315 testes, zero falhas/erros. Oito novos em test_member_preview.py: sessão/banner, GET sem métricas, bloqueio de POST, saída/auditoria, tentativa de aluno forjar sessão, acesso encerrado/troca, PDF/certificado sem escrita, payload malformado. Primeiros seis exercitados antes da implementação; cinco falharam por recurso ausente. Dois extras de regressão de segurança passaram. Makemigrations sem alterações e diff --check sem erros.

## 5. Causas e efeitos
Admin não vira o aluno na autenticação. Sessão validada por papel atual, IDs e log aberto do próprio administrador. Bloqueio central cobre endpoints futuros de membros; management/admin preservam a identidade de gestão. POST falsificado403. Acesso do alvo continua respeitando matrícula/plano/liberação. Respostas da prévia private,no-store.

## 6. Como conferir
admin@gomut.example → header Visualizar como membro → aluno → Ver como membro; ou Ver como na tabela Alunos. Navegar no Início, aula, e-books, conta e progresso; faixa Vendo como membro visível e ações desabilitadas. Voltar ao painel encerra log e conserva login admin. Chrome390/1440 em quatro páginas200, sem overflow; conclusão desativada. Zero POST espontâneo; heartbeat forjado403. Snapshot antes/depois confirmou progresso, tempo, notas, tentativas, PDFs abertos, visitas, certificados e último acesso INALTERADOS. Auditoria de saída encerrada.

## 7. Pendências/desvios
Prévia só escolhe contas de aluno ativas. Troca encerra o log anterior; aba abandonada conserva ended_at vazio até saída/troca, sem inventar horário de término. Login foi alinhado aos papéis da aplicação, sem tratar is_staff isolado como produtor. Link antigo do aviso de erro Vimeo corrigido para suporte real. Não houve conflito que exigisse alterar autenticação; o desenho do plano foi mantido.

## 8. Commit
feat: previa de membro somente leitura etapa 2.10; hash na entrega/diário. Sem push/merge.
