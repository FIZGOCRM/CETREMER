from datetime import timedelta
from datetime import date

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.decorators import painel_required
from courses.engagement_services import save_weekly_selection
from courses.models import Course, WeeklySelection
from painel.analytics_forms import WeekForm, WeeklySelectionForm
from painel.reporting import lesson_metrics
from .common import page


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
    rows.sort(key=lambda row: (-row["started"], -(row["avg_pct"] or 0), row["lesson"].title, row["lesson"].pk))
    selections = WeeklySelection.objects.filter(course=course)
    selection = selections.filter(week_start=week).first() if week else None
    initial = {'semana': week}
    if selection:
        for item in selection.items.all():
            initial[f'lesson_{item.position}'] = item.lesson_id
            initial[f'art_{item.position}'] = item.artwork
    form = WeeklySelectionForm(
        request.POST if request.method == 'POST' else None, request.FILES or None, initial=initial, rows=rows,
    )
    if request.method == 'POST' and form.is_valid():
        try:
            positions = form.cleaned_data['positions']
            artwork = {}
            for pos, lesson in positions.items():
                if f'art_{pos}' in request.FILES:
                    artwork[lesson] = form.cleaned_data[f'art_{pos}']
                elif request.POST.get(f'art_{pos}-clear'):
                    artwork[lesson] = False
            save_weekly_selection(course, week, positions, actor=request.user, artwork=artwork)
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Top 10 salvo.')
            url = reverse('painel:weekly_selection', args=[course.pk])
            return redirect(f'{url}?semana={week.isoformat()}')
    posters = {item.lesson_id: item.artwork.url for item in selection.items.all() if item.artwork} if selection else {}
    ranking_data = []
    for row in rows:
        lesson = row['lesson']
        cover = lesson.cover or course.cover_image
        ranking_data.append({'id': str(lesson.pk), 'title': lesson.title, 'module': lesson.module.title,
                             'started': row['started'], 'average': round(row['avg_pct']) if row['avg_pct'] is not None else None,
                             'art': posters.get(lesson.pk, ''), 'cover': cover.url if cover else ''})
    slots = [(position, form[f'lesson_{position}'], form[f'art_{position}']) for position in range(1, 11)]
    return page(request, 'weekly_selection', course=course, week=week, week_form=week_form,
                previous_week=week - timedelta(days=7) if week and week.toordinal() > 7 else None,
                next_week=week + timedelta(days=7) if week and week.toordinal() <= date.max.toordinal() - 7 else None,
                week_end=week + timedelta(days=min(6, date.max.toordinal() - week.toordinal())) if week else None,
                form=form, rows=rows, slots=slots, ranking_data=ranking_data,
                history=selections.annotate(total=Count('items')).order_by('-week_start'))
