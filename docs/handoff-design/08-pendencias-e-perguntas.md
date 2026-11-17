# Pendências e perguntas em aberto

O que **ainda não foi definido** pela responsável pelo design. Nada desta lista deve ser implementado por suposição. Cada item precisa de uma resposta dela antes.

## Telas sem conteúdo definido

1. **Relatórios** (painel). Hoje é uma tela provisória, com o título e "Tela em construção". Falta definir quais números e gráficos entram.
2. **Controle de acesso** (painel). Tela provisória. Falta definir o que ela controla (por exemplo: quem da equipe acessa o painel e com que permissão).
3. **Outras abas da página do curso**. A referência usada (Eduzz) tem Personalização, Configurações, Comunicação e divulgação. No painel existem hoje Básico, Visão geral, Conteúdo e Ao vivo. Não criar outras abas.

## Decisões de produto em aberto

4. **Vários cursos**. Comunidade, Alunos, Certificados, Chamados e Configurações ficam no painel lateral e hoje mostram os dados do curso "Plantão sem GPT". Falta definir como essas telas se comportam quando o produtor tiver mais de um curso (por exemplo, um seletor de curso).
5. **Página de um curso criado**. Um curso novo tem só a aba Básico. O cadastro de módulos e aulas está desenhado apenas no curso "Plantão sem GPT".
6. **Organização da mentoria de 12 meses**. A mentoria dura 12 meses, mas o conteúdo de exemplo mostra uma jornada de 8 semanas (e textos como "8 semanas" e "Oito semanas, uma por vez"). Falta definir a organização real.
7. **Conteúdo real**: nomes dos temas, aulas, preços, links de checkout, pessoas e textos. Tudo o que está em `prototipo/assets/js/data.js` é fictício.
8. **Lista de autores do curso**. No protótipo a seleção "Autor do curso" traz a marca e nomes de exemplo. Falta definir de onde vem essa lista.
9. **Top 10, Mais procurados, nota dos temas e Novos conteúdos** foram tratados como automáticos. Se a responsável quiser controlar algum deles à mão, a configuração ainda precisa ser desenhada.

## Tela de login

10. A tela não tem "Esqueci a senha", "Lembrar de mim" nem "Primeiro acesso / Ative sua conta". Elas existiam no login antigo da área de membros e saíram quando a tela foi unificada. Falta confirmar se voltam e, se voltarem, como ficam.
11. A frase do cartão do acesso de membro ("Entre e acesse seus cursos.") foi proposta do design e aguarda confirmação.

## Marca e arquivos

12. **Logotipo da GoMut em vetor**. Os arquivos em `prototipo/assets/marca/` foram recortados de uma imagem enviada. `gomut-logo.png` tem 1568 × 432 px e serve bem no tamanho em que é usado (até 40 px de altura). Se houver o arquivo vetorial original, ele deve substituir os dois PNG, mantendo tamanho, cor e opacidade.
13. **Logotipo do cliente** na área de membros. Hoje a marca aparece em texto ("Emergensimples"). Não criar logotipo.

## Envio de arquivos

14. **Capas** (curso, tema, trilha, encontro, curso à venda) e **e-books**: o protótipo só simula o envio. Falta definir, com a programação, tamanho máximo, corte da imagem e onde os arquivos ficam guardados. O tamanho recomendado mostrado ao produtor já está definido (curso 1920 × 1080 px; os demais 1280 × 720 px).

## Como registrar novas dúvidas

Ao encontrar algo que este pacote não responde, acrescente aqui um item com: a tela, o que falta e as opções possíveis. Não escolha uma opção por conta própria.
