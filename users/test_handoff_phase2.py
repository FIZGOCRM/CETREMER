import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from courses.models import Enrollment


User = get_user_model()


class AuthenticationFlowTests(TestCase):
    def test_login_uses_email_and_old_username(self):
        user = User.objects.create_user(username='oldadmin', email='Admin@Example.com', password='StrongPassword123!', is_staff=True)
        self.assertTrue(self.client.login(username='admin@example.com', password='StrongPassword123!'))
        self.client.logout()
        self.assertTrue(self.client.login(username='oldadmin', password='StrongPassword123!'))

    def test_signup_requires_terms_and_creates_student_without_enrollment(self):
        data = {'full_name': 'Maria Teste', 'email': 'Maria@example.com',
                'password': 'StrongPassword123!', 'password_confirm': 'StrongPassword123!'}
        self.assertEqual(self.client.post(reverse('register'), data).status_code, 200)
        self.assertFalse(User.objects.filter(email__iexact=data['email']).exists())
        response = self.client.post(reverse('register'), {**data, 'terms': 'on', 'role': 'ADMIN'})
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email__iexact=data['email'])
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertEqual(user.student_profile.full_name, 'Maria Teste')
        self.assertFalse(Enrollment.objects.filter(student=user.student_profile).exists())

    def test_password_reset_sends_link_and_changes_password(self):
        user = User.objects.create_user(username='student', email='student@example.com', password='OldPassword123!')
        response = self.client.post(reverse('password_reset'), {'email': user.email})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        match = re.search(r'http://testserver(/senha/nova/[^\s]+)', mail.outbox[0].body)
        self.assertIsNotNone(match)
        confirm = self.client.get(match.group(1), follow=True)
        self.assertContains(confirm, 'Criar nova senha')
        response = self.client.post(confirm.request['PATH_INFO'], {
            'new_password1': 'NewPassword123!', 'new_password2': 'NewPassword123!',
        }, follow=True)
        self.assertContains(response, 'Senha criada')
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPassword123!'))
