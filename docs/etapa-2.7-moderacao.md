# Etapa 2.7 — Comunidade e Chamados no painel

## 1. O que foi feito
Migração das duas telas para GoMut, abas/filtros/busca, cartões e respostas. Encaminhamento com nota interna separado das mensagens públicas. Assinaturas, solução, ocultação/fixação/reabertura e status de chamado conservam os serviços da fase1. Histórico e privacidade apresentados claramente.

## 2. Arquivos
templates/painel/{community,tickets}.html; static/css/gomut/panel-v1.css; community/selectors.py; painel/views/support.py; painel/test_moderation_design.py; core/test_handoff_phase0.py; este relatório.

## 3. Migrações
Nenhuma.

## 4. Testes
298 testes, zero falhas/erros. Dois novos RED→GREEN: formulário HTTP de encaminhamento/assinatura real e resolução de chamado com evento auditado. C21–C25 continuam nos testes da fase1.

## 5. Causas e efeitos
Texto oculto permanece acessível à equipe para auditoria. Campo de resposta de chamado informa que seu histórico é visto pelo aluno. Nota interna de comunidade tem seção Somente equipe. Status/assinatura vêm dos serviços, sem regras no JavaScript.

## 6. Como conferir
admin@gomut.example → Comunidade: filtros e Respostas e moderação. Encaminhar, responder, solução, fixar/ocultar/reabrir. Em Chamados: Em andamento/Resolvidos, buscar e atualizar resposta/status. Fluxo real pode ser iniciado pelo aluno em Suporte. Chrome390/1440: telas200 sem overflow/erroJS; Comunidade inspecionada.

## 7. Pendências/desvios
FAQ/assuntos e demais configurações migram na2.8. Nenhum chamado real ou resposta clínica foi inventado; lista vazia na demo continua um estado válido. Sem mudanças nas regras de negócio.

## 8. Commit
feat: moderacao GoMut etapa 2.7; hash na entrega/diário. Sem push/merge.
