# Etapa 2.1 — estrutura do painel GoMut

## 1. O que foi feito
Nova base clara, logo GoMut, header/conta, menu responsivo e barra lateral fixa248px. Contadores reais de Comunidade, Chamados e Vencimentos30dias. Dashboard sem métricas de venda, com cursos/alunos/acessos reais. Separação de identidade do aluno. Permissão do painel por ADMIN/CREATOR, sem conceder acesso por is_staff isolado.

## 2. Arquivos
templates/base_painel_gomut.html; templates/base_gomut.html; templates/painel/dashboard.html; static/css/gomut/panel-v1.css; static/js/gomut/panel.js; painel/{selectors,test_shell_v1}.py; painel/views/overview.py; core/{context_processors,decorators,test_handoff_phase0}.py; este relatório.

## 3. Migrações
Nenhuma.

## 4. Testes
281 testes, zero falhas/erros. Dois novos RED→GREEN: base/contadores e negação para aluno com is_staff. Contrato antigo do dashboard atualizado para a nova base; telas não migradas continuam na base anterior por enquanto.

## 5. Causas e efeitos
Contadores consideram novos+encaminhados, chamados abertos+em análise e planos terminando em30dias. Não contam vendas fictícias. Toda rota de gestão segue o decorator central por papel.

## 6. Como conferir
admin@gomut.example → /painel/. Conferir logo, barra248px, números reais e menu da conta. Em390px, abrir/fechar menu pelo botão; em1440px, lateral fixa. Chrome390/1440 sem overflow/erroJS; dashboard inspecionado. Header Visualizar como membro conduz à escolha de aluno; modo completo será ligado na2.10.

## 7. Pendências/desvios
Migração das demais telas ocorre nas próximas fatias. Botão de prévia ainda leva à tabela de escolha, sem simular sessão de aluno. Nenhuma regra de planos foi duplicada.

## 8. Commit
feat: estrutura GoMut do painel etapa 2.1; hash na entrega/diário. Sem push/merge.
