from io import StringIO

from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings

from courses.models import Course, Enrollment
from users.models import User


class DemoPreparationTests(TestCase):
    def test_refuses_without_demo_mode(self):
        with self.assertRaises(CommandError):
            call_command("prepare_demo", password="DemoPassword123!", stdout=StringIO())

    @override_settings(GOMUT_DEMO_MODE=True)
    def test_creates_only_two_courses_and_preserves_other_data_on_rerun(self):
        User.objects.create_user(username="preserve-this-user")
        call_command("prepare_demo", password="DemoPassword123!", stdout=StringIO())
        call_command("prepare_demo", password="ChangedPassword123!", stdout=StringIO())
        self.assertEqual(Course.objects.filter(slug__startswith="gomut-demo-").count(), 2)
        student = User.objects.get(username="gomut-demo-student")
        self.assertTrue(student.check_password("DemoPassword123!"))
        self.assertEqual(Enrollment.objects.filter(student=student.student_profile).count(), 2)
        self.assertTrue(User.objects.filter(username="preserve-this-user").exists())
