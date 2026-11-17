# Tela de login

Uma única tela, com a identidade da GoMut, usada nos dois acessos. Estilos: `prototipo/assets/css/login.css` (cópia organizada em `03-componentes/css-por-componente-login.md`). Montagem: função `telaLogin()` em `prototipo/assets/js/app.js`.

| | Acesso do produtor | Acesso do membro |
|---|---|---|
| Endereço no protótipo | `coprodutor.html` (sem sessão) | `index.html#/entrar` |
| Imagens | `telas/painel/computador-1440/01-login.png`, `telas/painel/celular-390/01-login.png` | `telas/membros/computador-1440/01-login.png`, `telas/membros/celular-390/01-login.png` |
| Título do cartão | **Gerenciar meus negócios** | **Acessar minhas compras** |
| Frase do cartão | Entre e gerencie seu negócio. | Entre e acesse seus cursos. |
| Depois de entrar | Abre "Meus cursos", no painel | Abre o Início da área de membros |

Todo o resto é idêntico nas duas.

## Partes da tela

### 1. Fundo

Verde profundo `#142724` com um brilho radial em Verde GO (valores em `02-tokens/tokens.md`, seção 3). A página em volta da tela (margens do navegador, área de rolagem além do fim) fica na mesma cor `#142724`, e a cor do navegador (`theme-color`) também, enquanto o login está aberto.

### 2. Barra do topo

- Caixa de **vidro claro**: fundo `rgba(255, 255, 255, 0.84)`, borda `1px rgba(255, 255, 255, 0.7)`, `backdrop-filter: blur(16px) saturate(1.3)`, raio `10px`.
- Margem: `clamp(12px, 1.6vw, 22px)` em cima e `clamp(12px, 3.4vw, 68px)` nos lados. Espaço interno: `10px clamp(14px, 2vw, 28px)`.
- À esquerda, o logotipo colorido da GoMut (`assets/marca/gomut-logo.png`) com `40px` de altura (36 px até 1199 px; 32 px até 699 px).
- À direita, o link **Entrar** com seta para baixo (ícone `down`, 18 px, traço 2.4; gira 180° com o menu aberto). Texto `16px` peso `600`, cor `#035a54`; ao passar o mouse `#202221`.
- O link abre um menu suspenso branco (borda de cima `2px #202221`, sombra `0 14px 44px rgba(20, 39, 36, 0.2)`) com duas opções, nesta ordem:
  1. **Gerenciar meus negócios** (ícone `sliders`)
  2. **Acessar minhas compras** (ícone `play`)
- A opção da própria tela leva o cursor ao campo de e-mail do cartão. A outra abre a tela de login do outro acesso.

### 3. Frase de destaque

- Título, em duas linhas fixas: **"Força para fazer"** / **"avançar."** A primeira linha não quebra.
  Archivo, peso `800`, largura `84%`, `clamp(42px, 4.75vw, 82px)`, `line-height: 1.04`, `letter-spacing: -0.012em`, cor `#ffffff`.
- Embaixo: **"Uma proposta de experiência com clareza, presença e ação."**
  Inter, peso `300`, `clamp(14px, 1.15vw, 17px)`, `line-height: 1.45`, cor `rgba(255, 255, 255, 0.92)`, largura máxima `26em`, a `clamp(10px, 1.1vw, 16px)` do título.
- Em telas a partir de 1200 px, o bloco de texto sobe `2.2vw` (`transform: translateY(-2.2vw)`) para a primeira linha passar acima da arte.

### 4. Arte "GO + mamute"

- Arquivo: `assets/marca/gomut-go-mamute-vidro-4k.png` (3840 × 1965 px), já na cor `rgb(9, 22, 20)`.
- Exibida com `opacity: 0.74`, proporção `3840 / 1965`.
- Tamanho e posição em telas a partir de 1200 px: `width: calc(54.47vw - 237px)` e `margin-left: max(calc(219px - 25.05vw), calc(67.6px - 14.47vw))`. A partir de 1900 px: `width: 798px` e `margin-left: calc(100% - 798px)`.
- A frase e o cartão ficam sempre por cima da arte (`z-index: 1`).
- É decorativa: `aria-hidden="true"` e `alt=""`.

### 5. Cartão de acesso

- Vidro escuro: fundo `rgba(9, 22, 20, 0.74)`, borda `1px rgba(255, 255, 255, 0.16)`, `backdrop-filter: blur(8px)`, raio `10px`, espaço interno `clamp(22px, 2.4vw, 34px)`.
- Título (`h2`): `clamp(20px, 1.6vw, 26px)`, peso `600`.
- Frase: `14px`, cor `rgba(255, 255, 255, 0.78)`, a `6px` do título.
- Campo de e-mail: texto de exemplo **"Seu e-mail"**. Campo de senha: texto de exemplo **"Sua senha"**. Os rótulos "E-mail" e "Senha" existem só para leitor de tela.
- Campos: altura `52px`, fundo `rgba(8, 20, 18, 0.55)`, borda `rgba(255, 255, 255, 0.26)` (mouse: `rgba(255, 255, 255, 0.52)`), texto `#fff`, texto de exemplo `rgba(255, 255, 255, 0.6)`; foco: contorno `2px #faad31` afastado `2px` e borda `#faad31`.
- Botão **Entrar**: largura total, altura `52px`, fundo `#faad31`, texto `#202221`, `18px` peso `600`; mouse `#ffbd52`; pressionado `#eb9d1f`.
- Vão entre os blocos do cartão: `18px`.

O cartão **não tem**: "Entrar com Google", "Entrar com Apple", "Lembrar de mim", "Esqueci a senha", "Primeiro acesso". Ver `08-pendencias-e-perguntas.md` antes de acrescentar qualquer um deles.

### 6. Rodapé

No protótipo há a linha "GoMut · protótipo de interface · nenhum dado é enviado" (`12px`, `rgba(255, 255, 255, 0.55)`). É texto do protótipo: não levar para o produto.

## Disposição por largura de tela

| Largura | Disposição |
|---|---|
| 1200 px ou mais | Três colunas: `minmax(0, 1.2fr) minmax(0, 1fr) minmax(300px, 372px)` (frase, arte, cartão), vão `clamp(20px, 2.6vw, 44px)`, espaço interno `clamp(24px, 4vw, 56px) clamp(12px, 3.4vw, 68px)`, alinhadas ao centro na vertical |
| de 700 a 1199 px | Duas colunas: `minmax(0, 1fr) minmax(290px, 340px)`. À esquerda a frase e, embaixo dela, a arte (largura `min(406px, 108%)`, centralizada); à direita o cartão, ocupando as duas linhas. O bloco de texto não sobe |
| até 699 px | Uma coluna centralizada, vão `20px`: frase, arte (largura `min(336px, 87vw)`), cartão (largura `min(440px, 100%)`, texto à esquerda) |

## Seleção de texto e foco

- Texto selecionado: fundo `#faad31`, letra `#202221`.
- Foco por teclado: contorno `2px #faad31`. Dentro da barra clara: `#04736b`.

## Regras fixas

1. A palavra "coprodutor" não aparece em nenhum texto desta tela.
2. A barra é clara e o logotipo é o colorido.
3. Não alterar o tamanho nem a opacidade da arte.
4. A tela é a mesma nos dois acessos; só mudam os dois textos do cartão.
