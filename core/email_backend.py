import logging

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend

from core.crypto import decrypt
from users.models import SiteSettings


logger = logging.getLogger(__name__)


class SiteEmailBackend(BaseEmailBackend):
    """Read the active SMTP configuration for each send."""

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        site = SiteSettings.load()
        if not site.email_host:
            if settings.DEBUG:
                return ConsoleEmailBackend(fail_silently=self.fail_silently).send_messages(email_messages)
            logger.error('SMTP não configurado: envio de e-mail ignorado.')
            return 0
        password = decrypt(site.email_password_encrypted) if site.email_password_encrypted else None
        if site.email_from:
            sender = f'{site.email_from_name} <{site.email_from}>' if site.email_from_name else site.email_from
            for message in email_messages:
                message.from_email = sender
        backend = SMTPEmailBackend(
            host=site.email_host, port=site.email_port,
            username=site.email_username or None, password=password,
            use_tls=site.email_use_tls, fail_silently=self.fail_silently,
        )
        return backend.send_messages(email_messages)
