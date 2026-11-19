from io import StringIO
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase, override_settings

from courses.models import LessonLike, LessonMaterial, LiveEvent, Progress, QuizChoice, SavedLesson, WeeklySelectionItem
from users.models import User


class CourseDemoTests(TestCase):
    @override_settings(GOMUT_DEMO_MODE=True)
    def test_second_run_preserves_the_students_activity_and_weekly_selection(self):
        with TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            for run in range(2):
                call_command("prepare_demo", password="PasswordOnlyForThisTest123!",
                             with_course_experience=True, stdout=StringIO())
                student = User.objects.get(username="aluno-v2").student_profile
                self.assertEqual(student.enrollments.count(), 1)
                self.assertEqual(SavedLesson.objects.filter(student=student).count(), 3)
                self.assertEqual(LessonLike.objects.filter(student=student).count(), 1)
                self.assertEqual(WeeklySelectionItem.objects.count(), 5)
                self.assertEqual(QuizChoice.objects.filter(order=5).exclude(explanation="").count(), 1)
                self.assertTrue(LiveEvent.objects.filter(recording_added_at__isnull=False).exists())
                self.assertGreaterEqual(LessonMaterial.objects.values("lesson__module").distinct().count(), 2)
                progress = Progress.objects.filter(student=student).first()
                if run:
                    self.assertEqual(progress.last_position_seconds, 3)
                else:
                    progress.last_position_seconds = 3
                    progress.save()

