from django.db import transaction


@transaction.atomic
def set_lesson_reaction(student, lesson, kind, active):
    from .access import require_lesson_access
    from .models import LessonLike, SavedLesson

    model = {"like": LessonLike, "saved": SavedLesson}[kind]
    require_lesson_access(student, lesson)
    if active:
        model.objects.get_or_create(student=student, lesson=lesson)
    else:
        model.objects.filter(student=student, lesson=lesson).delete()
    return active
