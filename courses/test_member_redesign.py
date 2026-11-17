from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User
from .models import AccessPeriod, Course, Enrollment, Lesson, Module, Progress


class MemberRedesignTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(username="owner-member", role=User.Role.CREATOR)
        self.student = User.objects.create_user(username="member-test")
        self.course = Course.objects.create(is_published=True, title="Curso Um", slug="curso-um", creator=owner.creator_profile)
        self.other = Course.objects.create(is_published=True, title="Curso Dois", slug="curso-dois", creator=owner.creator_profile)
        self.module = Module.objects.create(course=self.course, title="Fundamentos", order=1)
        self.lesson = Lesson.objects.create(module=self.module, title="Primeira aula", video_url="https://vimeo.com/76979871")
        self.enrollment = Enrollment.objects.create(student=self.student.student_profile, course=self.course)
        self.client.force_login(self.student)

    def detail_url(self, course=None):
        return reverse("member_course", args=[(course or self.course).slug])

    def test_dashboard_has_small_catalog_and_real_course_entry(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "gomut/members.css")
        self.assertContains(response, self.detail_url())
        self.assertNotContains(response, "Top 10")
        self.assertNotContains(response, 'href="/painel/')

    def test_course_detail_lists_only_its_lessons_and_real_progress(self):
        response = self.client.get(self.detail_url())
        self.assertContains(response, "Fundamentos")
        self.assertContains(response, "Primeira aula")
        self.assertContains(response, reverse("lesson_detail", args=[self.course.slug, self.lesson.id]))
        self.assertNotContains(response, "Curso Dois")

    def test_other_course_and_expired_period_do_not_leak_content(self):
        self.assertEqual(self.client.get(self.detail_url(self.other)).status_code, 403)
        self.enrollment.access_policy = Enrollment.AccessPolicy.PERIODS
        self.enrollment.save()
        today = timezone.localdate()
        AccessPeriod.objects.create(enrollment=self.enrollment, starts_on=today-timedelta(days=10),
                                    ends_on=today-timedelta(days=4), grace_days=3,
                                    source="manual", reference="expired")
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, "player.vimeo.com", status_code=403)
        response = self.client.post(reverse("complete_lesson", args=[self.lesson.id]))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Progress.objects.exists())

    def test_lesson_keeps_real_vimeo_and_private_notes_without_pending_features(self):
        response = self.client.get(reverse("lesson_detail", args=[self.course.slug, self.lesson.id]))
        self.assertContains(response, "https://player.vimeo.com/video/76979871")
        self.assertNotContains(response, "Necessita de backend")
        self.assertContains(response, 'Anotações')
        self.assertContains(response, "data-complete-url")

    def test_course_detail_requires_session(self):
        self.client.logout()
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_progress_page_shows_actual_completions_and_only_flags_missing_metrics(self):
        Progress.objects.create(student=self.student.student_profile, lesson=self.lesson, is_completed=True)
        response = self.client.get(reverse("member_section", args=["progresso"]))
        self.assertContains(response, "Aulas concluídas")
        self.assertContains(response, "Curso Um")
        self.assertEqual(response.context["completed_count"], 1)

    def test_hero_has_only_enrolled_accessible_courses_and_labels_by_progress(self):
        Lesson.objects.create(module=self.module, title="Segunda aula", order=2)
        Progress.objects.create(student=self.student.student_profile, lesson=self.lesson, is_completed=True)
        module = Module.objects.create(course=self.other, title="Outro módulo")
        Lesson.objects.create(module=module, title="Outra aula")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual([item["course"] for item in response.context["hero_courses"]], [self.course])
        self.assertContains(response, "Continuar")
        Enrollment.objects.create(student=self.student.student_profile, course=self.other)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(len(response.context["hero_courses"]), 2)
        self.assertContains(response, "Começar")
        self.assertContains(response, 'aria-label="Próximo curso"')
        self.enrollment.access_policy = Enrollment.AccessPolicy.PERIODS
        self.enrollment.save()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual([item["course"] for item in response.context["hero_courses"]], [self.other, self.course])
