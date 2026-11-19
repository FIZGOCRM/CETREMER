from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import transaction
from urllib.parse import urlsplit
from .first_access import verify_code
from .models import FirstAccessCode
from .models import User
from .forms import PortalPasswordResetForm


def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = ''
    next_path = urlsplit(next_url).path
    portal = getattr(request, 'portal', None)
    if portal:
        from core.portal_routing import allows_next
        if not allows_next(portal, next_path):
            next_url = ''
    producer_access = portal == 'producer' if portal else request.GET.get('acesso') == 'admin' or next_path == '/painel' or next_path.startswith('/painel/')
    def destination(user):
        return next_url or ('painel:dashboard' if user.role in ('ADMIN', 'CREATOR') else 'dashboard')
    if request.user.is_authenticated:
        return redirect(destination(request.user))
    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None and portal:
            from core.portal_routing import allows_user
            if not allows_user(portal, user):
                user = None
        if user is not None:
            login(request, user)
            return redirect(destination(user))
        error = 'E-mail ou senha incorretos. Confira e tente de novo.'
    return render(request, 'login_admin.html' if producer_access else 'login.html', {'error': error, 'next': next_url})


def logout_view(request):
    producer_access = request.user.is_authenticated and request.user.role in ('ADMIN', 'CREATOR')
    logout(request)
    if producer_access:
        from django.urls import reverse
        return redirect(reverse('login')+'?acesso=admin')
    return redirect('landing')


def register_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'
    if request.user.is_authenticated:
        return redirect(next_url)
    error = None
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirmation = request.POST.get('password_confirm', '')
        if not full_name or not email or not password or not confirmation:
            error = 'Preencha todos os campos.'
        elif password != confirmation:
            error = 'As senhas não coincidem.'
        elif not request.POST.get('terms'):
            error = 'Aceite os termos para criar sua conta.'
        elif User.objects.filter(email__iexact=email).exists():
            error = 'Este e-mail já está cadastrado.'
        else:
            base = slugify(email.split('@')[0]).replace('-', '_') or 'aluno'
            username = base
            suffix = 2
            while User.objects.filter(username=username).exists():
                username = f'{base}{suffix}'
                suffix += 1
            try:
                validate_password(password, user=User(username=username, email=email, role=User.Role.STUDENT))
            except ValidationError as exc:
                error = ' '.join(exc.messages)
            else:
                user = User.objects.create_user(username=username, email=email, password=password, role=User.Role.STUDENT)
                user.student_profile.full_name = full_name
                user.student_profile.save(update_fields=['full_name'])
                login(request, user, backend='users.backends.EmailBackend')
                return redirect(next_url)
    return render(request, 'register.html', {'error': error, 'next': next_url})


class PasswordResetView(auth_views.PasswordResetView):
    form_class = PortalPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['portal'] = getattr(self.request, 'portal', None)
        return kwargs

    def form_valid(self, form):
        from .models import SiteSettings
        self.extra_email_context={'school_name':SiteSettings.load().school_name}
        return super().form_valid(form)


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def get_user(self, uidb64):
        user = super().get_user(uidb64)
        if user is not None:
            from core.portal_routing import allows_user
            if not allows_user(getattr(self.request, 'portal', None), user):
                return None
        return user


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    def get(self, request, *args, **kwargs):
        messages.success(request, 'Senha criada. Entre com seu e-mail e a nova senha.')
        return redirect('login')


def first_access_view(request):
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        code = request.POST.get('code', '').strip()
        password = request.POST.get('password', '')
        confirmation = request.POST.get('password_confirm', '')
        if not email or not code or not password or not confirmation:
            error = 'Preencha todos os campos.'
        elif password != confirmation:
            error = 'As senhas não coincidem.'
        else:
            with transaction.atomic():
                user = User.objects.select_for_update().filter(email__iexact=email, role=User.Role.STUDENT, is_active=True).first()
                credential = FirstAccessCode.objects.select_for_update().filter(user=user).first() if user else None
                if not user or user.has_usable_password() or not credential or not verify_code(credential, code):
                    error = 'Código inválido ou expirado. Peça um novo código ao administrador.'
                else:
                    try:
                        validate_password(password, user=user)
                    except ValidationError as exc:
                        error = ' '.join(exc.messages)
                    else:
                        user.set_password(password)
                        user.save(update_fields=['password'])
                        credential.delete()
                        messages.success(request, 'Senha criada. Entre com seu e-mail e a nova senha.')
                        return redirect('login')
    return render(request, 'registration/first_access.html', {'error': error})

from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from sales.models import Order

@login_required
def settings_view(request):
    from django.core.exceptions import PermissionDenied
    from .forms import AccountForm
    from .services import update_member_account,update_member_personal,update_member_preferences
    if request.user.role != 'STUDENT':return redirect('painel:settings')
    error=success=None
    if request.method=='POST':
        action=request.POST.get('action')
        try:
            if action=='profile_account':
                form=AccountForm(request.POST,request.FILES)
                if not form.is_valid():raise ValidationError([str(e) for errors in form.errors.values() for e in errors])
                update_member_account(request.user,**form.cleaned_data)
            elif action=='profile_personal':
                update_member_personal(request.user,full_name=request.POST.get('full_name',''),cpf=request.POST.get('cpf',''))
            elif action=='profile_address':
                profile=request.user.student_profile;profile.address=request.POST.get('address','').strip();profile.save(update_fields=['address'])
            elif action=='preferences':
                update_member_preferences(request.user,new_lessons=bool(request.POST.get('email_new_lessons')),live_events=bool(request.POST.get('email_live_events')))
            elif action=='password':
                old=request.POST.get('password_old','');new=request.POST.get('password_new','')
                if not request.user.check_password(old):raise ValidationError('Senha atual incorreta.')
                if not new or new!=request.POST.get('password_confirm'):raise ValidationError('As senhas não coincidem.')
                validate_password(new,user=request.user)
                request.user.set_password(new);request.user.save(update_fields=['password']);update_session_auth_hash(request,request.user)
            else:raise ValidationError('Ação inválida.')
            success='Dados salvos com sucesso.'
        except ValidationError as exc:
            error=' '.join(exc.messages)
            request.user.refresh_from_db()
    return render(request,'users/settings.html',{'plans':_student_plans(request.user),'error':error,'success':success})


def _student_plans(user):
    if user.role != 'STUDENT':
        return []
    from courses.services import plan_status
    return [{'enrollment': e, 'plan': plan_status(e)} for e in user.student_profile.enrollments.select_related('course').prefetch_related('access_periods')]
