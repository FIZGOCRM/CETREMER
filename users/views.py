from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User

def login_view(request):
    """Authenticates and logs in existing users, checking the redirect path."""
    next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'
    if request.user.is_authenticated:
        return redirect(next_url)
    
    error = None
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            error = "Nome de usuário ou senha inválidos."
            
    return render(request, 'login.html', {'error': error, 'next': next_url})

def logout_view(request):
    """Logs out active users and redirects to the landing page."""
    if request.method == 'POST' or request.method == 'GET':
        logout(request)
    return redirect('landing')

def register_view(request):
    """Registers public users as students and logs them in."""
    next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'
    if request.user.is_authenticated:
        return redirect(next_url)
        
    error = None
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')
        
        if not u or not e or not p:
            error = "Todos os campos são obrigatórios."
        elif User.objects.filter(username=u).exists():
            error = "Este nome de usuário já existe."
        elif User.objects.filter(email=e).exists():
            error = "Este endereço de e-mail já está registrado."
        else:
            try:
                validate_password(p, user=User(username=u, email=e, role=User.Role.STUDENT))
            except ValidationError as exc:
                error = ' '.join(exc.messages)
            else:
                user = User.objects.create_user(username=u, email=e, password=p, role=User.Role.STUDENT)
                login(request, user)
                return redirect(next_url)
            
    return render(request, 'register.html', {'error': error, 'next': next_url})

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
            new_username = request.POST.get('username')
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
                success = "Dados da conta atualizados com sucesso!"
                
        elif action == 'profile_personal':
            if request.user.role == 'STUDENT':
                student_profile = request.user.student_profile
                student_profile.full_name = request.POST.get('full_name')
                student_profile.cpf = request.POST.get('cpf')
                student_profile.save()
                success = "Dados pessoais de certificação atualizados!"
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
                    success = "Senha alterada com sucesso!"
                
    return render(request, 'users/settings.html', {
        'orders': orders,
        'error': error,
        'success': success
    })
