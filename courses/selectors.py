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


def progress_info(student, course, lessons=None, *, enrollment=None, completed_ids=None):
    lessons = lessons if lessons is not None else ordered_lessons(course)
    done_ids = set(completed_ids) if completed_ids is not None else set(
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
    if enrollment is None:
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


def member_course_items(student):
    from collections import defaultdict
    from .access import access_decision
    from .models import Certificate, Enrollment
    from .services import plan_status, profile_data_ok
    enrollments = list(Enrollment.objects.filter(student=student).select_related('course__category').prefetch_related('access_periods', 'access_changes').order_by('-enrolled_at'))
    course_ids = [e.course_id for e in enrollments]
    lessons_by_course = defaultdict(list)
    for lesson in Lesson.objects.filter(module__course_id__in=course_ids, status='published', module__status='published').select_related('module__course').order_by('module__order', 'order', 'id'):
        lessons_by_course[lesson.module.course_id].append(lesson)
    records_by_course = defaultdict(list)
    for record in Progress.objects.filter(student=student, lesson__module__course_id__in=course_ids, lesson__status='published', lesson__module__status='published').select_related('lesson__module'):
        records_by_course[record.lesson.module.course_id].append(record)
    certificates = {cert.enrollment_id: cert for cert in Certificate.objects.filter(enrollment__student=student)}
    data_ok = profile_data_ok(student)
    items = []
    for enrollment in enrollments:
        records = records_by_course[enrollment.course_id]
        done = {r.lesson_id for r in records if r.is_completed}
        item = progress_info(student, enrollment.course, lessons_by_course[enrollment.course_id], enrollment=enrollment, completed_ids=done)
        item.update(enrollment=enrollment, access=access_decision(enrollment), plan=plan_status(enrollment),
            certificate=certificates.get(enrollment.pk), watched_seconds=sum(r.watched_seconds for r in records),
            started=any(r.is_completed or r.watched_seconds or r.last_position_seconds for r in records))
        item['certificate_ready'] = bool(item['status'] == 'done' and item['access'].allowed and data_ok and not item['certificate'])
        item['ring_offset'] = round(194.78*(1-item['pct']/100), 2)
        items.append(item)
    return items


def member_summary(student, *, on=None):
    from datetime import timedelta
    from math import ceil
    from django.urls import reverse
    from django.utils import timezone
    from .models import ActivityEvent, StudyDay
    today = on or timezone.localdate()
    items = member_course_items(student)
    days = dict(StudyDay.objects.filter(student=student, date__lte=today).values_list('date', 'seconds'))
    week_seconds = sum(days.get(today-timedelta(days=i), 0) for i in range(7))
    previous = sum(days.get(today-timedelta(days=i), 0) for i in range(7, 14))
    streak = 0
    while days.get(today-timedelta(days=streak), 0) >= 60:
        streak += 1
    max_seconds = max((days.get(today-timedelta(days=i), 0) for i in range(84)), default=0)
    heatmap = []
    for i in reversed(range(84)):
        day = today-timedelta(days=i); seconds = days.get(day, 0)
        heatmap.append({'date': day, 'seconds': seconds, 'level': ceil(seconds*4/max_seconds) if max_seconds else 0, 'today': i == 0})
    week = []
    max_minutes = max(40, max((days.get(today-timedelta(days=i), 0)/60 for i in range(7)), default=0))
    for index, offset in enumerate(reversed(range(7))):
        day = today-timedelta(days=offset); seconds = days.get(day, 0)
        height = round(seconds/60/max_minutes*140)
        week.append({'date': day, 'label': 'Hoje' if offset == 0 else ('Seg','Ter','Qua','Qui','Sex','Sáb','Dom')[day.weekday()],
            'seconds': seconds, 'minutes': round(seconds/60, 1), 'height': height or 2, 'y': 160-height if height else 158, 'x': 35+index*74, 'today': offset == 0})
    activity = list(ActivityEvent.objects.filter(student=student).select_related('lesson', 'course')[:6])
    labels = {'lesson_completed': 'Aula concluída', 'quiz_finished': 'Quiz concluído', 'final_passed': 'Avaliação aprovada', 'certificate_issued': 'Certificado emitido'}
    for event in activity:
        event.label = labels.get(event.kind, 'Atividade')
    next_steps = []
    for item in items:
        if not item['access'].allowed:
            continue
        lesson = item['next_lesson']
        if lesson and item['status'] != 'done':
            next_steps.append({'priority': 2 if item['started'] else 3, 'title': ('Continuar: '+lesson.title) if item['started'] else ('Começar '+item['course'].title),
                'detail': item['course'].title, 'url': reverse('lesson_detail', args=[item['course'].slug, lesson.pk]), 'icon': 'play'})
        elif item['status'] == 'done' and not item['certificate']:
            next_steps.append({'priority': 5, 'title': 'Emitir certificado', 'detail': item['course'].title+' · precisa de nome e CPF', 'url': reverse('certificates'), 'icon': 'award'})
        elif item['next_release']:
            next_steps.append({'priority': 6, 'title': 'Próximo módulo libera em '+item['next_release'].strftime('%d/%m'), 'detail': item['course'].title,
                'url': reverse('member_course', args=[item['course'].slug]), 'icon': 'lock'})
    next_steps.sort(key=lambda step: step['priority'])
    total = sum(item['total'] for item in items); completed = sum(item['completed'] for item in items)
    return {'items': items, 'total': total, 'completed': completed, 'remaining': total-completed,
        'week_seconds': week_seconds, 'previous_seconds': previous, 'difference_seconds': week_seconds-previous, 'difference_abs_seconds': abs(week_seconds-previous), 'streak': streak,
        'week': week, 'heatmap': heatmap, 'activity': activity, 'next_steps': next_steps[:4],
        'certificates_issued': sum(bool(item['certificate']) for item in items), 'certificates_ready': sum(item['certificate_ready'] for item in items)}
