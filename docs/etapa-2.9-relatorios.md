# Etapa 2.9 — relatórios reais

## 1. O que foi feito
Acessos diários únicos, últimos7dias, horas por StudyDay, progresso médio, aprovação pela melhor nota, aulas mais concluídas, alunos sem registro recente e vencimentos com progresso. Períodos7/30/90dias e CSV autenticado. Registro diário mínimo de visitas reais, sem reconstrução de histórico. Exportação neutraliza fórmulas em textos de usuário.

## 2. Arquivos
users/models.py e visit_middleware.py; users/migrations/0013_daily_student_visits.py; core/{settings,csv_export}.py; painel/{reporting,test_reporting,urls}.py; painel/views/{reports,students}.py; templates/{base_painel_gomut,painel/reports}.html; static/css/gomut/panel-v1.css; este relatório.

## 3. Migrações
users.0013: StudentVisit(student,date,first_at), único por aluno/dia. Aplicada somente demo; schema vazio pela suíte. Histórico começa nesta versão, sem backfill por last_login ou duração cadastrada.

## 4. Testes
307 testes, zero falhas/erros. Cinco novos RED→GREEN: visita diária/sem escrita em preview, horas reais/publicação, melhor nota por aluno, acesso/CSV seguro e últimos7dias. CSV de relatório baixado pelo navegador e lido: seis colunas, formato consistente. Makemigrations correspondente gerado e aplicado na demo.

## 5. Causas e efeitos
Conclusão manual não fabrica horas. Rascunho não entra no denominador acadêmico. Duas tentativas do mesmo aluno contam uma pessoa na aprovação. Ausência de histórico não é tratada como acesso antigo inventado. Registro de visitas ignora respostas com erro, POST e modo visualização. CSV não executa texto como fórmula ao abrir numa planilha.

## 6. Como conferir
admin@gomut.example → Relatórios; escolher7/30/90dias, conferir gráfico e tabelas, Exportar CSV. Valores demo refletem QA: um aluno acessou hoje; conclusão manual pode coexistir com zero horas creditadas. Chrome390/1440 em7/30dias200, sem overflow/erroJS; relatório desktop e download real conferidos.

## 7. Pendências/desvios
A contagem diária não existia. Foi acrescentado apenas StudentVisit, necessário para medir sem inventar passado; sem IP, aparelho ou identificação adicional. Progresso e melhores conclusões mostram situação atual; gráfico/horas respeitam o período selecionado e últimos7dias tem rótulo próprio. Sem registro recente significa ausência no novo histórico, não prova de que o aluno nunca fez login antes. Perfil de produção ainda não foi importado.

## 8. Commit
feat: relatorios reais GoMut etapa 2.9; hash na entrega/diário. Sem push/merge.
