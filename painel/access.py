"""E-mail de acesso e matrícula, compartilhados pela lista de alunos, pela ficha e pela importação."""
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import slugify

from core.activity import log_enrolled
from core.toasts import toast
from courses.models import Enrollment
from users.models import SiteSettings

User = get_user_model()


def access_email(request, user):
    """Envia o link para criar a senha. Guarda quando saiu (ficha do aluno, "E-mail de acesso enviado em")."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = request.build_absolute_uri(reverse('password_reset_confirm', args=[uid, token]))
    sent = send_mail('Seu acesso à CETREMER', f'Olá! Defina sua senha para acessar a CETREMER: {url}',
                     None, [user.email], fail_silently=False)
    profile = getattr(user, 'student_profile', None)
    if sent and profile is not None:
        profile.access_email_sent_at = timezone.now()
        profile.save(update_fields=['access_email_sent_at'])
    return sent


def try_access_email(request, user):
    try:
        return bool(access_email(request, user))
    except Exception:
        return False


def report_access_delivery(request, sent):
    if not sent:
        toast(request, 'O e-mail de acesso não foi enviado. Confira as configurações de SMTP.', level='error')
    elif django_settings.DEBUG and not SiteSettings.load().email_host:
        toast(request, 'Link de acesso gerado no console do servidor local. Nenhum e-mail chegou à caixa de entrada.', level='info')


def new_username(email):
    base = slugify(email.split('@')[0]) or 'aluno'
    username, index = base, 2
    while User.objects.filter(username=username).exists():
        username = f'{base}{index}'
        index += 1
    return username


def create_student(email, full_name='', cpf=''):
    """Cria o aluno com senha inutilizável (ele define a sua pelo link de acesso)."""
    user = User.objects.create(username=new_username(email), email=email, role=User.Role.STUDENT)
    user.set_unusable_password()
    user.save(update_fields=['password'])
    profile = user.student_profile
    if full_name:
        profile.full_name = full_name
    if cpf:
        profile.cpf = cpf
    profile.save()
    return user


def grant(user, course, source='manual', ref='', actor=None):
    """Libera o curso. Devolve True quando o acesso é novo (matrícula nova ou reativada)."""
    enrollment, created = Enrollment.objects.get_or_create(
        student=user.student_profile, course=course, defaults={'source': source, 'external_ref': ref})
    if created:
        log_enrolled(user, course, actor=actor)
        return True
    if not enrollment.is_active:
        enrollment.is_active = True
        enrollment.save(update_fields=['is_active'])
        log_enrolled(user, course, actor=actor)
        return True
    if ref and not enrollment.external_ref:
        enrollment.external_ref = ref
        enrollment.save(update_fields=['external_ref'])
    return False
