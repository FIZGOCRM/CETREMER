"""Aulas ao vivo do aluno (HANDOFF-v2 7.4) e convite .ics."""
import math
from datetime import timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import Course, Enrollment, LiveSession

BRASILIA = ZoneInfo('America/Sao_Paulo')
WEEKDAYS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
ENABLED_HINT = 'A sala já está aberta. O link abre o Google Meet em uma nova aba.'


def _local(moment):
    return timezone.localtime(moment, BRASILIA)


def _hm(moment):
    return f'{_local(moment):%H}h{_local(moment):%M}'


def _plural(n, one, many):
    return f'{n} {one if n == 1 else many}'


def _utc(moment):
    return moment.astimezone(ZoneInfo('UTC')).strftime('%Y%m%dT%H%M%SZ')


def calendar_url(session):
    """Link "Adicionar ao Google Agenda" (HANDOFF-v2 7.4)."""
    params = {'action': 'TEMPLATE', 'text': f'{session.course.title} · {session.title}',
              'dates': f'{_utc(session.starts_at)}/{_utc(session.ends_at)}',
              'details': session.join_url or '', 'location': 'Google Meet'}
    return 'https://calendar.google.com/calendar/render?' + urlencode(params)


def _length(session):
    minutes = round((session.ends_at - session.starts_at).total_seconds() / 60)
    hours, rest = divmod(minutes, 60)
    return f'{hours}h{rest:02d}' if hours else f'{rest} min'


def describe(session, now):
    """Acrescenta à sessão os textos e links que a tela usa."""
    start = _local(session.starts_at)
    state = session.state(now)
    session.live_state = state
    session.wd, session.day, session.mon = WEEKDAYS[start.weekday()], start.day, MONTHS[start.month - 1]
    session.time_range = f'{_hm(session.starts_at)} às {_hm(session.ends_at)}'
    session.calendar_url = calendar_url(session)
    session.ics_url = reverse('live_session_ics', args=[session.id])
    session.enable_at = (session.starts_at - timedelta(minutes=15)).astimezone(ZoneInfo('UTC')).strftime('%Y-%m-%dT%H:%M:%SZ')
    session.length = _length(session)
    if state == 'live':
        minutes = max(0, int((now - session.starts_at).total_seconds() // 60))
        session.badge_class, session.badge = 'badge--live', '● Ao vivo agora'
        session.hint = f'Começou há {_plural(minutes, "minuto", "minutos")}. Ainda dá tempo de entrar.'
    elif state == 'soon':
        minutes = max(1, math.ceil((session.starts_at - now).total_seconds() / 60))
        session.badge_class, session.badge = 'badge--warning', f'Começa em {minutes} min'
        session.hint = ENABLED_HINT
    else:
        days = (start.date() - _local(now).date()).days
        label = f'Hoje às {_hm(session.starts_at).replace("h00", "h")}' if days == 0 else 'Amanhã' if days == 1 else f'Em {days} dias'
        session.badge_class, session.badge = 'badge--blue', label
        session.hint = ('O botão de entrar libera 15 minutos antes do início. '
                        'Você recebe um lembrete por e-mail 1 hora antes.')
    return session


@login_required
def live_classes(request):
    if request.user.role != 'STUDENT':
        return redirect('painel:dashboard')
    profile = request.user.student_profile
    now = timezone.now()
    courses = list(Course.objects.filter(enrollments__student=profile, enrollments__is_active=True)
                   .exclude(status='archived').select_related('category').order_by('title').distinct())
    course_ids = [c.id for c in courses]
    sessions = LiveSession.objects.filter(course_id__in=course_ids).select_related('course')
    has_any = sessions.exists()

    selected = next((c for c in courses if c.slug == request.GET.get('curso')), None)
    pending = [describe(s, now) for s in sessions.filter(ends_at__gte=now).order_by('starts_at')]
    next_session = pending[0] if pending else None
    upcoming = [s for s in pending if selected is None or s.course_id == selected.id][:10]

    today = timezone.localdate()
    recordings = []
    for session in sessions.filter(ends_at__lt=now).exclude(recording_url='').order_by('-starts_at'):
        until = session.recording_until or (session.starts_at + timedelta(days=30)).date()
        if until >= today:
            describe(session, now)
            session.available_until = until
            recordings.append(session)

    return render(request, 'courses/live_classes.html', {
        'has_any': has_any, 'next_session': next_session, 'upcoming': upcoming, 'recordings': recordings,
        'courses': courses, 'selected_course': selected,
        'empty_course': selected if selected and not upcoming else None,
    })


def _ics_text(value):
    return (value.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,')
            .replace('\r\n', '\\n').replace('\n', '\\n'))


def _fold(line):
    """Dobra linhas longas (RFC 5545), sem cortar no meio de um caractere."""
    chunks, current = [], ''
    for char in line:
        if len((current + char).encode('utf-8')) > 73:
            chunks.append(current)
            current = char
        else:
            current += char
    chunks.append(current)
    return '\r\n '.join(chunks)


@login_required
def live_session_ics(request, session_id):
    session = LiveSession.objects.select_related('course').filter(pk=session_id).first()
    if (session is None or request.user.role != 'STUDENT' or
            not Enrollment.objects.filter(student=request.user.student_profile, course=session.course, is_active=True).exists()):
        raise Http404
    link = session.join_url
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//CETREMER//Aulas ao vivo//PT-BR', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
             'BEGIN:VEVENT', f'UID:live-{session.id}@{request.get_host()}', f'DTSTAMP:{_utc(timezone.now())}',
             f'DTSTART:{_utc(session.starts_at)}', f'DTEND:{_utc(session.ends_at)}',
             'SUMMARY:' + _ics_text(f'{session.course.title} · {session.title}')]
    if link:
        lines += ['LOCATION:' + _ics_text(link), 'DESCRIPTION:' + _ics_text(f'Link do Google Meet: {link}')]
    lines += ['END:VEVENT', 'END:VCALENDAR']
    response = HttpResponse('\r\n'.join(_fold(line) for line in lines) + '\r\n', content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="aula-ao-vivo-{session.id}.ics"'
    return response
