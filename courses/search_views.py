from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse

from community.models import CommunityPost
from .models import Course, Enrollment, Lesson, LessonMaterial
from .services import course_progress

LIMIT = 5


def _shortcuts():
    return {'label': 'Atalhos', 'items': [
        {'url': reverse('live_classes'), 'icon': 'video', 'title': 'Aulas ao vivo', 'sub': ''},
        {'url': reverse('certificates'), 'icon': 'award', 'title': 'Certificados', 'sub': ''},
        {'url': reverse('settings'), 'icon': 'user', 'title': 'Minha conta', 'sub': ''},
    ]}


def _lesson_item(lesson, suffix=''):
    course = lesson.module.course
    return {'url': reverse('lesson_detail', args=[course.slug, lesson.id]) + suffix, 'icon': 'play',
            'title': lesson.title, 'sub': f'{course.title} · {lesson.module.title}'}


@login_required
def search(request):
    """Busca do Ctrl K do aluno (HANDOFF-v2 6.2). Só enxerga cursos em que a pessoa está matriculada e ativa."""
    q = request.GET.get('q', '').strip()
    student = getattr(request.user, 'student_profile', None)
    course_ids = []
    if student is not None:
        course_ids = list(Enrollment.objects.filter(student=student, is_active=True).values_list('course_id', flat=True))

    groups = []
    if not q:
        courses = list(Course.objects.filter(id__in=course_ids, status='published'))
        best = None
        for course in courses:
            info = course_progress(request.user, course)
            if info['resume_lesson'] is None:
                continue
            key = info['last_seen_at'].timestamp() if info['last_seen_at'] else 0
            if best is None or key > best[0]:
                best = (key, info['resume_lesson'])
        if best is not None:
            groups.append({'label': 'Continuar', 'items': [_lesson_item(best[1])]})
        groups.append(_shortcuts())
        return render(request, 'partials/cmdk_results.html', {'groups': groups})

    lessons = list(Lesson.objects.filter(module__course_id__in=course_ids, status='published', title__icontains=q)
                   .select_related('module__course').order_by('module__course__title', 'module__order', 'order')[:LIMIT])
    if lessons:
        groups.append({'label': 'Aulas', 'items': [_lesson_item(lesson) for lesson in lessons]})

    posts = list(CommunityPost.objects.filter(is_hidden=False, title__icontains=q)
                 .filter(Q(course_id__in=course_ids) | Q(course__isnull=True))
                 .select_related('course').order_by('-created_at')[:LIMIT])
    if posts:
        groups.append({'label': 'Dúvidas', 'items': [
            {'url': reverse('community') + f'?duvida={post.id}', 'icon': 'chat', 'title': post.title,
             'sub': post.course.title if post.course_id else 'Discussão geral'} for post in posts]})

    materials = list(LessonMaterial.objects.filter(lesson__module__course_id__in=course_ids, lesson__status='published',
                                                   lesson__deleted_at__isnull=True, title__icontains=q)
                     .select_related('lesson__module__course').order_by('title')[:LIMIT])
    if materials:
        groups.append({'label': 'Materiais', 'items': [
            {**_lesson_item(material.lesson, '?aba=materiais'), 'icon': 'file', 'title': material.title,
             'sub': f'{material.lesson.module.course.title} · {material.lesson.title}'} for material in materials]})
    return render(request, 'partials/cmdk_results.html', {'groups': groups})
