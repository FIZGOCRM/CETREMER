# Etapa 2.2 — Meus cursos e Criar curso

## 1. O que foi feito
Cursos em cartões com capa, aulas, alunos e situação; busca/categoria e cartão de criação. Formulário de criação GoMut com dados básicos/capa/duração, sem venda/checkout. Criação reutiliza save_course e começa em rascunho.

## 2. Arquivos
templates/painel/{courses,course_create}.html; painel/views/course_management.py; painel/test_course_design.py; core/test_handoff_phase0.py; static/css/gomut/panel-v1.css; este relatório.

## 3. Migrações
Nenhuma.

## 4. Testes
283 testes, zero falhas/erros. Dois novos em painel/test_course_design.py: visual/formulário e persistência rascunho. Teste da interface observado RED→GREEN; regra existente de criação já passava. Asserts da base migrada ajustados.

## 5. Causas e efeitos
Não publica curso vazio automaticamente; preço/vitrine não aparecem na criação V1. Busca permanece no servidor e cartões mostram contagens reais.

## 6. Como conferir
admin@gomut.example → Meus cursos → Criar curso. Informar nome, descrição, categoria, duração e capa; salvar. O curso aparece como rascunho. Chrome390/1440: lista/criação200, zero errosJS. Detectado overflow de label sr-only no filtro móvel e corrigido; nova conferência sem overflow.

## 7. Pendências/desvios
Edição do curso existente migra na2.3. Nenhuma dependência instalada ou regra duplicada. Dados reais não alterados.

## 8. Commit
feat: cursos e criacao GoMut etapa 2.2; hash na entrega/diário. Sem push/merge.
