"""Nome de exibição de uma pessoa. Nunca o username (HANDOFF-v2 regra 7)."""


def full_name(user):
    profile = getattr(user, 'student_profile', None)
    return ((getattr(profile, 'full_name', '') or user.get_full_name() or user.email.split('@')[0]).strip())


def first_name(user):
    profile = getattr(user, 'student_profile', None)
    chosen = (getattr(profile, 'display_name', '') or '').strip()
    name = chosen or full_name(user).split(' ')[0]
    return name[:1].upper() + name[1:] if name else ''
