# V1 GoMut / Emergensimples — entrega para QA

Data: 17/11/2026. Branch: `feat/area-aluno-handoff`.

Fonte de decisão: [plano oficial](<handoff v1 oficial/prompt-implementacao-gomut_3.md>). Os documentos antigos não substituem esse plano. Esta entrega é local, para QA, e não uma implantação em produção.

**Atualização do QA:** [avisos de prazo](ajuste-avisos-vencimento.md) agora ficam nas notificações somente nos três últimos dias efetivos de acesso. Faixas do Início e contagens nos cursos foram retiradas. A conta fictícia também recebeu [histórico de estudo ilustrativo](qa-dados-demonstracao.md) solicitado para visualizar os gráficos. O [acesso do produtor](qa-login-produtor.md) agora mantém a identidade GoMut desde o redirecionamento de login até a saída de conta. A suíte atual tem **352 testes aprovados**; os números por etapa abaixo são registros históricos.

## 1. O que foi feito

- Área do aluno com cursos próprios, retomada, progresso, quizzes, avaliação opcional e certificado.
- Planos independentes por matrícula, datas corrigíveis, encerramento e reativação com histórico.
- Publicação, liberação mensal de módulos e proteção dos endpoints no servidor.
- Materiais autenticados, anotações privadas, comunidade, suporte e encontros ao vivo.
- Avisos internos, preferências e fila de e-mails com validação antes do envio.
- Painel GoMut para operar cursos, conteúdo, alunos, planos, moderação e configurações.
- Relatórios com dados registrados, exportação CSV e prévia de membro somente leitura.
- Revisão final independente; seis problemas importantes reproduzidos e corrigidos com regressões.
- Relatórios por etapa e decisões consolidados nos links abaixo.
- A etapa 1.16 permanece bloqueada pela planilha real, conforme determinação expressa do plano.

## 2. Arquivos e índice das entregas

Cada relatório descreve os arquivos, testes, causas e efeitos e verificação em tela da etapa. Os hashes abaixo permitem revisar a alteração exata com `git show HASH --stat` ou `git show HASH`.

| Etapa | Relatório | Commit | Resultado da suíte na etapa |
|---|---|---|---|
| 0 | [Preparação](etapa-0-preparacao-v1.md) | `bbbf883` | 138 |
| 1.1 | [Planos](etapa-1.1-planos.md) | `94a1e26` | 151 |
| 1.2 | [Publicação e liberação](etapa-1.2-liberacao.md) | `6bc5067` | 162 |
| 1.3 | [Player](etapa-1.3-player.md) | `f40813e` | 176 |
| 1.4 | [Progresso](etapa-1.4-progresso.md) | `9759b0f` | 182 |
| 1.5 | [Página da aula](etapa-1.5-aula.md) | `eb73876` | 188 |
| 1.6 | [Quizzes](etapa-1.6-quizzes.md) | `d19c885` | 200 |
| 1.7 | [Avaliação final](etapa-1.7-avaliacao.md) | `c75d8aa` | 210 |
| 1.8 | [Importação de perguntas](etapa-1.8-importacao-perguntas.md) | `7c7fd81` | 219 |
| 1.9 | [Certificados](etapa-1.9-certificados.md) | `5c92426` | 224 |
| 1.10 | [Materiais](etapa-1.10-materiais.md) | `eb4b8e4` | 233 |
| 1.11 | [Comunidade](etapa-1.11-comunidade.md) | `044d45b` | 243 |
| 1.12 | [Suporte](etapa-1.12-suporte.md) | `d2f9fde` | 252 |
| 1.13 | [Ao vivo](etapa-1.13-ao-vivo.md) | `aff234d` | 260 |
| 1.14 | [Notificações](etapa-1.14-notificacoes.md) | `51139b3` | 271 |
| 1.15 | [Navegação e conta](etapa-1.15-navegacao.md) | `edb861e` | 279 |
| 1.16 | [Importação: bloqueada](etapa-1.16-importacao-pendente.md) | `2f019fa` | Sem implementação desta etapa |
| 1.17 | [Operação](etapa-1.17-operacao.md) | `7a17844` | Última suíte: 279 |
| 2.1 | [Estrutura do painel](etapa-2.1-painel-base.md) | `dd8a5a3` | 281 |
| 2.2 | [Cursos e criação](etapa-2.2-cursos.md) | `d7b67fc` | 283 |
| 2.3 | [Básico e visão geral](etapa-2.3-curso.md) | `0bf2797` | 285 |
| 2.4 | [Conteúdo](etapa-2.4-conteudo.md) | `0bf2fce` | 287 |
| 2.5 | [Editor de aula](etapa-2.5-editor.md) | `516d727` | 291 |
| 2.6 | [Alunos e planos](etapa-2.6-alunos.md) | `dcddcd8` | 296 |
| 2.7 | [Moderação](etapa-2.7-moderacao.md) | `cf78734` | 298 |
| 2.8 | [Configurações](etapa-2.8-configuracoes.md) | `dce76fe` | 302 |
| 2.9 | [Relatórios](etapa-2.9-relatorios.md) | `b6a981a` | 307 |
| 2.10 | [Visualizar como membro](etapa-2.10-preview.md) | `72bb954` | 315 |

Leituras de apoio:

- [Decisões de produto e confirmações](decisoes-produto.md).
- [Decisões durante a execução, com consequências](decisoes-execucao-v1.md).
- [Revisão final e correções](revisao-final-v1.md).
- [Manual da equipe](manual-operacao.md).
- [Checklist de produção](producao-checklist.md).
- [Backup e restauração SQLite](operacao-sqlite.md).

## 3. Migrações

Aplicadas somente à demonstração `.venv/gomut-demo.sqlite3`; a suíte também constrói o esquema em banco de teste vazio.

| App / intervalo | Principais modelos e campos |
|---|---|
| courses `0010`–`0012` | Duração do plano, âncora original, observação da matrícula, `AccessChange`, encerramento antecipado e intervalo vazio condicionado |
| courses `0013` | Situação editorial e mês de liberação de módulo; situação da aula |
| courses `0014` | Posição, tempo creditado, relógio do player, `StudyDay`, `ActivityEvent` |
| courses `0015`–`0017` | `LessonNote`, quiz/perguntas/alternativas/tentativas e data de qualificação para certificado |
| courses `0018`–`0020` | `CourseMaterial`, `MaterialOpen`, `LiveEvent`, `LiveReminder`, data de publicação da aula |
| users `0007`–`0010` | Contato de suporte, relógio global do aluno, estado de reprodução e assinaturas do mentor/equipe |
| users `0011`–`0015` | `Notification`, `EmailLog`, prazo de entrega, `StudentVisit`, `MemberPreviewLog`, reserva temporária de envio |
| community `0004` | Solução, fixação, moderação, encaminhamento e assinatura de respostas |
| support `0001` | FAQ, assuntos, chamados, eventos do histórico e votos |

Nenhuma dependência adicionada; stack mantida: Django 4.2.30, templates, CSS/JS próprios e SQLite.

## 4. Verificação

- Suíte atual: **352 testes, zero falhas e zero erros**. Linha de base: 138.
- Migrações: esquema vazio nos testes e atualizações na demo; `makemigrations --check --dry-run` sem alterações pendentes.
- `git diff --check`: sem erros.
- Rodada geral da entrega: **72 combinações página/largura**, Chrome e Edge, 390 e 1440 px, HTTP 200, sem overflow horizontal ou `pageerror`. Após o ajuste dos avisos, mais dez combinações no Chrome e duas conferências do cartão de exemplo, sem overflow ou erro JS.
- Prévia de membro: conferência adicional em oito combinações; zero POST espontâneo, POST de heartbeat forjado recusado, snapshot dos dados do aluno inalterado e auditoria encerrada ao sair.
- SMTP/SQLite: três regressões também executadas em SQLite temporário **em disco**; heartbeat concorrente não aguarda o envio; reserva impede entrega concorrente e se recupera após expirar.
- Conferências anteriores por etapa incluem nota criada/removida, quiz 100%, avaliação 75%, emissão e impressão do certificado em uma página, PDF autenticado, janela de plano, reordenação por teclado e CSV baixado.
- Firefox e Opera **não foram validados**. A ausência de erro nos navegadores testados não equivale a certificação de todos os navegadores.
- Reprodução externa: SDK do Vimeo carregou, mas o vídeo público de demonstração exibiu “Questão de direitos / problemas para autorizar a reprodução”. A mensagem de falha C8 e a conclusão manual continuaram disponíveis. Reprodução efetiva, retomada e sequência real de eventos devem ser reconferidas com o vídeo do cliente e o domínio autorizado; não são declaradas aprovadas nesse teste externo.

As capturas e scripts locais ficam em `.venv/v1-qa/` e `.venv/`, ignorados pelo Git. Não contêm credenciais de produção e não compõem o produto.

## 5. Causas e efeitos

| Casos do plano | Evidência |
|---|---|
| C1 | Cálculo mensal testado; importação real continua pendente da 1.16 |
| C2–C7 | Testes de planos/liberação/publicação e histórico; revisão final ampliou proteção para tópicos e PDFs abertos |
| C8 | Mensagem de falha observada no navegador com recusa real do Vimeo; botão manual disponível |
| C9–C13 | Testes de relógio global, bloqueio no heartbeat, tolerância, encerramento e reativação auditada |
| C14–C17 | Testes de qualificação histórica, alterações editoriais, notas congeladas, exclusão recusada e desativação |
| C18–C20 | Quiz opcional, avaliação opcional e certificado emitido preservado; regressão C19 inclui aviso de vencimento e e-mail |
| C21–C25 | Testes de ocultação, matrícula, somente leitura após término, encaminhamento e privacidade dos chamados |
| C26–C28 | **Pendentes da importação V1**, não substituídos pelo importador legado |
| C29–C30 | Sem SMTP não envia; referências únicas, retentativa vigente, reserva concorrente e revalidação de acesso/evento |

## 6. Como conferir na tela

### Acessar

Abra [http://127.0.0.1:8016/login/](http://127.0.0.1:8016/login/).

| Perfil | E-mail | Senha |
|---|---|---|
| Aluno de demonstração | `aluno@gomut.example` | Senha de QA informada na conversa |
| Administrador de demonstração | `admin@gomut.example` | Senha de QA informada na conversa |

Após a entrega, a pedido do usuário, foi definida uma senha de QA para essas duas contas fictícias, somente no banco de demonstração. Os dois logins foram conferidos. A senha foi informada na conversa e não é versionada. Se o navegador já estiver no painel, use **Visualizar como membro** para a navegação sem gravação. Para testar conclusão, notas e quiz, entre com o aluno.

Se o servidor local tiver parado, na raiz do projeto:

```powershell
.venv/Scripts/python.exe -B .venv/run_v1.py runserver 127.0.0.1:8016
```

Esse lançador local usa apenas a configuração e a base de demonstração em `.venv/`; não é receita de produção. Não executar `seed.py`. Não usar `prepare_demo` para zerar os exercícios: ele é não destrutivo e não apaga histórico.

### Roteiro do aluno — primeiro

1. **Início:** conferir dois cursos no carrossel, pontos de continuidade, datas e resumo. Emergências cardiovasculares já está concluído na demo; Plantão sem GPT permite testar o começo.
2. **Meus cursos:** abrir as informações, expandir a janela e entrar no curso. Conferir que não aparecem cursos alheios.
3. **Curso:** abrir/fechar módulos, conferir aulas e indicação de quiz apenas nas aulas que o possuem.
4. **Aula:** verificar a mensagem se o Vimeo recusar o vídeo. Com vídeo autorizado, assistir, pausar, sair e voltar para conferir retomada; seek não deve contar como tempo assistido.
5. **Conclusão e quiz:** marcar uma aula manualmente, ver a etapa mudar, iniciar o quiz, responder, ler o comentário e revisar a nota. Pular quiz não deve bloquear a próxima aula.
6. **Anotações:** salvar uma nota no minuto da aula, navegar, voltar e removê-la. Outro aluno não pode vê-la.
7. **Progresso:** conferir aulas, próxima ação e gráficos. A conta fictícia agora tem um histórico ilustrativo solicitado no QA: 1h51 na semana, quatro dias de sequência e mapa preenchido. Está identificado na tela. A conclusão manual em si não inventa minutos assistidos; contas reais usam somente o tempo registrado pelo player.
8. **Avaliação/certificado:** no curso concluído, revisar a avaliação ilustrativa e abrir o certificado já emitido. Conferir CPF mascarado, copiar código/dados e imprimir/Salvar como PDF. A validação pública não mostra CPF.
9. **E-books:** abrir um PDF ilustrativo, conferir o visualizador do navegador e a indicação “já abri”.
10. **Comunidade:** criar dúvida, responder e marcar solução. No painel, encaminhar ao mentor e responder como equipe; voltar ao aluno e conferir a assinatura. Não usar dados de pacientes.
11. **Suporte:** buscar FAQ e abrir chamado ilustrativo; testar privado e público. No painel, passar por Em análise e Resolvido com resposta; conferir linha do tempo e aviso ao aluno.
12. **Ao vivo / conta / avisos:** conferir agenda, alternar lembrete, editar preferências, buscar conteúdo e marcar notificações como lidas. A demo não inventa link real de sala.

### Roteiro do painel — depois

1. **Meus cursos → Criar curso:** cadastrar um curso de QA em rascunho; criar módulo/aula e publicar conscientemente. Rascunho não deve aparecer para o aluno.
2. **Básico / Visão geral:** salvar descrição, duração do plano e demais dados; conferir os indicadores com os registros existentes.
3. **Conteúdo:** criar aula rápida, editar Vimeo/duração/PDF, mover e ordenar por teclado. Alterar liberação de módulo para um mês futuro deve exigir confirmação quando afetar alunos.
4. **Quiz / avaliação:** cadastrar pergunta ilustrativa, editar e desativar; tentativas anteriores devem manter o resultado. Conteúdo com histórico deve oferecer despublicar/desativar.
5. **Alunos → Gerenciar plano:** anotar as datas antes do teste; encerrar, conferir bloqueio no aluno, reativar dentro do limite e corrigir datas com motivo. Conferir histórico e independência dos dois cursos. Restaurar conscientemente os dados da demo ao terminar.
6. **Comunidade / Chamados:** conferir filtros, encaminhamento, assinatura, ocultação, solução e histórico do chamado.
7. **Configurações / Certificados:** conferir nomes e temas, FAQ, assuntos, dados do certificado e fila de avisos. Não cadastrar SMTP real nesta demo sem a definição operacional.
8. **Relatórios:** alternar janela e baixar CSV; comparar visitas/horas reais com a situação acadêmica atual, que não se limita à janela.
9. **Visualizar como membro:** escolher o aluno, navegar e tentar uma ação. Deve ficar desabilitada; ao voltar ao painel, o administrador continua autenticado e os dados do aluno não mudam.
10. Repetir os fluxos prioritários em 390 px e 1440 px. Capturar URL, perfil, ação, resultado esperado/obtido e imagem para cada defeito de QA.

## 7. Pendências e limites

| Item | Situação |
|---|---|
| Planilha real / etapa 1.16 | Bloqueada. Faltam dados, contrato validado do arquivo e prévia antes da confirmação. Não usar o importador legado para planos V1. |
| Vídeos, PDFs, perguntas e cronograma reais | Demo ilustrativa. Vimeo precisa de vídeo autorizado e validação no domínio final. |
| Assinatura do mentor/equipe | Textos de demonstração editáveis nas configurações. |
| SMTP real e agendamentos | Não configurados nem executados externamente. Os testes simulam transporte; aceite SMTP não garante caixa de entrada. |
| Infraestrutura, HTTPS, domínio, backups e restauração operacional | Checklist a preencher; testes de backup não substituem restauração operacional. |
| Segurança de implantação | Seis avisos no ambiente local: HSTS, redirecionamento HTTPS, chave local, cookies de sessão/CSRF seguros e DEBUG. Não declarar produção pronta. |
| Asaas / compras / renovação | Fora da V1; fundação anterior preservada, checkout permanece desativado. |
| Demais recursos fora da V1 | Conforme plano: sem marketplace/trilhas, multi-tenant, PDF servidor, PDF.js, anexos em chamados, novos papéis ou favoritos. |

Nenhum envio real, importação real, instalação, push, merge ou deploy foi realizado. A branch e o servidor local ficam disponíveis para QA.

## 8. Commits da revisão final

| Correção | Commit |
|---|---|
| Histórico de comunidade e material aberto impede exclusão | `f89b7da` |
| Chamados coletivos exigem acesso ativo | `d9c6cb0` |
| Qualificação para certificado acompanha mudanças editoriais | `9407801` |
| Publicação efetiva do curso | `dfd1a2d` |
| Avisos obsoletos não são entregues | `520695e` |
| SMTP sem manter trava SQLite; reserva recuperável | `d4d4470` |
| Interface do voto conforme permissão | `36a534e` |
| Aviso sem avaliação inexistente (C19) | `9f00248` |

O complemento de interface dos chamados e o ajuste C19 estão detalhados no [relatório final](revisao-final-v1.md). O commit deste próprio documento pode ser localizado por `git log -1 -- docs/entrega-v1-qa.md`.
