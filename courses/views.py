from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
import json

from .models import Course, Module, Lesson, Progress, Enrollment
from community.models import CommunityPost

def landing(request):
    """Lists published courses on landing page, checking enrollment details if logged in."""
    courses = Course.objects.filter(is_published=True).select_related('creator__user')
    
    # Query active Hero Banner
    from .models import HeroBanner
    hero = HeroBanner.objects.filter(is_active=True).first()
    
    enrolled_courses = []
    if request.user.is_authenticated:
        if request.user.role == 'STUDENT':
            student_profile = request.user.student_profile
            # Check enrolled courses using direct Enrollment model
            enrolled_courses = Course.objects.filter(enrollments__student=student_profile)
            
    return render(request, 'landing.html', {
        'courses': courses,
        'enrolled_courses': enrolled_courses,
        'hero': hero
    })

def course_preview(request, course_slug):
    """Renders the public Udemy-style course landing/preview page with syllabus and buy options."""
    course = get_object_or_404(Course, slug=course_slug)
    
    is_enrolled = False
    if request.user.is_authenticated:
        if request.user.role == 'STUDENT':
            student_profile = request.user.student_profile
            is_enrolled = Enrollment.objects.filter(student=student_profile, course=course).exists()
            
    modules = Module.objects.filter(course=course).prefetch_related('lessons')
    total_lessons = Lesson.objects.filter(module__course=course).count()
    
    # Calculate total duration
    total_seconds = sum(l.duration_seconds for m in modules for l in m.lessons.all())
    total_hours = total_seconds // 3600
    total_minutes = (total_seconds % 3600) // 60
    
    duration_str = ""
    if total_hours > 0:
        duration_str += f"{total_hours}h "
    duration_str += f"{total_minutes}min"
    
    return render(request, 'courses/course_preview.html', {
        'course': course,
        'modules': modules,
        'total_lessons': total_lessons,
        'duration_str': duration_str,
        'is_enrolled': is_enrolled
    })

@login_required
def dashboard(request):
    """Displays student library displaying all courses in Netflix sliders with locked/unlocked state."""
    if request.user.role != 'STUDENT':
        return render(request, 'courses/dashboard.html', {'essentials': [], 'specialties': [], 'leigos': []})
        
    student_profile = request.user.student_profile
    enrollments_qs = Enrollment.objects.filter(student=student_profile)
    enrolled_course_ids = set(enrollments_qs.values_list('course_id', flat=True))
    
    all_courses = Course.objects.filter(is_published=True).select_related('creator__user')
    
    essentials = []
    specialties = []
    leigos = []
    
    for course in all_courses:
        is_locked = course.id not in enrolled_course_ids
        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_lessons = 0
        progress_percent = 0
        
        if not is_locked:
            completed_lessons = Progress.objects.filter(
                student=student_profile, 
                lesson__module__course=course, 
                is_completed=True
            ).count()
            progress_percent = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
            
        item = {
            'course': course,
            'is_locked': is_locked,
            'total_lessons_count': total_lessons,
            'completed_lessons_count': completed_lessons,
            'progress_percent': progress_percent
        }
        
        # Categorize by slug for custom sliders
        if course.slug in ['suporte-basico-vida-bls', 'suporte-avancado-cardiologia-acls']:
            essentials.append(item)
        elif course.slug in ['suporte-avancado-pediatria-pals', 'plantao-sem-gpt']:
            specialties.append(item)
        else:
            leigos.append(item)
        
    # Calculate overall average progress
    enrolled_items = [item for item in (essentials + specialties + leigos) if not item['is_locked']]
    overall_progress = 0
    if enrolled_items:
        overall_progress = int(sum(item['progress_percent'] for item in enrolled_items) / len(enrolled_items))
        
    # Get active live course with Google Meet or calendar schedule
    active_live_course = None
    for item in enrolled_items:
        if item['course'].live_meet_url or item['course'].live_schedule_embed:
            active_live_course = item['course']
            break
        
    return render(request, 'courses/dashboard.html', {
        'essentials': essentials,
        'specialties': specialties,
        'leigos': leigos,
        'overall_progress': overall_progress,
        'active_live_course': active_live_course
    })

@login_required
def lesson_detail(request, course_slug, lesson_order):
    """Renders visual video container, modules list sidebar, and comment feed, enrolling students automatically."""
    course = get_object_or_404(Course, slug=course_slug)
    
    # Automatically enroll student when they open the course lessons
    if request.user.role == 'STUDENT':
        student_profile = request.user.student_profile
        Enrollment.objects.get_or_create(student=student_profile, course=course)
    else:
        student_profile = None

    # Retrieve all sorted lessons
    lessons = Lesson.objects.filter(module__course=course).order_by('module__order', 'order')
    total_lessons = lessons.count()
    if total_lessons == 0:
        raise Http404("This course has no lessons yet.")
        
    # Get active lesson by order field
    lesson = lessons.filter(order=lesson_order).first()
    if not lesson:
        lesson = lessons.first()
        
    # Fetch modules accordion structure
    modules = Module.objects.filter(course=course).prefetch_related('lessons')
    
    # Progress records and checks
    completed_lesson_ids = []
    completed_count = 0
    completed_percent = 0
    
    if student_profile:
        completed_lessons = Progress.objects.filter(student=student_profile, lesson__module__course=course, is_completed=True)
        completed_lesson_ids = list(completed_lessons.values_list('lesson_id', flat=True))
        completed_count = len(completed_lesson_ids)
        completed_percent = (completed_count / total_lessons) * 100 if total_lessons > 0 else 0
        
    is_completed = lesson.id in completed_lesson_ids
    
    # Fetch community discussion posts for this course
    posts = CommunityPost.objects.filter(course=course).prefetch_related('comments__author', 'author')
    
    return render(request, 'courses/lesson_detail.html', {
        'course': course,
        'lesson': lesson,
        'modules': modules,
        'completed_lesson_ids': completed_lesson_ids,
        'completed_count': completed_count,
        'total_lessons': total_lessons,
        'completed_percent': completed_percent,
        'is_completed': is_completed,
        'posts': posts
    })

@login_required
def toggle_progress(request, lesson_id):
    """AJAX POST view toggling completion state and updating student points/level."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid HTTP request method.'}, status=400)
        
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    student_profile = request.user.student_profile
    
    # Ensure enrollment exists
    Enrollment.objects.get_or_create(student=student_profile, course=course)
        
    progress, created = Progress.objects.get_or_create(student=student_profile, lesson=lesson)
    
    if created:
        progress.is_completed = True
        progress.save()
        student_profile.points += 10
    else:
        if progress.is_completed:
            progress.is_completed = False
            progress.save()
            if student_profile.points >= 10:
                student_profile.points -= 10
        else:
            progress.is_completed = True
            progress.save()
            student_profile.points += 10
            
    # Auto rank/title updates
    student_profile.level = (student_profile.points // 50) + 1
    if student_profile.level >= 5:
        student_profile.title = "Grandmaster"
    elif student_profile.level >= 3:
        student_profile.title = "Scholar"
    else:
        student_profile.title = "Novice"
    student_profile.save()
            
    # Calculate updated overall progress percentages
    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = Progress.objects.filter(
        student=student_profile, 
        lesson__module__course=course, 
        is_completed=True
    ).count()
    
    progress_percent = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
    
    return JsonResponse({
        'status': 'success',
        'is_completed': progress.is_completed,
        'completed_count': completed_lessons,
        'total_count': total_lessons,
        'percentage': progress_percent
    })

@login_required
def issue_certificate(request, course_slug):
    """Renders a beautiful A4 print-ready certificate for completed courses."""
    course = get_object_or_404(Course, slug=course_slug)
    
    if request.user.role != 'STUDENT':
        raise Http404("Apenas alunos podem obter certificados.")
        
    student_profile = request.user.student_profile
    
    # Verify enrollment
    if not Enrollment.objects.filter(student=student_profile, course=course).exists():
        raise Http404("Você não está matriculado neste curso.")
        
    # Calculate progress
    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = Progress.objects.filter(
        student=student_profile, 
        lesson__module__course=course, 
        is_completed=True
    ).count()
    
    progress_percent = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
    
    # Requirement: progress must be 100% to issue a certificate
    if progress_percent < 100:
        return render(request, 'courses/certificate_error.html', {
            'course': course,
            'progress_percent': progress_percent
        })
        
    # Gather dates and validations
    import hashlib
    # Generate unique certificate code
    raw_hash = f"{student_profile.id}-{course.id}-{request.user.email}"
    cert_code = hashlib.md5(raw_hash.encode()).hexdigest().upper()[:12]
    
    # Creator info (signature fields)
    creator = course.creator
    
    return render(request, 'courses/certificate.html', {
        'course': course,
        'student': student_profile,
        'cert_code': cert_code,
        'creator': creator,
        'date': course.created_at.strftime('%d/%m/%Y')
    })
