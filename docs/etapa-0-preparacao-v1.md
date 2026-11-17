# Etapa 0 — Preparação V1 GoMut / Emergensimples

Fonte de decisão: `docs/handoff v1 oficial/prompt-implementacao-gomut_3.md`, lido integralmente (815 linhas). Esta entrega executa somente a Etapa 0. A Etapa 1.1 não foi iniciada.

## 1. O que foi feito

1. Inventariado o estado local anterior e separadas fontes, documentação e dados locais.
2. Mostrada previamente a lista de arquivos com aparência de banco, upload ou credenciais.
3. Protegidos no ignore os dados locais e registros temporários; nenhum upload novo foi incluído.
4. Instalado o HTML entregue como protótipo-v2/index.html, byte a byte igual à origem.
5. Preservado o protótipo antigo com nota no README de sua pasta.
6. Criado docs/decisoes-produto.md com as seções 1, 4 e 5 integrais do plano.
7. Conferidos os 27 identificadores do aluno e os 16 do painel.
8. Executada a suíte completa: 138 testes, zero falhas.
9. Auditados os dois modelos CSV e o ciclo atual de AccessPeriod.
10. Nenhum modelo, regra de acesso, importador ou interface real foi modificado nesta etapa.

## 2. Arquivos criados e alterados

Criados nesta etapa:
- `docs/decisoes-produto.md`.
- `docs/handoff-design/prototipo-v2/index.html` — cópia exata de `docs/handoff v1 oficial/area-do-aluno.html`.
- `docs/handoff-design/prototipo-v2/README.md` — procedência e mapa dos 43 identificadores com linhas.
- `docs/handoff-design/prototipo/README.md` — aviso de referência histórica.
- `docs/etapa-0-preparacao-v1.md` — este relatório.
- `docs/etapa-0-arquivos-versionados.md` — manifesto completo, agrupado por código/documentação/configuração.

Alterado nesta etapa:
- `.gitignore` — proteção adicional de bancos SQLite/sidecars, media, variantes de ambiente e .superpowers. O exemplo de ambiente continua permitido.

O commit também registra o código, assets, testes e documentos que já estavam pendentes ANTES desta etapa. Esses arquivos estão discriminados no manifesto; registrá-los em Git não significa que foram implementados na Etapa 0.

Não incluídos:
- `.venv/`, incluindo banco e configuração com segredos locais.
- `.superpowers/`, caches, arquivos de ambiente reais e uploads novos.

Constatações do histórico: `data_dump.json` e 7 arquivos de `media/` já eram versionados. Não foram alterados, removidos ou acrescentados neste trabalho. A nova regra de ignore não remove arquivos já existentes no histórico.

O modelo `.env.example` foi conferido: os campos de chaves e tokens estão vazios. README, roteiro de demonstração e testes contêm credenciais fictícias de exemplo; essa categoria foi apresentada antes do commit. Não foram colocadas credenciais reais no relatório.

## 3. Migrações

Nenhuma migração criada na Etapa 0. Nenhum campo/modelo da Etapa 1.1 foi acrescentado.

Migrations que já existiam sem commit e são apenas preservadas no checkpoint:
- `courses/migrations/0009_access_periods.py`: política de acesso da matrícula e AccessPeriod.
- `sales/migrations/0004_offers_subscriptions.py`: Offer e Subscription.
- `sales/migrations/0005_gateway_records_webhook_inbox.py`: registros de cobrança, tentativa e evento.

A suíte criou seu banco isolado em memória do zero e passou. A base de demonstração foi consultada somente por SQLite `mode=ro`, com `query_only=ON`; as migrations acima já constam como aplicadas nela. Não foi reaplicada migração nem escrita na base de demonstração nesta etapa.

## 4. Testes

- Suíte completa: **138 testes; 0 falhas; 0 erros**.
- Nenhum teste novo: não houve novo comportamento da aplicação.
- Protótipo-v2 abriu no Chrome em 390 e 1440 px, sem erro JavaScript observado na abertura.
- SHA-256 da cópia e da origem iguais.
- Todos os 43 identificadores exigidos foram localizados.
- git diff --cached --check apontou somente uma linha em branco preexistente no fim de static/css/gomut/base.css. O arquivo foi preservado; a conferência com core.whitespace=-blank-at-eof passou, sem outros erros de whitespace.

Isso é linha de base, não homologação das funcionalidades futuras que o protótipo apenas simula.

## 5. Causas e efeitos cobertos

Não foi alegada nova cobertura dos casos C1–C30: eles pertencem às etapas futuras indicadas pelo plano.

Foram mantidos os testes existentes de isolamento por curso, vencimento e tolerância (`courses/test_access_periods.py`), registro manual (`painel/test_access_period_management.py`) e importação (`sales/test_migration.py`, `painel/tests.py`). Eles verificam o comportamento antigo; NÃO comprovam encerramento antecipado, reativação com limite, correção auditada ou a futura importação da V1.

Leitura da base demo: 2 matrículas com política periods; cada uma tem exatamente um período; zero matrículas sem período e zero matrículas com múltiplos períodos. Isso evita uma decisão de consolidação nessa base específica; não autoriza pressupor o mesmo em outra instalação.

## 6. Como conferir na tela

1. Abra `docs/handoff-design/prototipo-v2/index.html` no navegador. A tela de escolha e os usuários dessa página são simulações de referência, não contas do produto.
2. Abra a referência do aluno e confira Início, curso, progresso e player; os IDs estão no README da pasta.
3. Abra a referência do painel no mesmo HTML e confira cursos, alunos e configurações. Não há ligação com o banco Django.
4. Para conferir a aplicação real sem mudar dados: acesse `http://127.0.0.1:8016/login/` com o aluno fictício `aluno@gomut.example`; veja seus dois cursos e o progresso atual.
5. No painel real, entre com `admin@gomut.example`, abra `/painel/alunos/` e consulte o aluno fictício. O registro atual de períodos continua igual; não há ainda botões da V1 para encerrar/reativar/corrigir.
6. Use as credenciais locais já entregues; nenhuma senha foi copiada para este relatório.
7. A aparência da aplicação NÃO muda nesta etapa. A referência nova não foi ligada às views nem seus scripts foram copiados para static/.

## 7. Pendências, conflitos e opções — resposta à pergunta 1

### A. Modelo de períodos atual versus plano único auditável

Arquivos: `courses/models.py:258`, `courses/models.py:289`, `courses/services.py:142`, `courses/access.py:20`; plano, seção 4 e Etapa 1.1.

Hoje uma matrícula pode ter vários períodos e o serviço acrescenta intervalos não sobrepostos. O plano pede um único período corrente, que pode ser encerrado, reativado e corrigido com AccessChange.

Opções para decisão antes da 1.1:
- A: atualizar o mesmo período corrente, exclusivamente por serviços transacionais, guardando o antes/depois em AccessChange. A recusa de sobreposição continua para a criação de períodos adicionais; não é aplicada como se a edição criasse outro intervalo.
- B: manter versões de períodos imutáveis, com identificação explícita da versão vigente. Isso exigiria ampliar o desenho de dados do plano e alterar access_decision, que hoje considera todos os períodos.

Nenhuma opção foi implementada ou escolhida. A opção A acompanha o desenho de período único do plano, mas muda o serviço atual de somente acrescentar e precisa de confirmação conforme a regra de conflitos.

### B. Matrículas históricas sem período ou com vários períodos

Arquivos: `courses/models.py:258`, `courses/access.py:23`, `sales/migration_services.py`, Etapa 1.1.

A migração pede obter plan_started_on do período mais antigo, mas não define o que fazer quando não há período. UNRESTRICTED libera acesso independentemente de datas. Também não define consolidar vários períodos sem apagar histórico.

Opções: manter casos sem dados pendentes para preenchimento manual; ou fornecer datas explícitas para migração. Para múltiplos períodos, aprovar a escolha do período corrente e a preservação dos anteriores. Não deduzir início por enrolled_at sem decisão.

Na base demo esses casos não ocorrem. Seus períodos atuais são de demonstração, de aproximadamente 30 dias; ainda é necessário decidir se a 1.1 preserva essas datas ou as altera explicitamente para demonstrar 12 meses. Não vou ampliá-las silenciosamente.

### C. Qual é o fim original após uma correção?

Arquivos: `courses/models.py:289`; plano Etapa 1.1, reactivate_plan e correct_plan_dates; C13.

O modelo não guarda um limite original. O plano limita a reativação ao fim original, mas permite corrigir o fim.

Opções: fim da criação inicial, recuperado do evento created; ou fim corrigido, considerado a data contratual correta e registrado no histórico. Falta confirmar qual prevalece após uma correção legítima.

### D. Inclusividade da data de fim da planilha

Arquivos: `static/modelos/importar-alunos.csv`, `painel/forms.py:11`, `courses/services.py:142`; plano Formatos esperados e Etapa 1.1.

Hoje o formulário usa último dia quitado inclusivo e converte para ends_on exclusivo. O serviço futuro descreve ends_on exclusivo, mas o CSV só diz data de fim.

Opções: `fim_plano` ser último dia de acesso inclusivo, convertido pelo importador; ou ser o primeiro dia sem acesso, exclusivo. Precisa ser aprovado antes de escrever o contrato do importador. Encerrar hoje deve bloquear hoje, sem acrescentar um dia nem tolerância.

### E. Contato de suporte necessário já na 1.1

Arquivos: `users/models.py:72`; plano Etapa 1.1 e Fase 2.8.

SiteSettings possui whatsapp e configuração de remetente SMTP, mas não possui e-mail próprio de suporte. A tela de plano encerrado pede esse contato na 1.1.

Opções: aprovar campo dedicado support_email já na 1.1; ou definir explicitamente outra fonte/condição de omissão até o contato ser informado. Não reutilizar remetente SMTP como se fosse suporte sem decisão.

### F. Campos ausentes na importação

Arquivos: `users/importing.py:39`, `users/services.py:69`, `painel/views/students.py:231`, `users/models.py:25`.

O importador atual escolhe cursos globalmente para todo o arquivo, rejeita o mesmo e-mail repetido e não armazena telefone. Isso conflita com duas linhas por aluno/curso da V1.

Opções: um modo V1 separado ou evolução do modo atual preservando compatibilidade explicitamente. Em ambos, a futura unicidade de linha precisa considerar e-mail + curso. Não há alteração do CSV nem do parser nesta etapa; a proposta está abaixo e aguarda aprovação.

### G. Ambiguidade futura na regra ended sem duração

Fonte: plano, Critérios técnicos e Etapa 1.3; `static/js/aluno.js`.

O texto permite ended quando não há duration_seconds, mas também exige ao menos 50% creditado. Falta a duração de referência para calcular esse percentual.

Opções: definir como obter/validar a duração antes de calcular os 50%; ou explicitar uma exceção quando não existir duração. Nada desta etapa implementa telemetria ou muda a conclusão atual.

### Conflitos já resolvidos pela autoridade do plano

O login novo da Etapa 1.15 difere do login verde do handoff antigo; a prioridade do V1 é explícita. Não pedi nova decisão e não alterei o login agora. Trilhas, vitrine, áreas, favoritos e o gateway continuam fora do trabalho V1, mesmo que constem do protótipo.

A regra genérica de acesso deve ser lida junto às exceções expressas para aluno encerrado: progresso, certificados, conta e suporte continuam acessíveis e comunidade é só leitura. As views atuais ainda não implementam esse conjunto. Isso será tratado nas etapas indicadas, não adiantado na preparação.

## 8. Commit

Um único commit de Etapa 0, com prefixo docs:, na branch `feat/area-aluno-handoff`, registrará o checkpoint e a preparação. Seu hash é informado na entrega da conversa. Sem push ou merge.

## Colunas atuais e proposta — resposta à pergunta 2

### Modelo administrativo atual

Arquivo: `static/modelos/importar-alunos.csv`.

Cabeçalho exato: `nome,email,cpf`.

| Coluna | O que aceita hoje |
|---|---|
| nome | Texto aparado. O parser também aceita aliases como name, nome completo, cliente e comprador. Não obriga que o cabeçalho/nome estejam preenchidos. |
| email | Cabeçalho obrigatório; e-mail validado, aparado e normalizado para minúsculas. Aceita aliases e-mail, email do comprador e email do cliente. Diferencia usuário novo, aluno existente e outra conta. E-mail repetido no arquivo é marcado como erro. |
| cpf | Opcional. Aceita pontuação, normaliza os 11 dígitos e valida dígitos verificadores. CPF inválido vira vazio silenciosamente, sem o aviso específico que a V1 exige. Aceita documento, cpf/cnpj e documento do comprador como aliases, embora o validador aceite CPF, não CNPJ. |

Arquivo atual: vírgula ou ponto e vírgula detectados; UTF-8 com/sem BOM ou fallback Latin-1. O parser para após 5000 linhas. Os cursos são escolhidos na tela, não por coluna. Cabeçalhos financeiros são recusados nesse modo para evitar liberação sem prazo.

### Proposta para aprovação; não aplicada

Cabeçalho proposto: `nome,email,cpf,telefone,curso,inicio_plano,fim_plano`.

| Coluna | Situação | Contrato proposto conforme o plano |
|---|---|---|
| nome | Manter | Nome completo do aluno. |
| email | Manter | Identificador do usuário; reutilizar conta de aluno existente. |
| cpf | Manter, melhorar prévia na 1.16 | Opcional; inválido/vazio importa sem CPF e gera aviso explícito. |
| telefone | Nova | Texto opcional; formato/normalização e campo de armazenamento ainda precisam de definição. Não converter em número nem presumir E.164. |
| curso | Nova neste modelo | Slug exato do curso. Uma linha por aluno/curso, permitindo e-mail igual em cursos diferentes. |
| inicio_plano | Nova | Data original de início, dd/mm/aaaa. Não usar a data da importação. |
| fim_plano | Nova | Opcional, dd/mm/aaaa; vazio usa início + Course.plan_months. Inclusividade aguarda a decisão D. |

Meses devem usar calendário, não blocos de 30 dias. O plano define o tratamento de dia inexistente para liberação mensal; a convenção de cálculo e exibição de fim precisa ficar consistente com ends_on exclusivo.

Há também o modelo legado `static/modelos/migrar-mensalidades.csv`, que NÃO é a planilha V1:
`nome;email;curso;pago_de;pago_ate;proximo_vencimento;mensalidade;plataforma;assinatura_anterior;renovacao_anterior`.

Esse modelo trata quitação financeira externa e Subscription. Não será imposto à V1, que exclui gateway e renovação. Nenhuma coluna de mensalidade, plataforma ou vencimento recorrente foi proposta para a nova planilha.

## AccessPeriod — resposta à pergunta 3

**Não atende integralmente a encerrar, reativar e corrigir com histórico hoje.**

| Regra/ação | Estado atual | Consequência para a 1.1 |
|---|---|---|
| Início inclusivo / fim exclusivo | Existe; starts_on <= hoje < ends_on | Compatível, desde que o formulário/CSV tenham conversão explícita. |
| Tolerância | Campo configurável; serviço manual grava 3 dias | Suporta 3 no fim natural e zero no antecipado, mas não distingue os motivos hoje. |
| Sobreposição | Recusada no serviço de concessão, não por constraint SQL | Criar outro intervalo não serve para substituir/corrigir o corrente. |
| Um período por matrícula | Não é imposto; relação é 1:N | Precisa de regra de serviço/migração aprovada para V1. |
| Encerrar antecipadamente | Não existe serviço nem motivo de encerramento | Acrescentar um intervalo mais curto não bloqueia o intervalo original. |
| Reativar até fim original | Não existe; fim original não é registrado | Precisa de limite e política da decisão C. |
| Corrigir datas | Alteração direta no modelo é tecnicamente possível, mas sem trilha | Exige serviço com motivo e AccessChange; não usar update direto sem histórico. |
| Histórico auditável | Só created_at/created_by/source/reference do período | Não registra valores anteriores, ação, motivo ou autor de cada mudança. |
| Preservação do progresso | Registros separados da matrícula/período | Pode ser mantida; não apagar matrícula nem período para simular cancelamento. |

O modelo tem constraint de datas válidas e unicidade em matrícula + origem + referência. O PROTECT protege a relação na exclusão do pai, não cria auditoria de edições do próprio período. A checagem atual considera QUALQUER período ativo e depois QUALQUER tolerância: guardar versões antigas sem excluí-las da decisão de acesso permitiria acesso indevido após encerrar.

A solução fica pendente das decisões A–D. **Etapa 1.1 não iniciada.**
