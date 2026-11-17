# Etapa 1.16 — aguardando planilha real

## 1. O que foi feito
Verificada a dependência externa. O plano declara esta etapa bloqueada até a planilha chegar. Não foi inventada planilha de alunos, executada importação real nem enviado acesso real. Continuação autorizada das demais etapas.

## 2. Arquivos
Este relatório. Os importadores existentes continuam identificados em users/importing.py, users/services.py e painel/views/students.py; nenhum desses foi modificado nesta etapa.

## 3. Migrações
Nenhuma.

## 4. Testes
Última suíte:279 testes, zero falhas/erros (etapa1.15). Nenhum teste novo, pois nenhuma implementação desta etapa foi executada.

## 5. Causas e efeitos
C1/C26/C27/C28 relativos à importação V1 aguardam o contrato da planilha e a prévia. O parser legado não equivale à importação de planos V1: não valida curso/início/fim por linha. Não usar a confirmação legada para migrar planos reais.

## 6. Como conferir
Consultar docs/etapa-0-preparacao-v1.md, seção de colunas. Proposta aprovada por recomendação: nome,email,cpf,telefone,curso,inicio_plano,fim_plano; uma linha por aluno/curso; início original dd/mm/aaaa; fim na interface inclusivo, convertido para exclusivo. CPF ausente/inválido deve ser aviso; aluno existente reutilizado; plano encerrado exige confirmação expressa. Antes de aplicar: prévia por linha com mês atual e módulos já liberados.

## 7. Pendências/desvios
Falta a planilha real. É necessário validar nomes de cursos, datas e duplicatas no arquivo recebido. Importação em produção continua exigindo confirmação explícita após o relatório de prévia. O usuário autorizou avançar nas partes independentes; isso não substitui a planilha nem a confirmação exigida para produção.

## 8. Commit
docs: registrar dependencia da etapa 1.16; hash na entrega/diário. Sem push/merge.
