# Etapa 2.8 — Ao vivo, Certificados e Configurações

## 1. O que foi feito
Agenda, FAQ e assuntos migrados para GoMut. Contexto por curso na agenda. Lista de certificados emitidos com snapshots, código/cópia e validação pública, sem CPF. Configurações por seção: escola/logo, mentor/equipe, suporte, texto do plano, assinatura, SMTP e acompanhamento de avisos. Formulários validados e segredos nunca renderizados.

## 2. Arquivos
painel/{settings_forms,test_settings_design,urls}.py; painel/views/{settings,certificates,live,support}.py; users/{services,notifications}.py; templates/base_painel_gomut.html; templates/painel/{settings,certificates,live,support_settings}.html; static/{css/gomut/panel-v1.css,js/gomut/panel.js}; core/test_handoff_phase0.py; sales/test_asaas_configuration.py; este relatório.

## 3. Migrações
Nenhuma. Reutiliza campos e modelos da fase1; não criou novos controles globais de negócio.

## 4. Testes
302 testes, zero falhas/erros. Quatro novos: configuração/validação, certificado sem CPF, agenda por curso/FAQ e senha SMTP sem exposição. Três começaram RED; segurança de senha existente permaneceu verde. Assert antigo de texto do widget Asaas removido da V1 foi trocado pela nova base; todas as verificações de segredo/imutabilidade da fundação Asaas foram preservadas.

## 5. Causas e efeitos
Salvar e-mail inválido não salva os demais campos. Senha vazia conserva a configuração atual; senha nova criptografada. Sem SMTP, teste não declara entrega. Testes SMTP e links de acesso não entram em retentativa automática sem conteúdo apropriado. Campos de gateway continuam intocados e fora da interface.

## 6. Como conferir
admin@gomut.example → Configurações e cada seção. Mentor/equipe exibem valores ilustrativos editáveis; SMTP mostra apenas se há senha configurada. Avisos mostra fila vigente e resultados, sem botões fictícios. Ao vivo filtra curso e permite CRUD. Certificados mostra emissão demo/código e verificação, sem CPF. Chrome390/1440 em sete páginas200, sem overflow/erroJS; Mentoria inspecionada.

## 7. Pendências/desvios
Avisos expõe operação, resultados e preferências já aprovadas. Não foram inventadas chaves globais para silenciar comunidade/suporte ou vencimento: o modelo da fase1 não definiu essas políticas e a fase2 deve reutilizar regras. SMTP/domínios reais continuam pendentes de infraestrutura. Certificados são consultados, sem reemissão automática nem alteração do snapshot. Login do médico e novos papéis foraV1.

## 8. Commit
feat: configuracoes e certificados GoMut etapa 2.8; hash na entrega/diário. Sem push/merge.
