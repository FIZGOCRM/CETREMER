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
    url = request.build_absolute_uri(
        reverse("password_reset_confirm", args=[uid, token])
    )
    return send_mail(
        "Seu acesso à CETREMER",
        f"Olá! Defina sua senha para acessar a CETREMER: {url}",
        None,
        [user.email],
        fail_silently=False,
    )


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
