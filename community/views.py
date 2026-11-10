from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.db.models import Q, Count

from courses.models import Course, Enrollment, Lesson
from .models import CommunityPost, Comment

@login_required
def community_hub(request):
    if request.user.role == 'STUDENT':
        my_courses = Course.objects.filter(enrollments__student=request.user.student_profile)
    else:
        my_courses = Course.objects.all()
    posts = CommunityPost.objects.filter(is_hidden=False).filter(
        Q(course__isnull=True) | Q(course__in=my_courses)
    ).select_related('author__student_profile', 'course__category', 'lesson').annotate(comments_count=Count('comments'))
    current_filter = request.GET.get('curso', 'geral')
    if current_filter == 'geral':
        posts = posts.filter(course__isnull=True)
    elif current_filter != 'todos':
        posts = posts.filter(course__slug=current_filter)
    for post in posts:
        try:
            post.author_display = post.author.student_profile.full_name or post.author.email.split('@')[0]
        except Exception:
            post.author_display = post.author.email.split('@')[0] or post.author.username
        if post.lesson_id:
            lesson_ids = list(Lesson.objects.filter(module__course=post.course).order_by('module__order', 'order', 'id').values_list('id', flat=True))
            post.lesson_position = lesson_ids.index(post.lesson_id) + 1 if post.lesson_id in lesson_ids else None
    return render(request, 'community/hub.html', {'posts': posts, 'my_courses': my_courses, 'current_filter': current_filter})

@login_required
@require_POST
def create_hub_post(request):
    """Processes creation of a new thread from the centralized community board."""
    title = request.POST.get('title')
    content = request.POST.get('content')
    course_id = request.POST.get('course_id')
    
    course = None
    if course_id and course_id != 'general':
        course = get_object_or_404(Course, id=course_id)
        if request.user.role == 'STUDENT' and not Enrollment.objects.filter(
            student=request.user.student_profile, course=course
        ).exists():
            return HttpResponseForbidden('Matrícula necessária para publicar neste curso.')
        
    if title and content:
        CommunityPost.objects.create(
            course=course,
            author=request.user,
            title=title,
            content=content
        )
        
    return redirect('community_hub')

@login_required
@require_POST
def create_post(request, course_slug):
    """Creates a new top-level community post inside a course context."""
    course = get_object_or_404(Course, slug=course_slug)
    if request.user.role == 'STUDENT' and not Enrollment.objects.filter(
        student=request.user.student_profile, course=course
    ).exists():
        return HttpResponseForbidden('Matrícula necessária para publicar neste curso.')
    title = request.POST.get('title')
    content = request.POST.get('content')
    lesson_id = request.POST.get('lesson_id')
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course) if lesson_id else None
    if lesson and not title and content:
        title = content[:100]
    
    if title and content:
        CommunityPost.objects.create(
            course=course,
            lesson=lesson,
            author=request.user,
            title=title,
            content=content
        )
        
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    first_lesson = Lesson.objects.filter(module__course=course).order_by('module__order', 'order', 'id').first()
    if first_lesson:
        return redirect('lesson_detail', course_slug=course.slug, lesson_id=first_lesson.id)
    return redirect('course_preview', course_slug=course.slug)

@login_required
@require_POST
def create_comment(request, post_id):
    """Appends a reply comment to an existing community discussion post."""
    post = get_object_or_404(CommunityPost, id=post_id)
    if post.course_id and request.user.role == 'STUDENT' and not Enrollment.objects.filter(
        student=request.user.student_profile, course_id=post.course_id
    ).exists():
        return HttpResponseForbidden('Matrícula necessária para comentar neste curso.')
    content = request.POST.get('content')
    
    if content:
        Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )
        
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('community_hub')
