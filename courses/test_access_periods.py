from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Course, Enrollment, Lesson, Module, Progress
from users.models import User


class AccessPeriodTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.creator = User.objects.create_user(
            username="doctor-access", role=User.Role.CREATOR
        )
        self.user = User.objects.create_user(
            username="period-student", email="period@example.com"
        )
        self.course = Course.objects.create(
            title="BLS", slug="period-bls", creator=self.creator.creator_profile
        )
        self.lesson = Lesson.objects.create(
            module=Module.objects.create(course=self.course, title="M1"), title="A1"
        )
        self.enrollment = Enrollment.objects.create(
            student=self.user.student_profile, course=self.course
        )
        self.client.force_login(self.user)

    def managed_period(self, *, start=-30, end=0, grace=3):
        from courses.models import AccessPeriod

        self.enrollment.access_policy = "periods"
        self.enrollment.save(update_fields=["access_policy"])
        return AccessPeriod.objects.create(
            enrollment=self.enrollment,
            starts_on=self.today + timedelta(days=start),
            ends_on=self.today + timedelta(days=end),
            grace_days=grace,
            source="legacy",
            reference="legacy-period-1",
        )

    def test_existing_administrative_enrollment_still_allows_access(self):
        from courses.access import access_decision

        self.assertTrue(access_decision(self.enrollment, on=self.today).allowed)

    def test_end_is_exclusive_and_three_grace_days_are_exact(self):
        from courses.access import access_decision

        self.managed_period()
        self.assertEqual(
            access_decision(self.enrollment, on=self.today - timedelta(days=1)).state,
            "active",
        )
        for day in range(3):
            self.assertEqual(
                access_decision(
                    self.enrollment, on=self.today + timedelta(days=day)
                ).state,
                "grace",
            )
        self.assertFalse(
            access_decision(self.enrollment, on=self.today + timedelta(days=3)).allowed
        )

    def test_future_or_missing_paid_period_does_not_grant_access(self):
        from courses.access import access_decision

        self.managed_period(start=5, end=35)
        self.assertFalse(access_decision(self.enrollment, on=self.today).allowed)
        self.enrollment.access_periods.all().delete()
        self.assertFalse(access_decision(self.enrollment, on=self.today).allowed)

    def test_invalid_period_is_rejected(self):
        period = self.managed_period()
        period.ends_on = period.starts_on
        with self.assertRaises(ValidationError):
            period.full_clean()

    def test_expired_course_blocks_lesson_progress_and_community(self):
        from community.models import CommunityPost

        self.managed_period(end=-4)
        self.assertEqual(
            self.client.get(
                reverse("lesson_detail", args=[self.course.slug, self.lesson.id])
            ).status_code,
            403,
        )
        for endpoint in ["complete_lesson", "toggle_progress"]:
            self.assertEqual(
                self.client.post(reverse(endpoint, args=[self.lesson.id])).status_code,
                403,
            )
        self.assertFalse(Progress.objects.exists())
        response = self.client.post(
            reverse("create_post", args=[self.course.slug]),
            {"title": "Question", "content": "Text"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(CommunityPost.objects.exists())

    def test_expired_course_does_not_block_other_course_or_delete_history(self):
        self.managed_period(end=-4)
        other = Course.objects.create(
            title="Other", slug="other-access", creator=self.creator.creator_profile
        )
        Enrollment.objects.create(student=self.user.student_profile, course=other)
        lesson = Lesson.objects.create(
            module=Module.objects.create(course=other, title="M2"), title="A2"
        )
        Progress.objects.create(
            student=self.user.student_profile, lesson=self.lesson, is_completed=True
        )
        self.assertEqual(
            self.client.get(
                reverse("lesson_detail", args=[other.slug, lesson.id])
            ).status_code,
            200,
        )
        self.assertTrue(Progress.objects.filter(lesson=self.lesson).exists())
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Encerrado")

    def test_live_and_community_read_access_are_also_restricted(self):
        from community.models import CommunityPost

        self.course.live_meet_url = "https://meet.google.com/private-course-link"
        self.course.save()
        post = CommunityPost.objects.create(
            author=self.user,
            course=self.course,
            title="Private question",
            content="Secret content",
        )
        self.managed_period(end=-4)
        self.assertNotContains(
            self.client.get(reverse("live_classes")), "private-course-link"
        )
        self.assertNotContains(
            self.client.get(reverse("dashboard")), "private-course-link"
        )
        self.assertContains(
            self.client.get(reverse("community_hub"), {"curso": "todos"}),
            "Secret content",
        )
        self.assertEqual(
            self.client.post(
                reverse("create_comment", args=[post.id]), {"content": "Reply"}
            ).status_code,
            403,
        )

    def test_new_certificate_is_blocked_but_issued_certificate_is_preserved(self):
        from courses.services import issue_enrollment_certificate

        profile = self.user.student_profile
        profile.full_name, profile.cpf = "Aluno Teste", "52998224725"
        profile.save()
        Progress.objects.create(student=profile, lesson=self.lesson, is_completed=True)
        certificate = issue_enrollment_certificate(self.enrollment)
        self.managed_period(end=-4)
        url = reverse("issue_certificate", args=[self.course.slug])
        self.assertContains(self.client.get(url), certificate.student_name)
        certificate.delete()
        self.assertEqual(self.client.post(url).status_code, 403)

    def test_administrative_removal_preserves_paid_period_history(self):
        self.managed_period()
        self.creator.is_staff = True
        self.creator.save()
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("painel:students"),
            {
                "action": "unenroll",
                "student_id": self.user.id,
                "course_id": self.course.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Enrollment.objects.filter(pk=self.enrollment.pk).exists())
