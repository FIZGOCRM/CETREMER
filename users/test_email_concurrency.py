from datetime import timedelta
from threading import Thread
from unittest.mock import patch

from django.db import connections, close_old_connections
from django.test import TransactionTestCase
from django.utils import timezone

from courses.models import Course, Enrollment, Module, Lesson, Progress
from courses.services import record_heartbeat
from users.models import User, SiteSettings, EmailLog
from users.notifications import _deliver


class EmailConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.admin=User.objects.create_user(username='mail-admin',role='CREATOR')
        self.user=User.objects.create_user(username='mail-student',email='mail@example.org')
        course=Course.objects.create(title='Curso',slug='mail-lock',creator=self.admin.creator_profile,is_published=True)
        Enrollment.objects.create(student=self.user.student_profile,course=course)
        self.lesson=Lesson.objects.create(module=Module.objects.create(course=course,title='M'),title='A')
        site=SiteSettings.load();site.email_host='smtp.example.org';site.save()
        self.log=EmailLog.objects.create(user=self.user,kind='test',reference='concurrency',subject='Teste')

    def test_smtp_network_call_does_not_hold_database_transaction_or_block_player(self):
        failures=[]
        def heartbeat():
            close_old_connections()
            try:record_heartbeat(self.user.student_profile,self.lesson,position=15,playing=True)
            except Exception as exc:failures.append(type(exc).__name__)
            finally:connections['default'].close()
        def slow_smtp(*args,**kwargs):
            self.assertFalse(connections['default'].in_atomic_block,'SMTP não pode manter transação aberta.')
            worker=Thread(target=heartbeat);worker.start();worker.join(timeout=3)
            self.assertFalse(worker.is_alive(),'Player aguardou o SMTP para poder gravar.')
            self.assertEqual(failures,[])
            return 1
        with patch('users.notifications.send_mail',side_effect=slow_smtp):
            self.assertEqual(_deliver(self.log.pk).status,'sent')
        self.assertEqual(Progress.objects.get().last_position_seconds,15)

    def test_second_worker_does_not_deliver_an_already_claimed_email(self):
        entered=False
        def smtp(*args,**kwargs):
            nonlocal entered
            if not entered:
                entered=True
                _deliver(self.log.pk)
            return 1
        with patch('users.notifications.send_mail',side_effect=smtp) as send:
            _deliver(self.log.pk)
            self.assertEqual(send.call_count,1)

    def test_expired_claim_recovers_and_current_claim_is_not_stolen(self):
        EmailLog.objects.filter(pk=self.log.pk).update(delivery_token='a'*32,delivery_claimed_at=timezone.now())
        with patch('users.notifications.send_mail',return_value=1) as send:
            _deliver(self.log.pk);send.assert_not_called()
            EmailLog.objects.filter(pk=self.log.pk).update(delivery_claimed_at=timezone.now()-timedelta(minutes=6))
            _deliver(self.log.pk);send.assert_called_once()
        self.log.refresh_from_db()
        self.assertEqual(self.log.status,'sent')
        self.assertEqual(self.log.delivery_token,'')
        self.assertIsNone(self.log.delivery_claimed_at)
