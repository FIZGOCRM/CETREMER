# QA — identidade GoMut no acesso do produtor

## Correção

O login GoMut já existia em `templates/login_admin.html`, mas dependia de `?acesso=admin`. Ao acessar `/painel/` sem sessão, o decorator gerava `/login/?next=/painel/`, e a view escolhia indevidamente o login Emergensimples do aluno.

A view agora reconhece o destino seguro `/painel/` e suas subrotas, preservando `next`. O formulário GoMut mantém a identidade após erro de senha e usa o título “Painel do produtor”. Ao sair de uma conta ADMIN/CREATOR, o usuário volta ao login GoMut. O acesso do aluno conserva sua identidade Emergensimples.

O painel interno usa `base_painel_gomut.html`, logo GoMut, tema claro e controles verdes. Essa base e suas telas foram conferidas; a falha reproduzida estava na escolha do login. Nenhuma mudança de permissões, cadastro, senha, dependência ou banco foi necessária.

## Arquivos

- `users/views.py`: seleção de login pelo destino validado e retorno após logout.
- `templates/login_admin.html`: formulário preserva modo produtor e texto de gestão.
- `users/test_login_redesign.py`: cinco regressões adicionais.
- Este documento e o índice de QA.

## Verificação

Antes da correção, quatro regressões falharam mostrando o template de aluno. Depois: **352 testes aprovados**, zero falhas/erros; migrações sem mudanças e `git diff --check` sem erros.

Cobertos: acesso anônimo por painel e subrotas com query string, URL da captura enviada, POST incorreto, retorno ao destino após autenticação, limite de caminho `/painel/`, rejeição de destino externo e logout dos dois perfis. O contexto visual não concede permissão de produtor.

Chrome em 390/1440 px: login GoMut com logo carregado, erro e sucesso de autenticação, saída de conta e login do aluno. Oito combinações de páginas internas — painel inicial, cursos, alunos e configurações — com HTTP200, marca GoMut, sem overflow horizontal ou erro JS. Capturas em `.venv/v1-qa/producer-*-fixed-*`.

## Como conferir

1. Abrir `/painel/` em janela anônima ou atualizar a URL `/login/?next=/painel/` que estava na captura.
2. Conferir o login verde GoMut com o título “Painel do produtor”.
3. Entrar com a conta fictícia administrativa já informada; conferir painel claro com logo GoMut.
4. Sair pelo menu da conta; o login GoMut deve reaparecer.
5. Abrir `/login/` sem destino administrativo para conferir o login do aluno.

Sem pendências desta correção. As entradas externas da V1 continuam documentadas no índice de QA. O hash pode ser localizado por `git log -1 -- docs/qa-login-produtor.md`.
