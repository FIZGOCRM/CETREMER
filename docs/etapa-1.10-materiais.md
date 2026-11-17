# Etapa 1.10 — materiais e e-books

## 1. O que foi feito
Biblioteca agrupada por curso, busca e filtros por tipo, curso e material aberto. PDFs servidos por endpoint autenticado, com matrícula/plano/liberação verificados. Upload, troca e remoção lógica de material do curso no painel. Arquivos ilustrativos criados apenas pelo prepare_demo. Links diretos de materiais bloqueados no Django.

## 2. Arquivos
courses/{models,forms,services,selectors,validators,material_views,demo_materials,test_material_library,test_demo_preparation}.py; courses/management/commands/prepare_demo.py; courses/migrations/0018_protected_material_library.py; painel/{forms,urls}.py; painel/views/materials.py; core/urls.py; templates/courses/{ebooks,material_unavailable,lesson_detail}.html; templates/painel/{course_materials,course_edit,course_lessons}.html; templates/partials/gomut/member_header.html; static/css/gomut/members.css; este relatório.

## 3. Migrações
courses.0018: CourseMaterial(course,title,file,order,is_active); MaterialOpen(student,material_kind,material_id,opened_at), unicidade aluno/tipo/material. Aplicada somente no banco demo; schema vazio coberto pela suíte.

## 4. Testes
233 testes, zero falhas/erros. Nove novos em test_material_library.py: streaming privado, abertura única, material do curso, visitante, equipe, remoção, mídia direta, módulo futuro e falso PDF. Primeiros seis observados RED→GREEN. makemigrations --check --dry-run sem alterações.

## 5. Causas e efeitos
Acesso encerrado usa a mesma decisão central de planos; matrícula alheia, rascunho e liberação futura recusados. Remoção lógica conserva arquivo e histórico. Nenhum link /media/materials/ é exposto na biblioteca.

## 6. Como conferir na tela
1. aluno@gomut.example → avatar → E-books (/dashboard/ebooks/).
2. Buscar e filtrar, Abrir PDF, retornar e usar Já abri; Ir para a aula abre o contexto correto.
3. admin@gomut.example → curso → Materiais do curso: enviar PDF, trocar ou remover.
4. Chrome 390/1440: páginas HTTP200, sem overflow nem erros JS. PDF protegido aberto e inspecionado no visualizador nativo do Chrome; estado Já abri confirmado. Capturas locais em .venv/v1-qa/.

## 7. Pendências/desvios
Produção: o servidor/proxy também deve NEGAR /media/materials/ antes de qualquer regra estática; servir PDFs exclusivamente pelo endpoint /materiais/. O bloqueio Django não protege uma regra externa de Nginx/CDN. PDFs não devem ser públicos/cacheados no CDN. Isso entrará no checklist 1.17.
LessonMaterial.url legado continua por redirecionamento autorizado sem busca remota; um URL externo é controlado pelo fornecedor e não equivale ao arquivo protegido no servidor. Novos materiais de curso usam upload PDF. Leitor avançado/progresso de páginas fora da V1. Nenhum dado real importado.

## 8. Commit
Commit único feat: biblioteca e materiais protegidos da etapa 1.10; hash na entrega/diário. Sem push/merge.
