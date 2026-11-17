# Prompt 2 — implementação

Use depois que o relatório do `PROMPT-1-reconhecimento-da-stack.md` estiver pronto. Cole o texto abaixo no agente de código, com a pasta `handoff-design/` disponível para leitura.

---

```text
Você vai implementar um design fechado. A pasta handoff-design/ contém tudo o que define a
aparência e o comportamento. O seu trabalho é reproduzir esse design neste projeto, com
fidelidade total. Você não toma decisões de estilo.

LEIA PRIMEIRO, nesta ordem:
1. handoff-design/LEIA-PRIMEIRO.md
2. handoff-design/01-regras-inviolaveis.md
3. handoff-design/08-pendencias-e-perguntas.md
4. handoff-design/02-tokens/tokens.md e tokens.json
5. handoff-design/03-componentes/componentes.md
6. handoff-design/05-telas/ (os três arquivos)
7. handoff-design/06-comportamentos-e-regras.md e 07-mapa-de-configuracoes.md

REGRAS DE TRABALHO
- A fonte normativa de estilo é o CSS em handoff-design/prototipo/assets/css/. Os arquivos
  css-por-componente-*.md são cópia dele, organizada por componente e com as variáveis resolvidas.
  Reproduza cada regra: mesmas medidas, cores, raios, pesos, espaçamentos, estados e pontos de
  quebra.
- Não use o valor "mais próximo" da escala da ferramenta de estilo. Se o valor exato não existir,
  crie-o.
- Não troque fontes, ícones, cores nem textos. Os ícones são os SVG de handoff-design/04-icones/.
- Não use o estilo padrão de nenhuma biblioteca de interface. Se precisar de um componente de
  biblioteca pelo comportamento (foco, teclado, acessibilidade), use-o sem estilo e aplique o
  estilo do handoff.
- O JavaScript do protótipo é referência de estrutura HTML, classes, textos e fluxos. Não copie a
  arquitetura dele: escreva o código no padrão deste projeto.
- Partes marcadas como "só demonstração" em LEIA-PRIMEIRO.md (login simulado, dados fictícios,
  reprodutor simulado, armazenamento no navegador) não são comportamento a copiar.
- Nada do que está em 08-pendencias-e-perguntas.md pode ser implementado por suposição.
- Sempre que faltar uma informação, PARE aquele ponto, registre a pergunta e siga com o que está
  definido. Nunca preencha a lacuna com uma escolha sua.

ORDEM DE EXECUÇÃO
Etapa 1 — Plano. Antes de escrever código, entregue:
  a) o mapeamento de cada token (handoff-design/02-tokens/tokens.json) para a forma como este
     projeto define tema, nos três contextos: área de membros, painel do produtor e login;
  b) como as fontes Archivo (variável, com eixo de largura) e Inter serão carregadas;
  c) como os 51 ícones serão incluídos;
  d) a lista de componentes a criar ou adaptar, com o arquivo de destino de cada um;
  e) a lista de telas e rotas;
  f) as perguntas pendentes.
  Aguarde aprovação do plano.

Etapa 2 — Fundamentos: tokens, fontes, ícones, estilos de base (foco, seleção de texto, reset).

Etapa 3 — Componentes, na ordem de componentes.md. Para cada um, implemente todos os estados
(repouso, mouse, foco, pressionado, ligado, desligado) nas duas identidades.

Etapa 4 — Tela de login (uma só, usada nos dois acessos).

Etapa 5 — Painel do produtor, na ordem de 05-telas/painel-do-produtor.md: estrutura (barra do
topo e painel lateral), Meus cursos, página do curso (aba Básico), Criar curso, e as demais.

Etapa 6 — Área de membros, na ordem de 05-telas/area-de-membros.md.

Etapa 7 — Ligação dos dados, seguindo 07-mapa-de-configuracoes.md.

CONFERÊNCIA OBRIGATÓRIA AO FIM DE CADA TELA
1. Abra a tela em 1440 px e em 390 px de largura e compare com a imagem de mesmo nome em
   handoff-design/telas/. Confira também 1280, 1024, 900 e 768 px contra os pontos de quebra de
   tokens.md.
2. Confira os valores de handoff-design/03-componentes/medidas-de-conferencia.md com as
   ferramentas do navegador (tamanho, fonte, cor, borda, raio, espaço interno).
3. Confira os estados: mouse, foco por teclado, desligado, e as mensagens de erro e de sucesso.
4. Confira os textos, letra por letra, contra o protótipo.
5. Entregue um relatório curto: o que foi implementado, o que divergiu do handoff (com o motivo)
   e as perguntas novas. Divergência não relatada é erro.

O QUE NÃO FAZER
- Não criar tema escuro nem alternador de tema no painel.
- Não acrescentar elementos, textos, ícones, sombras, gradientes ou animações que não estejam no
  handoff.
- Não remover elementos do handoff por parecerem redundantes.
- Não criar link da área de membros para o painel.
- Não mostrar o autor do curso na área de membros.
- Não escrever a palavra "coprodutor" na tela de login.
```
