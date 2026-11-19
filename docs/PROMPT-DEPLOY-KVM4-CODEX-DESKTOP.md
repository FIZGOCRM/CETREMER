# Deploy remoto GoMut / Emergensimples na KVM4

Você vai operar minha VPS KVM4 da Hostinger e fazer o deploy desta aplicação. **O acesso remoto à VPS é obrigatório.** Não substitua o trabalho por uma simulação, pelo servidor local ou apenas por instruções para eu executar.

## Autorização e escopo

- Tenho duas páginas abertas no Chrome: o painel da KVM4 na Hostinger e seu console web. Use a conexão de navegador desta sessão para localizá-las e iniciar a inspeção.
- Autorizo as operações necessárias ao deploy da GoMut nessa VPS, preservando os serviços e dados que já existirem.
- **Domínio, subdomínio e DNS estão fora desta etapa.** Não altere registros nem configure gomut.com.br.
- Não formate, reinstale o sistema, restaure snapshots nem apague serviços ou dados existentes. Não contrate recursos nem altere o plano da Hostinger.
- Peça minha intervenção somente quando faltar autenticação, uma ferramenta exigir aprovação ou uma ação necessária ultrapassar esse escopo. Siga as políticas das ferramentas disponíveis.

## Projeto e estado atual

Repositório local: `C:\Users\Windows11\orca\CETREMER`.

- GoMut é a plataforma; Emergensimples é a identidade da área do aluno. Painel do produtor claro/verde; aluno escuro/vermelho.
- Django 4.2.30, templates do servidor, CSS/JavaScript próprios, SQLite. Sem React, Vue, DRF, Celery ou build de frontend.
- Cerca de 36 alunos; inicialmente dois cursos. Cada aluno pode ter um ou os dois, com matrículas e datas independentes.
- Cadastro e controle de acesso manuais. Checkout, cobranças, recorrência financeira e Asaas devem continuar desativados.
- Vimeo incorporado; PDFs privados, progresso, anotações, quizzes, avaliação final, certificados, comunidade, suporte, agenda, notificações e painel administrativo implementados.
- A última suíte registrou **358 testes aprovados**. QA prático é aceito pelo usuário; alunos e cursos reais serão providenciados depois.
- As correções D01–D04 estão no diretório de trabalho e podem estar **sem commit**. Confira `git status` e inclua essas mudanças na fonte publicada. Não use apenas o HEAD de um clone remoto presumindo equivalência. Não descarte mudanças locais.

Leia primeiro:

1. `docs/qa-correcoes-105209.md`: correções do Vimeo, tempo anterior à pausa, data efetiva de acesso e pluralização.
2. `docs/entrega-v1-qa.md`: estado da V1; contagens antigas por etapa são históricas.
3. `docs/producao-checklist.md`.
4. `docs/operacao-sqlite.md` e `docs/manual-operacao.md`.
5. `docs/decisoes-produto.md`: inclui decisões posteriores ao plano original.

As regras de negócio não devem ser redesenhadas. A atualização técnica do Django é uma adaptação para publicação: a série 4.2 já encerrou o suporte de segurança. Prepare a atualização para uma versão corrigida da **linha 5.2 LTS**, consulte a documentação oficial atual, use Python compatível e execute as regressões. Não implante silenciosamente a versão sem suporte nem modernize outras partes sem necessidade.

## Execução

### 1. Comprovar acesso remoto e inspecionar

Localize o painel e o console da Hostinger. Obtenha os dados de conexão e verifique sistema operacional, usuário, CPU/RAM, disco, processos, serviços, containers, portas e caminhos ocupados. Comprove a execução remota com `hostname`, identificação do sistema e usuário; não presuma que o terminal pertence à VPS.

Prefira SSH para comandos e transferência. Se ainda não houver acesso, use o console remoto para preparar o acesso SSH necessário dentro das permissões disponíveis. Preserve autenticação existente e acesso administrativo. Não exponha senhas, tokens, chaves privadas, cookies ou arquivos `.env` em respostas, capturas ou relatórios.

Se esta sessão não conseguir operar remotamente nem pelo console, informe o erro concreto e o requisito mínimo que falta. Não declare o deploy concluído e não execute uma demonstração local como substituição.

### 2. Preparar e publicar

Escolha o encaixe mais simples conforme os serviços encontrados. A proposta inicial é Gunicorn + Nginx + serviço gerenciado pelo sistema, com usuário próprio. Se a VPS já tiver um gerenciador de aplicações ou proxy, integre a aplicação preservando o que existe. Registre a escolha.

- Publique uma versão identificável do código atual, incluindo D01–D04 e a atualização do Django; mantenha os ajustes de deploy reproduzíveis no projeto ou em um patch de retorno.
- Use diretórios separados para código, SQLite, uploads e backups. Banco e aplicação devem usar disco local persistente da VPS; não coloque SQLite em compartilhamento remoto.
- Não transfira `.env`, chaves, cookies, ambientes virtuais, bancos, backups ou uploads locais por um pacote indiscriminado do repositório. Não publique a base local de demonstração como base de produção. Nunca execute `seed.py`.
- Crie um banco novo, aplique as migrações nele e execute `collectstatic`. Se precisar de conteúdo para a validação inicial, use uma base de homologação explicitamente identificada e separada; a preparação de demonstração existente é não destrutiva. Não invente dados reais.
- Gere/configure os segredos por canal seguro. Preserve a chave de criptografia em backups e restaurações.
- Desligue DEBUG, restrinja hosts e configure CSRF conforme o acesso realmente usado. Não use curingas como solução para erro de configuração.
- Sirva arquivos estáticos corretamente e mantenha imagens/uploads persistentes.
- PDFs devem passar pelos endpoints autenticados. Bloqueie o acesso direto a `/media/materials/`; não torne PDFs públicos nem cacheie respostas privadas.
- Prepare avisos diários, lembretes a cada 15 minutos e backups consistentes. Confirme a execução e os logs. Se SMTP não estiver configurado, registre envio como pendente/não enviado, sem inventar entrega.
- Preserve API/webhook/checkout do Asaas desativados.

### 3. Acesso sem domínio

Para esta etapa, prefira validar por **túnel SSH** até o serviço da VPS, sem expor login e dados pessoais em HTTP público. Explique o comando exato de acesso, usando os dados reais da VPS e uma porta local livre. O navegador pode usar um endereço local do túnel, mas o processo, banco e arquivos precisam estar executando **na KVM4**, não no Django local em `127.0.0.1:8016`.

Não crie domínio, DNS ou certificado associado a domínio. Não abra portas nem altere o firewall global sem verificar os serviços existentes e a necessidade concreta.

### 4. Validar o deploy

- Rode a suíte e as verificações de migrações e deploy no ambiente apropriado. Analise os avisos de `check --deploy`; não trate saída zero com avisos como aprovação automática.
- Confirme serviço ativo, diretório e versão implantada, processo remoto e reinicialização do serviço com persistência de dados. Não reinicie a VPS inteira como teste padrão.
- Acesse pelo Chrome o destino remoto via túnel e confira login dos dois perfis, CSS/JS/imagens e navegação principal.
- Valide sessão, matrícula, datas e bloqueio, PDF privado, Vimeo/retomada/tempo, anotações, conclusão, quiz, avaliação e certificado com dados fictícios quando necessários. Preserve os dados e restaure datas temporárias.
- Confirme backup e restauração em base separada, sem sobrescrever o banco ativo.
- Se Vimeo, SMTP ou outro serviço depender de configuração do cliente, identifique a dependência e o teste pendente. Não desabilite autorização ou proteções para conseguir um resultado verde.

## Entrega obrigatória

Gere um **Markdown baixável** chamado `RELATORIO-DEPLOY-GOMUT-KVM4.md` e um ZIP com evidências, sem segredos. Salve no diretório de saída permitido desta sessão e informe os caminhos.

O relatório deve conter:

1. Prova de acesso remoto e identificação da VPS, sem credenciais.
2. Inventário inicial e serviços preexistentes preservados.
3. Código implantado, versões, alterações locais incluídas e ajustes de deploy; forneça patch/arquivos alterados se não puder gravar no repositório.
4. Serviços, portas e diretórios de código, banco, uploads e backups.
5. Comando exato para abrir o túnel e acessar a aplicação remota; instruções de iniciar, parar, reiniciar, consultar logs, atualizar e reverter o release.
6. Migrações, testes, verificações, backup/restauração e respectivos resultados reais.
7. Capturas do Chrome acessando o ambiente remoto, incluindo aluno e produtor. Remova segredos das evidências.
8. Pendências e bloqueios, distinguindo funcionalidade, infraestrutura e configuração externa.

Só declare concluído quando a aplicação estiver realmente executando e acessível na VPS. Se algo impedir isso, entregue o estado exato e o próximo passo necessário, sem alegar sucesso parcial como deploy completo.
