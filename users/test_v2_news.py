from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from courses.models import Course, Enrollment, Lesson, LessonMaterial, LiveEvent, LiveReminder, Module
from users.models import EmailLog, Notification, User
from users.notifications import email_is_current, run_daily_notifications, run_live_reminders


class CourseNewsTests(TestCase):
    def setUp(self):
        creator = User.objects.create_user(username="creator", role="CREATOR")
        self.user = User.objects.create_user(username="member", email="member@example.test")
        self.course = Course.objects.create(creator=creator.creator_profile, slug="mentoria", is_published=True)
        self.enrollment = Enrollment.objects.create(course=self.course, student=self.user.student_profile)
        self.module = Module.objects.create(course=self.course)
        self.lesson = Lesson.objects.create(module=self.module, published_at=timezone.now())
        self.material = LessonMaterial.objects.create(lesson=self.lesson, file="materials/example.pdf")
        self.event = LiveEvent.objects.create(course=self.course, starts_at=timezone.now()-timedelta(days=1))
        self.event.recording_url = "https://vimeo.com/123"
        self.event.save(update_fields=["recording_url"])

    def test_quarter_hour_and_daily_share_publication_identity(self):
        run_live_reminders()
        kinds = {"new_lesson", "new_ebook", "new_recording"}
        self.assertEqual(set(Notification.objects.values_list("kind", flat=True)), kinds)
        self.lesson.published_at = timezone.now()
        self.lesson.save()
        self.material.file = "materials/replaced.pdf"
        self.material.save()
        original = self.event.recording_added_at
        self.event.recording_url = "https://vimeo.com/456"
        self.event.save()
        self.assertEqual(original, self.event.recording_added_at)
        run_daily_notifications()
        run_live_reminders()
        self.assertEqual(Notification.objects.filter(kind__in=kinds).count(), 3)
        self.assertEqual(EmailLog.objects.filter(kind__in=kinds).count(), 3)
        self.enrollment.access_policy = "periods"
        self.enrollment.save()
        self.assertFalse(any(email_is_current(log) for log in EmailLog.objects.all()))

    def test_interrupted_publication_retries_both_channels(self):
        with patch("users.notifications._email_log", side_effect=RuntimeError("interrupted")):
            with self.assertRaises(RuntimeError):
                run_live_reminders()
        self.assertFalse(Notification.objects.filter(kind="new_lesson").exists())
        run_live_reminders()
        self.assertEqual(Notification.objects.filter(kind="new_lesson").count(), 1)
        self.assertEqual(EmailLog.objects.filter(kind="new_lesson").count(), 1)

    def test_unreleased_ebook_and_opt_out(self):
        self.module.release_month = 2
        self.module.save()
        self.user.student_profile.email_live_events = False
        self.user.student_profile.save()
        run_live_reminders()
        self.assertEqual(list(Notification.objects.values_list("kind", flat=True)), ["new_recording"])
        self.assertFalse(EmailLog.objects.exists())

    def test_opt_in_windows_are_independent_and_deduplicated(self):
        now = timezone.now()
        self.event.starts_at = now + timedelta(hours=24)
        self.event.save()
        LiveReminder.objects.create(student=self.user.student_profile, event=self.event)
        for tick in (now, now, now+timedelta(hours=23), now+timedelta(hours=23)):
            with patch("users.notifications.timezone.now", return_value=tick):
                run_live_reminders()
        for kind in ("live_reminder_24h", "live_reminder"):
            self.assertEqual(Notification.objects.filter(kind=kind).count(), 1)
            self.assertEqual(EmailLog.objects.filter(kind=kind).count(), 1)

