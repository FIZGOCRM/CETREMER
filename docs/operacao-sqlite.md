# Operação com SQLite

**KVM4 atual:** banco e media ficam em diretórios persistentes próprios de cada ambiente; o agendador já cria conjuntos privados com SQLite, media e chaves. A operação Docker Compose e o procedimento de atualização/reversão estão no [manual da KVM4](operacao-kvm4.md). A cópia externa dos backups continua pendente. O procedimento genérico abaixo não substitui esses comandos do ambiente implantado.

SQLite permanece como banco da aplicação. Use um servidor com disco local persistente; não coloque o arquivo em armazenamento temporário ou compartilhamento de rede. O banco não contém os vídeos externos, mas contém contas, matrículas, progresso e pedidos.

## Backup

Com o ambiente Django configurado, crie uma pasta protegida fora do diretório público e execute:

```powershell
python manage.py backup_sqlite C:\Backups\cetremer-2026-11-13.sqlite3
```

O destino deve ser novo. O comando usa a API de backup do SQLite, incluindo alterações confirmadas no WAL, e executa `PRAGMA integrity_check`. Não copia o arquivo aberto diretamente e não sobrescreve backups existentes.

Agende a execução diária, mantenha versões conforme a perda de dados aceitável e envie cópia para outro armazenamento protegido. Agendamento e armazenamento remoto precisam ser configurados na infraestrutura; não foram criados automaticamente.

Também preserve `media/` e as chaves `SECRET_KEY` e `FIELD_ENCRYPTION_KEY` por meios seguros. Os valores das chaves não devem entrar no Git nem no HTML de documentação. Sem a chave de criptografia, segredos persistidos não poderão ser lidos.

## Restauração

1. Teste o backup em uma instalação separada com as mesmas versões do código e das migrations. Configure o banco dessa instalação para apontar para uma cópia do backup.
2. Confira integridade, login, matrícula, progresso, certificados e arquivos de `media/`. A integridade estrutural não substitui esses testes de funcionamento.
3. Para restaurar produção, entre em manutenção e pare todos os processos que acessam o banco. Faça um novo backup da base atual para permitir retorno.
4. Preserve a base atual e eventuais arquivos `-wal` e `-shm` como um conjunto separado, com todos os processos parados. Não deixe sidecars antigos ao lado do banco restaurado.
5. Coloque a cópia validada no caminho `db.sqlite3`, restaure arquivos necessários e permissões. Confira a compatibilidade de migrations antes de iniciar a aplicação.
6. Reinicie e confira os fluxos do passo 2. Registre o horário do backup e as alterações posteriores que precisarão ser reconciliadas.

Não foi executada restauração na base do cliente. Os testes automatizados exercitam backup e integridade em bancos temporários.

## Pagamentos

O checkout permanece bloqueado até existir integração real. Não há endpoint público de confirmação fictícia. Quando o gateway for escolhido, testar autenticidade de eventos, duplicidade, valor/moeda, falhas e transação de pedido/matrícula. Não depender de `select_for_update()` para exclusão mútua no SQLite.
