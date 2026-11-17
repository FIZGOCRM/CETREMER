# Etapa 1.15 — navegação, busca, conta e acesso

## 1. O que foi feito
Header e barra móvel com seções V1, estado ativo e avatar completo. Meus cursos tem rota própria, modal e expansão. Busca real em aulas/módulos próprios com cadeado futuro. Minha conta usa layout de membros, valida e-mail/imagem/CPF, salva preferências e senha. Login do aluno em duas metades, marca de pulso/check extraída do protótipo; login GoMut separado para produtor. Recuperação e primeiro acesso reais no mesmo estilo. Marca vem de SiteSettings. Rotas antigas de vitrine redirecionam para acesso privado.

## 2. Arquivos
users/{forms,services,views,test_member_navigation,test_login_redesign}.py; courses/{views,student_views,certificate_views,selectors,tests}.py; courses/templatetags/cetremer.py; core/{urls,test_handoff_phase0}.py; static/css/gomut/{members,member-login}.css; static/gomut/marca/pulse-check.svg; templates/{base_auth_member,base_gomut,base_membros,login,login_admin}.html; templates/users/settings.html; templates/courses/{my_courses,search,access_pending,course_detail,dashboard,ebooks,feature_pending,final_assessment,lesson_locked,material_unavailable}.html; templates/partials/gomut/{brand,member_header,lesson_notes,my_plans}.html; templates/registration/{first_access,password_reset_form,password_reset_done,password_reset_confirm}.html e password_reset_{email,subject}.txt; este relatório.

## 3. Migrações
Nenhuma. Logo é SVG nativo do protótipo; marca enviada nas configurações substitui o símbolo/nome padrão. Nenhuma biblioteca nova.

## 4. Testes
279 testes, zero falhas/erros. Oito novos em users/test_member_navigation.py, RED→GREEN: telas sem CSS legado/itens externos, busca isolada/rascunho/liberação, marca configurada, preferências, e-mail inválido, login, compatibilidade e rotas privadas. Corrigida validação de CPF com pontuação: normalizar antes do full_clean, detectado pelo teste existente. Asserts antigos de CSS público/landing foram ajustados à V1 privada. makemigrations sem alterações.

## 5. Causas e efeitos
Matrícula ausente não conduz mais a uma oferta de compra; recusa em tela de membros. Rascunho não entra na busca. Campo vazio de CPF conserva o já cadastrado, sem expor CPF completo no HTML da conta. Serviço mantém a elegibilidade histórica dos certificados e atualiza dados sem reescrever certificados emitidos. Links de suporte corrigidos.

## 6. Como conferir na tela
1. /login/: marca Emergensimples, painel vermelho/quadrícula à esquerda e formulário carvão à direita, topos alinhados. Esqueci minha senha e Recebi um código usam fluxos reais; Acesso do produtor abre GoMut (?acesso=admin).
2. aluno@gomut.example → header/barra móvel: navegar por todas as seis seções. Meu cursos abre modal e permite expandir.
3. Lupa → buscar Introdução ou nome de módulo. Sem matrícula/rascunho não aparece; futuro mostra cadeado.
4. Avatar → Minha conta: salvar e-mail, dados pessoais, preferências e senha. Vencimento não pode ser desligado.
5. Chrome390/1440: nove páginas públicas/privadas200, sem overflow/erroJS; login desktop e Meus cursos inspecionados visualmente.

## 7. Pendências/desvios
Login do produtor permanece com visual GoMut aprovado. Vitrine e página de venda antigas ficam fora da navegação V1 e suas URLs conduzem à área privada; dados legados preservados. Trilhas/Minha lista retornam404; notificações/ajuda antigas redirecionam aos recursos reais. Cadastro público legado permanece sem link no produto, sem conceder matrícula. Plano real e SMTP dependem de entradas externas. Não há mais cetremer.css nas telas ativas do aluno ou de recuperação/primeiro acesso; templates legados não servidos permanecem no repositório.

## 8. Commit
feat: navegacao e acesso de membros da etapa 1.15; hash na entrega/diário. Sem push/merge.
