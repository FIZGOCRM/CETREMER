import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Course, Enrollment
from users.models import FirstAccessCode


User = get_user_model()


class FirstAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin-first-access', email='admin@example.com',
            password='AdminPassword123!', role=User.Role.ADMIN, is_staff=True,
            is_superuser=True,
        )
        self.course = Course.objects.create(
            title='Curso de teste', slug='curso-primeiro-acesso',
            creator=self.admin.creator_profile,
        )

    def create_student_in_panel(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('painel:students'), {
            'action': 'enroll', 'email': 'aluna@example.com',
            'full_name': 'Aluna Teste', 'course_id': self.course.id,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        code = re.search(r'\b\d{10}\b', response.content.decode())
        self.assertIsNotNone(code)
        return User.objects.get(email='aluna@example.com'), code.group()

    def test_admin_creates_student_without_email_and_student_sets_password(self):
        user, code = self.create_student_in_panel()
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(user.has_usable_password())
        self.assertTrue(Enrollment.objects.filter(student=user.student_profile, course=self.course).exists())
        self.client.logout()
        response = self.client.post(reverse('first_access'), {
            'email': user.email, 'code': code,
            'password': 'NewPassword123!', 'password_confirm': 'NewPassword123!',
        }, follow=True)
        self.assertContains(response, 'Senha criada')
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPassword123!'))
        self.assertFalse(FirstAccessCode.objects.filter(user=user).exists())
        self.assertTrue(self.client.login(username=user.email, password='NewPassword123!'))

    def test_wrong_expired_and_reused_codes_are_rejected(self):
        user, code = self.create_student_in_panel()
        self.client.logout()
        data = {'email': user.email, 'code': '0000000000',
                'password': 'NewPassword123!', 'password_confirm': 'NewPassword123!'}
        self.assertContains(self.client.post(reverse('first_access'), data), 'Código inválido')
        self.assertFalse(user.has_usable_password())
        credential = FirstAccessCode.objects.get(user=user)
        credential.expires_at = timezone.now() - timedelta(seconds=1)
        credential.save(update_fields=['expires_at'])
        self.assertContains(self.client.post(reverse('first_access'), {**data, 'code': code}), 'Código inválido')

    def test_code_locks_after_five_failures_and_weak_password_does_not_consume_it(self):
        user, code = self.create_student_in_panel()
        self.client.logout()
        url = reverse('first_access')
        data = {'email': user.email, 'code': '0000000000',
                'password': 'NewPassword123!', 'password_confirm': 'NewPassword123!'}
        for _ in range(5):
            self.assertContains(self.client.post(url, data), 'Código inválido')
        self.assertContains(self.client.post(url, {**data, 'code': code}), 'Código inválido')
        self.client.force_login(self.admin)
        response = self.client.post(reverse('painel:students'), {
            'action': 'generate_first_access', 'student_id': user.id,
        }, follow=True)
        replacement = re.search(r'\b\d{10}\b', response.content.decode()).group()
        self.client.logout()
        self.assertContains(self.client.post(url, {**data, 'code': replacement,
            'password': '1', 'password_confirm': '1'}), '8 caracteres')
        self.assertTrue(FirstAccessCode.objects.filter(user=user).exists())

    def test_admin_can_regenerate_code_for_imported_student(self):
        user = User.objects.create(username='imported', email='imported@example.com')
        user.set_unusable_password()
        user.save(update_fields=['password'])
        self.client.force_login(self.admin)
        response = self.client.post(reverse('painel:students'), {
            'action': 'generate_first_access', 'student_id': user.id,
        }, follow=True)
        self.assertRegex(response.content.decode(), r'\b\d{10}\b')
        self.assertEqual(len(mail.outbox), 0)

    def test_explicit_email_send_reports_failure_when_backend_returns_zero(self):
        from unittest.mock import patch
        user, _ = self.create_student_in_panel()
        with patch('painel.views.send_mail', return_value=0):
            response = self.client.post(reverse('painel:students'), {
                'action': 'resend_access', 'student_id': user.id,
            }, follow=True)
        self.assertContains(response, 'não foi enviado')
