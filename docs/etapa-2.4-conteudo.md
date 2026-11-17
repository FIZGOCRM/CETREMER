# Etapa 2.4 — conteúdo, módulos e aulas

## 1. O que foi feito
Lista GoMut com módulos/aulas, situação e mês de liberação. Criação rápida sempre em rascunho. Janelas de módulo e confirmação de impacto no novo layout. Avaliação final depois dos módulos. Reordenação por arraste/teclado com feedback e validação central em serviço.

## 2. Arquivos
courses/services.py; painel/views/course_management.py; painel/test_content_design.py; templates/painel/{course_lessons,module_confirmation,lesson_editor_legacy}.html; static/css/gomut/panel-v1.css; static/js/{painel-grade,gomut/panel}.js; este relatório.

## 3. Migrações
Nenhuma.

## 4. Testes
287 testes, zero falhas/erros. Dois novos RED→GREEN: estrutura/posição da avaliação e criação rápida que não aceita módulo alheio nem publicação forjada. Teste existente de reordenação integral/ID alheio passa após mover regra ao serviço.

## 5. Causas e efeitos
Publicação/liberação e impacto continuam nos serviços1.2. Rascunho rápido não libera conteúdo acidental. Reordenação rejeita lista incompleta, duplicatas e IDs alheios, numa transação. Erro de rede não mostra Ordem salva.

## 6. Como conferir
admin@gomut.example → curso → Conteúdo. Editar módulo abre janela; criar rascunho; arrastar ou usar setas na alça. Abrir Avaliação final no fim. Chrome390/1440 sem overflow/erroJS. QA de teclado enviou200 ao mover e200 ao restaurar a ordem; janela nativa aberta/fechada. O helper de QA inicialmente usou locator first dinâmico após mover e foi corrigido para ID estável antes da conferência final.

## 7. Pendências/desvios
Editor de aula legado foi isolado como parcial transitório para não quebrar ?aula=ID antes da2.5, quando será substituído pelo editor dedicado. Overflow de input sr-only corrigido no CSS do novo formulário. Nenhum dado real alterado.

## 8. Commit
feat: conteudo GoMut da etapa 2.4; hash na entrega/diário. Sem push/merge.
