"""Read-only queries shared by student, certificate and management views."""

from .models import Lesson, Progress


def ordered_lessons(course):
    return list(
        Lesson.objects.filter(module__course=course).order_by(
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
    next_lesson = next(
        (lesson for lesson in lessons if lesson.id not in done_ids),
        lessons[-1] if lessons else None,
    )
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
    }
