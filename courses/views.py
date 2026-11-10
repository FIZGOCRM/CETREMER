from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from datetime import timedelta

from django.http import Http404, JsonResponse
from django.utils import timezone
import json

from .models import Course, CourseSlugRedirect, Module, Lesson, Progress, Enrollment
from .home_views import active_enrollment
from community.models import CommunityPost

def landing(request):
    """Lists published courses on landing page, checking enrollment details if logged in."""
    courses = Course.objects.filter(status='published').select_related('creator__user', 'category')
    from .models import Category
    
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
        , 'categories': Category.objects.all()
    })

def course_preview(request, course_slug):
    """Renders the public Udemy-style course landing/preview page with syllabus and buy options."""
    course = Course.objects.filter(slug=course_slug).first()
    if course is None:
        # Endereço antigo: redireciona por 90 dias depois que o curso mudou de endereço (HANDOFF-v2 8.5).
        moved = CourseSlugRedirect.objects.filter(old_slug=course_slug, created_at__gte=timezone.now() - timedelta(days=90)).select_related('course').first()
        if moved is None:
            raise Http404
        return redirect('course_preview', course_slug=moved.course.slug, permanent=True)
    if request.user.is_authenticated and request.GET.get('preview') != '1' and active_enrollment(request.user, course):
        return redirect('course_home', course_slug=course.slug)

    is_enrolled = False
    if request.user.is_authenticated:
        if request.user.role == 'STUDENT':
            student_profile = request.user.student_profile
            is_enrolled = Enrollment.objects.filter(student=student_profile, course=course).exists()
            
    modules = Module.objects.filter(course=course).prefetch_related(Prefetch('lessons', queryset=Lesson.objects.filter(status='published')))
    total_lessons = Lesson.objects.filter(status='published', module__course=course).count()
    first_lesson = Lesson.objects.filter(status='published', module__course=course).order_by('module__order', 'order', 'id').first()
    from .student_views import ordered_lessons, progress_info
    lessons = ordered_lessons(course)
    next_lesson = first_lesson
    if is_enrolled:
        next_lesson = progress_info(request.user.student_profile, course, lessons)['next_lesson']
    
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
        'is_enrolled': is_enrolled,
        'first_lesson': first_lesson
        , 'next_lesson': next_lesson,
        'total_seconds': total_seconds,
        'has_materials': Lesson.objects.filter(status='published', module__course=course, materials__isnull=False).exists(),
    })

@login_required
def dashboard(request):
    """Displays student library displaying all courses in Netflix sliders with locked/unlocked state."""
    if request.user.role != 'STUDENT':
        return render(request, 'courses/dashboard.html', {'essentials': [], 'specialties': [], 'leigos': []})
        
    student_profile = request.user.student_profile
    enrollments_qs = Enrollment.objects.filter(student=student_profile)
    enrolled_course_ids = set(enrollments_qs.values_list('course_id', flat=True))
    
    all_courses = Course.objects.filter(status='published').select_related('creator__user', 'category')
    
    essentials = []
    specialties = []
    leigos = []
    
    for course in all_courses:
        is_locked = course.id not in enrolled_course_ids
        total_lessons = Lesson.objects.filter(status='published', module__course=course).count()
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
            'first_lesson': Lesson.objects.filter(status='published', module__course=course).order_by('module__order', 'order', 'id').first(),
            'is_locked': is_locked,
            'total_lessons_count': total_lessons,
            'completed_lessons_count': completed_lessons,
            'progress_percent': progress_percent
        }
        
        # Keep the legacy dashboard groups until the phase 3 template is replaced.
        if course.category and course.category.slug == 'essenciais-aha':
            essentials.append(item)
        elif course.category and course.category.slug == 'especialidades-medicas':
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
        'active_live_course': active_live_course,
        'spotlight_lesson': Lesson.objects.filter(status='published', module__course__slug='plantao-sem-gpt').order_by('module__order', 'order', 'id').first()
    })

@login_required
def lesson_detail(request, course_slug, lesson_id):
    """Renders an enrolled student's lesson by its stable ID."""
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    if request.user.role != 'STUDENT':
        return redirect('course_preview', course_slug=course.slug)
    student_profile = request.user.student_profile
    if not Enrollment.objects.filter(student=student_profile, course=course).exists():
        return redirect('course_preview', course_slug=course.slug)

    # Retrieve all sorted lessons
    lessons = Lesson.objects.filter(status='published', module__course=course).order_by('module__order', 'order')
    total_lessons = lessons.count()

        
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
def issue_certificate(request, course_slug):
    """Renders a beautiful A4 print-ready certificate for completed courses."""
    course = get_object_or_404(Course, slug=course_slug)
    
    if request.user.role != 'STUDENT':
        return redirect('course_preview', course_slug=course.slug)
        
    student_profile = request.user.student_profile
    
    # Verify enrollment
    if not Enrollment.objects.filter(student=student_profile, course=course).exists():
        return redirect('course_preview', course_slug=course.slug)
        
    # Calculate progress
    total_lessons = Lesson.objects.filter(status='published', module__course=course).count()
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
            'first_lesson': Lesson.objects.filter(status='published', module__course=course).order_by('module__order', 'order', 'id').first(),
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
