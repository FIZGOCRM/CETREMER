# Regras invioláveis

Estas regras valem para toda a implementação. Elas vêm de decisões da responsável pelo design (dona da GoMut) e não estão abertas a interpretação.

## 1. Não supor nada

1. Se um valor de estilo, um texto, um estado ou um comportamento **não estiver neste pacote**, não escolha um: **pare e pergunte**. Escreva a pergunta em uma lista de pendências e siga com o que está definido.
2. Não "melhore" o design. Não troque um componente por um parecido da biblioteca que o projeto já usa. Não ajuste espaçamento, raio, peso de fonte ou cor "para ficar mais consistente".
3. Não arredonde valores para a escala da ferramenta de estilo (por exemplo, não troque `42px` por `40px`, `11px` por `12px`, `rgba(32, 34, 33, 0.13)` por um cinza pronto). Onde a ferramenta não tiver o valor exato, crie o valor.
4. Nenhum estilo padrão de biblioteca de interface pode vazar para a tela (Material, Bootstrap, Ant, shadcn, Chakra, etc.). Se o projeto usa uma, zere o tema dela ou use os componentes sem estilo.

## 2. Fidelidade ao estilo

5. **Tokens primeiro.** Antes de qualquer tela, implemente os tokens de `02-tokens/` com os mesmos nomes e valores, nos três contextos (área de membros, painel, login).
6. **Fontes**: Archivo (variável, com eixo de largura) nos títulos e Inter nos textos, carregadas exatamente como em `02-tokens/tokens.md`. Não substitua por fonte do sistema nem por outra família.
7. **Ícones**: use os SVG de `04-icones/`. Não substitua por ícones de biblioteca (Lucide, Heroicons, Font Awesome, Material Icons), mesmo que pareçam iguais.
8. **Componentes**: cada componente tem que ficar com as medidas e os estados de `03-componentes/` (repouso, passar o mouse, foco, pressionado, ligado, desligado).
9. **Textos**: use os textos do protótipo, em português do Brasil, com as mesmas maiúsculas e minúsculas e a mesma pontuação. Não reescreva, não traduza, não encurte.
10. **Responsivo**: use os pontos de quebra de `02-tokens/tokens.md`. Não substitua pelos pontos de quebra padrão da ferramenta.
11. **Movimento**: use as durações e a curva de `02-tokens/tokens.md`. Respeite `prefers-reduced-motion` como no CSS do protótipo.
12. **Acessibilidade**: mantenha o contorno de foco visível, os rótulos (`aria-label`), os papéis (`role`) e a navegação por teclado do protótipo.

## 3. Duas identidades, sem mistura

13. **Área de membros**: identidade do cliente (Emergensimples). Fundo escuro, vermelho `#e50914`. Está **aprovada**: implemente exatamente como está. A única tela dela com identidade da GoMut é o login.
14. **Painel do produtor**: identidade da GoMut. **Fundo branco, um tema só.** Não crie tema escuro nem alternador de tema.
15. **Login**: identidade da GoMut, com paleta própria e independente das outras duas. É a mesma tela nos dois acessos; mudam só o título do cartão, a frase abaixo dele e o item marcado no menu "Entrar".
16. Nunca use cor da área de membros no painel nem cor do painel na área de membros. Exceção definida: dentro do painel, as **capas** e a **prévia do certificado** mostram o que o aluno vê e por isso mantêm o vermelho da área de membros.

## 4. O que é proibido no painel do produtor

Estas proibições vêm de versões que foram recusadas. Não as reintroduza:

17. Nada de blocos escuros de destaque, faixas de impacto, gradientes ou títulos gigantes em maiúsculas.
18. Nada de botões em formato de pílula, cartões com cantos muito arredondados, sombras em cartões ou efeito de elevação ao passar o mouse. (Sombra existe só em menus suspensos, janelas, avisos rápidos e no painel lateral aberto no celular.)
19. Nada de quadros coloridos atrás dos ícones.
20. Não aplicar formas, tipografia ou grafismos do manual da marca GoMut. Da GoMut entram **só as cores e o logotipo**.
21. O painel deve ser limpo e profissional: telas montadas apenas com os componentes que já existem na área de membros.
22. O logotipo da GoMut é usado como arquivo (`prototipo/assets/marca/gomut-logo.png`), sem redesenho, sem sombra e sem inversão de cor, sempre sobre fundo claro.

## 5. O que é proibido na área de membros

23. Não incluir logotipo da GoMut no cabeçalho.
24. Não incluir link, botão ou tela do painel depois que o aluno entra. O único caminho da área de membros para o painel é a opção "Gerenciar meus negócios" no menu "Entrar" da **tela de login**.
25. "Visualizar como membro" e o botão "Voltar à área do coprodutor" só existem para quem tem permissão de produtor ou coprodutor. O aluno nunca vê nenhum dos dois.
26. O autor do curso não aparece na área de membros.
27. O aluno não cancela o próprio plano. Só o produtor ou coprodutor configura e cancela.

## 6. O que é proibido na tela de login

28. A palavra "coprodutor" não aparece em nenhum texto da tela de login.
29. Não incluir "Entrar com Google" nem "Entrar com Apple". O cartão tem só e-mail e senha.
30. A barra do topo é de vidro claro, com o logotipo colorido bem visível. Não escurecer a barra nem trocar o logotipo por uma versão branca.
31. Não alterar a opacidade (0,74) nem o tamanho da arte "GO + mamute": os dois foram aprovados.

## 7. Método de trabalho obrigatório

32. Antes de escrever código, rode o `PROMPT-1-reconhecimento-da-stack.md` e entregue o relatório. A implementação só começa depois que o mapeamento dos tokens para a stack estiver aprovado.
33. Implemente nesta ordem: tokens → fontes e ícones → componentes → telas.
34. Ao terminar cada tela, compare com a imagem correspondente em `telas/`, na mesma largura (1440 px e 390 px), e confira os valores de `03-componentes/medidas-de-conferencia.md`.
35. Tudo o que está em `08-pendencias-e-perguntas.md` fica **fora** da implementação até ser definido.
36. Toda divergência encontrada entre este pacote e o que foi implementado deve ser relatada, nunca resolvida em silêncio.
