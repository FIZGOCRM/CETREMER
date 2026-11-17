from django.test import TestCase
from django.urls import reverse

from .models import User


class LoginRedesignTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="demo-login", email="aluno@example.test", password="ExamplePassword123!"
        )
        self.admin = User.objects.create_user(
            username="demo-admin", password="ExamplePassword123!", role=User.Role.ADMIN
        )

    def test_student_login_uses_member_design_without_public_signup(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "member-login__box")
        self.assertContains(response, "Archivo:wdth,wght")
        self.assertNotContains(response, 'href="/register/"')

    def test_student_and_admin_have_separate_default_destinations(self):
        for user, destination in [(self.student, "dashboard"), (self.admin, "painel:dashboard")]:
            self.client.logout()
            response = self.client.post(reverse("login"), {
                "username": user.username, "password": "ExamplePassword123!"
            })
            self.assertRedirects(response, reverse(destination), fetch_redirect_response=False)

    def test_external_next_cannot_redirect_login_or_authenticated_user(self):
        response = self.client.post(reverse("login"), {
            "username": self.student.email, "password": "ExamplePassword123!",
            "next": "https://untrusted.example/",
        })
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

        response = self.client.get(reverse("login"), {"next": "//untrusted.example/"})
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    def test_anonymous_panel_entry_uses_gomut_login_and_keeps_destination(self):
        for path in ('/painel/','/painel/alunos/?q=teste','/painel/cursos/999/aulas/'):
            response=self.client.get(path,follow=True)
            self.assertTemplateUsed(response,'login_admin.html')
            self.assertContains(response,'Painel do produtor')
            self.assertContains(response,'css/gomut/login.css')
            self.assertNotContains(response,'member-login__box')
            self.assertEqual(response.context['next'],path)

    def test_screenshot_login_url_and_failed_post_keep_producer_identity(self):
        response=self.client.get('/login/?next=/painel/')
        self.assertTemplateUsed(response,'login_admin.html')
        self.assertContains(response,'action="/login/?acesso=admin"')
        response=self.client.post('/login/',{'username':self.admin.username,'password':'incorrect','next':'/painel/alunos/'})
        self.assertTemplateUsed(response,'login_admin.html')
        self.assertContains(response,'E-mail ou senha incorretos')
        self.assertContains(response,'Painel do produtor')
        self.assertEqual(response.context['next'],'/painel/alunos/')

    def test_producer_context_respects_path_boundary_and_safe_next(self):
        response=self.client.get('/login/',{'next':'http://testserver/painel/alunos/'})
        self.assertTemplateUsed(response,'login_admin.html')
        for target in ('/painel-falso/','https://untrusted.example/painel/'):
            response=self.client.get('/login/',{'next':target})
            self.assertTemplateUsed(response,'login.html')

    def test_admin_login_returns_to_requested_panel_with_gomut_layout(self):
        response=self.client.post('/login/?next=/painel/alunos/',{'username':self.admin.username,'password':'ExamplePassword123!'},follow=True)
        self.assertEqual(response.request['PATH_INFO'],'/painel/alunos/')
        self.assertTemplateUsed(response,'base_painel_gomut.html')
        self.assertContains(response,'gomut/marca/gomut-logo.png')
        self.assertNotContains(response,'member-login__box')

    def test_producer_logout_returns_to_gomut_login_student_logout_to_member(self):
        self.client.force_login(self.admin)
        response=self.client.post('/logout/',follow=True)
        self.assertTemplateUsed(response,'login_admin.html')
        self.client.force_login(self.student)
        response=self.client.post('/logout/',follow=True)
        self.assertTemplateUsed(response,'login.html')
