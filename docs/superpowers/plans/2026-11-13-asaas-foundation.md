# Asaas: consultas, configuração e caixa de entrada de eventos

**Objetivo:** preparar infraestrutura técnica sem criar cobranças ou renovar acessos antes da confirmação comercial.

**Arquitetura:** configuração única por ambiente do servidor; cliente HTTP somente de consulta com transporte injetável; DTOs para respostas; registros de cobranças/tentativas e inbox de webhook no app sales; serviços sem request/response; views e comandos como adaptadores. Django e SQLite permanecem.

## Contrato e limites

- API e webhook desativados por padrão, habilitação separada. Ambiente explicitamente sandbox/production; hosts HTTPS fixos, sem base URL arbitrária nem redirecionamentos.
- Fonte única: ASAAS_* em settings/ambiente. Campos históricos SiteSettings/CreatorProfile não são lidos pela integração nem alterados pelo painel; preservados no esquema para revisão posterior.
- Asaas usa access_token e User-Agent na API. Webhook usa asaas-access-token com segredo próprio (32–255 caracteres sem espaços, diferente da API key). Produção exige HTTPS no endpoint, respeitando configuração de proxy da instalação.
- Cliente consulta cobrança e pesquisa por referência; mapeia timeout, autenticação, limite, indisponibilidade e formato inválido em erros seguros. Nenhuma repetição automática de escrita; métodos de criação permanecem bloqueados nesta entrega.
- Inbox autenticada: JSON limitado, ID único por ambiente, conteúdo mínimo permitido, sem dados de cartão/documentos ou headers. Mesmo ID/conteúdo é aceito sem duplicar; mesmo ID com metadados financeiros suportados diferentes exige revisão (409), preservando o primeiro.
- HTTP 200 confirma somente persistência. Inbox não altera Order, Subscription ou AccessPeriod. Nenhum worker financeiro é ativado nesta etapa.
- Conciliação manual consulta API e confere ID/referência, cliente, valor, meio, vencimento e assinatura quando aplicável. Guarda observação do provedor e tentativa; divergências ficam para revisão. Não marca pedido como pago nem cria período.
- Sem credenciais reais, chamadas externas, publicação de webhook, criação de conta ou mudança em banco operacional.

## Tarefas

- [x] 1. Configuração + cliente: testes RED/GREEN de hosts, headers, timeout, erros sem segredos, JSON e consultas; criação bloqueada.
- [x] 2. Persistência + conciliação: migrations, vínculos e referências, tentativas, pesquisa de recuperação e verificações de identidade. Não alterar estados financeiros ou acesso.
- [x] 3. Webhook: método/autenticação/limites/validação, deduplicação por ambiente, minimização e conflitos; CSRF isento apenas nessa rota, autenticada pelo segredo do webhook.
- [x] 4. Painel/comandos/documentação: estado técnico sem credenciais no HTML, remoção de edição dos campos antigos, consulta operacional limitada e manual.
- [x] 5. Suite completa, migrations/check/lint, revisão independente e documentação de ativação segura no Sandbox.

## Revisão de falhas

Credenciais em erro/repr/redirect; troca de ambiente; evento falso/duplicado/reordenado; ID colidindo com conteúdo diferente; corpo excessivo; evento autenticado não implicando matrícula; consulta sem correspondência; criação duplicada após timeout; nova rotina não sobrescrever configurações legadas ou expor tokens.

## Referências oficiais consultadas em 13/11/2026

- https://docs.asaas.com/docs/autentica%C3%A7%C3%A3o-1
- https://docs.asaas.com/docs/receba-eventos-do-asaas-no-seu-endpoint-de-webhook
- https://docs.asaas.com/docs/about-webhooks
- https://docs.asaas.com/reference/recuperar-uma-unica-cobranca
- https://docs.asaas.com/reference/listar-cobrancas
- https://docs.asaas.com/docs/chaves-de-api

## Registro

Usuário autorizou esta sequência enquanto confirma regras com a Iza. Execução inline com planejamento e TDD. Repositório contém mudanças anteriores da mesma conversa, que serão preservadas. Homologação real com Sandbox depende da conta/chave/URL e não será alegada a partir de mocks.


## Evidencias finais

- Suite completa: 123 testes, OK, em 17.491 segundos; banco de teste destruido ao fim.
- System check Django: sem problemas. makemigrations --check --dry-run em memoria: nenhuma diferenca.
- Migration sales.0005_gateway_records_webhook_inbox gerada e exercitada pela suite; nao aplicada em base operacional.
- Ruff F/I nos modulos da etapa: sem erros. git diff --check: sem erros de espacos (apenas aviso normal de LF/CRLF em template anterior).
- Revisao independente confirmou limites e apontou um P2: divergencias de netValue/estornos ignoradas no fingerprint. Corrigido com regressao RED/GREEN; a whitelist foi ampliada para valores e detalhes financeiros reduzidos, sem dados de cartao/documento. Campos fora da whitelist continuam descartados e nao participam da comparacao.
- Casos adicionais exercitados: chave reconhecida de producao nao enviada a Sandbox, HTTP incompleto convertido em erro seguro, falha de persistencia nao confirmada, CSRF mantido nos outros endpoints e administracao legada oculta/preservada.
- Painel renderizado em navegador Edge headless, 320/375/768/1440px sem overflow; inspecao visual da secao Asaas realizada.
- Artefato HTML atualizado: 16 secoes, IDs unicos e JavaScript validado pelo Node.
- Nao existe db.sqlite3 operacional no workspace. Nenhuma credencial real, aluno real ou chamada ao Asaas foi usada. Nao houve cadastro/publicacao de webhook nem agendamento automatico de comandos.

## Proxima entrega

Confirmar regras comerciais e implementar cliente/pagador, contratacao e criacao real de cobrancas, processamento financeiro dos eventos e concessao/renovacao transacional de acesso. Depois homologar com conta Sandbox real e preparar implantacao. verified permanece apenas uma verificacao de correspondencia, nunca aprovacao de Order. Inbox permanece em received sem worker financeiro nesta etapa.
