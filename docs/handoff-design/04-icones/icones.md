# Ícones e capas geradas

## Ícones

51 ícones próprios, em `icones/`. **Use estes arquivos.** Não substitua por ícones de biblioteca, mesmo parecidos.

Todos seguem o mesmo padrão:

| Propriedade | Valor |
|---|---|
| Área de desenho (`viewBox`) | `0 0 24 24` |
| Preenchimento | `none` |
| Traço | `currentColor`, espessura `2`, pontas e junções arredondadas |
| Tamanho padrão | `1.25em` (acompanha o tamanho do texto) |
| Cor | a do texto em volta (`currentColor`) |

Exceção de desenho: `play` e `pause` são **preenchidos** (`fill="currentColor"`, sem traço). Esse detalhe já está dentro de cada arquivo.

Tamanhos fixos por contexto: dentro de botão `1.3em`; no painel lateral `20px`; em botão de ícone `16px`; no estado vazio `48px`; na barra do topo da área de membros `22px`; na barra inferior do celular `22px`; dentro de etiqueta `1em`.

### Principais usos de cada ícone

O uso exato em cada tela está no protótipo (`icon('nome')` em `prototipo/assets/js/app.js` e `admin.js`) e nas imagens de `telas/`.

| Ícone | Uso |
|---|---|
| `play` | Reproduzir, "Visualizar como membro", "Visualizar curso", aulas |
| `pause` | Reprodutor |
| `plus` | Criar, adicionar, "Criar curso" no painel lateral |
| `check` | Concluído, confirmação nos avisos rápidos, lembrete ativo |
| `info` | "Mais informações", avisos informativos |
| `search` | Busca |
| `bell` | Sininho, lembrete, Avisos |
| `right`, `left`, `down` | Setas. `down` girado 180° é a seta para cima |
| `close` | Fechar janela, tirar item |
| `thumb`, `heart` | Curtir |
| `clock` | Tempo de estudo |
| `download` | Baixar. Girado 180° (classe `cop-up`) é "enviar" |
| `fullscreen`, `volume`, `mute`, `captions`, `cinema`, `back10`, `fwd10`, `next` | Reprodutor |
| `sliders` | Configurações, filtro, configurar plano |
| `flame` | Sequência de estudo |
| `award` | Certificado, Certificados |
| `calendar` | Ao vivo, agenda |
| `users` | Alunos, participantes |
| `user` | Perfil, Área de membros |
| `cart` | Cursos à venda |
| `file`, `book` | Arquivo, e-book |
| `pencil` | Editar |
| `help` | Central de ajuda, Chamados |
| `home` | Início, Página inicial |
| `grid` | Cursos, Meus cursos, Áreas |
| `live` | Ao vivo (área de membros) |
| `lock` | Bloqueado, liberação |
| `share` | Compartilhar |
| `route` | Trilhas |
| `logout` | Sair |
| `star` | Nota do tema |
| `message` | Comunidade, respostas |
| `target` | Meu progresso |
| `bolt` | Mentoria |
| `list` | Minha lista, Plano do aluno |
| `trash` | Excluir, remover |
| `table` | Tabela |
| `painel-menu` | Botão de menu do painel, no celular |
| `painel-grafico` | Relatórios |
| `painel-escudo` | Controle de acesso |

## Capas geradas

Quando um curso, tema, trilha ou encontro **não tem imagem de capa enviada**, a capa é gerada pelo próprio sistema. Ela faz parte do design e precisa ser reproduzida.

Uma capa gerada é formada por:

1. **Fundo**: três degradês calculados a partir de um matiz `--h` (número de 0 a 360), definido pela área do tema:
   ```css
   background:
     radial-gradient(75% 95% at 92% 8%, hsl(var(--h) 88% 54% / 0.8), transparent 64%),
     radial-gradient(70% 90% at -5% 105%, hsl(calc(var(--h) + 38) 72% 34% / 0.6), transparent 70%),
     linear-gradient(135deg, hsl(var(--h) 52% 17%), hsl(calc(var(--h) - 18) 46% 6%));
   ```
2. **Desenho de linha** ("motivo"): um dos 14 arquivos de `motivos-das-capas/` (`viewBox` de `0 0 200 200`), posicionado à direita.
3. **Sobretítulo**: a área ou o tipo ("Mentoria", "Curso", "Trilha"), em maiúsculas.
4. **Título**: em Archivo condensada, peso 800, maiúsculas.

Todas as medidas internas da capa usam unidades de contêiner (`cqw`), para a capa manter a proporção em qualquer tamanho. A definição completa está em `03-componentes/css-por-componente-area-de-membros.md`, seção "Capas".

Matiz de cada área no conteúdo de exemplo: Emergência 2 · Cardiologia 338 · Via aérea e ventilação 198 · Terapia intensiva 172 · Neurologia 262 · Infectologia 96 · Pediatria 40 · Trauma e procedimentos 22 · Imagem e exames 222 · Rotina e carreira 300. A mentoria usa 357.

Motivos disponíveis: `bars`, `chat`, `clock`, `cross`, `drop`, `ecg`, `hex`, `net`, `pill`, `rings`, `scan`, `stitch`, `wave`, `xray`.

## Arquivos de marca

Em `prototipo/assets/marca/`:

| Arquivo | Tamanho | Uso |
|---|---|---|
| `gomut-logo.png` | 1568 × 432 px, fundo transparente | Logotipo da GoMut na barra do login e na barra do topo do painel. Exibido com 40 px de altura (36 e 32 px em telas menores) |
| `gomut-go-mamute-vidro-4k.png` | 3840 × 1965 px, fundo transparente, cor `rgb(9, 22, 20)` | Arte "GO + mamute" da tela de login, com opacidade 0,74 |
| `gomut-logo-original.webp` | 1774 × 887 px | Imagem original recebida. Só referência |
