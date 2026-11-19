# Redesign do painel do produtor GoMut

O pacote `gomut-handoff-redesign/gomut-handoff` orientou a atualização do painel Django. A implementação está na branch local `feat/plantao-sem-gpt-v2`. O endereço inicial é [Painel do produtor](http://127.0.0.1:8026/painel/).

## Como conferir

Entre com a conta fictícia de produtor `produtor-v2@gomut.example`. A senha utilizada na verificação local está em `.venv/v2-acessos-local.txt`. Se já estiver conectado como aluno e abrir uma página do produtor, use **Trocar para conta de produtor**. Depois da autenticação, o painel abre a página solicitada.

| Área | Onde conferir | O que observar |
|---|---|---|
| Início | `/painel/` | Pendências com destino de resolução, indicadores, acessos por dia, cursos com alunos e próximo encontro. |
| Alunos | `/painel/alunos/` | Busca e filtros na URL, ficha sobre a lista, matrículas, datas, histórico e observações. O código de primeiro acesso aparece em uma janela própria, com cópia e mensagem para entrega manual. |
| Cursos e aulas | `/painel/cursos/` | Criar um curso, abrir sua visão geral e navegar por Conteúdo, Detalhes, Vitrine, Materiais, Avaliação final e Ao vivo. Os editores de aula e quiz mantêm o contexto do curso. |
| Curadoria | Cursos → abrir o curso → Vitrine | Novidades e Outros cursos na página inicial. No Top 10, adicionar da biblioteca, ordenar por arraste ou teclado, escolher a arte, salvar e reabrir a seleção semanal. |
| Comunidade e chamados | `/painel/comunidade/` e `/painel/chamados/` | Lista e detalhe com URL própria para a seleção. A observação interna da comunidade é identificada. Nos chamados, o histórico de atendimento pode ser lido pelo aluno. |
| Operação | `/painel/vencimentos/`, `/painel/ao-vivo/` e `/painel/certificados/` | Abrir a ficha a partir de um vencimento, estender um plano elegível, agendar encontros e copiar ou verificar o código de um certificado. |
| Relatórios | `/painel/relatorios/` e `/painel/relatorios/aulas/` | Indicadores dos últimos 7, 30 ou 90 dias, métricas por curso e métricas de cada aula. |
| Configurações | `/painel/configuracoes/` | Navegação lateral, configuração de envio, registros e Central de ajuda. |
| Prévia de aluno | `/painel/visualizar/` | Escolher um aluno, conferir a faixa de somente leitura e retornar à tela de origem. |

Para iniciar outra instância local com o mesmo banco de demonstração, use o lançador abaixo em uma porta livre. A instância validada usa a porta 8026.

```powershell
.\.venv-v2\Scripts\python.exe .venv\run_v2.py runserver 127.0.0.1:8027
```

## Decisões aplicadas

- A solução padrão da fase 0 permite publicar um curso sem aula publicada e sinaliza esse curso no cartão, no menu de situação e na lista de atenção.
- A edição da aula permite trocar o primeiro PDF e abrir os materiais adicionais. A substituição preserva o identificador do material e seu histórico de abertura. Ações de exclusão de aula e módulo respeitam o histórico.
- Estender acesso reutiliza a correção de datas com motivo obrigatório. Datas inválidas reabrem o formulário na ficha do aluno. Vencimentos usa a janela existente de 60 dias.
- A busca geral leva a Alunos. O nome da escola aparece na navegação. Duplicação e arquivamento de curso ficaram fora desta versão conforme a alternativa prevista no handoff.
- O chamado pertence ao aluno e ao assunto. Por isso, o filtro **Curso do aluno** considera as matrículas do solicitante. A visibilidade pública ou privada de cada chamado segue o modelo existente.
- A área do aluno conserva sua identidade visual. A faixa de prévia identifica o aluno selecionado e dá acesso à troca de aluno e ao retorno ao painel.

## Verificação local

A referência anterior registrada em `docs/RELATORIO_NOITE_V2.md` era de 434 testes em Django 5.2.19. A suíte completa desta entrega passou com **453 testes em 153,475 segundos**, em Django 5.2.19, usando `.venv-v2` e um banco temporário de teste.

O roteiro do Chrome percorreu 27 páginas em cada uma das três larguras, 390, 1280 e 1440 px. A tabela de certificados também coube em seu próprio contêiner a 1280 px. Foram conferidos o HTTP 200 para o produtor, um único título principal por página e a largura do documento. O roteiro também exerceu busca com manutenção do foco, abertura e fechamento da ficha pelo teclado, abertura do cadastro e retorno da prévia ao Top 10. O teste de aluno confirmou o HTTP 403 e completou a troca de conta pelo formulário real de login. O roteiro específico de cursos verificou 11 páginas e exercitou arraste, controle pelo teclado, descarte e persistência.

Os testes de aplicação cobrem a exibição única do código, dados de planos inválidos, estados de matrícula, filtros de chamados, indicadores por período, prévia contextual e preservação das aberturas de PDF. O Django passou no `check` e no `makemigrations --check --dry-run`. A comparação visual usou as referências do pacote. A verificação não incluiu auditoria integral de contraste ou equivalência pixel a pixel.

## Arquivos e commits

A casca e as telas estão em `templates/base_painel_gomut.html`, `templates/painel/` e `static/gomut/painel/`. As consultas e os fluxos de gestão continuam em `painel/`; a política de acesso ao painel está em `core/decorators.py`. O redesign não exigiu migration. O trabalho e a verificação foram locais.

| Commit | Alteração |
|---|---|
| `87232b5` | Gestão de cursos, abas, editores e curadoria semanal. |
| `b7f5704` | Publicação com aviso, preservação do histórico dos PDFs e verificações do curso. |
| `6564dae` | Navegação e operação do painel, relatórios, prévia e troca de conta. |
