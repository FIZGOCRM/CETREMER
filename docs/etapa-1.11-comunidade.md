# Etapa 1.11 — comunidade

## 1. O que foi feito
Comunidade com filtros, busca, tópicos próprios/Geral, solução, votos útil e fixados. Publicação e resposta verificam plano ativo; encerrados conservam leitura dos cursos que possuem. Assinaturas mentor/equipe mantêm o autor real. Moderação preserva textos ocultos. Painel encaminha com nota interna, responde, marca solução, oculta/reabre e destaca espera superior a 24 h. Início mostra os quatro tópicos recentes e curso/aula têm atalho contextual.

## 2. Arquivos
community/{models,views,access,services,selectors,forms,test_v1,tests}.py; community/migrations/0004_community_v1.py; users/models.py e migrations/0010_community_v1.py; core/{urls,test_handoff_phase0}.py; courses/{student_views,tests,test_access_periods}.py; courses/management/commands/prepare_demo.py; painel/views/community.py; templates/community/{hub,new_topic,topic,post_card}.html; templates/painel/community.html; templates/courses/{dashboard,course_detail,lesson_detail}.html; static/css/gomut/members.css; este relatório.

## 3. Migrações
community.0004: solução, marcação, fixado, status/nota/encaminhamento; Comment.display_as/is_hidden; Helpful com alvo exclusivo e unicidade por usuário. users.0010: mentor_display_name, mentor_label, team_display_name. Aplicadas na demo, schema vazio na suíte.

## 4. Testes
243 testes, zero falhas/erros; dez novos em community/test_v1.py, primeiros oito RED→GREEN. Cobrem acesso direto alheio, plano encerrado, ocultação conservada, solução autor/equipe, assinatura falsa, nota interna, voto único, validação, outra resposta/tópico e destaque 24 h. Fixtures antigas ajustadas aos mínimos de texto, papel ADMIN e leitura após encerramento exigidos pela V1. Foi corrigida a codificação UTF-8 de arquivos escritos pelo helper local antes da suíte final.

## 5. Causas e efeitos
C21: oculta tópico/resposta sem apagar texto. C22: leitura e mutações recusam curso sem matrícula. C23: conserva leitura após encerramento e bloqueia escrita. C24: selector do painel identifica espera de mais de 24 h. Solução oculta deixa de ser solução; aluno não assina pela equipe nem marca a própria resposta.

## 6. Como conferir na tela
1. aluno@gomut.example → /community/: filtrar, buscar e abrir os tópicos demo.
2. Nova dúvida: escolher curso, carregar aulas desse curso se necessário, título ≥8 e texto ≥15. Há aviso sobre dados de pacientes. O atalho na aula já preenche curso/aula.
3. admin@gomut.example → /painel/comunidade/: encaminhar com nota interna; responder como mentor/equipe; marcar solução, fixar, ocultar e reabrir.
4. Aluno lê a resposta sem ver observação interna; autor pode marcar resposta de outra pessoa como solução e votar útil.
5. Chrome 390/1440: lista, formulário, detalhe, painel, Início e curso HTTP200, sem overflow/erro JS; capturas em .venv/v1-qa/.

## 7. Pendências/desvios
Notificações entram na 1.14; visual final do painel na Fase 2. Nomes demo só são preenchidos pelo prepare_demo quando vazios. Aluno sem qualquer plano iniciado também fica em leitura: a publicação requer ao menos um acesso permitido, sem conceder acesso novo. Ocultação e encaminhamento mantêm autor/texto, sem exclusão.

## 8. Commit
feat: comunidade e moderacao da etapa 1.11; hash na entrega/diário. Sem push/merge.
