# QA — histórico de estudo ilustrativo

Solicitação posterior do usuário: preencher os gráficos para visualizar seu funcionamento. Trata-se de mock intencional e identificado, exclusivamente na conta `aluno@gomut.example` da base de demonstração. Não é backfill de métricas reais nem evidência de estudo ocorrido.

## Dados disponíveis

- 111 minutos (1h51) nos últimos sete dias e 47 minutos na semana anterior.
- Sequência de quatro dias com pelo menos um minuto.
- Histórico variado nas últimas 12 semanas: 62 dias preenchidos, dias sem atividade e cinco níveis no mapa.
- O tempo ilustrativo foi associado às aulas fictícias já concluídas, como revisões. As conclusões e posições existentes não foram alteradas.
- A identificação “Dados ilustrativos de demonstração” aparece junto aos indicadores na conta fictícia, somente com modo de demonstração habilitado.

## Como reproduzir

Na base isolada e com `GOMUT_DEMO_MODE=True`, usar o comando já existente, agora com opção explícita:

```powershell
.venv/Scripts/python.exe -B .venv/run_v1.py prepare_demo --password "<senha-para-novas-contas>" --with-study-history
```

Sem essa opção o comando não adiciona o histórico. A senha é usada somente para contas novas e não é redefinida em reexecuções. Não usar `seed.py`.

Registros diários existentes são preservados. Apenas o tempo de novos registros ilustrativos é somado às aulas fictícias concluídas; repetir no mesmo dia não aumenta as métricas. Se o QA já mudou todas as aulas para não concluídas, o comando recusa preencher esse histórico até haver uma aula fictícia concluída, preservando as alterações. A transação do comando reverte qualquer preenchimento parcial nessa recusa.

## Verificação

Quatro testes novos: opção explícita/métricas/níveis do mapa, reexecução sem sobrescrever edições nem contas alheias, proteção da identidade fictícia e identificação visual restrita ao modo demo. A suíte completa passou com **347 testes**, sem falhas/erros; sem migração pendente.

Na base local foi conferido antes/depois: conclusões, posições dos vídeos, períodos, avaliações e certificados preservados. SMTP continua sem configuração; nenhum e-mail foi enviado.

Chrome em 390 e 1440 px: Início e Meu progresso com sete barras, 84 células e cinco níveis de cor, sem overflow horizontal ou erro JS. Atualizar essas páginas para visualizar os dados. Capturas em `.venv/v1-qa/mock-study-*`.

Arquivos: `courses/demo_study.py`, `courses/management/commands/prepare_demo.py`, `courses/selectors.py`, `courses/test_demo_preparation.py`, `templates/partials/gomut/study_summary.html` e documentação de QA. Sem dependência nova ou migração.
