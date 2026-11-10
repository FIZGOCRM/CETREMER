from django.contrib.auth import get_user_model
from django.test import TestCase

from core.activity import log
from core.models import ActivityLog

User = get_user_model()


class ActivityLogTests(TestCase):
    def test_log_stores_ready_text_and_orders_newest_first(self):
        student = User.objects.create_user(username='jane', email='j@example.com', password='x')
        log('enrolled', 'Jane foi matriculada em BLS', student=student)
        log('imported', 'Importação concluída')
        self.assertEqual(ActivityLog.objects.first().verb, 'imported')
        self.assertEqual(ActivityLog.objects.filter(student=student).get().text, 'Jane foi matriculada em BLS')

    def test_log_truncates_long_text(self):
        self.assertEqual(len(log('x', 'a' * 500).text), 200)
