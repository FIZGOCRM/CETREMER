from django.test import TestCase
from django.urls import reverse

from courses.models import Certificate, Course, Enrollment, Lesson, Module, Progress
from users.models import User


class CertificateHttpTests(TestCase):
    def setUp(self):
        creator = User.objects.create_user(username="doctor", role=User.Role.CREATOR)
        self.student = User.objects.create_user(username="learner")
        self.profile = self.student.student_profile
        self.profile.full_name = "Aluno Teste"
        self.profile.cpf = "52998224725"
        self.profile.save()
        self.course = Course.objects.create(is_published=True, 
            title="BLS", slug="bls", creator=creator.creator_profile
        )
        self.lesson = Lesson.objects.create(
            module=Module.objects.create(course=self.course, title="M1"), title="A1"
        )
        self.enrollment = Enrollment.objects.create(
            student=self.profile, course=self.course
        )
        Progress.objects.create(
            student=self.profile, lesson=self.lesson, is_completed=True
        )
        self.url = reverse("issue_certificate", args=[self.course.slug])
        self.client.force_login(self.student)

    def test_get_shows_issue_action_without_creating_certificate(self):
        self.assertContains(self.client.get(self.url), "Emitir certificado")
        self.assertFalse(Certificate.objects.exists())

    def test_post_issues_once_and_get_only_displays_snapshot(self):
        first = self.client.post(self.url)
        self.assertRedirects(first, self.url)
        certificate = Certificate.objects.get(enrollment=self.enrollment)
        self.assertRedirects(self.client.post(self.url), self.url)
        self.assertEqual(Certificate.objects.count(), 1)
        self.profile.full_name = "Nome alterado"
        self.profile.save()
        Progress.objects.filter(student=self.profile).update(is_completed=False)
        self.assertContains(self.client.get(self.url), certificate.student_name)
        self.assertEqual(Certificate.objects.get().code, certificate.code)

    def test_incomplete_student_cannot_issue(self):
        Progress.objects.all().delete()
        self.client.post(self.url)
        self.assertFalse(Certificate.objects.exists())

    def test_completion_and_toggle_keep_points_consistent(self):
        Progress.objects.all().delete()
        complete = reverse("complete_lesson", args=[self.lesson.id])
        self.client.post(complete)
        self.client.post(complete)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.points, 10)
        self.client.post(reverse("toggle_progress", args=[self.lesson.id]))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.points, 0)
