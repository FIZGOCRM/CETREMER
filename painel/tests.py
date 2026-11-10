import json
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from courses.models import Course, Enrollment, Lesson, Module
from users.models import SiteSettings

User = get_user_model()


class PanelFlowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password='StrongPassword123!', role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.student = User.objects.create_user(username='student', email='student@example.com', password='StrongPassword123!')
        self.course = Course.objects.create(title='BLS', slug='bls', creator=self.admin.creator_profile)
        self.module = Module.objects.create(course=self.course, title='Primeiro', order=1)
        self.lesson = Lesson.objects.create(module=self.module, title='Introdução', order=1)
        self.client.force_login(self.admin)

    def test_import_preview_and_confirm_creates_unusable_password_and_enrollment(self):
        upload = SimpleUploadedFile('alunos.csv', 'nome;email;cpf\nMaria Silva;maria@example.com;52998224725\n'.encode())
        response = self.client.post(reverse('painel:students_import'), {'courses': [self.course.id], 'file': upload})
        self.assertContains(response, 'Novo aluno')
        self.assertFalse(User.objects.filter(email='maria@example.com').exists())
        response = self.client.post(reverse('painel:students_import'), {'action': 'confirm'})
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email='maria@example.com')
        self.assertFalse(user.has_usable_password())
        self.assertTrue(Enrollment.objects.filter(student=user.student_profile, course=self.course, source='import').exists())
        self.assertNotIn('import_preview', self.client.session)

    def test_reorder_rejects_outsider_id_and_accepts_complete_payload(self):
        url = reverse('painel:course_reorder', args=[self.course.id])
        bad = self.client.post(url, data=json.dumps({'modules': [self.module.id], 'lessons': {str(self.module.id): [999]}}), content_type='application/json')
        self.assertEqual(bad.status_code, 400)
        good = self.client.post(url, data=json.dumps({'modules': [self.module.id], 'lessons': {str(self.module.id): [self.lesson.id]}}), content_type='application/json')
        self.assertEqual(good.json(), {'ok': True})

    def test_settings_secrets_are_encrypted_and_never_rendered(self):
        self.client.post(reverse('painel:settings'), {'school_name': 'CETREMER', 'gateway_key': 'supersecret1234', 'email_password': 'secretSMTP'})
        site = SiteSettings.load()
        self.assertNotIn('supersecret1234', site.gateway_key_encrypted)
        response = self.client.get(reverse('painel:settings'))
        self.assertNotContains(response, 'supersecret1234')
        self.assertContains(response, '1234')

    def test_student_cannot_enter_panel(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('painel:dashboard')).status_code, 403)
