# Preparação de assinaturas e migração de acesso

**Objetivo:** suportar contratos por curso e preservar períodos quitados fora do CETREMER, sem gerar cobranças.

**Arquitetura:** ofertas e contratos em sales; matrículas e períodos de acesso em courses; política de acesso central e verificações por requisição; parser e serviço de migração separados das views. SQLite e templates existentes permanecem.

**Requisitos confirmados:** mensalidade independente por curso; previsão de compra avulsa; Pix e cartão; tolerância de 3 dias corridos para renovação; acesso importado até fim do período pago; cobrança seguinte não pode ser antecipada pela data da migração.

**Pendências:** recorrência contínua ou número fixo de pagamentos; preços e dados reais; gateway e encerramento de cobranças anteriores. Contratos importados ficam em migração com termo desconhecido, nunca automaticamente ativos no gateway.

## Decisões de implementação

- Datas de acesso: início inclusivo e fim exclusivo internamente. CSV usa pago_de/pago_ate inclusivos; proximo_vencimento deve ser pago_ate + 1 dia. Nunca inferir 30 dias.
- Preservar matrículas atuais como acesso administrativo sem prazo. Só o modo explícito de migração cria acesso por períodos; não converter uma matrícula existente sem prazo silenciosamente.
- Uma linha por aluno/curso; repetir e-mail em cursos diferentes é permitido. Reimportação idêntica não duplica contratos ou períodos; divergências exigem revisão, não sobrescrevem quitação.
- Oferta mensal importada é rascunho e contrato fica MIGRATING. Informação de renovação antiga é anotação de operação, não cancelamento externo.
- Três dias de tolerância contados a partir do primeiro dia não quitado. Cancelamento/cronograma financeiro não serão implementados enquanto o modelo comercial não estiver confirmado.
- GETs de conteúdo consultam o acesso sem apagar matrícula, progresso ou certificados já emitidos. Bloquear aulas, alterações de progresso, links ao vivo e comunidade específica do curso expirado. Certificados existentes continuam consultáveis.
- Sem alteração na segurança de arquivos estáticos/media nesta etapa: links de PDFs já conhecidos não se tornam privados apenas por verificar matrícula na página. Documentar esse limite para a etapa de armazenamento privado.

## Tarefas e verificação

- [x] 1. Models e migrations: Offer, Subscription, AccessPeriod e política da matrícula; validações e restrições de datas/valores; teste de migração preservando registros existentes.
- [x] 2. Política de acesso: testes de início/fim/tolerância e independência por curso; ligar aulas, progresso, ao vivo, comunidade e emissão de novos certificados à política.
- [x] 3. Migração: parser CSV explícito, prévia sem escrita, validação integral, serviço transacional idempotente; preservar próximo vencimento e nenhum Order/Asaas criado.
- [x] 4. UI: modo de importação, modelo CSV, datas e status na prévia/detalhe administrativo e aviso de acesso na área do aluno; nenhuma cobrança fictícia.
- [x] 5. Suite completa, system check, migrations sem diferenças, revisão independente final e documentação de uso/limites.

## Arquivos previstos

courses/models.py, courses/access.py, courses/services.py, courses/student_views.py, courses/certificate_views.py; community/views.py; sales/models.py, sales/migration_import.py, sales/migration_services.py; painel/views/students.py; templates de importação/acesso/cards; migrations e testes associados.

## Registro

Usuário autorizou prosseguir enquanto confirma os dados com o médico. Aplicação e validação de migrations somente em banco de teste; não criar/popular base operacional nem chamar serviços externos. Execução inline com planejamento e TDD.


## Verificacao final

- Suite completa: 90 testes, OK (SQLite de teste).
- System check Django: sem problemas. makemigrations --check --dry-run: nenhuma diferenca de modelos/migrations.
- Ruff F/I e formatacao dos modulos desta etapa: sem erros.
- git diff --check: sem erros de espacos; Git informa conversao normal LF/CRLF no template.
- Migrações 0009 de courses e 0004 de sales verificadas em testes. Teste com MigrationExecutor confirmou preservacao de matricula antiga sem prazo e progresso.
- Revisao independente encontrou tres casos corrigidos e testados: normalizacao monetaria para idempotencia, colisao com oferta ativa e duplicidade conflitante aluno/curso.
- Navegador Edge headless: fluxo real de login, upload, previa, revisao, confirmacao e detalhe; SQLite temporario e dados ficticios. Sem pedidos ou assinaturas no gateway.
- Layout conferido em 320, 375, 768 e 1440px. Corrigido minimo intrinseco da coluna do menu responsivo, que provocava overflow horizontal herdado.
- JavaScript do artefato HTML deve continuar independente do servidor. Guia atualizado com etapa de mensalidades.
- Nao existe db.sqlite3 operacional neste workspace. Nenhuma base real foi criada, migrada ou populada e nenhum servico externo foi chamado.

## Limites registrados

Sem criacao de cobrancas, cliente Asaas, webhook ou renovacao automatica de periodos. Ofertas e contratos importados permanecem sem ativacao no gateway. Matrículas administrativas existentes continuam sem prazo; conversao exige revisao especifica. Entrega autenticada de PDFs por URL conhecida continua como etapa separada. A tolerancia de tres dias e registrada no periodo importado; mudancas futuras de politica precisam tratar explicitamente os periodos existentes. Informacao de renovacao anterior e declaratoria, sem cancelamento externo.
