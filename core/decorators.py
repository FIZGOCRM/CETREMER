from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def painel_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_staff or getattr(user, 'role', '') in ('ADMIN', 'CREATOR'):
            return view(request, *args, **kwargs)
        raise PermissionDenied

    return wrapper


def is_painel_admin(user):
    """Dono (superusuário), is_staff ou papel ADMIN. Instrutor (CREATOR) fica de fora (HANDOFF-v2 9)."""
    return bool(user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, 'role', '') == 'ADMIN'))


def painel_admin_required(view):
    """Pedidos e Configurações: só administrador. Instrutor recebe 403."""
    @wraps(view)
    @painel_required
    def wrapper(request, *args, **kwargs):
        if not is_painel_admin(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper
