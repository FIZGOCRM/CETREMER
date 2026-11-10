from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from decimal import Decimal

from courses.models import Course, Module, Lesson, LessonMaterial, Enrollment
from sales.models import Order
from users.models import CreatorProfile

def creator_required(view_func):
    """Decorator to restrict view access to users with the role of CREATOR."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'CREATOR':
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@creator_required
def creator_dashboard(request):
    """Renders the creator portal home screen showing stats (sales, courses) and product lists."""
    creator = request.user.creator_profile
    courses = Course.objects.filter(creator=creator)
    
    # Calculate stats
    paid_orders = Order.objects.filter(course__creator=creator, status='PAID')
    total_sales_count = paid_orders.count()
    total_revenue = sum(order.price for order in paid_orders)
    total_students = paid_orders.values('student').distinct().count()
    
    return render(request, 'creator/dashboard.html', {
        'courses': courses,
        'total_revenue': total_revenue,
        'total_students': total_students,
        'total_sales_count': total_sales_count
    })

@login_required
@creator_required
def course_create_or_edit(request, course_id=None):
    """Processes course details edits and cover uploads for creators."""
    creator = request.user.creator_profile
    course = None
    
    if course_id:
        course = get_object_or_404(Course, id=course_id, creator=creator)
        
    error = None
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        price_str = request.POST.get('price', '0.00')
        is_published = request.POST.get('is_published') == 'on'
        live_meet_url = request.POST.get('live_meet_url')
        live_schedule_embed = request.POST.get('live_schedule_embed')
        cover = request.FILES.get('cover_image')
        
        try:
            price = Decimal(price_str)
        except Exception:
            price = Decimal('0.00')
            
        if not title:
            error = "O título do curso é obrigatório."
        else:
            if not course:
                # Create slug
                slug = slugify(title)
                # Ensure unique slug
                base_slug = slug
                num = 1
                while Course.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{num}"
                    num += 1
                    
                course = Course.objects.create(
                    title=title,
                    slug=slug,
                    description=description,
                    creator=creator,
                    price=price,
                    is_published=is_published,
                    live_meet_url=live_meet_url,
                    live_schedule_embed=live_schedule_embed
                )
            else:
                course.title = title
                course.description = description
                course.price = price
                course.is_published = is_published
                course.live_meet_url = live_meet_url
                course.live_schedule_embed = live_schedule_embed
                
            if cover:
                course.cover_image = cover
            course.save()
            return redirect('creator_dashboard')
            
    return render(request, 'creator/course_form.html', {
        'course': course,
        'error': error
    })

@login_required
@creator_required
def course_builder(request, course_id):
    """Interactive syllabus editor to add, update, or remove modules and lessons in a single view."""
    creator = request.user.creator_profile
    course = get_object_or_404(Course, id=course_id, creator=creator)
    modules = Module.objects.filter(course=course).prefetch_related('lessons')
    
    def safe_int(val, default=0):
        if not val:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default
            
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_module':
            title = request.POST.get('module_title')
            order = safe_int(request.POST.get('module_order'), 0)
            if title:
                Module.objects.create(course=course, title=title, order=order)
                
        elif action == 'add_lesson':
            module_id = request.POST.get('module_id')
            module = get_object_or_404(Module, id=module_id, course=course)
            title = request.POST.get('lesson_title')
            desc = request.POST.get('lesson_desc')
            vid = request.POST.get('lesson_video')
            dur = safe_int(request.POST.get('lesson_duration'), 0)
            d_url = request.POST.get('lesson_download_url')
            d_name = request.POST.get('lesson_download_name')
            order = safe_int(request.POST.get('lesson_order'), 0)
            
            if title:
                lesson = Lesson.objects.create(
                    module=module,
                    title=title,
                    description=desc,
                    video_url=vid,
                    duration_seconds=dur,
                    order=order
                )
                if d_url:
                    LessonMaterial.objects.create(lesson=lesson, title=d_name or 'Material complementar', url=d_url)
                
        elif action == 'delete_module':
            mod_id = request.POST.get('module_id')
            Module.objects.filter(id=mod_id, course=course).delete()
            
        elif action == 'delete_lesson':
            les_id = request.POST.get('lesson_id')
            Lesson.objects.filter(id=les_id, module__course=course).delete()
            
        return redirect('course_builder', course_id=course.id)
        
    return render(request, 'creator/builder.html', {
        'course': course,
        'modules': modules
    })

@login_required
@creator_required
def creator_payments(request):
    """Processes payment setups, banking Details, and gateway credential configurations for creators."""
    creator = request.user.creator_profile
    success = False
    
    if request.method == 'POST':
        bank = request.POST.get('bank_name')
        pix = request.POST.get('pix_key')
        gateway = request.POST.get('gateway_name', 'MOCK_GATEWAY')
        key = request.POST.get('gateway_api_key')
        
        email_host = request.POST.get('email_host')
        email_port_str = request.POST.get('email_port', '587')
        email_username = request.POST.get('email_username')
        email_password = request.POST.get('email_password')
        email_use_tls = request.POST.get('email_use_tls') == 'on'
        
        try:
            email_port = int(email_port_str)
        except Exception:
            email_port = 587
        
        creator.bank_name = bank
        creator.pix_key = pix
        creator.gateway_name = gateway
        creator.gateway_api_key = key
        
        creator.email_host = email_host
        creator.email_port = email_port
        creator.email_username = email_username
        creator.email_password = email_password
        creator.email_use_tls = email_use_tls
        
        creator.save()
        success = True
        
    return render(request, 'creator/payments.html', {
        'creator': creator,
        'success': success
    })

@login_required
@creator_required
def creator_integrations(request):
    """View to configure creator integrations like Asaas, AI Tutor API, and Certificate Signatures."""
    creator = request.user.creator_profile
    success = False
    
    if request.method == 'POST':
        asaas_token = request.POST.get('asaas_token')
        asaas_sandbox = request.POST.get('asaas_sandbox') == 'on'
        ai_provider = request.POST.get('ai_provider', 'GEMINI')
        ai_api_key = request.POST.get('ai_api_key')
        ai_tutor_enabled = request.POST.get('ai_tutor_enabled') == 'on'
        cert_name = request.POST.get('certificate_signature_name')
        cert_role = request.POST.get('certificate_signature_role')
        
        creator.asaas_token = asaas_token
        creator.asaas_sandbox = asaas_sandbox
        creator.ai_provider = ai_provider
        creator.ai_api_key = ai_api_key
        creator.ai_tutor_enabled = ai_tutor_enabled
        creator.certificate_signature_name = cert_name
        creator.certificate_signature_role = cert_role
        creator.save()
        success = True
        
    return render(request, 'creator/integrations.html', {
        'creator': creator,
        'success': success
    })
