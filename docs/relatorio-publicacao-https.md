# Publicação HTTPS — GoMut / Emergensimples

Execução: 17/11/2026. Resultado: **produção publicada na KVM4, com dois portais HTTPS funcionando**.

## Acesso

| Portal | Endereço | Identidade e acesso |
|---|---|---|
| Aluno | <https://emergensimples.gomut.com.br> | Emergensimples; login de aluno |
| Produtor | <https://painel.emergensimples.gomut.com.br> | GoMut; login da equipe administrativa |

Os endereços não exigem túnel. São a mesma aplicação e o mesmo banco de produção, com seleção do portal pelo host, autorização por papel e cookies independentes. Entrar no produtor não autentica o navegador como aluno. A prévia administrativa válida continua no host do produtor, em somente leitura. O domínio principal e www não foram redirecionados para esta aplicação; configurações de e-mail não foram alteradas.

As credenciais existentes não foram trocadas e não constam desta entrega. Produção começou com o operador, **sem cursos e alunos reais**. As contas da demo local/homologação não são contas de produção. O fluxo inicial de aluno criado pela equipe usa código temporário de primeiro acesso; envio real de e-mail depende de SMTP.

## Versão e preservação

- Release ativo: `/srv/gomut/releases/20261117T202202Z`.
- Ponteiro: `/srv/gomut/current`.
- Imagem de produção: `gomut:kvm4-https-20261117t202202z`.
- Versão anterior privada: `/srv/gomut/releases/20261117T182000Z`, imagem `gomut:kvm4-20261117`.
- Runtime: Python 3.13.18, Django 5.2.19 LTS, Gunicorn 27.0.1, WhiteNoise 6.12.0.
- Operação: Docker Compose `gomut-kvm4`, sem cadastro da GoMut na interface Coolify.
- Produção: `gomut-web` saudável; `gomut-scheduler` em execução, sem porta pública.
- Homologação: `gomut-homolog` saudável, conservada na imagem anterior, dados próprios e acesso privado em loopback 18081.
- Backup anterior à publicação: `20261117T202642066792Z`, feito com web/agendador de produção parados, integridade SQLite válida. Banco, uploads e chaves mantidos em diretórios persistentes.
- Conferência de **437 arquivos de runtime na imagem ativa: nenhuma divergência** com a fonte selecionada. As correções locais D01–D04 foram incluídas e preservadas.
- **38 containers dos outros serviços preservados**, sem diferenças de identidade, reinícios, estado ou saúde em relação à captura anterior. O proxy global não foi reiniciado nem reconfigurado.

A única correção de conteúdo em produção foi substituir o nome padrão legado da escola, exatamente `CETREMER`, por `Emergensimples`. Não foram sobrescritos nomes personalizados nem preenchidos outros dados da escola. Não foram criados alunos ou cursos fictícios em produção. As alterações continuam na árvore local de trabalho; não houve commit/push automático. A documentação final de entrega foi complementada depois do build; os 437 arquivos de runtime são os verificados na imagem.

## Alterações técnicas

| Arquivos | Finalidade |
|---|---|
| `core/portal_routing.py`, `core/settings_public.py` | Hosts explícitos, autorização por portal, HTTPS, cookies Secure e host-only, healthcheck interno mínimo |
| `users/forms.py`, `users/views.py` | Login e recuperação de senha limitados ao papel de cada portal; destino de retorno validado |
| `painel/views/common.py` | Links de primeiro acesso/recuperação gerados no host correto do destinatário |
| `templates/login.html`, `templates/login_admin.html` | Identidade correspondente ao host, sem troca de portal por parâmetro de URL |
| `templates/registration/password_reset_email.txt` | Protocolo do link respeita HTTPS; corrigido HTTP fixo detectado na revisão |
| `deploy/compose.public.yaml`, `deploy/compose.sh` | Rotas específicas no Traefik existente, certificado automático e wrapper que conserva o override público |
| `core/test_public_portals.py` | 18 testes novos de isolamento, autenticação, prévia, recuperação, cookies, CSRF e configurações |

Traefik atende exclusivamente os dois hosts aprovados, usando a rede Docker `coolify`, entrypoints existentes e resolver `letsencrypt`. Gunicorn continua sem porta pública direta. Banco SQLite e uploads não mudaram de tecnologia/local. API/webhook Asaas permanecem desligados; nenhuma cobrança automática foi ativada.

## Validação executada

| Verificação | Resultado e limite |
|---|---|
| Suíte completa no runtime Linux da aplicação | **392 testes passaram**, 41,182 s; banco temporário isolado |
| Migrações | `migrate --check` e verificação de alterações de modelos sem pendências; nenhuma migration nova necessária |
| Revisão independente | Correção do link de recuperação HTTP validada por teste antes da publicação; sem bloqueios restantes |
| Cópia privada de homologação na VPS, com nova imagem/configuração | Login de aluno e produtor, oito páginas de aluno, PDF autenticado privado, bloqueio anônimo/direto, prévia somente leitura e isolamento de papéis passaram; container temporário removido |
| DNS público | Ambos os hosts resolvem para `72.60.151.178` |
| TLS externo, validação de certificado habilitada | TLS 1.3; Let's Encrypt YR2; SAN dos dois hosts; validade até **15/02/2027 19:28:35 UTC** |
| HTTP | Ambos retornam 301 para HTTPS |
| Chrome real 157.0.8103.52 | Logins com marcas corretas; login real do operador e painel acessível; nenhum erro JavaScript de página; sem ignorar erros de certificado |
| Separação no Chrome | Cookie de sessão Secure/HttpOnly restrito ao host produtor; não autentica o portal do aluno; credencial administrativa rejeitada no aluno; rotas cruzadas bloqueadas |
| Healthchecks e preservação | Web/homolog saudáveis; agendador rodando; demais 38 containers preservados |

As capturas mostram login do aluno, login do produtor e painel do produtor publicado. O teste de aluno com credencial fictícia aconteceu na cópia privada, não na produção vazia. Esta publicação não repetiu reprodução real completa de Vimeo em produção nem validação de SMTP; a suíte inclui as regressões de D01–D04. Vídeos reais precisam autorizar os domínios de incorporação, inclusive o host do produtor para prévia administrativa.

`check --deploy` público conserva somente W005/W021: política inicial de HSTS de 3600 segundos, sem includeSubDomains/preload. Os avisos não foram silenciados. A configuração HTTP privada não é usada para servir os portais públicos.

## Operação e atualização

Executar na VPS:

```bash
readlink -f /srv/gomut/current
sh /srv/gomut/current/deploy/compose.sh ps
sh /srv/gomut/current/deploy/compose.sh logs --tail 100 web scheduler
sh /srv/gomut/current/deploy/compose.sh restart web
docker exec gomut-scheduler python -B -m deploy.backup_bundle
```

**Usar o wrapper `compose.sh`**. Aplicar somente `compose.yaml` remove o override HTTPS. Não imprimir arquivos privados nem executar `docker compose config` para compartilhar saída. Não executar limpeza global, `down -v`, restaurar banco ativo ou reiniciar o proxy como rotina.

Atualizações devem seguir o [manual da KVM4](operacao-kvm4.md): build fora da VPS, imagem com tag nova, fonte selecionada incluindo correções locais, hashes conferidos, release separado, validação privada, backup com escritores parados, migrações avaliadas, subida apenas dos serviços necessários, validação externa e troca do ponteiro. Homologação tem base/imagem próprias e não deve ser atualizada implicitamente junto com a produção.

## Reversão desta publicação

O release anterior é **privado**. O procedimento abaixo retira os portais públicos e retorna à operação por túnel; não é uma troca transparente entre versões HTTPS. Só usar em manutenção deliberada, com diagnóstico da falha e preservação das gravações atuais. Não há mudança de esquema nesta publicação, portanto não restaurar banco automaticamente.

```bash
public_release=/srv/gomut/releases/20261117T202202Z
private_release=/srv/gomut/releases/20261117T182000Z

# Parar os escritores atuais e preservar o estado atual
sh "$public_release/deploy/compose.sh" stop web scheduler
sh "$public_release/deploy/compose.sh" run --rm --no-deps scheduler python -B -m deploy.backup_bundle

# Conferir o backup antes de executar a próxima ação
docker compose --env-file "$private_release/release.env" -f "$private_release/deploy/compose.yaml" up -d --no-deps web scheduler
docker compose --env-file "$private_release/release.env" -f "$private_release/deploy/compose.yaml" ps

# Depois de validar os serviços privados e o túnel
ln -sfn "$private_release" /srv/gomut/current
readlink -f /srv/gomut/current
```

Executar cada comando após conferir o anterior; interromper se o backup falhar. Os dados e as chaves permanecem nos mesmos diretórios. A homologação não precisa ser revertida. O túnel da produção privada usa `127.0.0.1:18080`; o login da versão anterior é `/login/?acesso=admin`. Credenciais não mudam. Para reversões futuras entre versões públicas, utilizar o wrapper de cada release.

## Pendências separadas

- Cadastrar configurações completas da escola, cursos/vídeos e alunos reais; configurar a permissão de incorporação no Vimeo para os dois hosts.
- SMTP/remetente e teste de recebimento real; código temporário continua sendo a alternativa de primeiro acesso entregue pela equipe.
- Backup externo protegido e ensaio de restauração da cópia externa; backup local não cobre perda total da VPS.
- Acompanhar CPU/steal, latência e disco; contenção do host já era observada antes desta publicação.
- Cobrança/Asaas, contratação e manutenção geral da VPS continuam separados desta entrega.

Evidências entregues no ZIP: três capturas do Chrome, validação do navegador sem valores de cookies, certificado/HTTP externos, suíte, verificação privada e conferência remota final. Sem senhas, chaves, arquivos de ambiente, bancos, backups ou cookies de sessão.
