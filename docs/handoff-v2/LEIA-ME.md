# Pacote handoff v2 · CETREMER

Para o agente: comece por `HANDOFF-v2.md` (seção 0) e siga as fases da seção 12.

Conteúdo:
- `HANDOFF-v2.md` · especificação completa (manda sobre tudo)
- `static/` · CSS v2 (colar no fim do cetremer.css), ui.js e player.js
- `templates/` · layouts base v2, partials e diálogos do painel
- `python/core/` · ajax.py, toasts.py, templatetags/ui.py, context_processors_v2.py
- `referencia-v2/` · os 21 protótipos aprovados (.dc.html)
- `capturas/` · 54 PNG das telas e estados (ver capturas/INDICE.md)
- `demo/componentes.html` · todos os componentes novos funcionando. Para abrir com a busca Ctrl K funcionando,
  rode na pasta do pacote: `python -m http.server 8777` e abra http://localhost:8777/demo/componentes.html
