from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import login
import uuid

from users.models import User, StudentProfile
from courses.models import Course, Enrollment, Lesson
from .models import Order, OrderBump

def checkout(request, course_slug):
    """Renders the secure checkout page for a specific course, open to guest users."""
    course = get_object_or_404(Course, slug=course_slug)
    
    if request.user.is_authenticated:
        if request.user.role == 'STUDENT':
            student_profile = request.user.student_profile
            # If already enrolled, redirect to the course lessons directly
            already_enrolled = Enrollment.objects.filter(student=student_profile, course=course).exists()
            if already_enrolled:
                first_lesson = Lesson.objects.filter(module__course=course).order_by('module__order', 'order', 'id').first()
                if first_lesson:
                    return redirect('lesson_detail', course_slug=course.slug, lesson_id=first_lesson.id)
                return redirect('course_preview', course_slug=course.slug)
            
    # Retrieve eligible order bumps associated with this course
    order_bumps = OrderBump.objects.filter(parent_course=course).select_related('bump_course')
    
    return render(request, 'sales/checkout.html', {
        'course': course,
        'order_bumps': order_bumps
    })

def process_checkout(request, course_slug):
    """Processes simulated transactions, creates User/Profile if needed, logs in, and enrolls in courses."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método HTTP inválido.'}, status=400)
        
    course = get_object_or_404(Course, slug=course_slug)
    email = request.POST.get('email', '').strip()
    name = request.POST.get('name', '').strip()
    payment_method = request.POST.get('payment_method', 'CREDIT_CARD')
    selected_bumps_str = request.POST.get('selected_bumps', '')

    if not email or not name:
        return JsonResponse({'status': 'error', 'message': 'Nome e E-mail são obrigatórios.'}, status=400)

    # 1. Resolve student profile (create account if guest)
    is_new_user = False
    temp_password = None
    creator = course.creator
    
    if request.user.is_authenticated:
        user = request.user
        student_profile = user.student_profile
    else:
        # Check if user with this email exists
        user = User.objects.filter(email=email).first()
        if not user:
            is_new_user = True
            # Generate username from email
            username_base = email.split('@')[0]
            username = username_base
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1
                
            # Generate random temporary password
            temp_password = User.objects.make_random_password()
            # Create user and automatically triggers student_profile creation via signals
            user = User.objects.create_user(
                username=username,
                email=email,
                password=temp_password,
                role=User.Role.STUDENT
            )
        student_profile = user.student_profile
        
        # Log in the user immediately
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        
    # Dispatch dynamic welcome email if user is new
    if is_new_user and temp_password:
        from django.core.mail import get_connection, send_mail
        connection = None
        from_email = 'no-reply@cetremer.com.br'
        
        # Try custom creator SMTP credentials
        if creator.email_username and creator.email_password:
            try:
                from django.conf import settings
                backend_class = 'django.core.mail.backends.smtp.EmailBackend'
                if settings.EMAIL_BACKEND == 'django.core.mail.backends.locmem.EmailBackend':
                    backend_class = 'django.core.mail.backends.locmem.EmailBackend'
                
                connection = get_connection(
                    backend=backend_class,
                    host=creator.email_host or 'smtp.gmail.com',
                    port=creator.email_port or 587,
                    username=creator.email_username,
                    password=creator.email_password,
                    use_tls=creator.email_use_tls
                )
                from_email = creator.email_username
            except Exception:
                pass
                
        # Send Email
        login_url = request.build_absolute_uri(reverse('login'))
        subject = f"Seu acesso ao curso {course.title} foi liberado!"
        message = (
            f"Olá {name},\n\n"
            f"Sua compra do curso '{course.title}' foi concluída com sucesso!\n\n"
            f"Para acessar as aulas, utilize as seguintes credenciais:\n"
            f"- E-mail: {email}\n"
            f"- Senha Temporária: {temp_password}\n\n"
            f"Faça o login em: {login_url}\n\n"
            f"Recomendamos alterar sua senha após o primeiro acesso na tela de Configurações.\n\n"
            f"Bons estudos,\n"
            f"Equipe {creator.company_name or 'CetrEmer'}"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[email],
            connection=connection,
            fail_silently=True
        )
        
    # 2. Create main course transaction record and Enrollment
    transaction_id = str(uuid.uuid4())
    Order.objects.create(
        student=student_profile,
        course=course,
        amount=course.price,
        payment_method=payment_method,
        status=Order.Status.COMPLETED,
        transaction_id=transaction_id
    )
    Enrollment.objects.get_or_create(student=student_profile, course=course, defaults={'source': 'purchase'})
    
    # 3. Create transaction records and Enrollments for chosen order bump upsells
    if selected_bumps_str:
        bump_ids = [int(x) for x in selected_bumps_str.split(',') if x.strip().isdigit()]
        for bump_id in bump_ids:
            try:
                bump = OrderBump.objects.get(id=bump_id, parent_course=course)
                Order.objects.create(
                    student=student_profile,
                    course=bump.bump_course,
                    amount=bump.discount_price,
                    payment_method=payment_method,
                    status=Order.Status.COMPLETED,
                    transaction_id=str(uuid.uuid4())
                )
                Enrollment.objects.get_or_create(student=student_profile, course=bump.bump_course, defaults={'source': 'purchase'})
            except OrderBump.DoesNotExist:
                pass
                
    first_lesson = Lesson.objects.filter(module__course=course).order_by('module__order', 'order', 'id').first()
    destination = (reverse('lesson_detail', kwargs={'course_slug': course.slug, 'lesson_id': first_lesson.id})
                   if first_lesson else reverse('course_preview', kwargs={'course_slug': course.slug}))
    return JsonResponse({
        'status': 'success',
        'redirect_url': destination
    })
