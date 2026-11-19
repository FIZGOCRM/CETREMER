from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, F
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.decorators import painel_required
from courses.models import Course, Lesson, WeeklySelection, WeeklySelectionItem
from painel.analytics_forms import WeekForm, WeeklySelectionForm
from painel.reporting import lesson_metrics
from .common import page


@transaction.atomic
def _save_selection(course, week, positions, actor):
    # Reserve the course before reading existing slots, including on SQLite.
    Course.objects.filter(pk=course.pk).update(title=F('title'))
    selected = set(positions.values())
    lessons = Lesson.objects.select_for_update().filter(module__course=course, pk__in=selected)
    if selected != set(lessons.values_list('pk', flat=True)):
        raise ValidationError('Uma das aulas já não está neste curso. Revise a seleção.')
    selection, _ = WeeklySelection.objects.get_or_create(
        course=course, week_start=week, defaults={'created_by': actor},
    )
    selection.items.all().delete()
    WeeklySelectionItem.objects.bulk_create([
        WeeklySelectionItem(selection=selection, lesson_id=lesson_id, position=position)
        for position, lesson_id in positions.items()
    ])


@painel_required
@require_http_methods(['GET', 'POST'])
def weekly_selection(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday())
    date_data = request.POST if request.method == 'POST' else request.GET
    week_form = WeekForm({'semana': date_data.get('semana', monday)})
    week = week_form.cleaned_data['semana'] if week_form.is_valid() else None
    rows = lesson_metrics(course=course, order='-started')
    selections = WeeklySelection.objects.filter(course=course)
    selection = selections.filter(week_start=week).first() if week else None
    initial = {'semana': week}
    if selection:
        initial.update({f'lesson_{position}': lesson_id for position, lesson_id
                        in selection.items.values_list('position', 'lesson_id')})
    form = WeeklySelectionForm(
        request.POST if request.method == 'POST' else None, initial=initial, rows=rows,
    )
    if request.method == 'POST' and form.is_valid():
        try:
            _save_selection(course, week, form.cleaned_data['positions'], request.user)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Seleção da semana salva.')
            url = reverse('painel:weekly_selection', args=[course.pk])
            return redirect(f'{url}?semana={week.isoformat()}')
    return page(request, 'weekly_selection', course=course, week=week, week_form=week_form,
                form=form, rows=rows, history=selections.annotate(total=Count('items')).order_by('-week_start'))
