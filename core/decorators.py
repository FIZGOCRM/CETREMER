from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


def painel_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if getattr(user, 'role', '') in ('ADMIN', 'CREATOR'):
            return view(request, *args, **kwargs)
        if request.method == "GET":
            return render(request, "painel/acesso_produtor.html", status=403)
        raise PermissionDenied

    return wrapper
