"""Management HTTP adapters: common."""

from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from users.models import SiteSettings


def access_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    from core.portal_routing import user_access_url
    url = user_access_url(request, user, reverse("password_reset_confirm", args=[uid, token]))
    from users.services import send_access_link
    return send_access_link(user,url)



def report_access_delivery(request, sent):
    if not sent:
        messages.error(
            request,
            "O e-mail de acesso não foi enviado. Confira as configurações de SMTP.",
        )
    elif django_settings.DEBUG and not SiteSettings.load().email_host:
        messages.info(
            request,
            "Link de acesso gerado no console do servidor local. Nenhum e-mail chegou à caixa de entrada.",
        )
    else:
        messages.success(request, "E-mail de acesso enviado.")


def page(request, template, **context):
    return render(request, "painel/" + template + ".html", context)
