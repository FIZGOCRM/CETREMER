from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.utils.text import slugify
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
        messages.success(request, 'Senha criada. Entre com seu e-mail e a nova senha.')
        return redirect('login')

from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from sales.models import Order

@login_required
def settings_view(request):
    """Allows student users to configure profile data, modify passwords, and view invoice order histories."""
    error = None
    success = None
    
    # Fetch billing history
    orders = []
    if request.user.role == 'STUDENT':
        student_profile = request.user.student_profile
        orders = Order.objects.filter(student=student_profile).order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'profile_account':
            new_username = request.POST.get('username') or request.user.username
            new_email = request.POST.get('email')
            avatar_file = request.FILES.get('avatar')
            
            if not new_username or not new_email:
                error = "Nome de usuário e e-mail são obrigatórios."
            elif User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
                error = "Este nome de usuário já está em uso."
            elif User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
                error = "Este e-mail já está registrado em outra conta."
            else:
                request.user.username = new_username
                request.user.email = new_email
                if avatar_file:
                    request.user.avatar = avatar_file
                request.user.save()
                success = "Dados salvos com sucesso."
                
        elif action == 'profile_personal':
            if request.user.role == 'STUDENT':
                student_profile = request.user.student_profile
                student_profile.full_name = request.POST.get('full_name')
                student_profile.cpf = request.POST.get('cpf')
                try:
                    student_profile.save()
                except ValidationError as exc:
                    error = ' '.join(exc.messages)
                else:
                    success = "Dados salvos com sucesso."
            else:
                error = "Apenas alunos possuem dados pessoais cadastrados."
                
        elif action == 'profile_address':
            if request.user.role == 'STUDENT':
                student_profile = request.user.student_profile
                student_profile.address = request.POST.get('address')
                student_profile.save()
                success = "Endereço atualizado com sucesso!"
            else:
                error = "Apenas alunos possuem endereço residencial cadastrado."
                
        elif action == 'password':
            old_pass = request.POST.get('password_old')
            new_pass = request.POST.get('password_new')
            confirm_pass = request.POST.get('password_confirm')
            
            if not old_pass or not new_pass or not confirm_pass:
                error = "Todos os campos de senha são obrigatórios."
            elif not request.user.check_password(old_pass):
                error = "Senha atual incorreta."
            elif new_pass != confirm_pass:
                error = "A nova senha e a confirmação não coincidem."
            else:
                try:
                    validate_password(new_pass, user=request.user)
                except ValidationError as exc:
                    error = ' '.join(exc.messages)
                else:
                    request.user.set_password(new_pass)
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    success = "Dados salvos com sucesso."
                
    return render(request, 'users/settings.html', {
        'orders': orders,
        'error': error,
        'success': success
    })
