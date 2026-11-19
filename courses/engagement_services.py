from collections.abc import Mapping
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from .models import Course, Lesson, WeeklySelection, WeeklySelectionItem
from .services import _plan_actor


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


@transaction.atomic
def save_weekly_selection(course, week_start, positions, *, actor, artwork=None):
    """Replace one course's weekly slots, preserving all other weeks."""
    _plan_actor(actor)
    if type(week_start) is not date or week_start.weekday() != 0:
        raise ValidationError('Escolha a segunda-feira da semana desejada.')
    if not isinstance(positions, Mapping) or any(type(slot) is not int or not 1 <= slot <= 10 for slot in positions):
        raise ValidationError('Use posições de 1 a 10.')
    if any(type(pk) is not int or not 1 <= pk <= 2**63 - 1 for pk in positions.values()):
        raise ValidationError('Informe identificadores de aula válidos.')
    selected = set(positions.values())
    if len(selected) != len(positions):
        raise ValidationError('Cada aula pode ocupar apenas uma posição.')

    # Reserve the course before reading existing slots, including on SQLite.
    Course.objects.filter(pk=course.pk).update(title=F('title'))
    lessons = Lesson.objects.select_for_update().filter(module__course=course, pk__in=selected)
    if selected != set(lessons.values_list('pk', flat=True)):
        raise ValidationError('Uma das aulas já não está neste curso. Revise a seleção.')
    selection, _ = WeeklySelection.objects.get_or_create(
        course=course, week_start=week_start, defaults={'created_by': actor},
    )
    covers = dict(selection.items.values_list('lesson_id', 'artwork'))
    covers.update(artwork or {})
    selection.items.all().delete()
    WeeklySelectionItem.objects.bulk_create([
        WeeklySelectionItem(selection=selection, lesson_id=lesson_id, position=position, artwork=covers.get(lesson_id) or '')
        for position, lesson_id in positions.items()
    ])
    return selection
