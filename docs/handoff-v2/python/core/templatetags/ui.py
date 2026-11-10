"""{% load ui %} · {% toast_meta message as meta %} lê undo/action gravados por core.toasts.toast."""
import json
from django import template
from django.contrib import messages as dj_messages

register = template.Library()

KIND = {dj_messages.SUCCESS: "ok", dj_messages.INFO: "info", dj_messages.WARNING: "error", dj_messages.ERROR: "error", dj_messages.DEBUG: "info"}


@register.simple_tag
def toast_meta(message):
    meta = {"kind": KIND.get(message.level, "ok"), "undo": "", "action_label": "", "action_href": ""}
    tags = message.extra_tags or ""
    if tags.startswith("toast:"):
        try:
            meta.update(json.loads(tags[6:]))
        except ValueError:
            pass
    return meta


@register.filter
def plural_pt(n, forms):
    """{{ n|plural_pt:"aula,aulas" }} -> "1 aula" / "3 aulas". Use em todo texto com número."""
    one, many = forms.split(",")
    try:
        n = int(n)
    except (TypeError, ValueError):
        return forms
    return f"{n} {one if n == 1 else many}"


@register.filter
def falta_pt(n):
    """{{ remaining|falta_pt }} -> "Falta 1 aula." / "Faltam 3 aulas." / "" (zero)."""
    n = int(n or 0)
    if n == 0:
        return ""
    return "Falta 1 aula." if n == 1 else f"Faltam {n} aulas."
