from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.ajax import json_ok, wants_json
from core.toasts import toast
from .models import Notification


@login_required
@require_POST
def notifications_read_all(request):
    """Marca todos os avisos do usuário como lidos."""
    Notification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now())
    if wants_json(request):
        return json_ok()
    toast(request, 'Avisos marcados como lidos')
    return redirect(request.META.get('HTTP_REFERER') or 'dashboard')


@login_required
def notification_open(request, notification_id):
    """Marca o aviso como lido e leva para o endereço dele. Só o dono abre (404 para os outros)."""
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=['read_at'])
    target = notification.url
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}) or target.startswith('//'):
        raise Http404
    return redirect(target)
