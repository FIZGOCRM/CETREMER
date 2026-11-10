from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.db import transaction
from core.toasts import toast
from .first_access import verify_code
from .models import FirstAccessCode
from .models import User


def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'
    if request.user.is_authenticated:
        return redirect(next_url)
    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            return redirect(next_url)
        error = 'E-mail ou senha incorretos. Confira e tente de novo.'
    return render(request, 'login.html', {'error': error, 'next': next_url})


def logout_view(request):
    logout(request)
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
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    def get(self, request, *args, **kwargs):
        toast(request, 'Senha criada. Entre com seu e-mail e a nova senha.')
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
                        toast(request, 'Senha criada. Entre com seu e-mail e a nova senha.')
                        return redirect('login')
    return render(request, 'registration/first_access.html', {'error': error})

from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from sales.models import Order
