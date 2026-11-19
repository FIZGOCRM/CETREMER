from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses import services
from courses.models import Course, Enrollment, Lesson, Module, Progress
from users.models import User


class EngagementTests(TestCase):
    def setUp(self):
        team = User.objects.create_user(username="editor", role="CREATOR")
        self.user = User.objects.create_user(username="member")
        self.student = self.user.student_profile
        course = Course.objects.create(creator=team.creator_profile, slug="teste", is_published=True)
        self.enrollment = Enrollment.objects.create(course=course, student=self.student)
        self.module = Module.objects.create(course=course)
        self.lesson = Lesson.objects.create(module=self.module, duration_seconds=10)
        self.client.force_login(self.user)

    def test_rewind_preserves_peak_and_first_start(self):
        now = timezone.now()
        services.record_heartbeat(self.student, self.lesson, position=8, playing=True)
        first = Progress.objects.get().started_at
        with patch("courses.services.timezone.now", return_value=now + timedelta(seconds=3)):
            services.record_heartbeat(self.student, self.lesson, position=1, playing=False)
        record = Progress.objects.get()
        self.assertIsNotNone(first)
        self.assertEqual((record.max_position_seconds, record.last_position_seconds, record.started_at), (8, 1, first))

    def test_closing_an_idle_lesson_does_not_steal_the_playing_lessons_time(self):
        other = Lesson.objects.create(module=self.module, duration_seconds=12)
        now = timezone.now()
        for seconds, lesson, position, playing in (
                (0, self.lesson, 0, True), (12, other, 0, False), (15, self.lesson, 10, False)):
            with patch("courses.services.timezone.now", return_value=now + timedelta(seconds=seconds)):
                services.record_heartbeat(self.student, lesson, position=position, playing=playing)
        idle = Progress.objects.get(lesson=other)
        self.assertEqual(idle.watched_seconds, 0)
        self.assertIsNone(idle.started_at)
        self.assertFalse(idle.is_completed)
        self.assertEqual(Progress.objects.get(lesson=self.lesson).watched_seconds, 15)

    def test_manual_and_auto_have_independent_evidence(self):
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        record = Progress.objects.get()
        self.assertIsNotNone(record.manual_completed_at)
        self.assertIsNone(record.auto_completed_at)
        now = timezone.now()
        with patch("courses.services.timezone.now", return_value=now):
            services.record_heartbeat(self.student, self.lesson, position=1, playing=True)
        with patch("courses.services.timezone.now", return_value=now + timedelta(seconds=10)):
            services.record_heartbeat(self.student, self.lesson, position=4, playing=False)
        record.refresh_from_db()
        self.assertIsNotNone(record.auto_completed_at)
        self.assertEqual(record.max_position_seconds, 4)

    def test_reactions_are_independent_idempotent_and_guarded(self):
        from courses.models import SavedLesson, LessonLike
        for kind, model in (("saved", SavedLesson), ("like", LessonLike)):
            url = reverse("lesson_reaction", args=[self.lesson.pk, kind])
            for unused in range(2):
                self.assertTrue(self.client.post(url, {"active": "true"}).json()["active"])
            self.assertEqual(model.objects.count(), 1)
            self.assertFalse(self.client.post(url, {"active": False}, content_type="application/json").json()["active"])
            self.assertFalse(model.objects.exists())
        self.module.status = "draft"
        self.module.save()
        self.assertEqual(self.client.post(url, {"active": "true"}).status_code, 403)
        self.module.status = "published"
        self.module.save()
        self.enrollment.access_policy = "periods"
        self.enrollment.save()
        self.assertEqual(self.client.post(url, {"active": "true"}).status_code, 403)
