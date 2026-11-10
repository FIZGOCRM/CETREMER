from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from community.models import CommunityPost
from .models import Course, Enrollment, Lesson, Module, Progress


def ordered_lessons(course):
    return list(Lesson.objects.filter(module__course=course).order_by('module__order', 'order', 'id'))


def progress_info(student, course, lessons=None):
    lessons = lessons if lessons is not None else ordered_lessons(course)
    done_ids = set(Progress.objects.filter(student=student, lesson__in=lessons, is_completed=True).values_list('lesson_id', flat=True))
    total = len(lessons)
    done = len(done_ids)
    next_lesson = next((lesson for lesson in lessons if lesson.id not in done_ids), lessons[-1] if lessons else None)
    return {'course': course, 'pct': round(100 * done / total) if total else 0, 'completed': done, 'total': total,
            'next_lesson': next_lesson, 'status': 'done' if total and done == total else 'in_progress' if done else 'not_started'}


@login_required
def dashboard(request):
    if request.user.role != 'STUDENT':
        return redirect('painel:dashboard')
    student = request.user.student_profile
    enrollments = list(Enrollment.objects.filter(student=student).select_related('course__category').order_by('-enrolled_at'))
    items = [progress_info(student, enrollment.course) for enrollment in enrollments]
    for item, enrollment in zip(items, enrollments):
        item['enrollment'] = enrollment
    continuing = [item for item in items if item['status'] != 'done' and item['next_lesson']]
    continuing.sort(key=lambda item: item['enrollment'].last_accessed_at or item['enrollment'].enrolled_at, reverse=True)
    live_item = next((item for item in items if item['course'].live_meet_url), None)
    other_courses = Course.objects.filter(is_published=True).exclude(id__in=[e.course_id for e in enrollments]).select_related('category')
    return render(request, 'courses/dashboard.html', {'continue_item': continuing[0] if continuing else None,
        'my_courses': items, 'live_item': live_item, 'other_courses': other_courses})


@login_required
def lesson_detail(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    if request.user.role != 'STUDENT':
        return redirect('course_preview', course_slug=course.slug)
    student = request.user.student_profile
    enrollment = Enrollment.objects.filter(student=student, course=course).first()
    if not enrollment:
        return redirect('course_preview', course_slug=course.slug)
    enrollment.last_accessed_at = timezone.now()
    enrollment.save(update_fields=['last_accessed_at'])
    lessons = ordered_lessons(course)
    info = progress_info(student, course, lessons)
    completed_ids = set(Progress.objects.filter(student=student, lesson__in=lessons, is_completed=True).values_list('lesson_id', flat=True))
    modules = list(Module.objects.filter(course=course).prefetch_related('lessons'))
    for position, item in enumerate(lessons, 1):
        item.position = position
    by_id = {item.id: item for item in lessons}
    for module in modules:
        module.lessons_list = [by_id[item.id] for item in module.lessons.all() if item.id in by_id]
        module.total_count = len(module.lessons_list)
        module.done_count = sum(item.id in completed_ids for item in module.lessons_list)
    index = next(i for i, item in enumerate(lessons) if item.id == lesson.id)
    posts = CommunityPost.objects.filter(lesson=lesson, is_hidden=False).select_related('author', 'course').prefetch_related('comments')
    return render(request, 'courses/lesson_detail.html', {'course': course, 'lesson': lesson,
        'modules': modules, 'completed_ids': completed_ids, 'completed_count': info['completed'],
        'total': info['total'], 'remaining': info['total'] - info['completed'], 'pct': info['pct'], 'total_seconds': sum(item.duration_seconds for item in lessons),
        'prev_lesson': lessons[index-1] if index else None,
        'next_lesson_nav': lessons[index+1] if index + 1 < len(lessons) else None,
        'lesson_index': index+1, 'is_completed': lesson.id in completed_ids,
        'materials': lesson.materials.all(), 'posts': posts,
        'completed_lesson_ids': completed_ids, 'total_lessons': info['total'],
        'completed_percent': info['pct']})


@login_required
@require_POST
def complete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Acesso negado.'}, status=403)
    student = request.user.student_profile
    if not Enrollment.objects.filter(student=student, course=lesson.module.course).exists():
        return JsonResponse({'error': 'Matrícula necessária.'}, status=403)
    progress, _ = Progress.objects.get_or_create(student=student, lesson=lesson)
    if not progress.is_completed:
        progress.is_completed = True
        progress.save(update_fields=['is_completed', 'completed_at'])
    info = progress_info(student, lesson.module.course)
    return JsonResponse({'is_completed': True, 'completed_count': info['completed'], 'total_count': info['total'], 'percentage': info['pct']})


@login_required
def live_classes(request):
    if request.user.role != 'STUDENT':
        return redirect('painel:dashboard')
    courses = Course.objects.filter(enrollments__student=request.user.student_profile).select_related('category')
    return render(request, 'courses/live_classes.html', {
        'live_courses': [c for c in courses if c.live_meet_url or c.live_calendar_url],
        'other_enrolled': [c for c in courses if not c.live_meet_url and not c.live_calendar_url]})
