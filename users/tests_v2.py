from django.contrib.auth import get_user_model
from django.test import TestCase

from users.models import Notification

User = get_user_model()


class V2ProfileTests(TestCase):
    def test_student_profile_defaults(self):
        profile = User.objects.create_user(username='jane', email='j@example.com', password='x').student_profile
        self.assertEqual(profile.display_name, '')
        self.assertTrue(profile.notify_answers and profile.notify_live and profile.notify_certificate)
        self.assertFalse(profile.notify_marketing)
        self.assertEqual(profile.dismissed_steps, [])
        profile.dismissed_steps = ['cpf', 'cert:bls']
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.dismissed_steps, ['cpf', 'cert:bls'])

    def test_creator_notify_new_questions_defaults_off(self):
        creator = User.objects.create_user(username='c', email='c@example.com', password='x', role=User.Role.CREATOR).creator_profile
        self.assertFalse(creator.notify_new_questions)

    def test_notification_ordering_and_unread(self):
        user = User.objects.create_user(username='jane', email='j@example.com', password='x')
        first = Notification.objects.create(user=user, kind='answer', title='Primeiro', url='/community/')
        second = Notification.objects.create(user=user, kind='live', title='Segundo', url='/ao-vivo/')
        self.assertEqual(list(Notification.objects.filter(user=user)), [second, first])
        self.assertEqual(Notification.objects.filter(user=user, read_at__isnull=True).count(), 2)
