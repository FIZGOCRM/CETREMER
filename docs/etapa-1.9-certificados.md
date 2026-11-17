# Etapa 1.9 — certificados

## 1. O que foi feito
- Lista de certificados no layout de membros, requisitos por curso e avaliação apenas quando existe.
- Nome/CPF na própria página, validação real, salvar dados antes de concluir e Salvar e emitir quando academicamente pronto.
- Emissão transacional e snapshot preservado; registro de atividade certificate_issued somente na primeira emissão.
- Certificado com código, cópia, link de validação e impressão nativa A4 paisagem.
- CPF privado mascarado, sem valor completo no HTML do certificado nem na verificação pública.
- LinkedIn com link público estático e Copiar dados, conforme aprovação e documentação atual.
- Marca da demo vem de SiteSettings, corrigindo apenas o nome legado padrão para Emergensimples no prepare_demo.

## 2. Arquivos
- `courses/certificate_views.py`
- `courses/forms.py`
- `courses/management/commands/prepare_demo.py`
- `courses/services.py`
- `courses/templatetags/cetremer.py`
- `courses/test_certificate_experience.py`
- `courses/tests.py`
- `docs/decisoes-produto.md`
- `docs/etapa-1.9-certificados.md`
- `static/css/gomut/members.css`
- `static/js/gomut/certificate.js`
- `templates/courses/certificate.html`
- `templates/courses/certificate_error.html`
- `templates/courses/certificate_ready.html`
- `templates/courses/certificates.html`
- `templates/courses/verify_certificate.html`

## 3. Migrações
Nenhuma. Reutiliza Certificate e a elegibilidade da 1.7; nenhum PDF é gerado no servidor.

## 4. Testes
224 testes, zero falhas/erros; cinco novos em courses/test_certificate_experience.py. Primeiro RED por ausência de formulário/layout/mascaramento; GREEN após implementação. Cobrem formulário inline, CPF inválido sem alterar perfil/emitir, emissão, ausência de CPF completo e dados LinkedIn sem CPF. Três asserts antigos presos à capitalização do título foram alinhados à nova tela; os de emissão passaram a conferir o código real do certificado.

## 5. Causas e efeitos
C14/C15 continuam cobertos pela 1.7 e emissão HTTP após fim; C20 continua coberto pela suíte de snapshot, que altera progresso/dados e conserva o certificado emitido. A primeira emissão adiciona atividade, sem duplicar em reenvios.

## 6. Como conferir na tela
1. aluno@gomut.example → Certificados (/certificados/). Cardiologia está concluída/aprovada pela QA da 1.7; foi emitido um certificado de demonstração pela nova tela com CPF ilustrativo validado.
2. Ver requisitos, Ver certificado, Copiar código e Copiar link. Outra disciplina permanece independente.
3. Adicionar ao LinkedIn abre o formulário público; Copiar dados reúne nome do curso, instituição, emissão, código e URL. O aluno preenche/confirma no LinkedIn.
4. Baixar PDF abre a impressão do navegador; escolher Salvar como PDF. Não há biblioteca PDF no backend.
5. Conferido em Chrome 390/1440, sem overflow/pageerror. O código e os dados LinkedIn foram copiados pela interface. PDF efetivamente impresso: uma página, MediaBox 841.92 × 594.96 pontos (A4 paisagem), aberto e inspecionado no renderizador nativo do Chrome. Capturas/PDF de QA em .venv/v1-qa/, não versionados.
6. /certificado/verificar/?codigo=<código> funciona sem login e não mostra CPF.

## 7. Pendências/desvios e decisões
A documentação oficial informa que o Add to Profile não preenche automaticamente os campos. O usuário aprovou o link estático e Copiar dados, em vez da URL legada personalizada. Fonte consultada em 17/11/2026: [FAQ oficial LinkedIn](https://www.linkedin.com/help/linkedin/answer/a528030). Não foi criado nada no perfil LinkedIn de ninguém.

O usuário também autorizou seguir as recomendações nas demais dúvidas e continuar todas as fatias para entrega de QA, sem novas paradas rotineiras; a decisão foi registrada em docs/decisoes-produto.md.

Carga horária e assinatura aparecem quando configuradas; nenhum dado real ausente foi inventado. PDFs usam apenas a impressão do navegador. As ferramentas Python/Poppler não estavam instaladas; nenhuma dependência foi acrescentada, e a verificação visual foi feita no renderizador de PDF existente do Chrome. Nenhum segredo ou senha foi versionado.

## 8. Commit
Commit único `feat: certificados e impressao da etapa 1.9`; hash na entrega/diário. Sem push/merge.
