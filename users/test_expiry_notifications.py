from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from courses.models import AccessPeriod, Course, Enrollment, Lesson, Module
from users.models import EmailLog, Notification, SiteSettings, User
from users.notifications import run_daily_notifications, retry_pending_emails


class ExpiryNotificationTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user(username='expiry-admin',role='CREATOR')
        self.user=User.objects.create_user(username='expiry-member',email='expiry@example.org')
        self.course=Course.objects.create(title='Curso de prazo',slug='expiry-course',creator=self.admin.creator_profile,is_published=True)
        self.enrollment=Enrollment.objects.create(student=self.user.student_profile,course=self.course,access_policy='periods',plan_started_on=timezone.localdate()-timedelta(days=30))
        self.today=timezone.localdate()
        self.period=AccessPeriod.objects.create(enrollment=self.enrollment,starts_on=self.today-timedelta(days=30),ends_on=self.today+timedelta(days=30),grace_days=3,source='manual',reference='expiry-test')
        Lesson.objects.create(module=Module.objects.create(course=self.course,title='Módulo'),title='Aula')
        self.client.force_login(self.user)

    def set_remaining_days(self,days,*,grace=3,early=False):
        if early:
            from courses.services import end_plan_early
            end_plan_early(self.enrollment,self.today+timedelta(days=days),'withdrawal',actor=self.admin)
            self.period.refresh_from_db()
            return
        self.period.ends_on=self.today+timedelta(days=days-grace)
        self.period.grace_days=grace
        self.period.ended_early=early
        self.period.save()

    def test_home_and_course_cards_have_no_expiry_banner_or_countdown(self):
        for path in ('/dashboard/','/dashboard/meus-cursos/','/dashboard/recursos/progresso/'):
            response=self.client.get(path)
            self.assertEqual(response.status_code,200)
            self.assertNotContains(response,'data-plan-notice')
            self.assertNotIn('termina em',response.content.decode().lower())

    def test_no_expiry_notification_before_last_three_access_days(self):
        for days in (33,30,15,7,4):
            self.set_remaining_days(days)
            run_daily_notifications()
            self.assertFalse(Notification.objects.filter(kind='expiry').exists(),f'Aviso antecipado com {days} dias')
            self.assertFalse(EmailLog.objects.filter(kind='expiry').exists())

    def test_one_notice_per_day_for_three_two_and_one_days_including_grace(self):
        self.set_remaining_days(3)
        initial_now=timezone.now()
        for offset,title in ((0,'3 dias'),(1,'2 dias'),(2,'amanhã')):
            with patch('django.utils.timezone.now',return_value=initial_now+timedelta(days=offset)):
                run_daily_notifications();run_daily_notifications()
                notices=Notification.objects.filter(kind='expiry')
                self.assertEqual(notices.count(),offset+1)
                notice=notices.latest('pk')
                self.assertIn(title,notice.title)
                self.assertIn(self.course.title,notice.body)
                self.assertIn((self.today+timedelta(days=2)).strftime('%d/%m/%Y'),notice.body)
                self.assertEqual(notice.url,'/settings/#meu-plano')
        self.assertEqual(EmailLog.objects.filter(kind='expiry').count(),3)
        with patch('django.utils.timezone.now',return_value=initial_now+timedelta(days=3)):
            run_daily_notifications()
        self.assertEqual(Notification.objects.filter(kind='expiry').count(),3)

    def test_early_end_warns_without_adding_tolerance(self):
        self.set_remaining_days(3,grace=0,early=True)
        run_daily_notifications()
        self.assertIn('3 dias',Notification.objects.get(kind='expiry').title)

    def test_courses_have_independent_deadlines_and_recipient(self):
        self.set_remaining_days(3)
        other=User.objects.create_user(username='expiry-other',email='other@example.org')
        course=Course.objects.create(title='Segundo curso',slug='expiry-other-course',creator=self.admin.creator_profile,is_published=True)
        enrollment=Enrollment.objects.create(student=self.user.student_profile,course=course,access_policy='periods',plan_started_on=self.today-timedelta(days=30))
        AccessPeriod.objects.create(enrollment=enrollment,starts_on=self.today-timedelta(days=30),ends_on=self.today+timedelta(days=2),grace_days=3,source='manual',reference='second')
        run_daily_notifications()
        self.assertEqual(Notification.objects.filter(kind='expiry').count(),1)
        self.assertFalse(Notification.objects.filter(user=other).exists())
        self.assertNotIn(course.title,Notification.objects.get(kind='expiry').body)

    def test_notifications_and_account_show_access_deadline(self):
        self.set_remaining_days(3)
        run_daily_notifications()
        response=self.client.get('/notificacoes/')
        self.assertContains(response,'Prazo de acesso')
        self.assertContains(response,self.course.title)
        self.assertContains(response,'/settings/#meu-plano')
        self.assertContains(self.client.get('/settings/'),f'Acesso até: {(self.today+timedelta(days=2)).strftime("%d/%m/%Y")}')

    def test_ended_unrestricted_inactive_or_draft_course_does_not_warn(self):
        self.set_remaining_days(0)
        run_daily_notifications()
        self.set_remaining_days(3)
        self.enrollment.access_policy='unrestricted';self.enrollment.save()
        run_daily_notifications()
        self.enrollment.access_policy='periods';self.enrollment.save()
        self.user.is_active=False;self.user.save()
        run_daily_notifications()
        self.user.is_active=True;self.user.save()
        self.course.is_published=False;self.course.save()
        run_daily_notifications()
        self.assertFalse(Notification.objects.filter(kind='expiry').exists())

    def test_pending_old_or_corrected_expiry_email_is_not_sent(self):
        self.set_remaining_days(3)
        run_daily_notifications()
        EmailLog.objects.create(user=self.user,kind='expiry',reference=f'{self.user.pk}:{self.enrollment.pk}:{self.period.ends_on}:30',subject='Aviso antigo')
        self.period.ends_on+=timedelta(days=30);self.period.save()
        site=SiteSettings.load();site.email_host='smtp.example.org';site.save()
        with patch('users.notifications.send_mail') as send:
            retry_pending_emails();send.assert_not_called()

    def test_current_expiry_email_is_sent_only_once(self):
        self.set_remaining_days(3)
        site=SiteSettings.load();site.email_host='smtp.example.org';site.save()
        with patch('users.notifications.send_mail',return_value=1) as send:
            run_daily_notifications();run_daily_notifications();retry_pending_emails()
            send.assert_called_once()
        self.assertEqual(EmailLog.objects.get(kind='expiry').status,'sent')
