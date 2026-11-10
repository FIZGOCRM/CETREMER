from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class HandoffPhaseZeroTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='phase0-student', password='StrongPassword123!', role=User.Role.STUDENT,
        )
        self.staff = User.objects.create_user(
            username='phase0-staff', password='StrongPassword123!', is_staff=True,
        )

    def test_public_placeholders_and_site_context(self):
        response = self.client.get(reverse('password_reset'))
        self.assertContains(response, 'Esqueci minha senha')
        self.assertContains(response, 'css/cetremer.css')
        response = self.client.get(reverse('verify_certificate'))
        self.assertContains(response, 'Verificar certificado')

    def test_student_placeholders_render_with_sidebar(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('live_classes'))
        self.assertContains(response, 'Aulas ao vivo')
        response = self.client.get(reverse('certificates'))
        self.assertContains(response, 'Certificados')

    def test_panel_placeholders_are_namespaced_and_restricted(self):
        panel_names = ('dashboard', 'courses', 'students', 'orders', 'community', 'settings')
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('painel:dashboard')).status_code, 403)
        self.client.force_login(self.staff)
        for name in panel_names:
            response = self.client.get(reverse(f'painel:{name}'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'base_admin.html')
            self.assertContains(response, 'css/cetremer.css')

    def test_complete_lesson_unknown_lesson_returns_404(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('complete_lesson', kwargs={'lesson_id': 1}))
        self.assertEqual(response.status_code, 404)
