from io import StringIO

from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings

from courses.models import Course, Enrollment
from users.models import User


class DemoPreparationTests(TestCase):
    def setUp(self):
        from tempfile import TemporaryDirectory
        self.folder = TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.media = override_settings(MEDIA_ROOT=self.folder.name);self.media.enable();self.addCleanup(self.media.disable)
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

    @override_settings(GOMUT_DEMO_MODE=True)
    def test_study_history_is_opt_in_and_populates_all_dashboard_charts(self):
        from django.utils import timezone
        from courses.models import StudyDay
        from courses.selectors import member_summary
        call_command('prepare_demo',password='DemoPassword123!',stdout=StringIO())
        self.assertFalse(StudyDay.objects.exists())
        call_command('prepare_demo',password='DemoPassword123!',with_study_history=True,stdout=StringIO())
        user=User.objects.get(username='gomut-demo-student')
        summary=member_summary(user.student_profile)
        self.assertEqual(summary['week_seconds'],111*60)
        self.assertEqual(summary['previous_seconds'],47*60)
        self.assertEqual(summary['streak'],4)
        self.assertEqual(len(summary['heatmap']),84)
        self.assertEqual({day['level'] for day in summary['heatmap']},{0,1,2,3,4})
        self.assertTrue(all(day.date<=timezone.localdate() for day in StudyDay.objects.all()))
        self.assertEqual(sum(row['watched_seconds'] for row in summary['items']),sum(StudyDay.objects.values_list('seconds',flat=True)))

    @override_settings(GOMUT_DEMO_MODE=True)
    def test_study_history_rerun_preserves_edits_passwords_and_other_students(self):
        from django.utils import timezone
        from courses.models import StudyDay,Progress,AccessPeriod,QuizAttempt,Certificate
        other=User.objects.create_user(username='preserve-study-user')
        other_day=StudyDay.objects.create(student=other.student_profile,date=timezone.localdate(),seconds=321)
        call_command('prepare_demo',password='DemoPassword123!',with_study_history=True,stdout=StringIO())
        user=User.objects.get(username='gomut-demo-student')
        StudyDay.objects.filter(student=user.student_profile,date=timezone.localdate()).update(seconds=999)
        Progress.objects.filter(student=user.student_profile).update(last_position_seconds=17)
        before=(list(StudyDay.objects.order_by('pk').values()),list(Progress.objects.order_by('pk').values()),list(AccessPeriod.objects.order_by('pk').values()),QuizAttempt.objects.count(),Certificate.objects.count())
        call_command('prepare_demo',password='ChangedPassword123!',with_study_history=True,stdout=StringIO())
        after=(list(StudyDay.objects.order_by('pk').values()),list(Progress.objects.order_by('pk').values()),list(AccessPeriod.objects.order_by('pk').values()),QuizAttempt.objects.count(),Certificate.objects.count())
        self.assertEqual(before,after)
        user.refresh_from_db();self.assertTrue(user.check_password('DemoPassword123!'))
        other_day.refresh_from_db();self.assertEqual(other_day.seconds,321)

    @override_settings(GOMUT_DEMO_MODE=True)
    def test_demo_history_cannot_be_added_to_account_with_changed_identity(self):
        call_command('prepare_demo',password='DemoPassword123!',stdout=StringIO())
        User.objects.filter(username='gomut-demo-student').update(email='another@example.org')
        with self.assertRaises(CommandError):
            call_command('prepare_demo',password='DemoPassword123!',with_study_history=True,stdout=StringIO())

    @override_settings(GOMUT_DEMO_MODE=True)
    def test_mock_chart_data_is_labelled_only_in_demo_account(self):
        call_command('prepare_demo',password='DemoPassword123!',with_study_history=True,stdout=StringIO())
        user=User.objects.get(username='gomut-demo-student')
        self.client.force_login(user)
        self.assertContains(self.client.get('/dashboard/'),'Dados ilustrativos de demonstração')
        with override_settings(GOMUT_DEMO_MODE=False):
            self.assertNotContains(self.client.get('/dashboard/'),'Dados ilustrativos de demonstração')
