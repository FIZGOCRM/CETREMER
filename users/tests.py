from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class PublicAccountTests(TestCase):
    def test_registration_ignores_submitted_role(self):
        for role in ('CREATOR', 'ADMIN'):
            username = role.lower()
            response = self.client.post(reverse('register'), {
                'full_name': username,
                'email': f'{username}@example.com',
                'password': 'ComplexStudentPassword123!',
                'password_confirm': 'ComplexStudentPassword123!',
                'terms': 'on',
                'role': role,
            })
            self.assertEqual(response.status_code, 302)
            user = User.objects.get(email=f'{username}@example.com')
            self.assertEqual(user.role, User.Role.STUDENT)
            self.assertTrue(hasattr(user, 'student_profile'))
            self.assertFalse(hasattr(user, 'creator_profile'))
            self.client.logout()

    def test_registration_rejects_weak_password(self):
        response = self.client.post(reverse('register'), {
            'full_name': 'Weak Student', 'email': 'weak@example.com', 'password': '1',
            'password_confirm': '1', 'terms': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='weakstudent').exists())

    def test_password_change_rejects_weak_password(self):
        user = User.objects.create_user(username='student', password='OldStrongPassword123!', role=User.Role.STUDENT)
        self.client.force_login(user)
        response = self.client.post(reverse('settings'), {
            'action': 'password', 'password_old': 'OldStrongPassword123!',
            'password_new': '1', 'password_confirm': '1',
        })
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('OldStrongPassword123!'))
