from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from .access import accessible_courses
from .models import LiveEvent,LiveReminder
from .live_services import room_available


def student_events(student):
    ids=list(accessible_courses(student).values_list('pk',flat=True))
    if not ids:return LiveEvent.objects.none()
    return LiveEvent.objects.filter(Q(course_id__in=ids)|Q(course__isnull=True),is_active=True).select_related('course')


def live_agenda(student, *, course=None):
    now=timezone.now();upcoming=[];past=[]
    reminded=set(LiveReminder.objects.filter(student=student).values_list('event_id',flat=True))
    events = student_events(student)
    if course is not None:
        events = events.filter(Q(course=course) | Q(course__isnull=True))
    for event in events:
        event.reminded=event.pk in reminded;event.room_available=room_available(event,at=now);event.can_remind=event.starts_at>now
        if event.starts_at+timedelta(minutes=event.duration_minutes)>=now:upcoming.append(event)
        else:past.append(event)
    return upcoming,list(reversed(past))
