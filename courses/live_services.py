from datetime import timedelta
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction
from django.utils import timezone
from community.access import is_team
from .access import accessible_courses
from .models import LiveReminder


def require_event_access(user,event):
    if not event.is_active:raise PermissionDenied('Encontro indisponível.')
    if is_team(user):return
    if user.role!='STUDENT':raise PermissionDenied
    courses=accessible_courses(user.student_profile)
    if not (courses.filter(pk=event.course_id).exists() if event.course_id else courses.exists()):
        raise PermissionDenied('Seu plano não permite acessar este encontro.')


def room_available(event,*,at=None):
    at=at or timezone.now()
    return bool(event.room_url and event.starts_at-timedelta(minutes=10)<=at<=event.starts_at+timedelta(minutes=event.duration_minutes))

@transaction.atomic
def toggle_reminder(user,event):
    require_event_access(user,event)
    if user.role!='STUDENT':raise PermissionDenied
    if event.starts_at<=timezone.now():raise ValidationError('O encontro já começou.')
    reminder,created=LiveReminder.objects.get_or_create(student=user.student_profile,event=event)
    if not created:reminder.delete()
    return created


def save_event(user,event):
    if not is_team(user):raise PermissionDenied
    event.full_clean();event.save();return event


def remove_event(user,event):
    if not is_team(user):raise PermissionDenied
    event.is_active=False;event.save(update_fields=['is_active'])
