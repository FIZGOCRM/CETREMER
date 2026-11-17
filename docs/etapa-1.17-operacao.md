# Etapa 1.17 — preparação operacional

## 1. O que foi feito
Checklist de produção com campos em branco e nomes de variáveis, sem segredos. Manual simples para cursos, planos, quizzes/CSV, comunidade, suporte, encontros, certificados e falhas. Agendamentos necessários e bloqueio de PDFs no proxy documentados. check --deploy executado no ambiente demo.

## 2. Arquivos
docs/producao-checklist.md; docs/manual-operacao.md; este relatório. Nenhuma configuração de produção foi inventada.

## 3. Migrações
Nenhuma.

## 4. Testes
Última suíte do código:279 testes, zero falhas/erros. check --deploy executado: seis avisos; makemigrations --check --dry-run sem alterações. Documentação conferida contra comandos/settings existentes. Sem novos testes de código nesta etapa documental.

## 5. Causas e efeitos
C29/C30: operação e pendências de e-mail documentadas. PDFs privados exigem negação no proxy, além do bloqueio Django. Backup consistente e restauração estão vinculados ao procedimento já existente.

## 6. Como conferir
Abrir producao-checklist.md e preencher infraestrutura/domínios/discos/backup/SMTP; não há valores de produção pré-preenchidos. Ler manual-operacao.md com a demo aberta em127.0.0.1:8016. Executar check --deploy novamente com a configuração final antes de publicar.

## 7. Pendências/desvios
Seis avisos locais: security.W004 HSTS; W008 HTTPS; W009 qualidade da chave local; W012 cookie de sessão seguro; W016 cookie CSRF seguro; W018 DEBUG. A execução retornou0 com avisos, sem tornar o ambiente apto para produção. CSRF_TRUSTED_ORIGINS ainda não é carregado do ambiente: configurar explicitamente quando o domínio for conhecido. Sem instalação, implantação, e-mail externo, importação real ou agendamento no computador. Etapa1.16 continua pendente da planilha. Prosseguir Fase2 autorizado pela instrução de executar todas as fatias, sem novo gate rotineiro.

## 8. Commit
docs: checklist e manual da etapa 1.17; hash na entrega/diário. Sem push/merge.
