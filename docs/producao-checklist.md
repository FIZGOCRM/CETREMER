# Produção — checklist de preenchimento

Este documento não publica o sistema. Preencha com quem opera o servidor. A demo local e seus usuários não são dados de produção. Pagamento/checkout permanecem fora da V1.

| Item | Definição / evidência |
|---|---|
| Responsável pela operação | ____________________ |
| Servidor / provedor | ____________________ |
| Sistema e versão | ____________________ |
| Servidor de aplicação WSGI / processo de inicialização | ____________________ |
| Proxy e terminação HTTPS | ____________________ |
| Domínio público | ____________________ |
| Domínio liberado na privacidade do Vimeo | ____________________ |
| Pasta do código / release | ____________________ |
| Disco local persistente do SQLite | ____________________ |
| Caminho absoluto do SQLite | ____________________ |
| Pasta persistente de media/ | ____________________ |
| Pasta protegida de backups | ____________________ |
| Cópia externa dos backups | ____________________ |
| Frequência / retenção / perda de dados aceitável | ____________________ |
| Data do teste real de restauração em ambiente separado | ____________________ |
| SMTP / remetente verificado no SiteSettings | ____________________ |
| Envio real de teste e recebimento confirmado | ____________________ |
| Importação real: prévia aprovada e confirmação explícita | ____________________ |

O Django necessita de um processo Python WSGI e acesso ao disco persistente. O projeto não inclui receita de implantação no provedor escolhido. Separar banco do processo de aplicação por compartilhamento remoto de arquivo SQLite não é a operação documentada; banco e aplicação devem usar disco local persistente. Proxy/CDN pode ficar à frente, sem tornar media/materials público.

## Ambiente — nomes, sem valores

O código lê SECRET_KEY, FIELD_ENCRYPTION_KEY, DEBUG, ALLOWED_HOSTS, DJANGO_DATABASE_PATH, GOMUT_DEMO_MODE. Guardar chaves fora do Git; preservar a chave de criptografia em restaurações. DEBUG deve estar desligado; ALLOWED_HOSTS deve conter somente hosts aprovados. GOMUT_DEMO_MODE desligado em produção.

A fundação de pagamentos também lê ASAAS_ENVIRONMENT, ASAAS_API_ENABLED, ASAAS_API_KEY, ASAAS_WEBHOOK_ENABLED, ASAAS_WEBHOOK_TOKEN, ASAAS_TIMEOUT. Na V1, API e webhook devem continuar desativados. Não cadastrar credenciais reais nem ativar checkout como parte deste checklist.

CSRF_TRUSTED_ORIGINS é uma configuração Django ainda não carregada por variável de ambiente neste projeto. Definir no settings de produção quando o domínio/HTTPS forem conhecidos; apenas criar uma variável com esse nome hoje não altera a configuração. Também definir SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, redirecionamento HTTPS e HSTS de acordo com o proxy. Não confiar indiscriminadamente em cabeçalhos de origem para detectar HTTPS.

SMTP fica no SiteSettings, com senha criptografada; nenhum valor deve ir para documento, commit, print ou chamado público.

## Arquivos e proxy

- [ ] NEGAR /media/materials/ antes de qualquer regra genérica que sirva /media/. Não redirecionar para um diretório público, bucket público ou CDN.
- [ ] PDFs servidos exclusivamente por /materiais/lesson/ID/ e /materiais/course/ID/, que validam sessão, matrícula, plano e liberação.
- [ ] Não cachear /materiais/, páginas privadas ou respostas autenticadas na CDN. Confirmar Cache-Control private,no-store para PDFs.
- [ ] Validar sem sessão: URL privada leva ao login e caminho direto do arquivo responde404/403.
- [ ] Servir static/ coletado separadamente, sem confundir com uploads privados.
- [ ] Persistir media/, aplicar permissões mínimas e limitar tamanho de upload no proxy conforme MATERIAL_MAX_MB e IMAGE_MAX_MB do settings.
- [ ] Não usar runserver em produção. Executar migrations do release com backup e janela planejada.

## Agendamentos

| Comando (ambiente da aplicação) | Frequência | Agendamento / responsável |
|---|---|---|
| python manage.py run_daily_notifications | Diário, no fuso da plataforma | ____________________ |
| python manage.py run_live_reminders | A cada15min | ____________________ |
| python manage.py backup_sqlite CAMINHO-NOVO.sqlite3 | Conforme política, ao menos diário proposto | ____________________ |

Nomes de backup devem ser novos (ex.: data/hora), fora de diretórios públicos. O comando não sobrescreve arquivos. Não foram criados agendamentos automaticamente. Inspecionar execução/saída e EmailLog, não presumir que um cron agendado executou.

## Backup e restauração

O comando usa a API de backup SQLite e verifica integridade. Preservar media/ e chaves por meios seguros. Instruções existentes: [operação e restauração](operacao-sqlite.md). Testar restauração em instalação separada; só depois planejar uma troca em produção. Não copiar o banco aberto com um comando genérico nem misturar WAL/SHM de bases diferentes. Registrar último backup válido e testar login, matrícula, planos, progresso, certificados e PDFs restaurados.

## Conferência antes de liberar

- [ ] python manage.py check --deploy com o ambiente final, sem avisos não avaliados.
- [ ] HTTPS, cookies, CSRF e hosts aprovados conferidos pelo endereço público.
- [ ] Vimeo liberado no domínio final e retomada/progresso conferidos.
- [ ] Backup e restauração testados; dados reais só após prévia aprovada.
- [ ] Fluxo aluno de1/2cursos; plano futuro/ativo/encerrado; módulo futuro; certificado; suporte privado.
- [ ] Visualizar como membro bloqueia escrita e não altera métricas.
- [ ] SMTP recebido de verdade e logs coerentes; sem SMTP permanece not_sent.

## Diagnóstico local de implantação (17/11/2026)

check --deploy no ambiente de demonstração retornou seis avisos: security.W004 (HSTS), W008 (redirecionamento HTTPS), W009 (qualidade da chave local), W012 (cookie de sessão seguro), W016 (cookie CSRF seguro), W018 (DEBUG ligado). Não houve correção com valores de produção desconhecidos. O código de saída do check foi0 com avisos; isso NÃO significa ambiente pronto para publicar.
