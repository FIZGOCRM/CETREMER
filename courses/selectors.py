"""Read-only queries shared by student, certificate and management views."""

from .models import Lesson, Progress


def course_modules(enrollment):
    from django.db.models import Prefetch
    from .models import Module
    from .access import lesson_availability, module_release_date
    done = set(Progress.objects.filter(student=enrollment.student, lesson__module__course=enrollment.course, is_completed=True).values_list('lesson_id', flat=True))
    modules = list(Module.objects.filter(course=enrollment.course, status='published').prefetch_related(Prefetch('lessons', queryset=Lesson.objects.filter(status='published').select_related('module__course').prefetch_related('materials'))))
    for module in modules:
        module.release_date = module_release_date(enrollment, module)
        for lesson in module.lessons.all():
            lesson.availability = lesson_availability(enrollment, lesson, completed_ids=done)
    return modules


def ordered_lessons(course):
    return list(
        Lesson.objects.filter(module__course=course, status='published', module__status='published').select_related('module__course').order_by(
            "module__order", "order", "id"
        )
    )


def progress_info(student, course, lessons=None):
    lessons = lessons if lessons is not None else ordered_lessons(course)
    done_ids = set(
        Progress.objects.filter(
            student=student,
            lesson__in=lessons,
            is_completed=True,
        ).values_list("lesson_id", flat=True)
    )
    total = len(lessons)
    completed = len(done_ids)
    from .access import lesson_availability
    from .models import Enrollment
    enrollment = Enrollment.objects.filter(student=student, course=course).prefetch_related('access_periods').first()
    availability = {lesson.pk: lesson_availability(enrollment, lesson, completed_ids=done_ids) for lesson in lessons}
    available = [lesson for lesson in lessons if availability[lesson.pk].state == 'available']
    next_lesson = next((lesson for lesson in available if lesson.id not in done_ids), available[-1] if available and completed == total else None)
    scheduled = [a.release_date for a in availability.values() if a.state == 'scheduled' and a.release_date]
    status = "not_started"
    if total and completed == total:
        status = "done"
    elif completed:
        status = "in_progress"
    return {
        "course": course,
        "pct": round(100 * completed / total) if total else 0,
        "completed": completed,
        "total": total,
        "next_lesson": next_lesson,
        "status": status,
        'next_release': min(scheduled) if scheduled else None,
    }
