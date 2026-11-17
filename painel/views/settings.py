"""Management HTTP adapters: settings."""

from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect

from core.crypto import encrypt
from core.decorators import painel_required
from sales.integrations.asaas.config import AsaasConfig
from users.models import SiteSettings

from .common import page


@painel_required
def settings(request):
    site = SiteSettings.load()
    if request.method == "POST":
        for field in (
            "school_name",
            "support_email",
            "whatsapp",
            "terms_url",
            "privacy_url",
            "email_from_name",
            "email_from",
            "email_host",
            "email_username",
            "signer_name",
            "signer_role",
        ):
            if field in request.POST:
                setattr(site, field, request.POST[field].strip())
        try:
            site.email_port = int(request.POST.get("email_port") or 587)
        except ValueError:
            site.email_port = 587
        site.email_use_tls = bool(request.POST.get("email_use_tls"))
        for field in ("logo", "signature_image"):
            if request.FILES.get(field):
                setattr(site, field, request.FILES[field])
        if request.POST.get("email_password"):
            site.email_password_encrypted = encrypt(request.POST["email_password"])
        site.save()
        if request.POST.get("action") == "test_email":
            try:
                count = send_mail(
                    "Teste de e-mail CETREMER",
                    "Configuração de e-mail funcionando.",
                    None,
                    [request.user.email],
                    fail_silently=False,
                )
                if count:
                    messages.success(request, "E-mail de teste enviado.")
                else:
                    messages.error(request, "SMTP não configurado.")
            except Exception as exc:
                messages.error(request, f"Erro no SMTP: {exc}")
        else:
            messages.success(request, "Configurações salvas.")
        return redirect("painel:settings")
    return page(
        request,
        "settings",
        site=site,
        asaas_status=AsaasConfig.from_settings().public_status(),
        email_password_set=bool(site.email_password_encrypted),
    )
