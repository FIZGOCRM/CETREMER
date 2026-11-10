# Relatório do redesign CETREMER

Data: 10/11/2026. Inspeção visual no navegador não executada, conforme instrução da revisão da fase 1; conferir externamente em 375, 768 e 1280 px.

## Commits

| Fase | Commit | Entrega | Testes após a fase |
| --- | --- | --- | --- |
| 2 | `3af97d8` | Login por e-mail, cadastro de aluno, recuperação de senha, SMTP dinâmico e telas de autenticação | 37 OK |
| 3 | `79add78` | Área do aluno, aula, Vimeo, progresso idempotente, ao vivo, comunidade e conta | 39 OK |
| 4 | `c4d6c6f` | Emissão e bloqueio de certificado, lista e verificação pública | 40 OK |
| 5 | `04cdb81` | Landing, página do curso e checkout | 40 OK |
| 6 | `5321fe1` | Painel, gestão de cursos/aulas, alunos, importação CSV, pedidos, comunidade e configurações | 44 OK |
| 7 | `f7cba15` | Limpeza de CSS/JS/templates antigos; kit removido do Git e ignorado; textos da landing alinhados à referência | 44 OK |

**Resultado final:** `python manage.py test --verbosity 0` — 44 testes, OK. `python manage.py makemigrations --check --dry-run` — nenhuma alteração pendente. `python manage.py migrate --noinput` aplicou `courses.0008_legacy_calendar` na base local. Um smoke test de todas as páginas públicas, do aluno e do painel retornou HTTP 200 usando o Django Client.

## Decisões sem confirmação

- A página pública usa os três números já presentes no handoff; dependem de confirmação da cliente.
- O cadastro usa o prefixo do e-mail como `username` interno e acrescenta sufixo em colisões. A interface pede apenas nome completo e e-mail.
- O gateway exibido no painel é MOCK até a cliente escolher o provedor. Não há transação real.
- Na falta de carga horária, assinatura, logo, links de termos e agenda, os trechos correspondentes ficam vazios ou são omitidos como na seção 10.
- O link de verificação usa `request.get_host`. A exportação de certificado usa a impressão A4 do CSS, sem biblioteca de PDF.
- A base local contém o seed sem certificados ou aulas concluídas; os estados são alcançados pelos passos abaixo, sem alterar dados automaticamente.

## Desvios e pendências

- Não houve inspeção visual nas três larguras por proibição explícita. A comparação com as telas de referência e a checagem de rolagem horizontal ficam para a revisão externa.
- **Classes em `29. Extras`: nenhuma.** O token `--c-success-hover` recebeu o valor `#DDF0E4` que já estava no CSS do kit, para cumprir a regra de cores apenas em `:root`.
- O painel de aulas oferece inclusão de PDF, mas ainda não oferece remoção individual de material. O aviso de exclusão de aula não mostra a contagem de alunos que a concluíram. A dica de duração automática do Vimeo após salvar também não aparece no formulário.
- O resumo lateral de edição de curso não mostra tempo total de vídeo. A importação mostra as 50 primeiras linhas, mas ainda não informa numericamente quantas ficaram fora da prévia visual.
- As exportações reais da Eduzz/Hotmart precisam de um CSV da cliente para validar aliases de colunas adicionais. A integração SMTP e o gateway de pagamento dependem das credenciais e decisão da cliente. O domínio de produção e a privacidade dos vídeos no Vimeo também precisam ser configurados pela cliente.
- No servidor de desenvolvimento, sem SMTP configurado, os e-mails aparecem no console. Em produção, o backend registra o erro e não entrega o e-mail até a configuração.
- A tela do painel de configurações preserva os papéis e campos antigos no banco; os gateways e tutor de IA seguem fora de escopo do handoff.

## Verificações da fase 7 e checklist da seção 8

- `style=` em `templates/`: apenas `partials/progress.html` para largura da barra. Nenhum `<style>`.
- Busca por emojis em `templates/`: vazia. Busca por `|safe` em `templates/`: vazia.
- Busca por `TheMembers`, `Desenvolvido com Python`, `/admin/`, `main.css`, `components.css` e `netflix.js` em templates e JS: vazia.
- CSS carregado: só `cetremer.css`. Cores hexadecimais de CSS: apenas em `:root`. `.env` e `db.sqlite3` ignorados. `_handoff/` mantido no disco e removido do controle de versão.
- Dinheiro com `|brl`, campos rotulados, permissão do painel, 404 de aula inexistente, matrícula no acesso pago, certificado com CPF válido e 100%, verificação pública sem CPF: verificados por testes e smoke test.
- Comparação visual, comportamento manual do Vimeo e do checkout e acessibilidade por tecnologia assistiva: pendentes de revisão externa.

## URLs para conferência em localhost

Servidor: <http://localhost:8000/>. Seed: admin `admin@cetremer.com.br` / `password123`; aluno `jane@student.com` / `password123`; criador `john@creator.com` / `password123`. As senhas são apenas do seed local. Se recriar a base, rode `migrate` e `loaddata data_dump.json`.

| Tela ou estado | URL | Como chegar |
| --- | --- | --- |
| Landing | `/` | Público. |
| Página do curso BLS | `/courses/suporte-basico-vida-bls/` | Público; com o aluno logado aparece “Ir para o curso”. |
| Checkout BLS | `/courses/suporte-basico-vida-bls/checkout/` | Público; alternar cartão/Pix e finalizar em ambiente MOCK. |
| Login | `/login/` | Entrar com e-mail. |
| Cadastro | `/register/` | Criar aluno sem matrícula automática. |
| Esqueci senha | `/senha/esqueci/` | Solicitar link do e-mail do seed; procurar link no console do servidor. |
| Link enviado | `/senha/enviado/` | Após enviar formulário de senha. |
| Criar senha | `/senha/nova/<uidb64>/<token>/` | Abrir link recebido no console; senha fraca deve ser recusada. |
| Verificar certificado | `/certificado/verificar/?codigo=<codigo>` | Após emitir, copiar o código; testar com e sem hífens. |
| Meus cursos | `/dashboard/` | Entrar como Jane. |
| Aula BLS | `/courses/suporte-basico-vida-bls/lessons/89/` | Entrar como Jane; botão conclui e atualiza progresso. |
| Aula inexistente | `/courses/suporte-basico-vida-bls/lessons/999999/` | Deve retornar 404. |
| Aulas ao vivo | `/ao-vivo/` | Entrar como Jane. |
| Comunidade | `/community/` | Entrar como Jane; filtro geral e cursos matriculados. |
| Minha conta | `/settings/` | Entrar como Jane; completar nome e CPF para certificado. |
| Certificados | `/certificados/` | Entrar como Jane. |
| Certificado bloqueado | `/courses/suporte-basico-vida-bls/certificate/` | Jane ainda sem progresso/CPF completos. |
| Certificado emitido | `/courses/suporte-basico-vida-bls/certificate/` | Como Jane, conclua as aulas 89, 90, 91 e 92 pelo botão; em `/settings/` informe nome completo e um CPF válido seu; volte à URL. Para imprimir, acrescente `?imprimir=1`. |
| Painel | `/painel/` | Entrar como admin. |
| Cursos | `/painel/cursos/` | Como admin; busca e categoria. |
| Novo curso | `/painel/cursos/novo/` | Como admin. |
| Editar curso | `/painel/cursos/60/` | Como admin, BLS do seed. |
| Grade de aulas | `/painel/cursos/60/aulas/` | Como admin; `?aula=89` edita, `?nova=<id do módulo>` cria aula. |
| Alunos | `/painel/alunos/` | Como admin; `?aluno=<id>` abre detalhe e matrícula. |
| Importar alunos | `/painel/alunos/importar/` | Como admin; baixe o modelo CSV e envie três linhas: uma nova, `jane@student.com` e uma com e-mail inválido. Confira a prévia antes de confirmar. |
| Pedidos | `/painel/pedidos/` | Como admin; filtros e CSV. |
| Comunidade admin | `/painel/comunidade/` | Como admin; abas pendentes/respondidos/ocultos. |
| Configurações | `/painel/configuracoes/` | Como admin; testar segredo salvo sem expor valor completo no HTML. |

URLs `/creator/` e filhas redirecionam com 301 para o painel. O arquivo `_handoff/cetremer-kit/HANDOFF.md` permanece no disco para comparação externa.
