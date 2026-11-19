# GoMut — HTTPS e endereços separados

Endereços aprovados pelo usuário em 17/11/2026:

- Aluno: `https://emergensimples.gomut.com.br`.
- Produtor: `https://painel.emergensimples.gomut.com.br`.

O DNS de ambos aponta para a KVM4. O domínio principal, www e e-mail não são alterados. Uma aplicação e um SQLite de produção atendem os dois portais; a homologação permanece privada.

## Operação desta versão

O modo público usa `core.settings_public` e o override `deploy/compose.public.yaml`. O aluno não recebe as rotas administrativas; o produtor só acessa telas de aprendizagem durante a prévia administrativa válida e somente leitura. Cada host escolhe o login e o papel permitido. Cookies `__Host-` são Secure e host-only. Links de acesso enviados pela equipe usam o portal do destinatário; recuperação de senha respeita papel e HTTPS.

Traefik usa os entrypoints `http`/`https`, a rede Docker `coolify` e o resolver `letsencrypt` existentes. Roteadores exclusivos `gomut-public`/`gomut-public-http` atendem somente esses dois hosts e redirecionam HTTP para HTTPS. Não é criado recurso na interface Coolify, não há alteração do proxy global nem porta pública direta do Gunicorn.

**Na versão pública, use o wrapper abaixo.** Ele aplica os dois arquivos Compose; usar apenas o arquivo base pode remover as rotas HTTPS e voltar ao modo de túnel.

```bash
# Executar na VPS
sh /srv/gomut/current/deploy/compose.sh ps
sh /srv/gomut/current/deploy/compose.sh logs --tail 100 web scheduler
sh /srv/gomut/current/deploy/compose.sh restart web
sh /srv/gomut/current/deploy/compose.sh up -d web scheduler

# Backup manual, sem imprimir dados/chaves
docker exec gomut-scheduler python -B -m deploy.backup_bundle
```

O agendador continua privado com sua configuração original e o mesmo banco persistente. A homologação mantém `core.settings_deploy` e o acesso por túnel em 18081. A porta interna de produção em loopback não é mais uma tela alternativa de login: o modo público exige os hosts HTTPS; `/healthz/` responde somente um estado mínimo para os healthchecks.

## Atualização e reversão

Siga o [manual da KVM4](operacao-kvm4.md) para preparar imagem fora da VPS, release novo, backup com escritores parados e avaliação de migrations. Para releases que incluem `deploy/compose.sh`, use `sh CAMINHO-DO-RELEASE/deploy/compose.sh COMANDO` no lugar do comando Compose que passa só o arquivo base. Isso vale para a nova versão e para futuras reversões entre versões públicas.

A reversão para a primeira versão privada é deliberadamente diferente: parar `web`/`scheduler` usando o wrapper público, reativar a imagem anterior com seu Compose base e restaurar `/srv/gomut/current` ao release anterior. Isso remove as rotas públicas e devolve o acesso por túnel; pode ser necessária uma janela de manutenção e a conferência de cookies/URL. Nenhuma migration de modelo é prevista nesta mudança. Conservar os bancos, uploads, chaves e backup; não executar `down -v`.

## Segurança e limites

O modo público ativa redirecionamento HTTPS, cookies Secure, hosts explícitos e confiança no cabeçalho de protocolo definido pelo Traefik. Acesso direto ao backend continua restrito ao host/rede Docker administrados pela equipe. HSTS começa com uma hora, sem includeSubDomains/preload, para não impor uma política irreversível durante a publicação inicial; os avisos opcionais W005/W021 são avaliados, sem silenciamento. PDFs não são servidos diretamente por `/media/materials/`.

Não há mudança de Asaas, cobrança, matrícula automática, SMTP, backup externo, dados reais ou configuração completa da escola. Os dois hosts foram conferidos externamente com TLS 1.3, certificado válido do Let's Encrypt, HTTP redirecionado e login real do produtor no Chrome. Consulte o [relatório de execução](relatorio-publicacao-https.md), que distingue validação em produção dos testes com dados fictícios em cópia privada.
