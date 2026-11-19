from datetime import datetime,time,timedelta
from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.db import transaction
from django.db.models import Q
from uuid import uuid4
from django.urls import reverse
from django.utils import timezone
from .models import EmailLog,Notification,SiteSettings


def notify(user,kind,reference,title,body='',url='',*,email=False,send_before=None):
    # Commit the bell entry and its outbox row together. A stopped scheduler can
    # retry the pending message without generating a second publication.
    log = None
    with transaction.atomic():
        notice, created = Notification.objects.get_or_create(
            user=user, kind=kind, reference=str(reference), defaults={"title": title, "body": body, "url": url})
        if email and created:
            log, _ = _email_log(user, kind, f"{user.pk}:{reference}", title, body, send_before=send_before)
    if log:
        _deliver(log.pk, preview=True)
    return notice


REMINDER_KINDS = {"live_reminder", "live_reminder_24h"}
CONTENT_KINDS = {"new_lesson", "new_ebook", "new_recording"}


def recording_available(event, now):
    return bool(event.is_active and event.recording_url and event.recording_added_at and
                event.starts_at + timedelta(minutes=event.duration_minutes) <= now)


def email_is_current(log):
    """Revalidate the event, recipient and entitlement at delivery time."""
    from courses.access import access_decision, lesson_availability, module_release_date
    from courses.models import Enrollment, Lesson, Module, LiveEvent, LiveReminder
    from courses.live_services import require_event_access
    from courses.services import plan_expiry_notice
    from django.core.exceptions import PermissionDenied
    if log.status=='sent' or log.kind in ('first_access','reset_access','smtp_test'):return False
    if log.send_before and log.send_before<=timezone.now():return False
    if not log.user.is_active or not log.user.email:return False
    if log.kind not in CONTENT_KINDS | REMINDER_KINDS | {"module_release", "expiry"}:return True
    if log.user.role!='STUDENT':return False
    student=log.user.student_profile
    if log.kind in ('new_lesson','new_ebook','module_release') and not student.email_new_lessons:return False
    if log.kind in REMINDER_KINDS | {'new_recording'} and not student.email_live_events:return False
    parts=log.reference.split(':',2 if log.kind in REMINDER_KINDS else 3)
    def identifier(value):
        return value.isdecimal() and 0<int(value)<2**63
    if not parts or not identifier(parts[0]) or int(parts[0])!=log.user_id:return False
    if log.kind == "new_recording":
        if len(parts) != 2 or not identifier(parts[1]):
            return False
        event = LiveEvent.objects.filter(pk=parts[1]).first()
        if not event or not recording_available(event, timezone.now()):
            return False
        try:
            require_event_access(log.user, event)
        except PermissionDenied:
            return False
        return True
    if log.kind in REMINDER_KINDS:
        if len(parts)!=3 or not identifier(parts[1]):return False
        event=LiveEvent.objects.filter(pk=int(parts[1]),is_active=True,starts_at__gt=timezone.now()).first()
        if not event or event.starts_at.isoformat()!=parts[2] or not LiveReminder.objects.filter(student=student,event=event).exists():return False
        try:require_event_access(log.user,event)
        except PermissionDenied:return False
        return True
    if len(parts)!=4 or not identifier(parts[1]):return False
    enrollment=Enrollment.objects.filter(pk=int(parts[1]),student=student).select_related('course').prefetch_related('access_periods','access_changes').first()
    if not enrollment:return False
    if log.kind=='expiry':
        notice=plan_expiry_notice(enrollment)
        return bool(notice and str(notice['last_day'])==parts[2] and str(notice['days'])==parts[3])
    if not enrollment.course.is_published or not access_decision(enrollment).allowed or not identifier(parts[2]):return False
    if log.kind == "new_ebook":
        from courses.models import LessonMaterial
        material = LessonMaterial.objects.filter(pk=parts[2], lesson__module__course=enrollment.course).select_related("lesson__module__course").first()
        return bool(material and (material.file or material.url) and lesson_availability(enrollment, material.lesson).state == "available")
    if log.kind=='new_lesson':
        lesson=Lesson.objects.filter(pk=int(parts[2]),module__course=enrollment.course).select_related('module__course').first()
        return bool(lesson and lesson.published_at and lesson_availability(enrollment,lesson).state=='available')
    module=Module.objects.filter(pk=int(parts[2]),course=enrollment.course,status='published').first()
    release=module_release_date(enrollment,module) if module else None
    return bool(release and str(release)==parts[3] and release<=timezone.localdate())


def _deliver(log_id, *, preview=False):
    log=EmailLog.objects.select_related('user').get(pk=log_id)
    if not email_is_current(log):return log
    if not SiteSettings.load().email_host:
        if preview and settings.DEBUG:
            console = get_connection("django.core.mail.backends.console.EmailBackend")
            send_mail(log.subject, log.body, None, [log.user.email], connection=console)
        return log
    # A single conditional UPDATE claims the delivery in autocommit. No SQLite
    # transaction is kept open during the network call. SMTP has a 15s timeout;
    # a five-minute lease permits recovery after a crashed scheduler.
    now=timezone.now();token=uuid4().hex
    available=Q(delivery_token='')|Q(delivery_claimed_at__lt=now-timedelta(minutes=5))
    claimed=EmailLog.objects.filter(pk=log_id).exclude(status='sent').filter(available).update(delivery_token=token,delivery_claimed_at=now)
    if not claimed:return EmailLog.objects.get(pk=log_id)
    status=log.status
    try:
        log=EmailLog.objects.select_related('user').get(pk=log_id)
        if email_is_current(log):
            try:
                count=send_mail(log.subject,log.body,None,[log.user.email],fail_silently=False)
                status='sent' if count else 'failed'
            except Exception:
                # Do not expose SMTP credentials or transport error text.
                status='failed'
    finally:
        EmailLog.objects.filter(pk=log_id,delivery_token=token).update(status=status,delivery_token='',delivery_claimed_at=None)
    return EmailLog.objects.get(pk=log_id)


def _email_log(user,kind,reference,subject,body,*,send_before=None):
    log,created=EmailLog.objects.get_or_create(kind=kind,reference=str(reference),defaults={'user':user,'subject':subject,'body':body,'send_before':send_before})
    if log.user_id!=user.pk:raise ValueError('A referência de e-mail deve identificar seu destinatário.')
    return log, created


def queue_email(user,kind,reference,subject,body,*,send_before=None):
    log, created = _email_log(user, kind, reference, subject, body, send_before=send_before)
    return _deliver(log.pk, preview=True) if created else log


def retry_pending_emails():
    if not SiteSettings.load().email_host:return 0
    count=0
    for pk in EmailLog.objects.exclude(status='sent').exclude(kind__in=['first_access','reset_access','smtp_test']).values_list('pk',flat=True):
        count+=_deliver(pk).status=='sent'
    return count


def run_daily_notifications(*,on=None):
    from courses.access import access_decision,module_release_date,lesson_availability
    from courses.models import Enrollment,Lesson,Module,LiveReminder
    from courses.services import plan_expiry_notice
    from courses.live_services import require_event_access
    from django.core.exceptions import PermissionDenied
    today=on or timezone.localdate()
    before=Notification.objects.count()
    enrollments=Enrollment.objects.select_related('student__user','course').prefetch_related('access_periods','access_changes')
    for enrollment in enrollments:
        user=enrollment.student.user
        if not user.is_active:continue
        notice=plan_expiry_notice(enrollment,on=today)
        if notice:
            remaining='amanhã' if notice['days']==1 else f'em {notice["days"]} dias'
            notify(user,'expiry',f'{enrollment.pk}:{notice["last_day"]}:{notice["days"]}',f'Seu acesso termina {remaining}',
                f'O acesso a {enrollment.course.title} fica disponível até {notice["last_day"].strftime("%d/%m/%Y")}. Confira as datas do seu plano em Minha conta.',reverse('settings')+'#meu-plano',email=True,send_before=timezone.make_aware(datetime.combine(today+timedelta(days=1),time.min)))
        if not enrollment.course.is_published or not access_decision(enrollment,on=today).allowed:continue
        for module in Module.objects.filter(course=enrollment.course,status='published'):
            if module.release_month>1 and module_release_date(enrollment,module)==today:
                notify(user,'module_release',f'{enrollment.pk}:{module.pk}:{today}','Módulo liberado',f'{module.title} já está disponível em {enrollment.course.title}.',reverse('member_course',args=[enrollment.course.slug]),email=enrollment.student.email_new_lessons)
    run_content_notifications(on=today)
    for reminder in LiveReminder.objects.select_related('student__user','event').filter(event__is_active=True,event__starts_at__date=today):
        try:require_event_access(reminder.student.user,reminder.event)
        except PermissionDenied:continue
        notify(reminder.student.user,'live_today',str(reminder.pk),f'Hoje: {reminder.event.title}',timezone.localtime(reminder.event.starts_at).strftime('Seu encontro começa às %H:%M.'),reverse('live_classes'))
    retry_pending_emails()
    return Notification.objects.count()-before


def run_content_notifications(*, on=None):
    """Catch up on publications since enrollment, including newly unlocked modules."""
    from courses.access import access_decision, lesson_availability
    from courses.models import Enrollment, Lesson, LessonMaterial, LiveEvent

    from courses.selectors import course_publication_time

    now = timezone.now()
    enrollments = Enrollment.objects.filter(student__user__is_active=True, course__is_published=True
        ).select_related("course", "student__user").prefetch_related("access_periods")
    for enrollment in enrollments:
        if not access_decision(enrollment, on=on).allowed:
            continue
        student = enrollment.student
        scope = {"module__course": enrollment.course, "module__status": "published", "status": "published"}
        lessons = Lesson.objects.filter(**scope).select_related("module__course")
        # V1 references used the publication timestamp. Recognize those existing notices as delivered too.
        seen = {reference.split(":", 2)[1] for reference in Notification.objects.filter(
            user=student.user, kind="new_lesson", reference__startswith=f"{enrollment.pk}:"
        ).values_list("reference", flat=True)}
        for lesson in lessons.filter(published_at__isnull=False):
            published = course_publication_time(enrollment, lesson.module, lesson.published_at)
            if not enrollment.enrolled_at <= published <= now:
                continue
            if str(lesson.pk) in seen or lesson_availability(enrollment, lesson, on=on).state != "available":
                continue
            notify(student.user, "new_lesson", f"{enrollment.pk}:{lesson.pk}:publication",
                   "Nova aula disponível", f"{lesson.title} foi publicada em {enrollment.course.title}.",
                   reverse("lesson_detail", args=[enrollment.course.slug, lesson.pk]), email=student.email_new_lessons)
        materials = LessonMaterial.objects.filter(lesson__in=lessons, created_at__isnull=False
            ).exclude(file="", url="").select_related("lesson__module__course")
        announced_books = set(Notification.objects.filter(user=student.user, kind="new_ebook",
            reference__startswith=f"{enrollment.pk}:").values_list("reference", flat=True))
        for material in materials:
            if f"{enrollment.pk}:{material.pk}:publication" in announced_books:
                continue
            published = course_publication_time(enrollment, material.lesson.module, material.lesson.published_at,
                                                attachment_created_at=material.created_at)
            if not enrollment.enrolled_at <= published <= now:
                continue
            if lesson_availability(enrollment, material.lesson, on=on).state == "available":
                notify(student.user, "new_ebook", f"{enrollment.pk}:{material.pk}:publication",
                       "Novo e-book disponível", f"{material.title} · {enrollment.course.title}",
                       reverse("material_open", args=["lesson", material.pk]), email=student.email_new_lessons)
        recordings = LiveEvent.objects.filter(Q(course=enrollment.course) | Q(course__isnull=True),
            is_active=True, recording_added_at__range=(enrollment.enrolled_at, now)).exclude(recording_url="")
        for event in recordings:
            if recording_available(event, now):
                notify(student.user, "new_recording", event.pk, "Gravação disponível", event.title,
                       reverse("live_link", args=[event.pk, "gravacao"]), email=student.email_live_events)


def run_live_reminders():
    from django.core.exceptions import PermissionDenied
    from courses.models import LiveReminder
    from courses.live_services import require_event_access

    now = timezone.now()
    count = 0
    reminders = LiveReminder.objects.select_related("student__user", "event").filter(
        student__user__is_active=True, event__is_active=True, event__starts_at__gt=now,
        event__starts_at__lte=now+timedelta(hours=24))
    for reminder in reminders:
        event = reminder.event
        try:
            require_event_access(reminder.student.user, event)
        except PermissionDenied:
            continue
        soon = event.starts_at <= now + timedelta(hours=1)
        kind = "live_reminder" if soon else "live_reminder_24h"
        title = ("Em breve: " if soon else "Nas próximas 24 horas: ") + event.title
        notify(reminder.student.user, kind, f"{event.pk}:{event.starts_at.isoformat()}", title,
               timezone.localtime(event.starts_at).strftime("Encontro em %d/%m às %H:%M. Acesse Ao vivo na plataforma."),
               reverse("live_classes"), email=reminder.student.email_live_events,
               send_before=event.starts_at if soon else event.starts_at-timedelta(hours=1))
        count += 1
    run_content_notifications()
    retry_pending_emails()
    return count


def pending_email_count():
    from django.db.models import Q
    logs=EmailLog.objects.exclude(status='sent').exclude(kind__in=['first_access','reset_access','smtp_test']).filter(Q(send_before__isnull=True)|Q(send_before__gt=timezone.now())).select_related('user','user__student_profile')
    return sum(email_is_current(log) for log in logs.iterator())

