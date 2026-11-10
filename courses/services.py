"""Progresso do aluno (HANDOFF-v2 6.4). Único lugar onde o progresso é calculado.

Todas as telas (Início, curso, aula, certificados, menu) usam estas funções. Só contam aulas
publicadas e não excluídas (Lesson.objects já esconde as excluídas).
"""
from django.urls import reverse

from .models import Lesson, Progress


def ordered_lessons(course):
    """Aulas publicadas do curso, na ordem de exibição: módulo, aula, id."""
    return list(Lesson.objects.filter(module__course=course, status='published')
                .select_related('module').order_by('module__order', 'module_id', 'order', 'id'))


def _student(user):
    return getattr(user, 'student_profile', None) if getattr(user, 'is_authenticated', False) else None


def completed_lesson_ids(user, course_ids):
    """Conjunto de ids de aulas publicadas já concluídas nos cursos informados."""
    student = _student(user)
    if student is None or not course_ids:
        return set()
    return set(Progress.objects.filter(
        student=student, is_completed=True, lesson__module__course_id__in=list(course_ids),
        lesson__status='published', lesson__deleted_at__isnull=True,
    ).values_list('lesson_id', flat=True))


def build_progress(lessons, records):
    """Resumo do progresso a partir das aulas (ordenadas) e dos registros {lesson_id: Progress}.

    Também serve às telas que calculam vários cursos de uma vez (Início), sem uma consulta por curso.
    """
    total = len(lessons)
    done_ids = {lesson_id for lesson_id, record in records.items() if record.is_completed}
    done = len(done_ids)
    pending = [lesson for lesson in lessons if lesson.id not in done_ids]
    resume_lesson = None
    resume_seconds = 0
    started = [r for r in records.values() if not r.is_completed]
    if started:
        latest = max(started, key=lambda r: r.updated_at)
        resume_lesson = next((lesson for lesson in lessons if lesson.id == latest.lesson_id), None)
        resume_seconds = latest.position_seconds
    if resume_lesson is None and pending:
        resume_lesson = pending[0]
        resume_seconds = 0
    last_seen = max((r.updated_at for r in records.values()), default=None)
    return {
        'done': done, 'total': total, 'pct': round(100 * done / total) if total else 0,
        'remaining': total - done, 'next_lesson': pending[0] if pending else None,
        'resume_lesson': resume_lesson, 'resume_seconds': resume_seconds, 'last_seen_at': last_seen,
    }


def course_progress(user, course):
    """Resumo do progresso: done, total, pct, remaining, next_lesson, resume_lesson, resume_seconds, last_seen_at."""
    lessons = ordered_lessons(course)
    student = _student(user)
    records = {}
    if student is not None and lessons:
        records = {r.lesson_id: r for r in Progress.objects.filter(student=student, lesson__in=lessons)}
    return build_progress(lessons, records)


def lesson_payload(user, lesson):
    """JSON de toggle_progress e complete_lesson (HANDOFF-v2 6.4)."""
    course = lesson.module.course
    lessons = ordered_lessons(course)
    student = _student(user)
    done_ids = completed_lesson_ids(user, [course.id]) if student else set()
    total = len(lessons)
    done = len(done_ids)
    module_lessons = [item for item in lessons if item.module_id == lesson.module_id]
    index = next((i for i, item in enumerate(lessons) if item.id == lesson.id), None)
    following = lessons[index + 1] if index is not None and index + 1 < len(lessons) else None
    return {
        'is_completed': lesson.id in done_ids,
        'completed_count': done,
        'total_count': total,
        'percentage': round(100 * done / total, 1) if total else 0,
        'module': {'id': lesson.module_id, 'done': sum(item.id in done_ids for item in module_lessons),
                   'total': len(module_lessons)},
        'remaining': total - done,
        'course_done': bool(total) and done == total,
        'next': {'url': reverse('lesson_detail', args=[course.slug, following.id]), 'title': following.title}
                if following else None,
        'certificate_url': reverse('certificates') + '?emitir=' + course.slug,
    }
