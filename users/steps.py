"""Itens dispensados de "Próximos passos" no Início (HANDOFF-v2 7.1 e 6.2).

`StudentProfile.dismissed_steps` guarda as chaves dispensadas. A chave "cpf" volta depois de 7 dias se a
pendência continuar, então ela é guardada com a data: "cpf@2026-11-10".
"""
import re
from datetime import date, timedelta

from django.utils import timezone

CPF_RETURNS_AFTER_DAYS = 7
KEY_PATTERN = re.compile(r'^(cpf|cert:[-\w]+|live:\d+|resp:\d+)$')


def is_valid_key(key):
    return bool(KEY_PATTERN.match(key or ''))


def dismissed(profile):
    """Conjunto de chaves que não devem aparecer agora."""
    keys = set()
    today = timezone.localdate()
    for entry in profile.dismissed_steps or []:
        if entry.startswith('cpf@'):
            try:
                when = date.fromisoformat(entry[4:])
            except ValueError:
                continue
            if today < when + timedelta(days=CPF_RETURNS_AFTER_DAYS):
                keys.add('cpf')
        else:
            keys.add(entry)
    return keys


def _entries_for(profile, key):
    return [e for e in (profile.dismissed_steps or []) if e == key or e.startswith(key + '@')]


def dismiss(profile, key):
    entries = [e for e in (profile.dismissed_steps or []) if e not in _entries_for(profile, key)]
    entries.append(f'cpf@{timezone.localdate().isoformat()}' if key == 'cpf' else key)
    profile.dismissed_steps = entries
    profile.save(update_fields=['dismissed_steps'])


def restore(profile, key):
    stale = _entries_for(profile, key)
    if stale:
        profile.dismissed_steps = [e for e in profile.dismissed_steps if e not in stale]
        profile.save(update_fields=['dismissed_steps'])
