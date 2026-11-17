from datetime import timedelta
from uuid import uuid4

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.access import access_decision
from courses.models import AccessPeriod, Course, Enrollment
from users.models import User


class ManualPeriodTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="period-owner", role=User.Role.CREATOR)
        self.student = User.objects.create_user(username="period-student")
        self.course = Course.objects.create(title="Curso", slug="manual-period", creator=self.admin.creator_profile)
        self.other = Course.objects.create(title="Outro", slug="manual-other", creator=self.admin.creator_profile)
        self.enrollment = Enrollment.objects.create(student=self.student.student_profile, course=self.course)
        self.other_enrollment = Enrollment.objects.create(student=self.student.student_profile, course=self.other)
        self.client.force_login(self.admin)
        self.today = timezone.localdate()

    def data(self, **changes):
        data = {"action": "grant_period", "student_id": self.student.pk, "course_id": self.course.pk,
                "starts_on": str(self.today), "paid_through": str(self.today + timedelta(days=29)),
                "reference": str(uuid4()), "confirm_periods": "on"}
        return {**data, **changes}

    def test_inclusive_end_idempotent_and_separate_courses(self):
        payload = self.data()
        self.client.post(reverse("painel:students"), payload)
        self.client.post(reverse("painel:students"), payload)
        period = AccessPeriod.objects.get(enrollment=self.enrollment)
        self.assertEqual(period.ends_on, self.today + timedelta(days=30))
        self.assertEqual(period.grace_days, 3)
        self.assertEqual(period.created_by, self.admin)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.access_policy, "periods")
        self.assertTrue(access_decision(self.enrollment).allowed)
        self.assertFalse(access_decision(self.enrollment, on=period.ends_on+timedelta(days=3)).allowed)
        self.other_enrollment.refresh_from_db()
        self.assertEqual(self.other_enrollment.access_policy, "unrestricted")
        self.assertFalse(AccessPeriod.objects.filter(enrollment=self.other_enrollment).exists())

    def test_invalid_dates_missing_confirmation_and_overlap_do_not_replace_history(self):
        for payload in [self.data(paid_through=str(self.today-timedelta(days=1))),
                        self.data(confirm_periods=""), self.data(paid_through="9999-12-31")]:
            self.client.post(reverse("painel:students"), payload)
            self.assertFalse(AccessPeriod.objects.exists())
        self.client.post(reverse("painel:students"), self.data())
        self.client.post(reverse("painel:students"), self.data())
        self.assertEqual(AccessPeriod.objects.count(), 1)

    def test_expired_grant_does_not_reopen_access_and_student_cannot_grant(self):
        self.client.post(reverse("painel:students"), self.data(
            starts_on=str(self.today-timedelta(days=20)), paid_through=str(self.today-timedelta(days=5))))
        self.enrollment.refresh_from_db()
        self.assertFalse(access_decision(self.enrollment).allowed)
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(reverse("painel:students"), self.data()).status_code, 403)
        self.assertEqual(AccessPeriod.objects.count(), 1)
