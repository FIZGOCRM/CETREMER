"""Configurações da escola (HANDOFF-v2 8.11): Escola, Pagamentos, E-mails, Certificado e Equipe. Só administrador."""
import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import URLValidator, validate_email
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.ajax import json_error, json_ok, wants_json
from core.crypto import decrypt, encrypt
from core.decorators import painel_admin_required
from core.toasts import toast
from users.display import full_name
from users.models import CreatorProfile, SiteSettings

from .access import try_access_email, report_access_delivery

User = get_user_model()
SECTIONS = (('escola', 'Escola'), ('pagamentos', 'Pagamentos'), ('emails', 'E-mails'), ('certificado', 'Certificado'), ('equipe', 'Equipe'))
IMAGE_MAX = 2 * 1024 * 1024
ROLE_LABEL = {'ADMIN': 'Administrador', 'CREATOR': 'Instrutor (conteúdo e comunidade)'}


def _is_team(user):
    return user.is_active and (user.is_superuser or user.is_staff or user.role in ('ADMIN', 'CREATOR'))


def team_members():
    members = [u for u in User.objects.filter(is_active=True).order_by('first_name', 'email') if _is_team(u)]
    for user in members:
        user.display_name = full_name(user)
        user.is_owner = user.is_superuser
        user.role_label = 'Dono' if user.is_owner else ROLE_LABEL.get(user.role, 'Administrador')
    return members


def _url_ok(value):
    try:
        URLValidator(schemes=['http', 'https'])(value)
        return True
    except ValidationError:
        return False


def _image_error(upload):
    if not (upload.content_type or '').startswith('image/'):
        return 'Envie uma imagem PNG, JPG ou SVG.'
    if upload.size > IMAGE_MAX:
        return 'A imagem deve ter no máximo 2 MB.'
    return ''


def _failure(request, errors, back):
    total = len(errors)
    summary = 'Corrija 1 campo para salvar.' if total == 1 else f'Corrija {total} campos para salvar.'
    if wants_json(request):
        return JsonResponse({'ok': False, 'errors': {k: [v] for k, v in errors.items()}, 'error': summary}, status=400)
    toast(request, next(iter(errors.values())), level='error')
    return redirect(back)


def _back(section):
    return reverse('painel:settings') + f'?secao={section}'


@painel_admin_required
def settings(request):
    section = request.GET.get('secao') or request.POST.get('section') or 'escola'
    section = section if section in dict(SECTIONS) else 'escola'
    site = SiteSettings.load()
    if request.method == 'POST':
        return _save(request, site, section)
    last4 = decrypt(site.gateway_key_encrypted)[-4:] if site.gateway_key_encrypted else None
    context = {'section': section, 'sections': SECTIONS, 'site': site, 'gateway_key_last4': last4,
               'email_password_set': bool(site.email_password_encrypted)}
    if section == 'equipe':
        context['members'] = team_members()
        context['roles'] = [('ADMIN', ROLE_LABEL['ADMIN']), ('CREATOR', ROLE_LABEL['CREATOR'])]
    return render(request, 'painel/settings.html', context)


def _save(request, site, section):
    post, back, errors = request.POST, _back(section), {}
    if section == 'escola':
        name = post.get('school_name', '').strip()
        whatsapp = re.sub(r'\D', '', post.get('whatsapp', ''))
        if not name:
            errors['school_name'] = 'Informe o nome da escola.'
        if post.get('whatsapp', '').strip() and not 10 <= len(whatsapp) <= 15:
            errors['whatsapp'] = 'Informe o WhatsApp com DDD, só números.'
        for field in ('terms_url', 'privacy_url'):
            value = post.get(field, '').strip()
            if value and not _url_ok(value):
                errors[field] = 'Cole o link completo, começando com https://.'
        logo = request.FILES.get('logo')
        if logo and _image_error(logo):
            errors['logo'] = _image_error(logo)
        if errors:
            return _failure(request, errors, back)
        site.school_name, site.whatsapp = name, whatsapp
        site.terms_url, site.privacy_url = post.get('terms_url', '').strip(), post.get('privacy_url', '').strip()
        if logo:
            site.logo = logo
        message = 'Dados da escola salvos'
    elif section == 'pagamentos':
        if post.get('action') == 'test_connection':
            toast(request, 'Nenhuma conta conectada. As vendas usam a simulação.', level='info')
            return json_ok(redirect=back) if wants_json(request) else redirect(back)
        site.gateway_sandbox = post.get('gateway_sandbox') == '1'
        if post.get('gateway_key'):
            site.gateway_key_encrypted = encrypt(post['gateway_key'])
        message = 'Pagamentos salvos'
    elif section == 'emails':
        sender = post.get('email_from', '').strip()
        if sender:
            try:
                validate_email(sender)
            except ValidationError:
                errors['email_from'] = 'Informe um e-mail de remetente válido.'
        port_text = post.get('email_port', '').strip() or '587'
        if not port_text.isdigit() or not 1 <= int(port_text) <= 65535:
            errors['email_port'] = 'Informe a porta do servidor, de 1 a 65535.'
        if errors:
            return _failure(request, errors, back)
        site.email_from_name = post.get('email_from_name', '').strip()[:80] or site.email_from_name
        site.email_from, site.email_host = sender, post.get('email_host', '').strip()
        site.email_port, site.email_username = int(port_text), post.get('email_username', '').strip()
        site.email_use_tls = post.get('email_use_tls') == '1'
        if post.get('email_password'):
            site.email_password_encrypted = encrypt(post['email_password'])
        site.save()
        if post.get('action') == 'test_email':
            return _test_email(request, back)
        message = 'E-mails salvos'
    else:
        signature = request.FILES.get('signature_image')
        if signature and _image_error(signature):
            errors['signature_image'] = _image_error(signature)
        if errors:
            return _failure(request, errors, back)
        site.signer_name = post.get('signer_name', '').strip()[:120]
        site.signer_role = post.get('signer_role', '').strip()[:120]
        site.signer_registration = post.get('signer_registration', '').strip()[:60]
        if signature:
            site.signature_image = signature
        message = 'Certificado salvo'
    site.save()
    toast(request, message)
    return json_ok(redirect=back) if wants_json(request) else redirect(back)


def _test_email(request, back):
    try:
        sent = send_mail('Teste de e-mail CETREMER', 'Configuração de e-mail funcionando.', None, [request.user.email], fail_silently=False)
    except Exception as exc:
        toast(request, f'Erro no SMTP: {exc}', level='error')
    else:
        if sent:
            toast(request, f'E-mail de teste enviado para {request.user.email}')
        else:
            toast(request, 'SMTP não configurado.', level='error')
    return json_ok(redirect=back) if wants_json(request) else redirect(back)


# ------------------------------------------------------------------ Equipe


def _team_error(request, message, field='email'):
    if wants_json(request):
        return JsonResponse({'ok': False, 'errors': {field: [message]}, 'error': message}, status=400)
    toast(request, message, level='error')
    return redirect(_back('equipe'))


def _team_done(request):
    url = _back('equipe')
    return json_ok(redirect=url) if wants_json(request) else redirect(url)


@painel_admin_required
@require_POST
def team_invite(request):
    email = request.POST.get('email', '').strip().lower()
    role = request.POST.get('role', 'CREATOR')
    if role not in ROLE_LABEL:
        return _team_error(request, 'Escolha um papel da lista.', 'role')
    try:
        validate_email(email)
    except ValidationError:
        return _team_error(request, 'Informe um e-mail válido.')
    user = User.objects.filter(email__iexact=email).first()
    if user is not None and user.role == User.Role.STUDENT:
        return _team_error(request, 'Este e-mail já é de um aluno e não pode entrar na equipe.')
    if user is not None and _is_team(user):
        return _team_error(request, 'Esta pessoa já está na equipe.')
    if user is None:
        from .access import new_username
        user = User.objects.create(username=new_username(email), email=email, role=role)
        user.set_unusable_password()
        user.save(update_fields=['password'])
    else:
        user.role, user.is_active = role, True
        user.save(update_fields=['role', 'is_active'])
    CreatorProfile.objects.get_or_create(user=user)
    sent = try_access_email(request, user)
    if sent:
        toast(request, f'Convite enviado para {email}')
    else:
        toast(request, f'{email} entrou na equipe, mas o e-mail de acesso não foi enviado. Confira as configurações de SMTP.', level='error')
    return _team_done(request)


@painel_admin_required
@require_POST
def team_role(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    role = request.POST.get('role', '')
    if role not in ROLE_LABEL:
        return _team_error(request, 'Escolha um papel da lista.', 'role')
    if user.is_superuser:
        return _team_error(request, 'O papel do Dono não muda.', 'role')
    if user.pk == request.user.pk:
        return _team_error(request, 'Você não pode mudar o seu próprio papel.', 'role')
    if not _is_team(user):
        return _team_error(request, 'Esta pessoa não está na equipe.', 'role')
    user.role = role
    if role == 'CREATOR':
        user.is_staff = False
    user.save(update_fields=['role', 'is_staff'])
    toast(request, f'{full_name(user)} agora é {ROLE_LABEL[role].split(" (")[0].lower()}')
    return _team_done(request)


@painel_admin_required
@require_POST
def team_remove(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser:
        return _team_error(request, 'O Dono não pode ser removido da equipe.', 'user')
    if user.pk == request.user.pk:
        return _team_error(request, 'Você não pode se remover da equipe.', 'user')
    if not _is_team(user):
        return _team_error(request, 'Esta pessoa não está na equipe.', 'user')
    name = full_name(user)
    user.is_active = False
    user.is_staff = False
    user.save(update_fields=['is_active', 'is_staff'])
    toast(request, f'{name} saiu da equipe')
    return _team_done(request)
