"""Respostas para formulários e ações com data-async (ui.js, seção 3).

Uso numa view:
    from core.ajax import wants_json, json_ok, json_errors
    from core.toasts import toast

    if form.is_valid():
        form.save()
        if wants_json(request):
            return json_ok(toast="Alterações salvas")
        toast(request, "Alterações salvas")
        return redirect(request.path)
    if wants_json(request):
        return json_errors(form)
"""
from django.http import JsonResponse


def wants_json(request):
    """True quando a chamada veio do ui.js (fetch) e não de um POST normal do navegador."""
    return request.headers.get("X-Requested-With") in ("fetch", "XMLHttpRequest") or "application/json" in request.headers.get("Accept", "")


def json_ok(toast=None, undo_url=None, redirect=None, reload=False, remove=None, replace=None, counts=None, action=None, **extra):
    data = {"ok": True}
    if toast: data["toast"] = toast
    if undo_url: data["undo_url"] = undo_url
    if redirect: data["redirect"] = redirect
    if reload: data["reload"] = True
    if remove: data["remove"] = remove
    if replace: data["replace"] = replace
    if counts: data["counts"] = counts
    if action: data["action"] = action  # {"label": "Ver aluno", "href": "/painel/alunos/?aluno=3"}
    data.update(extra)
    return JsonResponse(data)


def json_errors(form, status=400):
    """Erros de validação no formato que o ui.js mostra embaixo de cada campo."""
    errors = {name: [str(e) for e in errs] for name, errs in form.errors.items() if name != "__all__"}
    total = len(form.errors)
    summary = "Corrija 1 campo para salvar." if total == 1 else f"Corrija {total} campos para salvar."
    if "__all__" in form.errors:
        summary = str(form.errors["__all__"][0])
    return JsonResponse({"ok": False, "errors": errors, "error": summary}, status=status)


def json_error(message, status=400):
    return JsonResponse({"ok": False, "error": message}, status=status)
