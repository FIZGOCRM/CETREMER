import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from community.models import CommunityPost
from community.questions import lesson_questions
from core.activity import log_completed_lesson
from core.toasts import toast
from users.models import Notification
from users.notify import notify
from .models import Certificate, Course, Enrollment, Lesson, Module, Progress
from .services import completed_lesson_ids, course_progress, lesson_payload, ordered_lessons


def progress_info(student, course, lessons=None):
    lessons = lessons if lessons is not None else ordered_lessons(course)
    done_ids = set(Progress.objects.filter(student=student, lesson__in=lessons, is_completed=True).values_list('lesson_id', flat=True))
    total = len(lessons)
    done = len(done_ids)
    next_lesson = next((lesson for lesson in lessons if lesson.id not in done_ids), lessons[-1] if lessons else None)
    return {'course': course, 'pct': round(100 * done / total) if total else 0, 'completed': done, 'total': total,
            'next_lesson': next_lesson, 'status': 'done' if total and done == total else 'in_progress' if done else 'not_started'}


logger = logging.getLogger(__name__)
ABAS = ('sobre', 'materiais', 'duvidas', 'aulas')


@login_required
def lesson_detail(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    if request.user.role != 'STUDENT':
        return redirect('course_preview', course_slug=course.slug)
    student = request.user.student_profile
    enrollment = Enrollment.objects.filter(student=student, course=course, is_active=True).first()
    if not enrollment:
        return redirect('course_preview', course_slug=course.slug)
    if lesson.status != 'published':
        raise Http404
    if not lesson.module.is_released_for(enrollment):
        released_on = lesson.module.release_on(enrollment)
        toast(request, f'Este módulo libera em {released_on:%d/%m}.', level='info')
        return redirect('course_home', course_slug=course.slug)

    enrollment.last_accessed_at = timezone.now()
    enrollment.save(update_fields=['last_accessed_at'])
    progress, _ = Progress.objects.get_or_create(student=student, lesson=lesson)

    lessons = ordered_lessons(course)
    completed_ids = completed_lesson_ids(request.user, [course.id])
    total = len(lessons)
    done = len(completed_ids)
    pct = round(100 * done / total) if total else 0
    for position, item in enumerate(lessons, 1):
        item.position = position
    by_id = {item.id: item for item in lessons}
    modules = []
    for module in Module.objects.filter(course=course).prefetch_related('lessons'):
        module.lessons_list = [by_id[item.id] for item in module.lessons.all() if item.id in by_id]
        if not module.lessons_list:
            continue
        module.lessons_list.sort(key=lambda item: item.position)
        module.total_count = len(module.lessons_list)
        module.done_count = sum(item.id in completed_ids for item in module.lessons_list)
        modules.append(module)
    index = next(i for i, item in enumerate(lessons) if item.id == lesson.id)
    module_index = next((i for i, module in enumerate(modules, 1) if module.id == lesson.module_id), 1)
    aba = request.GET.get('aba') if request.GET.get('aba') in ABAS else 'sobre'
    remaining = total - done
    if not (lesson.vimeo_id or lesson.youtube_embed_url):
        logger.warning('Aula %s (%s) aberta sem vídeo disponível', lesson.id, course.slug)
    return render(request, 'courses/lesson_detail.html', {
        'course': course, 'lesson': lesson, 'modules': modules, 'module_index': module_index,
        'completed_ids': completed_ids, 'completed_count': done, 'total': total, 'remaining': remaining,
        'pct': pct, 'total_seconds': sum(item.duration_seconds for item in lessons),
        'prev_lesson': lessons[index - 1] if index else None,
        'next_lesson_nav': lessons[index + 1] if index + 1 < len(lessons) else None,
        'is_last': index + 1 == len(lessons),
        'lesson_index': index + 1, 'is_completed': lesson.id in completed_ids,
        'resume_seconds': progress.position_seconds, 'aba': aba,
        'cert': {'remaining': remaining, 'ready': bool(total) and remaining == 0},
        'course_done': bool(total) and remaining == 0,
        'data_ok': bool(student.full_name and student.cpf),
        'materials': lesson.materials.all(), 'posts': lesson_questions(lesson),
        'completed_lesson_ids': completed_ids, 'total_lessons': total, 'completed_percent': pct,
    })


def _progress_target(request, lesson_id):
    """Aula publicada do aluno com matrícula ativa, ou a resposta de erro que a view deve devolver."""
    lesson = get_object_or_404(Lesson, id=lesson_id, status='published')
    if request.user.role != 'STUDENT':
        return None, None, JsonResponse({'error': 'Acesso negado.'}, status=403)
    student = request.user.student_profile
    if not Enrollment.objects.filter(student=student, course=lesson.module.course, is_active=True).exists():
        return None, None, JsonResponse({'error': 'Matrícula necessária.'}, status=403)
    return lesson, student, None


def _log_completed(user, lesson):
    course = lesson.module.course
    ids = [item.id for item in ordered_lessons(course)]
    position = ids.index(lesson.id) + 1 if lesson.id in ids else lesson.order
    log_completed_lesson(user, course, position)


def _course_done(user, course):
    info = course_progress(user, course)
    return bool(info['total']) and info['done'] == info['total']


def _announce_certificate(request, course, was_done):
    """Ao concluir o curso pela primeira vez, avisa que o certificado está pronto (HANDOFF-v2 6.1)."""
    if was_done or not course.certificate_enabled or not _course_done(request.user, course):
        return
    if Certificate.objects.filter(enrollment__student=request.user.student_profile, enrollment__course=course).exists():
        return
    url = reverse('certificates') + '?emitir=' + course.slug
    if Notification.objects.filter(user=request.user, kind='certificate', url=url).exists():
        return
    notify(request.user, 'certificate', 'Seu certificado está pronto para emitir',
           f'{course.title} · confira nome e CPF', url, request=request)


@login_required
@require_POST
def complete_lesson(request, lesson_id):
    lesson, student, error = _progress_target(request, lesson_id)
    if error:
        return error
    course = lesson.module.course
    was_done = _course_done(request.user, course)
    progress, _ = Progress.objects.get_or_create(student=student, lesson=lesson)
    if not progress.is_completed:
        progress.is_completed = True
        progress.save(update_fields=['is_completed', 'completed_at', 'updated_at'])
        _log_completed(request.user, lesson)
    _announce_certificate(request, course, was_done)
    return JsonResponse(lesson_payload(request.user, lesson))


@login_required
@require_POST
def toggle_progress(request, lesson_id):
    """Marca ou desmarca a aula. Os pontos do aluno continuam sendo gravados, mas nenhuma tela v2 os mostra."""
    lesson, student, error = _progress_target(request, lesson_id)
    if error:
        return error
    course = lesson.module.course
    was_done = _course_done(request.user, course)
    progress, created = Progress.objects.get_or_create(student=student, lesson=lesson)
    progress.is_completed = True if created else not progress.is_completed
    progress.save(update_fields=['is_completed', 'completed_at', 'updated_at'])
    if progress.is_completed:
        _log_completed(request.user, lesson)
        student.points += 10
    else:
        student.points = max(0, student.points - 10)
    student.level = student.points // 50 + 1
    student.title = 'Grandmaster' if student.level >= 5 else 'Scholar' if student.level >= 3 else 'Novice'
    student.save(update_fields=['points', 'level', 'title'])
    _announce_certificate(request, course, was_done)
    return JsonResponse({'status': 'success', **lesson_payload(request.user, lesson)})


@login_required
@require_POST
def save_position(request, lesson_id):
    """Guarda até onde o aluno assistiu (aceita sendBeacon). Não altera a conclusão."""
    lesson, student, error = _progress_target(request, lesson_id)
    if error:
        return error
    try:
        seconds = int(request.POST.get('seconds', ''))
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'Posição inválida.'}, status=400)
    progress, _ = Progress.objects.get_or_create(student=student, lesson=lesson)
    progress.position_seconds = max(0, min(seconds, 86400))
    progress.save(update_fields=['position_seconds', 'updated_at'])
    return JsonResponse({'ok': True})
