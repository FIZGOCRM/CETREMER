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

    def test_login_uses_gomut_design_without_public_signup(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "gm-login__cartao")
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
