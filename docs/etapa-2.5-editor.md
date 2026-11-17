# Etapa 2.5 — editor da aula

## 1. O que foi feito
Editor dedicado GoMut com conteúdo, módulo, situação, Vimeo, duração exata min:seg e PDF. Prévia incorporada sem rastrear aluno. Quiz e avaliação no novo layout. Troca do primeiro PDF conserva sua identidade; materiais adicionais legados preservados. URL antiga ?aula=ID redireciona ao editor.

## 2. Arquivos
painel/{forms,urls,test_lesson_editor}.py; painel/views/{lessons,course_management}.py; courses/services.py; templates/painel/{lesson_edit,lesson_quiz,course_materials,course_lessons}.html; removido parcial transitório lesson_editor_legacy.html; static/css/gomut/panel-v1.css; este relatório.

## 3. Migrações
Nenhuma.

## 4. Testes
291 testes, zero falhas/erros. Quatro novos RED→GREEN: editor/prévia/duração, mover módulo e zerar posição, troca PDF sem duplicar material, rejeição PDF falso/módulo alheio sem gravar alterações. Corrigida conversão da ValidationError de modelo para erro de formulário detectada pelo upload inválido.

## 5. Causas e efeitos
C7 continua no serviço: trocar vídeo/duração zera retomada sem apagar conclusão. PDF validado antes de salvar alterações, transação conserva o estado em caso de erro. Módulo deve pertencer ao mesmo curso. Nova interface aceita links reais de vídeo Vimeo, não URLs arbitrárias. Gabarito continua só no painel autorizado.

## 6. Como conferir
admin@gomut.example → curso → Conteúdo → Editar aula. Ver duração1:02 da demo, prévia Vimeo, módulo/situação, e-book e Editar quiz. Salvar mudanças; para despublicar, escolher Rascunho. Quiz/avaliação conservam ações de criar/editar/ordenar/desativar. Chrome390/1440 em editor/quiz/materiais200, sem overflow/erroJS; editor desktop inspecionado.

## 7. Pendências/desvios
A troca de PDF atua no primeiro material, preservando extras legados e histórico de abertura. Arquivo anterior não é apagado do disco automaticamente. A duração é informada com precisão, sem arredondar62seg para minutos inteiros ao salvar. A prévia usa Vimeo sem heartbeat de aluno. Sem dependências novas.

## 8. Commit
feat: editor de aulas GoMut etapa 2.5; hash na entrega/diário. Sem push/merge.
