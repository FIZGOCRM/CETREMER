"""Minha conta (HANDOFF-v2 7.7): perfil, dados do certificado, senha e acesso, pedidos e acessos, avisos por e-mail."""
import logging

from django import forms
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.sessions.models import Session
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.ajax import json_errors, json_ok, wants_json
from core.toasts import toast
from courses.models import Certificate, Enrollment
from sales.models import Order
from .validators import only_digits, validate_cpf

logger = logging.getLogger(__name__)
User = get_user_model()

SECTIONS = ('perfil', 'certificado', 'senha', 'pedidos', 'avisos')
STAFF_SECTIONS = ('perfil', 'senha')
SAVED = 'Alterações salvas'
PASSWORD_UPDATED = 'Senha atualizada. Use a nova senha no próximo acesso'
LOGGED_OUT_OTHERS = 'Você saiu dos outros aparelhos. Este continua conectado'
EMAIL_SALT = 'users.email-change'
EMAIL_MAX_AGE = 3 * 24 * 3600
PHOTO_TYPES = ('image/jpeg', 'image/png')
PHOTO_MAX_MB = 2


class ProfileForm(forms.Form):
    display_name = forms.CharField(max_length=40, required=False)
    email = forms.EmailField(error_messages={'required': 'Informe o e-mail de acesso.', 'invalid': 'Informe um e-mail válido.'})
    whatsapp = forms.CharField(max_length=30, required=False)
    avatar = forms.ImageField(required=False, error_messages={'invalid_image': 'Envie uma imagem JPG ou PNG.'})

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_display_name(self):
        return ' '.join(self.cleaned_data['display_name'].split())

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Este e-mail já está em uso em outra conta.')
        return email

    def clean_whatsapp(self):
        digits = only_digits(self.cleaned_data['whatsapp'])
        if digits and not 10 <= len(digits) <= 15:
            raise ValidationError('Informe o WhatsApp com DDD, só números.')
        return digits

    def clean_avatar(self):
        photo = self.cleaned_data.get('avatar')
        if not photo:
            return photo
        if getattr(photo, 'content_type', '') not in PHOTO_TYPES:
            raise ValidationError('Envie uma imagem JPG ou PNG.')
        if photo.size > PHOTO_MAX_MB * 1024 * 1024:
            raise ValidationError(f'A foto deve ter no máximo {PHOTO_MAX_MB} MB.')
        return photo


class CertificateDataForm(forms.Form):
    full_name = forms.CharField(max_length=255, required=False)
    cpf = forms.CharField(required=False)

    def clean_full_name(self):
        return ' '.join(self.cleaned_data['full_name'].split())

    def clean_cpf(self):
        value = self.cleaned_data['cpf'].strip()
        return validate_cpf(value) if value else ''


class PasswordForm(forms.Form):
    password_old = forms.CharField(error_messages={'required': 'Informe a senha atual.'})
    password_new = forms.CharField(error_messages={'required': 'Informe a nova senha.'})
    password_confirm = forms.CharField(error_messages={'required': 'Repita a nova senha.'})

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password_old(self):
        value = self.cleaned_data['password_old']
        if not self.user.check_password(value):
            raise ValidationError('Senha atual incorreta.')
        return value

    def clean_password_new(self):
        value = self.cleaned_data['password_new']
        if len(value) < 8:
            raise ValidationError('A nova senha precisa ter pelo menos 8 caracteres.')
        if not (any(c.isalpha() for c in value) and any(c.isdigit() for c in value)):
            raise ValidationError('Use letras e números na nova senha.')
        if self.cleaned_data.get('password_old') == value:
            raise ValidationError('A nova senha precisa ser diferente da atual.')
        try:
            validate_password(value, user=self.user)
        except ValidationError as exc:
            raise ValidationError(' '.join(exc.messages))
        return value

    def clean(self):
        data = super().clean()
        if data.get('password_new') and data.get('password_confirm') and data['password_new'] != data['password_confirm']:
            self.add_error('password_confirm', 'A confirmação não é igual à nova senha.')
        return data


class NoticesForm(forms.Form):
    notify_answers = forms.CharField(required=False)
    notify_live = forms.CharField(required=False)
    notify_certificate = forms.CharField(required=False)
    notify_marketing = forms.CharField(required=False)


def _flag(value):
    return str(value) in ('1', 'true', 'on')


def _eligible_enrollments(profile):
    return (Enrollment.objects.filter(student=profile, is_active=True).exclude(course__status='archived')
            .select_related('course'))


def _pending_certificates(profile):
    issued = set(Certificate.objects.filter(enrollment__student=profile).values_list('enrollment__course_id', flat=True))
    return sum(1 for e in _eligible_enrollments(profile) if e.course.certificate_enabled and e.course_id not in issued)


def _origin(enrollment, order):
    if enrollment.source == 'purchase':
        return f'Compra no site · #{order.id}' if order else 'Compra no site'
    label = {'manual': 'Liberado pela equipe', 'import': 'Importado', 'signup': 'Cadastro no site'}.get(enrollment.source, 'Liberado pela equipe')
    return f'{label} · {enrollment.external_ref}' if enrollment.external_ref else label


def _access_rows(profile):
    orders = {}
    for order in Order.objects.filter(student=profile, status=Order.Status.COMPLETED).order_by('created_at'):
        orders[order.course_id] = order
    rows = []
    for enrollment in _eligible_enrollments(profile).order_by('-enrolled_at'):
        rows.append({'enrollment': enrollment, 'course': enrollment.course, 'origin': _origin(enrollment, orders.get(enrollment.course_id))})
    return rows


def _initial_section(request, is_student):
    allowed = SECTIONS if is_student else STAFF_SECTIONS
    chosen = request.GET.get('secao') or request.POST.get('section')
    if chosen in allowed:
        return chosen
    if is_student and not (request.user.student_profile.full_name and request.user.student_profile.cpf):
        return 'certificado'
    return 'perfil'


def _context(request, section, forms_by_section):
    user = request.user
    is_student = user.role == 'STUDENT'
    profile = user.student_profile if is_student else None
    ctx = {'section': section, 'is_student': is_student, 'forms': forms_by_section, 'pending_email': user.pending_email}
    if is_student:
        locked = Certificate.objects.filter(enrollment__student=profile).exists()
        data_ok = bool(profile.full_name and profile.cpf)
        rows = _access_rows(profile)
        ctx.update({
            'certificate_locked': locked, 'data_ok': data_ok, 'pending_certificates': _pending_certificates(profile),
            'access_rows': rows, 'access_count': len(rows),
            'orders': Order.objects.filter(student=profile).select_related('course').order_by('-created_at'),
        })
    return ctx


def _initial_forms(request):
    user = request.user
    profile = getattr(user, 'student_profile', None)
    forms_by_section = {
        'perfil': ProfileForm(user=user, initial={'display_name': getattr(profile, 'display_name', ''), 'email': user.email,
                                                  'whatsapp': getattr(profile, 'whatsapp', '')}),
        'senha': PasswordForm(user=user),
    }
    if profile is not None:
        forms_by_section['certificado'] = CertificateDataForm(initial={'full_name': profile.full_name or '', 'cpf': profile.cpf or ''})
        forms_by_section['avisos'] = NoticesForm(initial={
            'notify_answers': int(profile.notify_answers), 'notify_live': int(profile.notify_live),
            'notify_certificate': int(profile.notify_certificate), 'notify_marketing': int(profile.notify_marketing)})
    return forms_by_section


def _send_email_confirmation(request, new_email):
    token = signing.dumps({'u': request.user.pk, 'e': new_email}, salt=EMAIL_SALT)
    link = request.build_absolute_uri(reverse('email_confirm', args=[token]))
    try:
        send_mail('Confirme seu novo e-mail', f'Para trocar o e-mail de acesso para {new_email}, abra o link: {link}', None, [new_email], fail_silently=False)
    except Exception:
        logger.exception('Falha ao enviar a confirmação de e-mail para o usuário %s', request.user.pk)


def _respond_saved(request, section, message, reload=False):
    if wants_json(request):
        return json_ok(toast=message, reload=reload)
    toast(request, message)
    return redirect(reverse('settings') + f'?secao={section}')


def _save_profile(request, form):
    user = request.user
    profile = getattr(user, 'student_profile', None)
    data = form.cleaned_data
    message = SAVED
    if data['email'].lower() != user.email.lower():
        user.pending_email = data['email']
        _send_email_confirmation(request, data['email'])
        message = f'Enviamos um link de confirmação para {data["email"]}. Até confirmar, continua valendo o e-mail atual.'
    elif user.pending_email:
        user.pending_email = ''
    if data.get('avatar'):
        user.avatar = data['avatar']
    user.save()
    if profile is not None:
        profile.display_name, profile.whatsapp = data['display_name'], data['whatsapp']
        profile.save(update_fields=['display_name', 'whatsapp'])
    return message


@login_required
def settings_view(request):
    user = request.user
    is_student = user.role == 'STUDENT'
    section = _initial_section(request, is_student)
    forms_by_section = _initial_forms(request)

    if request.method == 'POST':
        posted = request.POST.get('section')
        allowed = SECTIONS if is_student else STAFF_SECTIONS
        if posted not in allowed or posted in ('pedidos',):
            return redirect(reverse('settings') + f'?secao={section}')
        section = posted
        profile = getattr(user, 'student_profile', None)

        if posted == 'perfil':
            form = ProfileForm(request.POST, request.FILES, user=user)
            forms_by_section['perfil'] = form
            if form.is_valid():
                return _respond_saved(request, 'perfil', _save_profile(request, form))
        elif posted == 'certificado':
            locked = Certificate.objects.filter(enrollment__student=profile).exists()
            if locked:
                return _respond_saved(request, 'certificado', SAVED)
            form = CertificateDataForm(request.POST)
            forms_by_section['certificado'] = form
            if form.is_valid():
                profile.full_name = form.cleaned_data['full_name'] or None
                profile.cpf = form.cleaned_data['cpf'] or None
                profile.save(update_fields=['full_name', 'cpf'])
                return _respond_saved(request, 'certificado', SAVED)
        elif posted == 'senha':
            form = PasswordForm(request.POST, user=user)
            forms_by_section['senha'] = form
            if form.is_valid():
                user.set_password(form.cleaned_data['password_new'])
                user.save()
                update_session_auth_hash(request, user)
                return _respond_saved(request, 'senha', PASSWORD_UPDATED, reload=True)
        elif posted == 'avisos':
            form = NoticesForm(request.POST)
            forms_by_section['avisos'] = form
            if form.is_valid():
                for field in ('notify_answers', 'notify_live', 'notify_certificate', 'notify_marketing'):
                    setattr(profile, field, _flag(form.cleaned_data[field]))
                profile.save(update_fields=['notify_answers', 'notify_live', 'notify_certificate', 'notify_marketing'])
                return _respond_saved(request, 'avisos', SAVED)

        if wants_json(request):
            return json_errors(form)
        response = render(request, 'users/settings.html', _context(request, section, forms_by_section))
        response.status_code = 400
        return response

    return render(request, 'users/settings.html', _context(request, section, forms_by_section))


@login_required
@require_POST
def logout_others(request):
    """Encerra as outras sessões da pessoa e mantém esta."""
    user = request.user
    current = request.session.session_key
    for session in Session.objects.filter(expire_date__gt=timezone.now()).exclude(session_key=current):
        if session.get_decoded().get('_auth_user_id') == str(user.pk):
            session.delete()
    update_session_auth_hash(request, user)
    if wants_json(request):
        return json_ok(toast=LOGGED_OUT_OTHERS)
    toast(request, LOGGED_OUT_OTHERS)
    return redirect(reverse('settings') + '?secao=senha')


@login_required
def email_confirm(request, token):
    """Confirma a troca de e-mail pelo link enviado ao endereço novo."""
    try:
        payload = signing.loads(token, salt=EMAIL_SALT, max_age=EMAIL_MAX_AGE)
    except signing.BadSignature:
        toast(request, 'Este link de confirmação não vale mais. Peça a troca de e-mail de novo.', level='error')
        return redirect(reverse('settings') + '?secao=perfil')
    user = request.user
    new_email = payload.get('e', '')
    if payload.get('u') != user.pk or user.pending_email.lower() != new_email.lower():
        toast(request, 'Este link de confirmação não vale mais. Peça a troca de e-mail de novo.', level='error')
    elif User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
        toast(request, 'Este e-mail já está em uso em outra conta.', level='error')
    else:
        user.email, user.pending_email = new_email, ''
        user.save(update_fields=['email', 'pending_email'])
        toast(request, 'E-mail de acesso atualizado')
    return redirect(reverse('settings') + '?secao=perfil')
