from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden

from courses.models import Course, Enrollment, Lesson
from .models import CommunityPost, Comment

@login_required
def community_hub(request):
    """Renders the centralized interactive community discussion board for students."""
    posts = CommunityPost.objects.all().prefetch_related('comments__author', 'author').select_related('course')
    
    # Fetch user's courses for posting options
    if request.user.role == 'STUDENT':
        student_profile = request.user.student_profile
        my_courses = Course.objects.filter(enrollments__student=student_profile)
    else:
        my_courses = Course.objects.all()
        
    return render(request, 'community/hub.html', {
        'posts': posts,
        'my_courses': my_courses
    })

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
    
    if title and content:
        CommunityPost.objects.create(
            course=course,
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
