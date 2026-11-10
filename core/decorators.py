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
