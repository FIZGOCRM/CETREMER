from datetime import datetime,time,timedelta
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from .models import EmailLog,Notification,SiteSettings


def notify(user,kind,reference,title,body='',url='',*,email=False,send_before=None):
    notice,_=Notification.objects.get_or_create(user=user,kind=kind,reference=str(reference),defaults={'title':title,'body':body,'url':url})
    if email:queue_email(user,kind,f'{user.pk}:{reference}',title,body,send_before=send_before)
    return notice


@transaction.atomic
def _deliver(log_id):
    # Reserve the SQLite writer before reading delivery state, including parallel cron runs.
    EmailLog.objects.filter(pk=log_id).update(status=F('status'))
    log=EmailLog.objects.select_related('user').get(pk=log_id)
    if log.status=='sent' or log.kind in ('first_access','reset_access','smtp_test'):return log
    if log.send_before and log.send_before<=timezone.now():return log
    if log.kind in ('new_lesson','module_release') and not log.user.student_profile.email_new_lessons:return log
    if log.kind=='live_reminder' and not log.user.student_profile.email_live_events:return log
    if not SiteSettings.load().email_host or not log.user.email or not log.user.is_active:
        log.status='not_sent'
    else:
        try:
            count=send_mail(log.subject,log.body,None,[log.user.email],fail_silently=False)
            log.status='sent' if count else 'failed'
        except Exception:
            # Do not expose SMTP credentials or transport error text in the interface/log record.
            log.status='failed'
    log.save(update_fields=['status']);return log


def queue_email(user,kind,reference,subject,body,*,send_before=None):
    log,created=EmailLog.objects.get_or_create(kind=kind,reference=str(reference),defaults={'user':user,'subject':subject,'body':body,'send_before':send_before})
    if log.user_id!=user.pk:raise ValueError('A referência de e-mail deve identificar seu destinatário.')
    return _deliver(log.pk) if created else log


def retry_pending_emails():
    if not SiteSettings.load().email_host:return 0
    count=0
    for pk in EmailLog.objects.exclude(status='sent').exclude(kind__in=['first_access','reset_access','smtp_test']).values_list('pk',flat=True):
        count+=_deliver(pk).status=='sent'
    return count


def run_daily_notifications(*,on=None):
    from courses.access import access_decision,module_release_date,lesson_availability
    from courses.models import Enrollment,Lesson,Module,LiveReminder
    from courses.services import plan_status
    from courses.live_services import require_event_access
    from django.core.exceptions import PermissionDenied
    today=on or timezone.localdate()
    before=Notification.objects.count()
    enrollments=Enrollment.objects.select_related('student__user','course').prefetch_related('access_periods','access_changes')
    for enrollment in enrollments:
        user=enrollment.student.user
        if not user.is_active:continue
        plan=plan_status(enrollment,on=today)
        if plan.get('days') in (30,15,7) and plan.get('state')=='ending_soon':
            notify(user,'expiry',f'{enrollment.pk}:{plan["ends_on"]}:{plan["days"]}',f'Seu acesso termina em {plan["days"]} dias',
                f'O acesso a {enrollment.course.title} termina em {plan["last_day"].strftime("%d/%m/%Y")}. Conclua as aulas e a avaliação para emitir seu certificado.',reverse('settings'),email=True,send_before=timezone.make_aware(datetime.combine(today+timedelta(days=1),time.min)))
        if not access_decision(enrollment,on=today).allowed:continue
        for module in Module.objects.filter(course=enrollment.course,status='published'):
            if module.release_month>1 and module_release_date(enrollment,module)==today:
                notify(user,'module_release',f'{enrollment.pk}:{module.pk}:{today}','Módulo liberado',f'{module.title} já está disponível em {enrollment.course.title}.',reverse('member_course',args=[enrollment.course.slug]),email=enrollment.student.email_new_lessons)
        for lesson in Lesson.objects.filter(module__course=enrollment.course,status='published',module__status='published',published_at__isnull=False,published_at__gte=enrollment.enrolled_at).select_related('module__course'):
            if lesson_availability(enrollment,lesson,on=today).state=='available':
                notify(user,'new_lesson',f'{enrollment.pk}:{lesson.pk}:{lesson.published_at.isoformat()}','Nova aula disponível',f'{lesson.title} foi publicada em {enrollment.course.title}.',reverse('lesson_detail',args=[enrollment.course.slug,lesson.pk]),email=enrollment.student.email_new_lessons)
    for reminder in LiveReminder.objects.select_related('student__user','event').filter(event__is_active=True,event__starts_at__date=today):
        try:require_event_access(reminder.student.user,reminder.event)
        except PermissionDenied:continue
        notify(reminder.student.user,'live_today',str(reminder.pk),f'Hoje: {reminder.event.title}',timezone.localtime(reminder.event.starts_at).strftime('Seu encontro começa às %H:%M.'),reverse('live_classes'))
    retry_pending_emails()
    return Notification.objects.count()-before


def run_live_reminders():
    from datetime import timedelta
    from django.core.exceptions import PermissionDenied
    from courses.models import LiveReminder
    from courses.live_services import require_event_access
    now=timezone.now();count=0
    for reminder in LiveReminder.objects.select_related('student__user','event').filter(event__is_active=True,event__starts_at__gt=now,event__starts_at__lte=now+timedelta(hours=1),student__email_live_events=True):
        try:require_event_access(reminder.student.user,reminder.event)
        except PermissionDenied:continue
        queue_email(reminder.student.user,'live_reminder',f'{reminder.student.user_id}:{reminder.event_id}:{reminder.event.starts_at.isoformat()}',f'Em breve: {reminder.event.title}',timezone.localtime(reminder.event.starts_at).strftime('Seu encontro começa às %H:%M. Acesse Ao vivo na plataforma.'),send_before=reminder.event.starts_at)
        count+=1
    retry_pending_emails();return count


def pending_email_count():
    from django.db.models import Q
    return EmailLog.objects.exclude(status='sent').exclude(kind__in=['first_access','reset_access','smtp_test']).filter(Q(send_before__isnull=True)|Q(send_before__gt=timezone.now())).count()

