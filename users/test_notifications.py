from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase,override_settings
from django.utils import timezone
from courses.models import Course,Enrollment,Module,Lesson,AccessPeriod
from users.models import User,SiteSettings

class NotificationTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user(username='notice-admin',role='CREATOR')
        self.user=User.objects.create_user(username='notice-student',email='notice@example.org')
        self.other=User.objects.create_user(username='notice-other',email='other@example.org')
        self.course=Course.objects.create(is_published=True, title='Curso de avisos',slug='notices',creator=self.admin.creator_profile)
        self.enrollment=Enrollment.objects.create(student=self.user.student_profile,course=self.course,plan_started_on=timezone.localdate(),access_policy='PERIODS')
        AccessPeriod.objects.create(enrollment=self.enrollment,starts_on=timezone.localdate(),ends_on=timezone.localdate()+timedelta(days=30),source='manual',reference='notice-plan')
        self.module=Module.objects.create(course=self.course,title='Módulo')

    def test_daily_expiry_is_mandatory_and_idempotent_without_smtp(self):
        from users.notifications import run_daily_notifications
        from users.models import Notification,EmailLog
        self.user.student_profile.email_new_lessons=False;self.user.student_profile.email_live_events=False;self.user.student_profile.save()
        period=self.enrollment.access_periods.get()
        period.starts_on=timezone.localdate()-timedelta(days=30);period.ends_on=timezone.localdate();period.grace_days=3;period.save()
        with patch('users.notifications.send_mail') as send:
            run_daily_notifications();run_daily_notifications()
        self.assertEqual(Notification.objects.filter(kind='expiry').count(),1)
        self.assertEqual(EmailLog.objects.get().status,'not_sent');send.assert_not_called()

    @override_settings(DEBUG=True)
    def test_console_backend_is_not_mistaken_for_delivery(self):
        from users.notifications import queue_email
        from users.models import EmailLog
        queue_email(self.user,'test','user-1','Teste','Mensagem')
        self.assertEqual(EmailLog.objects.get().status,'not_sent')

    def test_smtp_sent_and_failure_are_logged_and_sent_is_never_repeated(self):
        from users.notifications import queue_email
        from users.models import EmailLog
        site=SiteSettings.load();site.email_host='smtp.example.org';site.save()
        with patch('users.notifications.send_mail',return_value=1) as send:
            queue_email(self.user,'test','sent','Teste','Mensagem');queue_email(self.user,'test','sent','Teste','Mensagem')
            self.assertEqual(send.call_count,1)
        with patch('users.notifications.send_mail',side_effect=OSError('SMTP indisponível')):
            queue_email(self.user,'test','failed','Teste','Mensagem')
        self.assertEqual(EmailLog.objects.get(reference='failed').status,'failed')

    def test_pending_email_retries_after_smtp_configuration(self):
        from users.notifications import queue_email,retry_pending_emails
        from users.models import EmailLog
        queue_email(self.user,'test','retry','Teste','Mensagem')
        site=SiteSettings.load();site.email_host='smtp.example.org';site.save()
        with patch('users.notifications.send_mail',return_value=1) as send:
            retry_pending_emails();retry_pending_emails();self.assertEqual(send.call_count,1)
        self.assertEqual(EmailLog.objects.get().status,'sent')

    def test_new_lesson_only_notifies_after_module_available(self):
        from users.notifications import run_daily_notifications
        from users.models import Notification
        from courses.services import save_lesson
        self.module.release_month=2;self.module.save()
        lesson=Lesson(module=self.module,title='Aula nova');save_lesson(lesson)
        run_daily_notifications();self.assertFalse(Notification.objects.filter(kind='new_lesson').exists())
        self.module.release_month=1;self.module.save()
        run_daily_notifications();run_daily_notifications()
        self.assertEqual(Notification.objects.filter(kind='new_lesson').count(),1)

    def test_module_release_notifies_once_and_not_to_outsider(self):
        from users.notifications import run_daily_notifications
        from users.models import Notification
        from courses.services import add_calendar_months
        self.enrollment.plan_started_on=add_calendar_months(timezone.localdate(),-1);self.enrollment.save()
        self.module.release_month=2;self.module.save()
        run_daily_notifications();run_daily_notifications()
        self.assertEqual(Notification.objects.filter(kind='module_release',user=self.user).count(),1)
        self.assertFalse(Notification.objects.filter(user=self.other).exists())

    def test_team_reply_solution_and_ticket_changes_create_notifications(self):
        from users.models import Notification
        from community.models import CommunityPost
        from community.services import add_reply,mark_solution
        from support.models import SupportSubject
        from support.services import create_ticket,update_ticket
        post=CommunityPost.objects.create(author=self.user,course=self.course,title='Dúvida da turma',content='Dúvida com conteúdo ilustrativo.')
        reply=add_reply(self.admin,post,'Resposta da equipe',display_as='team')
        self.assertTrue(Notification.objects.filter(user=self.user,kind='team_reply').exists())
        student_reply=add_reply(self.user,post,'Outra resposta ilustrativa')
        mark_solution(self.admin,post,student_reply)
        self.assertTrue(Notification.objects.filter(user=self.user,kind='solution').exists())
        ticket=create_ticket(self.user,subject=SupportSubject.objects.create(name='Acesso'),title='Dúvida de acesso',body='Descrição suficiente do problema.',device='Celular')
        update_ticket(self.admin,ticket,status='in_review')
        self.assertTrue(Notification.objects.filter(user=self.user,kind='ticket_update').exists())

    def test_live_reminder_today_and_one_hour_email_are_idempotent(self):
        from users.notifications import run_daily_notifications,run_live_reminders
        from users.models import Notification,EmailLog
        from courses.models import LiveEvent,LiveReminder
        event=LiveEvent.objects.create(course=self.course,title='Encontro',starts_at=timezone.now()+timedelta(minutes=45))
        LiveReminder.objects.create(student=self.user.student_profile,event=event)
        run_daily_notifications();run_daily_notifications();run_live_reminders();run_live_reminders()
        self.assertEqual(Notification.objects.filter(kind='live_today').count(),1)
        self.assertEqual(EmailLog.objects.filter(kind='live_reminder').count(),1)

    def test_read_all_only_changes_current_users_notifications(self):
        from users.models import Notification
        a=Notification.objects.create(user=self.user,kind='test',title='Meu aviso',reference='a')
        b=Notification.objects.create(user=self.other,kind='test',title='Outro aviso',reference='b')
        self.client.force_login(self.user)
        self.assertContains(self.client.get('/notificacoes/'),'Meu aviso')
        self.assertNotContains(self.client.get('/notificacoes/'),'Outro aviso')
        self.client.post('/notificacoes/lidas/')
        a.refresh_from_db();b.refresh_from_db();self.assertIsNotNone(a.read_at);self.assertIsNone(b.read_at)

    def test_expired_live_email_is_not_delivered_late(self):
        from users.notifications import queue_email,retry_pending_emails
        from users.models import EmailLog
        queue_email(self.user,'live_reminder','old-live','Encontro','Texto',send_before=timezone.now()-timedelta(minutes=1))
        site=SiteSettings.load();site.email_host='smtp.example.org';site.save()
        with patch('users.notifications.send_mail') as send:
            retry_pending_emails();send.assert_not_called()
        self.assertEqual(EmailLog.objects.get().status,'not_sent')

    def test_publishing_draft_module_notifies_its_published_lessons(self):
        from courses.services import save_module,save_lesson
        from users.notifications import run_daily_notifications
        from users.models import Notification
        self.module.status='draft';self.module.save()
        lesson=Lesson(module=self.module,title='Aula do módulo');save_lesson(lesson)
        self.assertIsNotNone(lesson.published_at)
        previous_publication=lesson.published_at
        self.module.status='published';save_module(self.module,actor=self.admin)
        lesson.refresh_from_db();self.assertGreater(lesson.published_at,previous_publication)
        run_daily_notifications()
        self.assertTrue(Notification.objects.filter(kind='new_lesson').exists())

    def retry_with_smtp(self):
        from users.notifications import retry_pending_emails
        site=SiteSettings.load();site.email_host='smtp.example.org';site.save()
        with patch('users.notifications.send_mail',return_value=1) as send:
            retry_pending_emails()
            return send.call_count

    def test_queued_lesson_email_rechecks_access_and_publication(self):
        from courses.services import save_lesson,end_plan_early
        from users.notifications import run_daily_notifications
        from users.models import EmailLog
        save_lesson(Lesson(module=self.module,title='Aula publicada'))
        run_daily_notifications()
        self.assertTrue(EmailLog.objects.filter(kind='new_lesson').exists())
        end_plan_early(self.enrollment,timezone.localdate(),'withdrawal',actor=self.admin)
        self.assertEqual(self.retry_with_smtp(),0)

    def test_queued_lesson_email_rechecks_postponed_module(self):
        from courses.services import save_lesson
        from users.notifications import run_daily_notifications
        save_lesson(Lesson(module=self.module,title='Aula publicada'))
        run_daily_notifications()
        self.module.release_month=3;self.module.save()
        # No expiry warning before the last three access days; postponed lesson is unavailable.
        self.assertEqual(self.retry_with_smtp(),0)

    def test_queued_live_email_rechecks_cancellation_removal_and_schedule(self):
        from courses.models import LiveEvent,LiveReminder
        from users.notifications import run_live_reminders
        for mode in ('cancel','remove','reschedule'):
            site=SiteSettings.load();site.email_host='';site.save()
            event=LiveEvent.objects.create(course=self.course,title=mode,starts_at=timezone.now()+timedelta(minutes=45))
            reminder=LiveReminder.objects.create(student=self.user.student_profile,event=event)
            run_live_reminders()
            if mode=='cancel':event.is_active=False;event.save()
            elif mode=='remove':reminder.delete()
            else:event.starts_at+=timedelta(days=1);event.save()
        self.assertEqual(self.retry_with_smtp(),0)

    def test_obsolete_emails_are_not_counted_as_actionable_pending(self):
        from courses.models import LiveEvent,LiveReminder
        from users.notifications import run_live_reminders,pending_email_count
        event=LiveEvent.objects.create(course=self.course,title='Encontro',starts_at=timezone.now()+timedelta(minutes=45))
        reminder=LiveReminder.objects.create(student=self.user.student_profile,event=event)
        run_live_reminders();self.assertEqual(pending_email_count(),1)
        reminder.delete();self.assertEqual(pending_email_count(),0)
