from django.shortcuts import render

from core.decorators import is_painel_admin


def permission_denied(request, exception=None):
    """403 dentro do layout certo: painel para a equipe, área do aluno para quem está logado, público para o resto."""
    user = request.user
    in_painel = user.is_authenticated and (is_painel_admin(user) or getattr(user, 'role', '') == 'CREATOR')
    if in_painel:
        layout, home = 'base_admin.html', '/painel/'
    elif user.is_authenticated:
        layout, home = 'base_aluno.html', '/'
    else:
        layout, home = 'base_public.html', '/'
    return render(request, '403.html', {'layout': layout, 'home_url': home, 'in_painel': in_painel}, status=403)
