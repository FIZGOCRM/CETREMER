# Incorporação do deploy KVM4 ao repositório

Data: 17/11/2026. Branch: `feat/area-aluno-handoff`. Trabalho realizado no diretório solicitado pelo usuário, preservando a árvore de trabalho e as correções locais existentes; não houve reset, troca de branch ou reaplicação do deploy na VPS.

> Registro histórico da integração inicial privada. A publicação posterior está no [relatório HTTPS](relatorio-publicacao-https.md); use os comandos públicos do manual atualizado.

## Escopo e entradas

Foram lidos o relatório completo `RELATORIO-DEPLOY-GOMUT-KVM4.md`, o patch `AJUSTES-DEPLOY-GOMUT-KVM4.patch` e as evidências do ZIP entregues pelo Codex Desktop, no diretório local `Documents/Codex/2026-11-17/verifique-a-disponibilidade-da-minha-vps/outputs`.

O relatório confirma uma implantação já feita por **Docker Compose**, projeto `gomut-kvm4`, sem cadastro na interface Coolify. A tarefa atual incorporou a receita ao repositório, verificou compatibilidade, reexecutou testes e registrou manutenção; não repetiu bootstrap, migrações ou criação de contas no servidor.

## Alterações incorporadas

- Django 5.2.19 LTS; Gunicorn 27.0.1; WhiteNoise 6.12.0; versões restantes mantidas.
- `.dockerignore`, `deploy/Dockerfile` e `deploy/compose.yaml`.
- `core/settings_deploy.py`, `core/urls_deploy.py`, `core/deploy_media.py`.
- `deploy/jobs.py`, `deploy/backup_bundle.py` e pacote `deploy`.
- `core/test_deploy_runtime.py` e `core/test_deploy_jobs.py`: 16 testes recebidos.
- Plano histórico da implantação em `docs/superpowers/plans/2026-11-17-deploy-kvm4.md`, importado como recebido. Seu checklist não é uma ordem para repetir o deploy; a execução realizada está no relatório de origem.
- [Manual operacional da KVM4](operacao-kvm4.md), com acesso, serviços, atualização, backup e reversão. README, manual da equipe, checklist e guia SQLite passam a apontar para a operação atual.

O patch passou em `git apply --check`, sem conflito. Antes da aplicação, os 11 arquivos já modificados/não rastreados foram registrados por SHA256; imediatamente depois, todos continuavam idênticos. Os oito arquivos de código/testes de D01–D04 permaneceram idênticos também na conferência final. A documentação geral foi atualizada deliberadamente para registrar o novo runtime, sem apagar o relatório histórico do QA. Em `requirements.txt` foram normalizados somente finais de linha para evitar avisos de whitespace; versões são as do patch.

## Compatibilidade com a fonte implantada

Foram comparados **432 arquivos** de runtime, estáticos, templates, dependências e receita de deploy contra o pacote de fonte realmente transferido: **zero divergências**, considerando equivalência de finais de linha. A comparação também foi executada por SSH contra os mesmos arquivos em `/app` de `gomut-web`: **432 arquivos, zero divergências**, Django **5.2.19**.

A suíte usou a imagem Linux `gomut:kvm4-20261117`, com a fonte atual integrada montada em somente leitura, sem rede e sem acesso aos bancos/segredos da VPS ou à base de demonstração local. O ambiente Windows `.venv` antigo não foi atualizado no lugar e o servidor local não foi reiniciado; a verificação de compatibilidade usa o runtime efetivamente implantado. Para desenvolvimento nativo, sincronizar o ambiente virtual com `requirements.txt` antes de presumir execução em Django 5.2.

## Verificações executadas

| Verificação | Resultado |
|---|---|
| Suíte completa na fonte integrada, em Linux | **374 testes, zero falhas e zero erros**, incluindo D01–D04 e os 16 testes de deploy |
| `makemigrations --check --dry-run` | Nenhuma alteração detectada |
| `check --deploy --settings=core.settings_deploy` | Exatamente W004, W008, W012 e W016, sem silenciamento |
| `git diff --check` | Sem erro de whitespace |
| Revisão independente do patch e integrações | Nenhum bloqueio de compatibilidade/segurança identificado |
| Acesso SSH dedicado | Autenticado, com verificação estrita de chave de host |
| Estado remoto consultado às 19:26:55 UTC | `gomut-web` e `gomut-homolog` saudáveis; `gomut-scheduler` ativo; portas somente em loopback 18080/18081 |
| Fonte do container remoto x repositório | 432 arquivos conferidos, zero divergências |

Na primeira execução, o `/tmp` do container de testes havia sido limitado pelo executor a 256 MiB. O teste de backup recusou corretamente uma cópia por não manter os 2 GiB de reserva. Foi ampliado somente o tamanho virtual do tmpfs de testes para 3 GiB; a implementação e a proteção de disco não foram alteradas. A suíte completa foi reexecutada e passou.

Os quatro avisos de segurança são exclusivos da decisão de transporte por túnel SSH: HTTP local de loopback, sem domínio/HTTPS público. Não foram tratados como aprovação de publicação pública. A pré-compressão dos estáticos no build é uma otimização já adiada na implantação original; o serviço WhiteNoise continua funcional. A revisão do manual também levou à inclusão explícita de parada e backup da homologação antes das migrations, evitando gravações do código antigo durante o ensaio de atualização.

As evidências desta integração ficam em `.venv/deploy-integration/`: hashes anteriores, comparações de fonte, log completo da suíte Linux e consulta remota. São artefatos locais ignorados pelo Git e não contêm valores de chaves privadas ou ambientes de produção. O acesso SSH usou somente os arquivos privados externos já existentes; seu conteúdo não foi copiado para o projeto.

## Limites e pendências

Nenhum container ou serviço remoto foi reiniciado por esta tarefa. Não houve envio de e-mail, escrita em bases da VPS, mudança de credenciais, instalação na VPS, alteração de DNS/domínio, contratação ou acesso a segredos de outros projetos.

Permanecem: SMTP, backup externo protegido, configurações da escola, conta nominal da equipe, cursos/alunos reais, acompanhamento de CPU/steal e a manutenção/continuidade do host documentadas na implantação. O acesso atual é por túnel. A primeira implantação não tem um release anterior de GoMut para prometer reversão já testada: a contingência inicial é parar apenas os serviços próprios, preservando dados. Atualizações futuras exigem conservar imagem/release anterior e avaliar compatibilidade das migrações antes de voltar o código.
