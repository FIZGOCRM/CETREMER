from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from courses.models import Course, Lesson
from painel import tests as panel_tests
from users.models import User


class InputValidationTests(TestCase):
    setUp = panel_tests.PanelFlowTests.setUp

    def test_invalid_price_is_not_silently_converted_to_free_course(self):
        for price in ("invalid", "-10", "NaN", "Infinity"):
            with self.subTest(price=price):
                response = self.client.post(
                    reverse("painel:course_new"), {"title": "Invalid", "price": price}
                )
                self.assertEqual(response.status_code, 200)
                self.assertFalse(Course.objects.filter(title="Invalid").exists())

    def test_invalid_material_does_not_partially_save_lesson(self):
        response = self.client.post(
            reverse("painel:course_lessons", args=[self.course.id]),
            {
                "action": "save_lesson",
                "lesson_id": self.lesson.id,
                "module_id": self.module.id,
                "title": "Changed",
                "materials": SimpleUploadedFile(
                    "not.pdf", b"not a pdf", content_type="text/plain"
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "Introdução")
        self.assertFalse(self.lesson.materials.exists())

    def test_negative_duration_does_not_create_lesson(self):
        self.client.post(
            reverse("painel:course_lessons", args=[self.course.id]),
            {
                "action": "save_lesson",
                "module_id": self.module.id,
                "title": "Invalid",
                "duration_minutes": "-1",
            },
        )
        self.assertFalse(Lesson.objects.filter(title="Invalid").exists())

    def test_invalid_manual_email_does_not_create_account(self):
        self.client.post(
            reverse("painel:students"),
            {
                "action": "enroll",
                "course_id": self.course.id,
                "email": "not-an-email",
                "full_name": "Student",
            },
        )
        self.assertFalse(User.objects.filter(email="not-an-email").exists())

    def test_foreign_module_does_not_receive_lesson(self):
        self.client.post(
            reverse("painel:course_lessons", args=[self.course.id]),
            {
                "action": "save_lesson",
                "module_id": "999999",
                "title": "Invalid",
            },
        )
        self.assertFalse(Lesson.objects.filter(title="Invalid").exists())

    def test_long_course_titles_generate_unique_bounded_slugs(self):
        for _ in range(2):
            response = self.client.post(
                reverse("painel:course_new"),
                {
                    "title": "Emergency medicine training " * 5,
                    "price": "100",
                },
            )
            self.assertEqual(response.status_code, 302)
        courses = Course.objects.filter(title__startswith="Emergency")
        self.assertEqual(courses.count(), 2)
        self.assertEqual(len(set(courses.values_list("slug", flat=True))), 2)
        self.assertTrue(all(len(course.slug) <= 50 for course in courses))

    def test_invalid_identifiers_return_user_errors(self):
        cases = [
            ("painel:students", [], {"action": "enroll", "student_id": "abc"}),
            (
                "painel:course_lessons",
                [self.course.id],
                {"action": "save_lesson", "module_id": "abc"},
            ),
            (
                "painel:course_lessons",
                [self.course.id],
                {"action": "save_lesson", "lesson_id": "abc"},
            ),
        ]
        for name, args, data in cases:
            with self.subTest(name=name, data=data):
                self.assertEqual(
                    self.client.post(reverse(name, args=args), data).status_code, 302
                )
        self.assertEqual(
            self.client.get(reverse("painel:students"), {"aluno": "abc"}).status_code,
            400,
        )
        self.assertEqual(
            self.client.get(
                reverse("painel:course_lessons", args=[self.course.id]), {"aula": "abc"}
            ).status_code,
            400,
        )
