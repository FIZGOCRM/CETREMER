# Etapa 2.3 — Básico e Visão geral

## 1. O que foi feito
Edição básica GoMut com capa, publicação, duração, carga horária e descrição da formação. Abas do curso. Visão geral com acessos ativos, aulas publicadas/rascunhos, dúvidas, chamados dos alunos, liberações futuras, Vimeo ausente e vencimentos. Valores reais em selectors; dados legados de venda/sala preservados sem aparecer no formulário.

## 2. Arquivos
painel/{forms,selectors,urls,test_course_design}.py; painel/views/course_management.py; templates/painel/{course_edit,course_tabs,course_overview,dashboard}.html; static/css/gomut/panel-v1.css; este relatório.

## 3. Migrações
Nenhuma.

## 4. Testes
285 testes, zero falhas/erros. Dois novos RED→GREEN: indicadores/liberação e formulário que preserva campos legados. Os dois testes da2.2 permanecem verdes.

## 5. Causas e efeitos
Ativo depende do AccessPeriod, não só existência de matrícula. Publicada exige aula+módulo publicados. Próximas liberações calculadas por início original de cada plano. Campos foraV1 omitidos do ModelForm, para não zerar os dados existentes ao salvar.

## 6. Como conferir
admin@gomut.example → Meus cursos → curso → Básico/Visão geral. Conferir números e ferramentas; salvar descrição/capa/publicação; ver conteúdo e planos pelos atalhos. Chrome390/1440: ambas as telas200, sem overflow/erroJS; Visão geral desktop inspecionada.

## 7. Pendências/desvios
Ticket não possui curso no modelo aprovado; o indicador é explicitamente Chamados dos alunos deste curso, filtrado pelas matrículas. Não se inventou vínculo direto de chamado com curso. Aulas sem vimeo_id contam como sem Vimeo. Agenda e demais abas serão migradas nas fatias correspondentes.

## 8. Commit
feat: basico e visao geral GoMut etapa 2.3; hash na entrega/diário. Sem push/merge.
