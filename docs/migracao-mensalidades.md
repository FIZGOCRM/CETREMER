# Preparação de mensalidades e migração

Esta etapa prepara a base para mensalidades independentes por curso e compra avulsa. Não chama o Asaas, não gera pedidos pagos e não encerra a renovação na Eduzz/Hotmart. O checkout continua indisponível.

## Estrutura

- `sales.Offer`: curso, modalidade mensal/avulsa, preço e termos. Ofertas começam inativas. Uma oferta mensal com recorrência “a confirmar” não pode ser ativada pela validação do modelo. A compra avulsa exige prazo de acesso antes da ativação.
- `sales.Subscription`: contrato independente por matrícula, valor acordado, próximo vencimento e situação da renovação anterior. Importações ficam **em migração**, sem identificador de assinatura no gateway.
- `courses.AccessPeriod`: intervalo quitado, origem, referência idempotente e quem o importou. O fim é exclusivo internamente; os dados importados e o painel apresentam o último dia quitado inclusive.
- `courses.access`: decisão central de acesso em cada requisição. Não exige agendador para perceber o vencimento. O futuro agendamento de cobranças continua sendo outra responsabilidade.

O serviço de migração valida e grava tudo em uma transação. Matrículas atuais sem prazo não são convertidas automaticamente; uma revisão específica deve decidir como migrá-las. Um contrato/período divergente é rejeitado, não substituído.

## Fluxo no painel

1. Aplicar as migrations no ambiente da instalação antes de usar a versão atual: `python manage.py migrate`. Elas foram verificadas em banco de teste; não foram aplicadas em uma base operacional nesta etapa. Fazer backup antes de atualizar uma instalação com dados.
2. Em `/painel/alunos/importar/`, baixar o modelo **mensalidades** e selecionar **Migração de mensalidades quitadas**.
3. Preencher uma linha por aluno/curso. Usar o identificador de curso exibido na própria tela. O mesmo aluno pode aparecer em dois cursos com datas e valores diferentes.
4. Ler o arquivo e conferir a prévia. Nenhum aluno, período ou contrato é criado nessa leitura. Se um novo arquivo falhar, a prévia anterior é descartada para evitar confirmação acidental do arquivo antigo.
5. Corrigir linhas com erro. Duplicidade do mesmo aluno/curso invalida ambas as linhas, para não escolher uma quitação pela ordem do arquivo. Até 50 linhas são exibidas; o total é informado e o arquivo completo precisa ser conferido.
6. Marcar a revisão explícita e confirmar. A transação importa apenas linhas válidas. Se houver conflito com um contrato ou matrícula existente, nenhuma linha dessa transação é gravada.
7. Abrir o detalhe do aluno para conferir acesso quitado, próximo vencimento e situação de migração. Para novos alunos sem senha, gerar o código de primeiro acesso pelo fluxo existente.

## CSV

Modelo: `static/modelos/migrar-mensalidades.csv`.

| Coluna | Conteúdo |
| --- | --- |
| nome | Nome do aluno, obrigatório. |
| email | E-mail do aluno, normalizado sem diferenciar maiúsculas. |
| curso | Slug exato do curso exibido no painel. |
| pago_de | Primeiro dia efetivamente quitado, inclusive. |
| pago_ate | Último dia efetivamente quitado, inclusive. |
| proximo_vencimento | Dia imediatamente seguinte a pago_ate. Divergências exigem revisão, não cálculo automático de 30 dias. |
| mensalidade | Valor positivo, sem símbolo monetário, com ponto decimal. |
| plataforma | eduzz, hotmart ou other. |
| assinatura_anterior | Referência externa, opcional; não é uma credencial. |
| renovacao_anterior | pendente, ativa ou encerrada. É uma informação da operação, não um cancelamento executado. |

Datas em `AAAA-MM-DD` ou `DD/MM/AAAA`. CSV UTF-8 (ou Latin-1), separado por vírgula ou ponto e vírgula. Limites: 5 MB e 5000 linhas, sem truncamento silencioso no modo de mensalidades. Não incluir dados de cartão ou chaves de API.

Arquivos com as colunas financeiras do modelo não são aceitos no modo de liberação administrativa, evitando que a seleção errada gere acesso sem prazo.

Reimportar um registro idêntico não duplica período ou contrato. `89.9` e `89.90` são tratados como o mesmo valor. Mudanças de quitação, preço ou situação anterior não são aplicadas por reimportação; exigem revisão explícita. No Django Admin é possível consultar períodos e contratos, e atualizar a informação de renovação anterior; isso não cancela nada externamente.

## Exemplo de acesso

Período quitado: **10/11 a 09/12**, inclusive. Próximo vencimento: **10/12**.

- Até 09/12: acesso quitado.
- De 10/12 a 12/12: três dias corridos de tolerância.
- Em 13/12: acesso suspenso apenas para esse curso se não houver outro período válido.

Aulas, progresso, ao vivo, comunidade do curso e emissão de novos certificados consultam a mesma regra. Conta, matrícula, progresso e certificados existentes são preservados. Matrículas administrativas sem prazo continuam liberadas.

## Limites e próxima etapa

A expiração de acesso funciona mesmo sem gateway conectado. Não iniciar a transição financeira real sem preparar o fluxo de renovação e o atendimento aos alunos; os testes desta etapa não importaram alunos reais.

- Confirmar recorrência contínua ou número fixo de pagamentos, valores reais e políticas comerciais antes de habilitar novas contratações.
- Não presumir transferência de cartão/autorização de outra plataforma. Preparar a nova forma de pagamento e coordenar o encerramento das renovações anteriores separadamente.
- Implementar cliente Asaas, cobrança, webhook autenticado, renovação de períodos e reconciliação. Nesta etapa nenhum desses caminhos chama serviços externos.
- O estado “renovação anterior encerrada” é declaratório. Não é prova automática de cancelamento e não cria assinatura no Asaas.
- A consulta dos períodos usa o fuso configurado no Django (`America/Campo_Grande`) e dias de calendário; o próximo ciclo não é inferido a partir da data da migração.
- Links de PDFs em `media/` já conhecidos não se tornam privados apenas por bloquear a página da aula. Entrega autenticada de materiais e proteção do armazenamento precisam de uma etapa específica antes de prometer revogação de downloads.
- Não foram importados alunos reais, aplicadas migrations na base operacional ou configuradas cobranças/agendamentos externos.
