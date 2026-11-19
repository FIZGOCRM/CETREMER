from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import SiteSettings, User
from .models import (
    Course, Enrollment, Lesson, LessonMaterial, LiveEvent, Module, Progress,
    SavedLesson, WeeklySelection, WeeklySelectionItem,
)


class CourseHomeTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="mentor", role="CREATOR")
        self.user = User.objects.create_user(username="membro")
        self.student = self.user.student_profile
        self.course = self.make_course("principal")
        self.enrollment = Enrollment.objects.create(course=self.course, student=self.student, plan_started_on=timezone.localdate())
        self.module = Module.objects.create(course=self.course, title="Respiração")
        self.a = Lesson.objects.create(module=self.module, title="Aula inicial", duration_seconds=600)
        self.b = Lesson.objects.create(module=self.module, title="Aula posterior", duration_seconds=300, order=1)
        self.now = timezone.now()
        self.client.force_login(self.user)

    def make_course(self, slug):
        return Course.objects.create(title=slug, slug=slug, creator=self.owner.creator_profile, is_published=True)

    def page(self, name):
        return self.client.get(reverse(name, args=[self.course.slug]))

    def test_dashboard_opens_only_active_course_and_many_offer_a_choice(self):
        response = self.client.get(reverse("dashboard"))
        self.assertTemplateUsed(response, "courses/course_home.html")
        other = self.make_course("segundo")
        Enrollment.objects.create(student=self.student, course=other)
        response = self.client.get(reverse("dashboard"))
        self.assertTemplateUsed(response, "courses/dashboard.html")
        self.assertContains(response, reverse("course_home", args=[other.slug]))

    def test_all_interrupted_sorted_with_resume_and_completed_omitted(self):
        Progress.objects.create(lesson=self.a, student=self.student, last_position_seconds=92, started_at=self.now-timedelta(days=1))
        Progress.objects.create(lesson=self.b, student=self.student, started_at=self.now, last_position_seconds=66)
        response = self.page("course_home")
        self.assertEqual(response.context["resume"]["lesson"], self.b)
        self.assertEqual([card["lesson"] for card in response.context["interrupted"]], [self.b, self.a])
        self.assertContains(response, "Aula 2 · Aula posterior · 4 min restantes")
        self.assertContains(response, "01:32")
        Progress.objects.filter(student=self.student, lesson=self.b).update(is_completed=True)
        self.assertEqual(self.page("course_home").context["resume"]["lesson"], self.a)

    def test_top_ten_last_effective_selection_with_no_fallback_for_hidden_items(self):
        monday = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        for offset, lesson in ((-14, self.a), (-7, self.b), (7, self.a)):
            week = WeeklySelection.objects.create(course=self.course, week_start=monday+timedelta(days=offset))
            WeeklySelectionItem.objects.create(selection=week, lesson=lesson, position=1)
        self.assertEqual([c["lesson"] for c in self.page("course_home").context["weekly"]], [self.b])
        self.b.status = "draft"
        self.b.save()
        self.assertFalse(self.page("course_home").context["weekly"])

    def test_recent_content_uses_publication_times_and_checks_access(self):
        self.a.published_at = self.now-timedelta(days=13)
        self.a.save()
        self.b.published_at = self.now-timedelta(days=15)
        self.b.save()
        material = LessonMaterial.objects.create(lesson=self.b, title="Caderno novo", url="https://example.org/test.pdf")
        recording = LiveEvent.objects.create(title="Gravação nova", starts_at=self.now-timedelta(days=2), recording_url="https://example.org/video")
        unrelated = self.make_course("outra")
        LiveEvent.objects.create(title="Evento particular", course=unrelated, starts_at=self.now-timedelta(days=2), recording_url="https://example.org/outro")
        response = self.page("course_news")
        self.assertContains(response, self.a.title)
        self.assertNotContains(response, self.b.title)
        self.assertContains(response, reverse("material_open", args=["lesson", material.pk]))
        self.assertContains(response, reverse("live_link", args=[recording.pk, "gravacao"]))
        self.assertNotContains(response, "Evento particular")
        self.module.release_month = 3
        self.module.save()
        response = self.page("course_news")
        self.assertNotContains(response, self.a.title)
        self.assertNotContains(response, material.title)

    def test_personal_list_scoped_to_student_course_and_release(self):
        SavedLesson.objects.create(student=self.student, lesson=self.b)
        other = User.objects.create_user(username="vizinho").student_profile
        SavedLesson.objects.create(student=other, lesson=self.a)
        response = self.page("course_saved")
        self.assertContains(response, self.b.title)
        self.assertNotContains(response, self.a.title)
        self.module.release_month = 2
        self.module.save()
        self.assertNotContains(self.page("course_saved"), self.b.title)

    def test_only_unenrolled_offers_and_contextual_school_contact(self):
        site = SiteSettings.load()
        site.whatsapp = "+55 (67) 99999-1234"
        site.save()
        other = self.make_course("cardiologia")
        inactive = self.make_course("ja-matriculado")
        Enrollment.objects.create(course=inactive, student=self.student, access_policy="periods")
        response = self.page("course_home")
        self.assertContains(response, "À venda")
        self.assertContains(response, "https://wa.me/5567999991234?")
        self.assertContains(response, other.title)
        self.assertNotContains(response, inactive.title)
        self.assertNotContains(response, "/checkout/")

    def test_reminder_json_and_course_or_global_events_only(self):
        other = self.make_course("curso-extra")
        events = [LiveEvent.objects.create(course=course, title=title, starts_at=self.now+timedelta(days=2))
                  for course, title in ((self.course, "Da mentoria"), (None, "Geral"), (other, "Privado"))]
        response = self.page("course_home")
        self.assertContains(response, "Da mentoria")
        self.assertContains(response, "Geral")
        self.assertNotContains(response, "Privado")
        url = reverse("live_remind", args=[events[0].pk])
        self.assertTrue(self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()["active"])
        self.assertFalse(self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()["active"])

    def test_every_course_page_rejects_outsiders_and_expired_plans(self):
        for role in ("expired", "outsider"):
            if role == "expired":
                self.enrollment.access_policy = "periods"
                self.enrollment.save()
            else:
                self.client.force_login(User.objects.create_user(username="de-fora"))
            for name in ("course_home", "course_saved", "course_news", "course_live", "course_trail", "course_ebooks"):
                with self.subTest(role=role, name=name):
                    response = self.page(name)
                    self.assertEqual(response.status_code, 403)
                    self.assertNotContains(response, self.a.title, status_code=403)
