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


@register.filter
def ago_pt(value):
    """{{ quando|ago_pt }} -> "agora mesmo", "há 25 min", "há 1 h", "há 2 dias" (só a maior unidade)."""
    from django.utils import timezone
    if not value:
        return ""
    seconds = int((timezone.now() - value).total_seconds())
    if seconds < 60:
        return "agora mesmo"
    if seconds < 3600:
        return f"há {seconds // 60} min"
    if seconds < 86400:
        return f"há {seconds // 3600} h"
    days = seconds // 86400
    return f"há {days} dia" if days == 1 else f"há {days} dias"


@register.filter
def seen_pt(value):
    """Último acesso: "agora mesmo", "há 25 min", "há 1 h", "ontem", "há 3 dias" ou "" (nunca)."""
    from django.utils import timezone
    if not value:
        return ""
    days = (timezone.localdate() - timezone.localtime(value).date()).days
    if days == 1:
        return "ontem"
    if days >= 2:
        return f"há {days} dias"
    return ago_pt(value)


@register.filter
def when_pt(value):
    """"hoje, 08:40", "ontem, 08:40" ou "10/11, 08:40"."""
    from django.utils import timezone
    if not value:
        return ""
    local = timezone.localtime(value)
    days = (timezone.localdate() - local.date()).days
    clock = local.strftime("%H:%M")
    if days == 0:
        return f"hoje, {clock}"
    if days == 1:
        return f"ontem, {clock}"
    return f"{local:%d/%m}, {clock}"
