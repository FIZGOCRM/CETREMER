# Demonstração da área do aluno — 16/11/2026

## Abrir agora

Servidor de demonstração local: <http://127.0.0.1:8016/login/>.

| Acesso fictício | E-mail | Senha da demonstração local |
|---|---|---|
| Aluno | aluno@gomut.example | DemoGomut2026! |
| Administrador | admin@gomut.example | DemoGomut2026! |

Essas contas pertencem apenas à base fictícia em `.venv/gomut-demo.sqlite3`. Não são credenciais de produção. A configuração local fica em `.venv/gomut-demo-env.json`, que contém segredos locais e não deve ser versionada ou enviada.

## Roteiro para apresentar

1. Abrir o login da GoMut e entrar como aluno.
2. Mostrar os dois cursos, o destaque, a busca e o progresso salvo.
3. Abrir as informações de um curso pelo cartão; fechar com o botão ou Escape.
4. Abrir o curso pela página própria e navegar pelos módulos e aulas.
5. Na aula, mostrar o iframe real do Vimeo, anterior/próxima, conclusão e materiais.
6. Marcar uma aula como concluída, recarregar e conferir que o progresso permanece.
7. Abrir **Quiz**, favoritos, ajuda ou notificações: os recursos indisponíveis têm indicação **Necessita de backend**.
8. Abrir **Meu progresso**: conclusões e percentuais vêm do banco; tempo e sequência de estudo são indicados como pendentes.
9. Sair e entrar como administrador. Abrir `/painel/alunos/`, selecionar o aluno e expandir **Definir período quitado** no curso desejado.
10. Informar início e último dia quitado inclusive, revisar e confirmar. Um novo período é registrado sem criar cobrança; períodos sobrepostos são recusados para preservar o histórico. A tolerância atual é de três dias após o período quitado.

## O que foi entregue

- Login com a identidade e as artes fornecidas da GoMut, autenticação real e destinos separados por papel.
- Tokens isolados, Archivo variável e Inter, 51 SVG fornecidos pelo handoff e CSS normativo.
- Início do aluno, cartões dos dois cursos, janela de informações, página interna do curso, módulos e aula.
- Vimeo incorporado, materiais existentes, navegação e conclusão com persistência. A conclusão manual funciona mesmo com indisponibilidade do SDK externo do Vimeo.
- Página de progresso com os dados já existentes. Nenhuma estatística fictícia de tempo de estudo é apresentada como medida real.
- Controle manual e auditado de períodos por matrícula, com datas inclusivas na interface, confirmação explícita, idempotência e proteção contra sobreposição.
- Comando `prepare_demo` explícito e não destrutivo, permitido somente com `GOMUT_DEMO_MODE=True`.
- Nenhuma chamada de cobrança ou ativação do Asaas. Nenhum aluno real importado.

## Diferenças e limites declarados

- Top 10 removido e catálogo reduzido a dois cursos conforme solicitado. Fileiras de mentoria/trilhas não foram preenchidas artificialmente.
- Marca do aluno e conteúdo continuam fictícios, conforme o pacote. A marca real do cliente pode ser configurada na etapa de conteúdo.
- O painel administrativo e as telas secundárias já existentes de conta, comunidade, certificados e ao vivo preservam a implementação e o visual anteriores. A reformulação visual completa dessas telas não faz parte desta entrega prioritária. O novo controle de datas foi incluído no painel existente.
- Os dados reais continuam em Curso → Módulo → Aula, com acesso por curso. Não foi criada a estrutura fictícia de mentoria/temas/trilhas do protótipo.
- O certificado mantém as regras existentes por curso; não foi aplicada a regra fictícia de certificado único após 12 meses de mentoria.
- As datas manuais acrescentam intervalos e não apagam ou substituem períodos anteriores. Correção retroativa e cancelamento com revogação de um período já concedido continuam pendentes.
- O login não promove cadastro público. Primeiro acesso e recuperação continuam disponíveis nas rotas existentes; a inclusão de links novos no cartão fechado não foi decidida nesta entrega.
- O vídeo cadastrado é um exemplo público do Vimeo e não contém uma aula do médico. O iframe e seus controles carregaram, mas a reprodução não avançou nos testes automatizados: não considerar streaming ou conclusão automática homologados. Validar os vídeos reais e suas permissões de incorporação quando forem fornecidos.
- Não há PDFs fictícios carregados: a aba mostra o estado vazio quando não há material. Upload e links de PDF existentes foram preservados.
- Pesquisa atual do início filtra metadados dos cursos exibidos; busca global em aulas ainda não foi entregue.
- Janelas usam diálogo nativo com foco contido e retorno de foco, mantendo o conteúdo acessível também por URL própria.
- A composição do curso e da lista lateral foi adaptada ao modelo de dois cursos, reutilizando os componentes do handoff. Não declarar equivalência visual integral com as 26 telas do protótipo.

## Verificação

- Suíte Django: 138 testes passaram. `manage.py check` sem problemas; `makemigrations --check --dry-run` sem mudanças; sintaxe dos três JavaScript alterados verificada com Node.
- Edge: login, dois cursos, janela e fechamento por Escape, acesso à aula, persistência da conclusão, abas por teclado, pesquisa sem resultado, recursos pendentes e formulário administrativo.
- Larguras verificadas em Edge: 390, 768, 900, 1024, 1280 e 1440 px, sem overflow horizontal nas telas principais.
- Chrome: login, cursos, aula, conclusão e indicação de recurso pendente em 390 px.
- Firefox instalado: captura e inspeção da tela de login em 1440 × 900. Fluxo autenticado completo ainda não verificado nesse navegador.
- Opera: não verificado. Nenhum navegador ou pacote adicional foi instalado.
- Fontes: Archivo variável carregada e verificada no navegador; login usa campos e botão de 52 px; os controles normativos mantêm seus tamanhos conforme o contexto.
- Capturas de conferência locais ficam em `.venv/gomut-*.png`, sem serem misturadas às imagens normativas do handoff.

## Reabrir a demonstração em outro terminal

Na raiz do projeto, o comando abaixo reutiliza a configuração local já preparada e executa o servidor em primeiro plano. Requer que a base/configuração da demonstração já existam. Não publica nada na internet.

```powershell
@'
import json, os
from pathlib import Path
from django.core.management import execute_from_command_line

config = json.loads(Path('.venv/gomut-demo-env.json').read_text(encoding='utf-8'))
os.environ.update(config)
os.environ['ASAAS_API_ENABLED'] = 'False'
os.environ['ASAAS_WEBHOOK_ENABLED'] = 'False'
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8016'])
'@ | ./.venv/Scripts/python.exe -
```

Para criar outra demonstração, configurar `DJANGO_DATABASE_PATH` para um arquivo dedicado, as chaves locais necessárias e `GOMUT_DEMO_MODE=True`; executar `migrate` e depois `prepare_demo --password SENHA-DE-TESTE`. O comando preserva contas e senhas já existentes. Não usar `seed.py` para esse preparo, porque ele apaga dados.

## Revisão da página inicial — solicitada após a primeira apresentação

- Hero compacto, com títulos redimensionados sem partir as palavras de “Emergências cardiovasculares”. Em 1440px de largura, a altura ficou em aproximadamente 413px após o carregamento da fonte.
- Um slide por curso matriculado com acesso liberado. Curso não iniciado mostra “Começar”, em andamento mostra “Continuar” e concluído mostra “Rever”.
- Vários cursos: setas, indicadores e rotação a cada oito segundos, com botão de pausa. Interação, foco, janela aberta e preferência por movimento reduzido impedem a troca automática.
- Slides compartilham a altura do maior conteúdo; os inativos ficam invisíveis, fora da navegação por teclado e da árvore de acessibilidade.
- “Meus cursos” é a primeira seção; “Seu progresso” usa os totais reais da conta. Cartões foram ampliados para o catálogo de dois cursos.
- Modal com barra fixa: “Expandir janela”/“Recolher janela”, “Página do curso” e fechar. No celular a janela já ocupa a tela.
- Verificados em Chrome: rotação, pausa, alternância manual, expansão/recolhimento, Escape e seis larguras (320, 390, 768, 1024, 1440 e 1920px). Sem overflow horizontal; fonte carregada antes de comparar alturas.
- Esta revisão adapta as medidas originais do handoff por solicitação expressa do usuário.
