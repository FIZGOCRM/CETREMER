# Etapa 2.6 — Alunos e Vencimentos

## 1. O que foi feito
Tabela GoMut, filtros, paginação e seleção de aluno. Gestão do plano em janela com início/fim/encerramento/reativação/correção/observação/histórico pelos mesmos serviços. Novo cadastro manual exige início original e cria plano auditado. Primeiro acesso/recuperação registra resultado e data sem persistir token; sem SMTP oferece código seguro para entrega externa. Vencimentos no novo layout.

## 2. Arquivos
painel/{forms,test_student_design}.py; painel/views/{students,plans,common}.py; users/{services,notifications,test_first_access}.py; core/test_handoff_phase0.py; templates/{base_panel_embed,painel/students,painel/plan,painel/plan_dialog,painel/expirations}.html; static/{css/gomut/panel-v1.css,js/gomut/panel.js}; este relatório.

## 3. Migrações
Nenhuma. EmailLog registra o resultado de cada envio; created_at é a data do registro após a tentativa. Token/código não é armazenado no log nem retentado automaticamente.

## 4. Testes
296 testes, zero falhas/erros. Cinco novos em test_student_design.py: tabela/modal, criação com datas, preservação de plano existente, falta de SMTP e envio confirmado sem token persistido. Quatro começaram RED; contrato SAMEORIGIN adicionado RED→GREEN para permitir somente incorporação na própria origem. Fixture antiga de primeiro acesso agora fornece data explícita.

## 5. Causas e efeitos
Sem data, não cria aluno/matrícula. Plano existente não é substituído pelo formulário de cadastro. C29: console não conta como envio. Logs de acesso sem token não entram na retentativa automática; o administrador solicita novo link/código. Plano/histórico continuam centralizados e a janela mantém autenticação/CSRF.

## 6. Como conferir
admin@gomut.example → Alunos; filtrar, selecionar aluno e Configurar plano. Janela abre/fecha e permite as ações. Cadastro exige início e fim opcional. Enviar primeiro acesso sem SMTP mostra código (somente naquele momento); aluno com senha usa recuperação. Vencimentos abre a mesma janela. Chrome390/1440 em tabela/seleção/vencimentos/embed sem overflow/erroJS. QA abriu janela, salvou observação temporária e restaurou o valor original, sem mudar datas; fechamento confirmado.

## 7. Pendências/desvios
Importação real permanece1.16 pendente. Link de importação legado retirado da navegação V1 para não confundir cadastro simples com planos novos; implementações legadas e seus testes conservados, sem execução real. Janela usa documento do mesmo domínio com X-Frame-Options SAMEORIGIN só no endpoint de plano; demais páginas conservam proteção padrão. Cadastro manual agora usa create_plan, sem conceder acesso indefinido. CPF do aluno na seleção aparece mascarado.

## 8. Commit
feat: alunos e planos GoMut etapa 2.6; hash na entrega/diário. Sem push/merge.
