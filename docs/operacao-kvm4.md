# Operação GoMut na KVM4 — Docker Compose e HTTPS

Atualizado em 17/11/2026 após a publicação dos dois portais HTTPS aprovados. Consulte o [relatório de execução](relatorio-publicacao-https.md) e a [configuração pública](publicacao-https.md). O domínio principal, www, e-mail e contratação não foram alterados. **Use o wrapper público nos comandos de operação; o Compose base sozinho não mantém a publicação HTTPS.**

## Implantação atual

| Item | Valor |
|---|---|
| VPS | `srv1149758`, Ubuntu 24.04.3 LTS, `72.60.151.178` |
| Gerenciamento da GoMut | **Docker Compose**, projeto `gomut-kvm4`; não cadastrada na interface Coolify |
| Release atual | `/srv/gomut/releases/20261117T202202Z` |
| Ponteiro ativo | `/srv/gomut/current` |
| Imagem de produção | `gomut:kvm4-https-20261117t202202z` |
| Release anterior privado | `/srv/gomut/releases/20261117T182000Z`, imagem `gomut:kvm4-20261117` |
| Runtime da imagem | Python 3.13.18, Django 5.2.19 LTS, Gunicorn 27.0.1, WhiteNoise 6.12.0 |
| Produção | `gomut-web`, HTTPS nos dois hosts via Traefik; backend em `127.0.0.1:18080` e rede Docker privada |
| Homologação | `gomut-homolog`, publicado somente em `127.0.0.1:18081` |
| Rotinas | `gomut-scheduler`, sem porta publicada, dados de produção |
| Usuário dos containers | UID/GID `10001:10001`, sem usuário SSH correspondente no host |

O Coolify/Traefik e os serviços dos demais projetos continuam independentes. Não reiniciar o proxy, não executar comandos globais de limpeza Docker e não reutilizar volumes de PostgreSQL/Redis/Supabase para a GoMut.

Produção começou com banco novo, operador `gomut-operator`, zero cursos e zero alunos. Homologação usa banco próprio com dados fictícios. As contas e senhas da demo local não são as contas da VPS.

## Acesso no Windows

A chave privada permanece fora do repositório. Os caminhos abaixo indicam os arquivos locais já criados; não são valores de chaves nem credenciais de aplicação.

```powershell
$gomutWork = 'C:\Users\Windows11\Documents\Codex\2026-11-17\verifique-a-disponibilidade-da-minha-vps\work'
$gomutSshKey = Join-Path $gomutWork 'private\id_ed25519_gomut_kvm4'
$gomutKnownHosts = Join-Path $gomutWork 'kvm4-known-hosts'
$gomutServer = 'root@72.60.151.178'
$gomutSshOptions = @('-F', 'NUL', '-i', $gomutSshKey,
    '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=yes',
    '-o', "UserKnownHostsFile=$gomutKnownHosts", '-o', 'ServerAliveInterval=30',
    '-o', 'ServerAliveCountMax=3')

# Sessão administrativa remota
ssh @gomutSshOptions $gomutServer

# Opcional: túnel de homologação que deve permanecer aberto
ssh @gomutSshOptions -o ExitOnForwardFailure=yes -N `
    -L 127.0.0.1:18081:127.0.0.1:18081 $gomutServer
```

- Produção: aluno em <https://emergensimples.gomut.com.br>; produtor em <https://painel.emergensimples.gomut.com.br>. Não exige túnel. O loopback 18080 não é um login alternativo no modo público.
- Homologação: <http://127.0.0.1:18081/login/>.
- Encerrar o túnel com Ctrl+C fecha somente esse acesso, sem parar os containers.
- Se as portas locais estiverem ocupadas, verifique se o túnel já existe. Não encerre processos desconhecidos. Uma porta local alternativa exige ajustar as origens CSRF do ambiente correspondente antes de usar formulários; mantenha as portas documentadas nesta etapa.
- Não ignore falha de chave de host. A identidade ED25519 conferida é `SHA256:Wrv+yLrR2Ak1WcKJrj9fwad3f/zy8QZrEKMnqLiavCA`.

Para definir a senha do operador, use a sessão SSH interativa, sem colocar a senha no comando ou em documentos:

```bash
docker exec -it gomut-web python -B manage.py changepassword gomut-operator
```

## Comandos de rotina — executar na VPS

Estes comandos operam somente a GoMut. Os arquivos de ambiente privados não devem ser impressos em tela ou logs.

```bash
# Registrar qual release está ativo
readlink -f /srv/gomut/current

# Estado e healthchecks
sh /srv/gomut/current/deploy/compose.sh ps

# Iniciar produção; homologação não é atualizada implicitamente
sh /srv/gomut/current/deploy/compose.sh up -d web scheduler

# Reiniciar apenas as aplicações web, sem apagar dados
sh /srv/gomut/current/deploy/compose.sh restart web homolog

# Parar somente a GoMut
sh /srv/gomut/current/deploy/compose.sh stop web homolog scheduler

# Logs limitados; não compartilhar sem conferir dados pessoais e segredos
sh /srv/gomut/current/deploy/compose.sh logs --tail 100 web scheduler

# Recursos atuais e contenção da CPU
uptime
vmstat 1 5
docker stats --no-stream gomut-web gomut-homolog gomut-scheduler
```

Não use `docker compose config` para produzir relatórios públicos: a renderização completa pode incluir variáveis secretas dos `env_file`. Não use o monitor de preservação antigo como rotina automática de manutenção: ele pode parar a GoMut se outro projeto tiver sido atualizado legitimamente desde o inventário inicial.

## Persistência, configuração e rotinas

| Host | Container / finalidade |
|---|---|
| `/srv/gomut/production/db` | `/data/db`, SQLite de produção |
| `/srv/gomut/production/media` | `/data/media`, uploads de produção |
| `/srv/gomut/production/backups` | `/data/backups`, snapshots privados do agendador |
| `/srv/gomut/production/run` | `/data/run`, lock e checkpoints do agendador |
| `/srv/gomut/homolog/db`, `media`, `backups` | Dados próprios de homologação, sem compartilhar a produção |
| `/srv/gomut/private/production.env`, `homolog.env` | Configuração privada, fora dos releases e do Git |

Releases e imagens são substituíveis; dados e chaves não. Os diretórios de dados precisam continuar graváveis pelo UID 10001; o diretório privado é root/700 e seus arquivos root/600. Docker lê os arquivos privados e injeta a configuração sem montá-los publicamente.

Produção usa `core.settings_public`, hosts HTTPS explícitos, CSRF e cookies Secure/host-only. Homologação e agendador conservam sua configuração privada. O módulo `core.settings_deploy` exige modo túnel, hosts de loopback explícitos, caminhos absolutos para banco/media e chave de criptografia. Ele força DEBUG e Asaas/API/webhook desligados, rejeita cadastro público e separa nomes de cookies de produção/homologação. Estáticos usam WhiteNoise; imagens têm diretórios/extensões permitidos, e PDFs continuam exclusivamente nos endpoints autenticados. `/media/materials/` deve responder 404.

O container `gomut-scheduler` é o único agendador deste release, no fuso `America/Campo_Grande`:

- Avisos diários a partir das 04:00, recuperando o dia pendente se iniciar mais tarde.
- Lembretes em intervalos de 15 minutos.
- Backup diário a partir das 04:15, também com recuperação após início tardio.
- Lock exclusivo, checkpoint em `run/jobs.json`; falhas não impedem a tentativa das outras rotinas.

Não duplique essas tarefas em cron/Coolify. Homologação não tem agendador automático. Sem SMTP, um comando concluído não significa e-mail entregue: conferir `EmailLog`, cujo resultado atual esperado é `not_sent`.

## Backup e restauração

Backup manual de produção, quando o agendador estiver ativo:

```bash
docker exec gomut-scheduler python -B -m deploy.backup_bundle
```

Se o lock estiver ocupado, aguarde a execução corrente; não apague o lock nem execute em paralelo. O conjunto contém banco consistente pela API SQLite, cópia de `media`, chaves e manifesto. É publicado após conclusão, retém os 14 conjuntos completos mais recentes e recusa uma nova cópia que não preserve a reserva estimada de 2 GiB. Backups contêm segredos: manter privados, fora de Git, relatórios e ZIPs de evidências.

Persistência e backup local não substituem cópia externa; essa cópia permanece pendente. A reserva de espaço é uma estimativa, não garantia contra crescimento concorrente. Para manutenção/migrações, faça o conjunto com escritores parados, conforme o procedimento abaixo.

Restauração: primeiro copie um conjunto para **novo diretório privado**, valide `integrity_check`, media, chaves, versões e migrations; abra a cópia com um container de teste separado, sem portas públicas, agendador ou rede externa. Só depois considere restaurar produção, com autorização específica, todos os escritores parados e o conjunto atual preservado. Não sobrescreva a base ativa, não misture WAL/SHM antigos com o banco restaurado e não exponha o arquivo `keys.json`. Veja também [operação SQLite](operacao-sqlite.md).

O relatório da primeira implantação comprova um ensaio em diretórios separados, com 55 tabelas, integridade válida e login/dashboard acessíveis na cópia. Não houve restauração sobre a produção ativa.

## Atualizar um release

Este é um procedimento para uma atualização futura entre releases públicos. O release novo deve incluir `deploy/compose.public.yaml` e `deploy/compose.sh`. A primeira versão privada não possui esse wrapper: sua reversão está no [relatório HTTPS](relatorio-publicacao-https.md). Homologação ainda usa a imagem inicial; atualizar sua imagem é uma ação separada, após backup, com aprovação do esquema.

1. Registre o caminho/imagem atual e o estado dos serviços. Teste a fonte que será publicada, incluindo mudanças ainda sem commit quando existirem. Não use apenas um `git archive HEAD` se houver correções locais.
2. Faça o build **fora da VPS**, com tag nova e imutável; não sobrescreva `gomut:kvm4-20261117`. Dockerfile: `deploy/Dockerfile`. Comando: `docker build -f deploy/Dockerfile -t gomut:kvm4-NOVA-VERSAO .`. Use apenas contexto sem segredos/dados; confira `.dockerignore` e o conteúdo antes de transferir.
3. Salve a imagem com `docker save --output IMAGEM.tar gomut:kvm4-NOVA-VERSAO`. Transfira por SCP/SFTP com a chave dedicada. Verifique SHA256 na origem e destino antes de `docker load --input IMAGEM.tar` na VPS; não publique em registry sem autorização.
4. Prepare **outro** diretório `/srv/gomut/releases/NOVA-VERSAO`, com a fonte selecionada, `deploy/compose.yaml` e `release.env` contendo `GOMUT_IMAGE=gomut:kvm4-NOVA-VERSAO`. Não inclua banco, media, backups, ambientes virtuais, `seed.py`, dumps ou `.env` privados. Não modifique o release atual no lugar. Preserve cópia auditável da fonte e sua relação com a imagem.
5. Faça as verificações e migrações planejadas primeiro em homologação. Os comandos `compose run` abaixo não usam `--service-ports`, portanto não publicam portas adicionais. Não os substitua por uma execução apontando à base de produção sem janela de manutenção.

No SSH, defina os dois caminhos já conferidos. Substitua o marcador por um diretório existente; não execute literalmente `NOVA-VERSAO`:

```bash
old_release=$(readlink -f /srv/gomut/current)
new_release=/srv/gomut/releases/NOVA-VERSAO

# Suspender também o escritor de homologação e preservar seu estado
sh "$old_release/deploy/compose.sh" stop homolog
sh "$old_release/deploy/compose.sh" run --rm --no-deps homolog python -B -m deploy.backup_bundle

# Prévia das migrações e validação na homologação, sem o código antigo gravando
sh "$new_release/deploy/compose.sh" run --rm --no-deps homolog python -B manage.py migrate --plan
sh "$new_release/deploy/compose.sh" run --rm --no-deps homolog python -B manage.py migrate --noinput
sh "$new_release/deploy/compose.sh" run --rm --no-deps homolog python -B manage.py migrate --check
sh "$new_release/deploy/compose.sh" run --rm --no-deps homolog python -B manage.py check --deploy
sh "$new_release/deploy/compose.sh" up -d --no-deps homolog
```

Execute cada comando após conferir o anterior. Se backup ou migração falhar, não avance: mantenha a homologação parada até avaliar a compatibilidade do esquema antes de reiniciar qualquer versão; produção continua independente. Confirme login, CSS, imagem, PDFs privados, Vimeo, progresso, quiz e certificado na homologação. `migrate --check` antes de aplicar migrações pode retornar pendência legítima; isso não autoriza ignorar uma falha de migração.

Depois de validar e planejar a compatibilidade de esquema, faça a janela de produção:

```bash
# Suspender todos os escritores de produção; homologação permanece separada
sh "$old_release/deploy/compose.sh" stop web scheduler

# Backup do estado anterior com os escritores parados
sh "$old_release/deploy/compose.sh" run --rm --no-deps scheduler python -B -m deploy.backup_bundle

# Aplicar somente migrações previamente avaliadas
sh "$new_release/deploy/compose.sh" run --rm --no-deps --label traefik.enable=false web python -B manage.py migrate --plan
sh "$new_release/deploy/compose.sh" run --rm --no-deps --label traefik.enable=false web python -B manage.py migrate --noinput
sh "$new_release/deploy/compose.sh" run --rm --no-deps --label traefik.enable=false web python -B manage.py migrate --check
sh "$new_release/deploy/compose.sh" run --rm --no-deps --label traefik.enable=false web python -B manage.py check --deploy
sh "$new_release/deploy/compose.sh" up -d --no-deps web scheduler
sh "$new_release/deploy/compose.sh" ps
```

Execute um comando por vez e confira a saída. Em containers temporários do serviço web, conservar `--label traefik.enable=false` para não anunciar uma rota pública durante os comandos administrativos. Se backup, migração ou check falhar, não avance automaticamente. Em produção, somente W005/W021 são esperados pela política inicial de HSTS sem includeSubDomains/preload; os quatro avisos HTTP se aplicam apenas à homologação privada. Avisos novos precisam de avaliação. Confira healthchecks, certificado real e login HTTPS nos dois hosts, PDFs privados, logs e impacto nos serviços existentes; só após sucesso atualize o ponteiro:

```bash
ln -sfn "$new_release" /srv/gomut/current
readlink -f /srv/gomut/current
```

Mantenha o caminho anterior e a imagem antiga. Não rode limpeza global do Docker nem apague releases/backups para liberar espaço sem avaliar retenção e necessidade de reversão.

## Reversão

O release anterior é privado e volta ao acesso por túnel; veja os comandos específicos no [relatório HTTPS](relatorio-publicacao-https.md). O exemplo abaixo vale somente quando ambos os releases incluem o wrapper público. Preserve dados e demais projetos.

Em atualizações futuras, se o esquema atual ainda for compatível com o código anterior, pare os escritores da versão nova e reative a imagem antiga usando seu arquivo de release:

```bash
sh "$new_release/deploy/compose.sh" stop web scheduler
sh "$old_release/deploy/compose.sh" up -d --no-deps web scheduler
sh "$old_release/deploy/compose.sh" ps
```

Confira o acesso e só então aponte `/srv/gomut/current` ao release anterior. A homologação tem imagem controlável pelo mesmo Compose, mas base própria; reverta-a separadamente após conferir o esquema dela. Se migrations quebrarem compatibilidade, voltar apenas a imagem não é uma reversão segura: valide um plano de restauração separado e reconcilie gravações posteriores ao backup antes de alterar a produção. Não use `down -v` nem restaure banco como etapa automática.

## Pendências e limites

- SMTP/remetente e recebimento real de teste.
- Cópia externa protegida de backups e ensaio de restauração dessa cópia.
- Configurações da escola, conta nominal da equipe, vídeos privados e cursos/alunos reais.
- Acompanhamento de CPU/steal, latência e crescimento de disco; limites atuais de CPU/memória não garantem ausência de contenção no host físico.
- Conferência da continuidade contratual indicada pelo provedor para 24/11/2026, sem alterar contratação nesta tarefa.
- Manutenção pendente do host e eventual cadastro futuro no Coolify, tratados separadamente.

Na homologação privada, HSTS, redirecionamento HTTPS e cookies seguros estão desligados para o túnel; `check --deploy` apresenta W004, W008, W012 e W016 sem silenciá-los. Este settings **não deve ser exposto publicamente**. A produção pública usa o módulo separado `core.settings_public`, validado com HTTPS, cookies seguros e confiança no Traefik; não expor publicamente a homologação nem trocar produção pelo settings de túnel. Não modificar DNS de outros hosts nesta rotina. A pré-compressão de estáticos no build ainda é uma otimização pendente, sem alterar o funcionamento do WhiteNoise validado.
