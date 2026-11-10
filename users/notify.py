"""Avisos do sino e e-mail correspondente (HANDOFF-v2 6.1)."""
import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Notification

logger = logging.getLogger(__name__)

# Tipo de aviso -> preferência do aluno em "Avisos por e-mail". Tipos sem preferência seguem o parâmetro `email`.
EMAIL_PREFERENCE = {
    'answer': 'notify_answers',
    'live': 'notify_live',
    'certificate': 'notify_certificate',
}


def _wants_email(user, kind):
    field = EMAIL_PREFERENCE.get(kind)
    if field is None:
        return True
    profile = getattr(user, 'student_profile', None)
    return bool(getattr(profile, field, True)) if profile is not None else True


def notify(user, kind, title, meta, url, email=True, request=None):
    """Cria o aviso do sino e, se a preferência do aluno permitir, manda o e-mail.

    `request` serve só para montar o link absoluto no e-mail. Falha de e-mail nunca derruba a ação do usuário.
    """
    notification = Notification.objects.create(user=user, kind=kind, title=title[:120], meta=meta[:160], url=url)
    if email and user.email and _wants_email(user, kind):
        link = request.build_absolute_uri(url) if request is not None else f'{settings.SITE_URL}{url}'
        body = f'{title}\n{meta}\n\n{link}' if meta else f'{title}\n\n{link}'
        try:
            send_mail(title, body, None, [user.email], fail_silently=False)
        except Exception:
            logger.exception('Falha ao enviar e-mail de aviso %s para o usuário %s', kind, user.pk)
    return notification
