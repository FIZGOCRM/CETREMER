# Asaas: infraestrutura de integração preparada

Esta etapa entrega consultas, registros técnicos e recepção de eventos. **Não cria cobranças/assinaturas no Asaas, não aprova pedidos e não renova acesso.** O checkout continua indisponível enquanto as regras comerciais são confirmadas e o fluxo financeiro não está implementado.

## Organização

| Componente | Responsabilidade |
| --- | --- |
| `sales/integrations/asaas/config.py` | Configuração única do servidor, ambiente, validação e indicadores públicos sem segredos. |
| `sales/integrations/asaas/client.py` | Consultar cobrança por ID e pesquisar por referência, com transporte injetável, timeout e destinos fixos. |
| `sales/integrations/asaas/dto.py` | Converter a resposta em metadados tipados: ID, cliente, valor, status, meio, vencimento e referência. |
| `sales/gateway_models.py` | Cobranças locais de integração, tentativas de conferência e caixa de entrada de eventos. |
| `sales/payment_services.py` | Preparação local idempotente e conferência de correspondência com o provedor. |
| `sales/webhook_services.py` | Minimização, impressão de conteúdo e persistência idempotente por ambiente/ID. |
| `sales/webhook_views.py` | Adaptador HTTP que autentica, limita e recebe JSON; não executa regras financeiras. |

Os models técnicos são descobertos pelo Django através de `sales/models.py`. A migration `sales.0005_gateway_records_webhook_inbox` cria as estruturas. Foi verificada em banco de teste; antes de atualizar uma instalação real, fazer backup e aplicar `python manage.py migrate` no ambiente correspondente.

## Configuração única

Configurar no ambiente protegido do servidor ou `.env` não versionado:

```dotenv
ASAAS_ENVIRONMENT=sandbox
ASAAS_API_ENABLED=False
ASAAS_API_KEY=
ASAAS_WEBHOOK_ENABLED=False
ASAAS_WEBHOOK_TOKEN=
ASAAS_TIMEOUT=10
```

- API e webhook ficam desativados por padrão e possuem habilitação independente. Alterar essas flags não disponibiliza criação de cobranças nesta versão.
- Os únicos ambientes aceitos são `sandbox` e `production`, associados aos hosts HTTPS oficiais. A integração não aceita URL base configurável nem segue redirecionamentos. O cliente envia `access_token` e `User-Agent`; requisições GET não têm body. [Autenticação Asaas](https://docs.asaas.com/docs/autentica%C3%A7%C3%A3o-1).
- `ASAAS_API_KEY` é a credencial da conta daquele ambiente. Não inserir no frontend, logs ou repositório. [Gestão de chaves](https://docs.asaas.com/docs/chaves-de-api).
- `ASAAS_WEBHOOK_TOKEN` é um segredo próprio de 32 a 255 caracteres, sem espaços, diferente da chave da API. A implementação aceita caracteres ASCII imprimíveis. Configurar o mesmo valor como token de autenticação do webhook. O Asaas o envia em `asaas-access-token`. [Recepção de eventos](https://docs.asaas.com/docs/receba-eventos-do-asaas-no-seu-endpoint-de-webhook).
- Timeout de 1 a 30 segundos, padrão 10. Falhas são classificadas sem persistir mensagens ou respostas brutas que possam conter segredos.

Os campos históricos de gateway em `CreatorProfile` e `SiteSettings` foram preservados no banco, mas **não são consultados pela integração nem editados pelo painel/Django Admin**. Não há fallback automático para esses valores. Uma futura remoção dos campos exige revisão própria dos dados.

O painel mostra somente ambiente e se a configuração local está habilitada. Isso não comprova conexão, aprovação da conta ou homologação.

## Webhook: recebimento não é aprovação

Rota preparada: `POST /webhooks/asaas/`.

1. Validar a configuração e comparar o token antes de ler/persistir o evento.
2. Em produção, exigir que o Django reconheça HTTPS. A configuração de um proxy confiável deve ser tratada na implantação; não confiar em headers encaminhados por qualquer origem.
3. Aceitar somente JSON até 128 KiB e validar campos do envelope.
4. Preservar apenas campos permitidos: identidade/referência do recurso, valores, estado, datas financeiras e detalhes reduzidos de estorno/encargos. Dados de cartão, tokens, documentos e o payload bruto completo não são armazenados.
5. Persistir com unicidade de ambiente + ID do evento e responder HTTP 200. Reenvio equivalente retorna 200 sem criar outro registro. Divergência nos metadados suportados retorna 409, preservando o primeiro evento. Diferenças apenas em campos descartados não constituem conflito.

Eventos desconhecidos são guardados com o envelope mínimo, sem executar efeitos. Os registros permanecem em `received` e **ainda não existe worker de aprovação financeira**. Eventos de split e outros produtos fora do escopo não têm tratamento financeiro. O payload minimizado não substitui um arquivo integral do evento nem a consulta do estado atual na API.

O Asaas recomenda persistir e confirmar a recepção antes de processamento demorado; eventos podem ser reenviados. [Funcionamento de webhooks](https://docs.asaas.com/docs/about-webhooks). Campos financeiros conhecidos e eventos de estorno são descritos na [referência de cobranças](https://docs.asaas.com/docs/webhook-para-cobrancas).

| Resposta | Significado nesta implementação |
| --- | --- |
| 200 | Persistido ou reenvio equivalente. Não significa matrícula liberada. |
| 400 / 413 / 415 | Evento inválido, corpo excessivo ou tipo de conteúdo incorreto. |
| 401 | Token inválido ou ausente. |
| 405 | Método diferente de POST. |
| 409 | Mesmo ID com metadados suportados divergentes; revisar. |
| 503 | Recepção desativada/configuração incompleta ou persistência falhou. Não confirmar como recebido. |

Não cadastrar um webhook de produção como fluxo financeiro ativo nesta etapa. A homologação externa precisa de uma conta Sandbox, credenciais próprias e URL pública; nenhum webhook foi cadastrado/publicado automaticamente por este trabalho.

## Preparação e conferência de cobranças

`prepare_charge()` cria somente um registro local associado a um **Order pendente**, com valor/meio já determinados pelo pedido, cliente esperado, vencimento e uma referência UUID. Repetir a preparação com os mesmos dados reutiliza o registro; dados divergentes exigem revisão. Esse serviço ainda não está ligado ao checkout.

`reconcile_charge()` consulta o recurso por ID ou, quando ainda não existe vínculo externo, pesquisa pela referência local. A pesquisa é limitada e nunca gera uma nova cobrança após timeout. A API oferece consulta por ID e filtro `externalReference` para recuperação pontual: [consulta individual](https://docs.asaas.com/reference/recuperar-uma-unica-cobranca), [pesquisa de cobranças](https://docs.asaas.com/reference/listar-cobrancas).

Para associar a cobrança externa, a conferência exige ID compatível, referência, cliente, valor, meio, vencimento e assinatura de origem quando aplicável. Resultado ambíguo ou divergente fica em revisão. Ambiente incorreto é rejeitado antes da chamada externa. Falha de comunicação gera tentativa com código seguro; não há repetição automática de criação.

Estados técnicos:

- `pending`: ainda não consultado.
- `verified`: correspondência conferida; **não equivale a Order COMPLETED**.
- `review`: divergência ou ambiguidade que precisa de intervenção.
- `error`: consulta falhou ou recurso ainda não foi localizado.

Comandos operacionais, após aplicar as migrations:

```powershell
# Apenas listar a quantidade selecionada, sem rede nem gravação
python manage.py reconcile_asaas_charges --dry-run

# Conferir até 20 pendentes/falhas no ambiente habilitado
python manage.py reconcile_asaas_charges --limit 20

# Conferir um registro local específico, inclusive se já foi verificado
python manage.py reconcile_asaas_charges --charge 123
```

O limite máximo é 100 por execução. O comando não é agendado automaticamente. Cobranças, tentativas e eventos podem ser inspecionados no Django Admin, sem edição/exclusão por esses formulários.

## O que continua faltando

- Respostas sobre recorrência contínua ou prazo fixo, preços, cancelamento e condições finais.
- Cadastro/vínculo do pagador e contratação real com Pix/cartão, incluindo autorização do aluno.
- Criação de cobranças/assinaturas, checkout hospedado e configuração efetiva do webhook no Asaas.
- Processador financeiro para mapear eventos/consultas em transações de pedido e períodos de acesso, com testes de renovação, atraso, estorno e contestação.
- Homologação com uma conta Sandbox real e posterior implantação/monitoramento em produção.

Os testes desta etapa usam transporte simulado e SQLite temporário. Não comprovam homologação junto ao Asaas. Credenciais, dados reais de alunos e base operacional não foram utilizados.
