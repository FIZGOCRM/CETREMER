# Etapa 1.8 — importação das perguntas

## 1. O que foi feito
- Comando import_quizzes com --dry-run, CSV UTF-8 e colunas do plano.
- Resumo por curso/aula e erros por linha; qualquer erro recusa o arquivo inteiro.
- Validação de curso, aula única pelo título exato, alternativas/correta e ordem repetida.
- Gravação em uma transação; prévia não escreve nem desativa nada.
- Perguntas anteriores ficam desativadas e alternativas/tentativas preservadas; dados importados deixam de ser demo.
- Quiz com tentativas reais não é sobrescrito nem desativado.
- Exemplo versionado em courses/tests/fixtures sem converter tests.py em pacote nem perder testes existentes.

## 2. Arquivos
- `courses/management/commands/import_quizzes.py`
- `courses/quiz_importing.py`
- `courses/services.py`
- `courses/test_quiz_import.py`
- `courses/tests/fixtures/quizzes-exemplo.csv`
- `docs/etapa-1.8-importacao-perguntas.md`

## 3. Migrações
Nenhuma. Reutiliza os modelos e serviços das fatias anteriores.

## 4. Testes
219 testes, zero falhas/erros; nove novos em courses/test_quiz_import.py. Primeiro RED: comando inexistente; negativos passaram a exigir os motivos específicos. Cobrem prévia sem escrita inclusive com quiz a desativar, fixture versionada, arquivo válido aula/final, erro que recusa tudo, ordem/correta/título ambíguo, bloqueio por tentativa real, substituição demo e rollback após falha de gravação no segundo quiz. A suíte cria schema vazio.

## 5. Causas e efeitos
Preserva C16/C17: tentativas/notas não recalculadas nem apagadas. Mesmo uma tentativa real iniciada e não finalizada bloqueia a sobrescrita. O exemplo de rollback comprova que não sobra o primeiro quiz se a segunda gravação falhar.

## 6. Como conferir
1. Não há tela nova: a etapa é um comando. Configure o ambiente da base demo conforme o projeto; nunca use seed.py.
2. `python manage.py import_quizzes "caminho/perguntas.csv" --dry-run`
3. Confira o resumo de perguntas, erros e desativações antes da execução sem --dry-run.
4. Sem erros: `python manage.py import_quizzes "caminho/perguntas.csv"`.
5. No painel, abrir a aula → Gerenciar quiz, ou Avaliação final do curso, para conferir as perguntas. No aluno, continuam valendo as regras de liberação.
6. Foi executada prévia real na base demo com as quatro perguntas finais do protótipo: válida e sem gravação. A importação com escrita foi validada somente no banco isolado dos testes. Nada foi importado na produção nem sobrescrito na demo nesta fatia.

## 7. Pendências, formato e cuidados
Perguntas reais continuam pendentes. Nos cursos presentes no arquivo, a regra “aula que não aparece no CSV fica sem quiz” é aplicada por desativação dos quizzes de aula não citados; a prévia lista cada um. Outros cursos e avaliação final omitida não são alterados. Caso isso atingisse quiz com tentativa real, o arquivo inteiro é recusado.

Há títulos repetidos de aula na demonstração atual. O CSV continua exatamente no formato aprovado, sem coluna extra: o importador recusa a aula homônima e informa o motivo. Antes de importar perguntas reais, diferencie os títulos pelo painel ou traga uma decisão de formato; não escolhe a primeira aula por conta própria.

A conta fictícia reconhecida para distinguir tentativas demo é exclusivamente o par gomut-demo-student + aluno@gomut.example; todas as outras são tratadas como reais, inclusive contas com endereços de exemplo em testes. A criação de dados continua em prepare_demo; este comando importa somente o conteúdo explicitamente fornecido.

O uso acima será incorporado ao manual na 1.17. Nenhuma dependência nova.

## 8. Commit
Commit único `feat: importacao transacional de perguntas da etapa 1.8`; hash na entrega/diário. Sem push/merge.
