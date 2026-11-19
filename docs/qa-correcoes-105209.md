# GoMut / Emergensimples — correções do QA-GM-20261117-105209

Data: 17/11/2026. Ambiente: demo local, `http://127.0.0.1:8016/`.

**Resultado:** D01, D02, D03 e D04 corrigidos. Reprodução real no Google Chrome 157.0.8103.52, testes de regressão e suíte completa com **358 testes aprovados**. Sem migração, instalação de dependências ou alteração da integração de pagamentos.

## 1. Causas e mudanças

| Defeito | Causa confirmada | Correção |
|---|---|---|
| D01 — vídeo avança, GoMut fica em 0% | O iframe não declarava `encrypted-media`. O Vimeo emitia `drminitfailed`; seu SDK acrescentava a permissão e recarregava o iframe. As assinaturas de `play`, `pause`, `timeupdate` e `ended` haviam sido feitas antes da recarga e não eram registradas novamente. O vídeo podia tocar, enquanto a GoMut deixava de receber os eventos. | Permissão declarada no iframe desde sua criação, evitando essa recarga de recuperação de DRM. |
| D01 — perda do trecho anterior à pausa | O servidor só creditava o intervalo se tanto o estado anterior quanto o novo fossem “reproduzindo”. Um envio com `playing=false` descartava o tempo assistido desde o envio anterior. | O estado anterior abre o intervalo; a pausa fecha e credita esse intervalo. O intervalo parado até a retomada não concede tempo. Mantidos o relógio do servidor e o limite de 20 segundos por envio. |
| D02 — dois significados para “Acesso até” | O detalhe do curso usava `access.paid_through`, último dia contratual. Minha conta usava `plan.access_last_day`, último dia efetivo, incluindo a tolerância natural. | O detalhe do curso passou a receber `plan_status(enrollment)` e usar o mesmo `access_last_day` da conta. Nenhuma regra de autorização ou duração da tolerância foi alterada. |
| D03 — “1 horas” | Os templates do certificado e da validação pública tinham “horas” fixo. A impressão usa o mesmo template do certificado. | Pluralização no template: “1 hora”, “2 horas”. Preservado o conteúdo dos registros de certificados já emitidos. |
| D04 — “1 dias” | As mensagens de `plan_status` tinham “dias” fixo, tanto no período ativo quanto na tolerância. | Singular/plural centralizado na montagem dessas mensagens: “Termina em 1 dia” e “Seu acesso termina em 1 dia”. |

### Arquivos alterados

- `templates/courses/lesson_detail.html:10`: permissão do iframe Vimeo.
- `courses/services.py:416`: crédito do intervalo que termina em pausa.
- `courses/student_views.py:90` e `templates/courses/course_detail.html:14`: data efetiva de acesso.
- `templates/courses/certificate.html:1` e `templates/courses/verify_certificate.html:1`: carga horária.
- `courses/services.py:322`: singular/plural de dias.
- `courses/test_player_tracking.py`: regressões de permissão, pausa, retomada e limiar de conclusão.
- `courses/test_qa_105209.py`: regressões de datas e pluralização nas telas reais.

O comportamento de recuperação de DRM foi conferido também no [código oficial do SDK do Vimeo, função `updateDRMEmbeds`](https://github.com/vimeo/player.js/blob/master/src/lib/embed.js). O diagnóstico local registrou a sequência de mensagens e a recarga correspondente.

## 2. Reprodução e validação no Chrome

Automação com Playwright no Chrome instalado, usando navegador com interface e sandbox habilitado para reprodução de mídia protegida. A sessão de teste foi autenticada com o mecanismo de sessão do Django. Não foi usada a extensão do Chrome nesta execução.

### D01 — reprodução anterior e resultado corrigido

Para reproduzir a condição anterior depois da alteração, somente a resposta HTML recebida por esse navegador de diagnóstico teve a permissão removida. Nenhum arquivo ou dado foi revertido para isso. A validação corrigida não interceptou respostas nem simulou eventos do player.

1. Com a permissão original ausente, a aula 1.1 avançou **17,193 s**, mas o minuto da anotação permaneceu **0:00** e houve **zero heartbeats** durante a reprodução. A sequência mostrou `drminitfailed`, um segundo `ready` e ausência de novas assinaturas dos eventos de progresso.
2. Com a correção, uma conta fictícia adicional iniciou a mesma aula com **zero segundos assistidos**. O vídeo real do Vimeo foi reproduzido a 1x, sem saltos ou alteração dos contadores.
3. Pausa em **18,116 s**; anotação gravada no segundo **18**, exibida como **0:18**. Espera de cinco segundos em pausa, seguida de recarga da página.
4. Posição persistida **18,116 s**; posição retornada pelo Vimeo na retomada **18,116 s**.
5. O primeiro heartbeat com conclusão automática registrou **58 segundos de 62 — 94%**, na posição **59,028 s**, antes do evento de fim do vídeo. O limiar continua sendo 90%; a interface recebe a atualização no heartbeat seguinte, em intervalos de 15 segundos.
6. Ao fim: **60 segundos creditados, 97% assistido**, aula concluída e quiz liberado. O endpoint `ended` foi posterior à conclusão, sem duplicá-la. Reabertura confirmou a persistência do resultado.

Evidências:

- [Condição anterior e sequência de eventos](../.venv/qa-correcoes-105209/evidence/D01-original.json).
- [Captura da reprodução anterior](../.venv/qa-correcoes-105209/evidence/D01-original-permissao-ausente.png).
- [Pausa e anotação](../.venv/qa-correcoes-105209/evidence/D01-pausa-anotacao.png).
- [Retomada](../.venv/qa-correcoes-105209/evidence/D01-retomada.png).
- [Conclusão durante a execução](../.venv/qa-correcoes-105209/evidence/D01-conclusao-automatica.png).
- [Resultado persistido após reabertura](../.venv/qa-correcoes-105209/evidence/D01-resultado-persistido.png).
- [Anotação persistida](../.venv/qa-correcoes-105209/evidence/D01-anotacao-persistida.png).
- [Respostas HTTP e resultados medidos](../.venv/qa-correcoes-105209/evidence/D01-validacao.json).

### D02 — datas e bloqueio

| Situação no Chrome | Detalhe do curso | Minha conta | Aula / heartbeat |
|---|---|---|---|
| Matrícula com as datas originais | Acesso até 20/12/2026 | Acesso até 20/12/2026 | Aula permitida |
| Último dia da tolerância natural em 17/11/2026 | Acesso até 17/11/2026 | Acesso até 17/11/2026 | Aula permitida |
| Acesso efetivo encerrado em 16/11/2026 | Curso bloqueado, HTTP 403 | Acesso até 16/11/2026 | Aula e heartbeat bloqueados, HTTP 403 |

O relógio do computador permaneceu intacto. No Chrome, a fronteira do dia seguinte foi exposta deslocando o período fictício um dia para trás. Nos testes automatizados, o mesmo período foi testado no último dia às **23:59:59.999999** e no dia seguinte às **00:00**, com controle do relógio somente dentro do teste. As correções temporárias de datas e a restauração ficaram no histórico administrativo.

- [Curso no último dia](../.venv/qa-correcoes-105209/evidence/D02-ultimo-dia-curso.png).
- [Minha conta no último dia](../.venv/qa-correcoes-105209/evidence/D02-ultimo-diaconta.png).
- [Bloqueio da aula após o limite](../.venv/qa-correcoes-105209/evidence/D02-dia-seguinte-bloqueio-aula.png).
- [Conta após o limite](../.venv/qa-correcoes-105209/evidence/D02-dia-seguinteconta.png).
- [Resultados e restauração](../.venv/qa-correcoes-105209/evidence/D02-D04-validacao.json).

### D03 e D04 — textos

Chrome conferido no certificado do aluno, na validação pública em sessão anônima e no layout de impressão. Foi gerado também um PDF de uma página usando a impressão do Chrome. Os testes cobrem “1 hora” e “2 horas”.

O painel foi conferido em duas condições: período ativo a um dia do fim contratual e último dia da tolerância natural. Os testes cobrem um e dois dias em ambos os estados.

- [Certificado](../.venv/qa-correcoes-105209/evidence/D03-certificado.png).
- [Validação pública](../.venv/qa-correcoes-105209/evidence/D03-validacao-publica.png).
- [Layout de impressão](../.venv/qa-correcoes-105209/evidence/D03-certificado-impressao.png).
- [PDF gerado pelo Chrome](../.venv/qa-correcoes-105209/evidence/D03-certificado-impressao.pdf).
- [Plano ativo — 1 dia](../.venv/qa-correcoes-105209/evidence/D04-ativo.png).
- [Plano em tolerância — 1 dia](../.venv/qa-correcoes-105209/evidence/D04-tolerancia.png).

## 3. Testes executados

As regressões falharam antes das respectivas correções e passaram depois. Um teste antigo que esperava descartar o intervalo anterior à pausa foi corrigido para expressar a regra: creditar o trecho reproduzido e não creditar o tempo parado até a retomada.

```powershell
.venv/Scripts/python.exe -B .venv/run_v1.py test courses.test_qa_105209 courses.test_player_tracking --verbosity 0
# 20 testes aprovados

.venv/Scripts/python.exe -B .venv/run_v1.py test --verbosity 0
# 358 testes aprovados

.venv/Scripts/python.exe -B .venv/run_v1.py makemigrations --check --dry-run
# No changes detected

git diff --check
# Sem erros de whitespace
```

Além dos novos casos, a suíte preserva os controles de CSRF, acesso expirado, ausência de crédito por salto de posição, relógio compartilhado entre dispositivos, limite de crédito por envio e prévia somente leitura.

[Log da suíte completa](../.venv/qa-correcoes-105209/evidence/testes.txt).

## 4. Preservação dos dados

- Backup SQLite feito antes dos testes; integridade verificada. O backup permanece local e não integra o ZIP de evidências.
- Matrícula **3** restaurada: início **15/11/2026**, `ends_on` exclusivo **18/12/2026**, último dia contratual **17/12/2026**, tolerância **3 dias**, último acesso efetivo **20/12/2026**, sem encerramento antecipado.
- Política de acesso, observação administrativa e data de qualificação originais conferidas.
- Nenhum ID original de aluno, curso, aula, matrícula, comunidade, suporte ou pagamentos foi removido.
- Certificados comparados integralmente com o backup: registros preservados, inclusive código **51FEFE12A1B3**.
- As quatro aulas do aluno QA original continuam concluídas. A data histórica de conclusão alterada durante o diagnóstico inicial foi restaurada a partir do registro anterior. O tempo realmente assistido e as anotações de teste foram mantidos.
- Foi adicionada uma conta fictícia de regressão, `qa.regressao.105209@gomut.example`, com matrícula própria no curso QA. Ela não tem senha utilizável; sua sessão foi criada apenas para a automação local. O resultado de uma aula concluída e 60 segundos assistidos permanece para inspeção administrativa.
- Novas entradas de histórico identificam os ajustes de QA; nenhum histórico original foi apagado.

[Auditoria de preservação](../.venv/qa-correcoes-105209/evidence/dados-preservados.json).

## 5. Pendências e limites desta rodada

- **Nenhuma pendência identificada nos quatro defeitos solicitados.**
- O Vimeo gerou um erro próprio de telemetria ao descarregar a página: tentativa de XHR síncrono em `page dismissal`, bloqueada pelo Chrome. Está registrado no JSON; não impediu persistência, retomada, anotação ou conclusão. Não houve correção de código de terceiros.
- A reprodução real foi validada no Chrome. Outros navegadores e a reprodução simultânea em dispositivos não foram retestados manualmente nesta rodada; os testes de servidor correspondentes continuam aprovados.
- Os demais cenários bloqueados ou não testados do relatório original não foram reclassificados por este trabalho. Esta rodada não validou cobranças ou recorrência e não envolveu o Asaas.

O pacote de entrega contém este relatório, as capturas, os resultados HTTP, a auditoria de preservação, o PDF de impressão e o log dos testes. As evidências originais recebidas no ZIP de QA foram mantidas sem alterações.
