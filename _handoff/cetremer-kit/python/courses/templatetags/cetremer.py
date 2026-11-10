"""Filtros de formatação da CETREMER.

Uso nos templates: {% load cetremer %}

    {{ course.price|brl }}                 -> R$ 1.234,56
    {{ lesson.duration_seconds|duracao }}  -> 7 min | 1h 05min
    {{ lesson.duration_seconds|mmss }}     -> 07:00 (rótulo do player)
    {{ profile.cpf|cpf }}                  -> 123.456.789-09
    {{ user.get_full_name|iniciais }}      -> JS
    {{ certificate.code|codigo_cert }}     -> 2A0E-307C-F993
    {% pct done total as p %}              -> inteiro 0 a 100

Não usar |floatformat nem localização do Django para dinheiro: o padrão
da plataforma é sempre "R$ 1.234,56".
"""
from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def brl(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return value
    text = f"{number:,.2f}"  # 1,234.56
    text = text.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"R$ {text}"


@register.filter
def duracao(seconds):
    try:
        seconds = int(seconds or 0)
    except (TypeError, ValueError):
        return ""
    if seconds <= 0:
        return ""
    minutes = max(1, round(seconds / 60))
    if minutes < 60:
        return f"{minutes} min"
    hours, rest = divmod(minutes, 60)
    return f"{hours}h" if rest == 0 else f"{hours}h {rest:02d}min"


@register.filter
def mmss(seconds):
    try:
        seconds = int(seconds or 0)
    except (TypeError, ValueError):
        return ""
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


@register.filter
def cpf(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) != 11:
        return value
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


@register.filter
def iniciais(name):
    parts = [p for p in str(name or "").replace("_", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


@register.filter
def codigo_cert(code):
    raw = "".join(ch for ch in str(code or "") if ch.isalnum()).upper()
    return "-".join(raw[i:i + 4] for i in range(0, len(raw), 4))


@register.simple_tag
def pct(done, total):
    try:
        done, total = int(done or 0), int(total or 0)
    except (TypeError, ValueError):
        return 0
    if total <= 0:
        return 0
    return round(done * 100 / total)
