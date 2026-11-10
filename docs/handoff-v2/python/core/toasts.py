"""Toast a partir do servidor, usando django.contrib.messages.

    from core.toasts import toast
    toast(request, "Aula excluída", undo_url=reverse("painel:lesson_restore", args=[lesson.id]))
    toast(request, "Curso liberado. E-mail enviado para aluno@test.com", action=("Ver aluno", url))
    toast(request, "Não foi possível importar 3 linhas", level="error")

O layout renderiza cada mensagem com partials/toasts.html, e o ui.js transforma em toast.
"""
import json
from django.contrib import messages

LEVELS = {"success": messages.SUCCESS, "ok": messages.SUCCESS, "info": messages.INFO, "error": messages.ERROR, "warning": messages.WARNING}


def toast(request, text, level="success", undo_url=None, action=None):
    meta = {}
    if undo_url:
        meta["undo"] = undo_url
    if action:
        meta["action_label"], meta["action_href"] = action
    messages.add_message(request, LEVELS[level], text, extra_tags=("toast:" + json.dumps(meta)) if meta else "")
