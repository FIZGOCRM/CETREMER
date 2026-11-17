from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses import selectors
from courses.models import ActivityEvent, Course, Enrollment, Lesson, Module, Progress, StudyDay
from users.models import User


class ProgressDashboardTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='dashboard-owner', role='CREATOR')
        self.user = User.objects.create_user(username='dashboard-student')
        self.student = self.user.student_profile
        self.course = Course.objects.create(is_published=True, title='Curso', slug='dashboard-course', creator=self.owner.creator_profile)
        self.lesson = Lesson.objects.create(module=Module.objects.create(course=self.course, title='M'), title='A', duration_seconds=3600)
        Enrollment.objects.create(student=self.student, course=self.course)
        self.today = timezone.localdate()
        self.client.force_login(self.user)

    def summary(self):
        method = getattr(selectors, 'member_summary', None)
        self.assertTrue(callable(method), 'Resumo de estudo ainda não implementado')
        return method(self.student)

    def test_completed_duration_is_not_counted_as_time_studied(self):
        Progress.objects.create(student=self.student, lesson=self.lesson, is_completed=True)
        summary = self.summary()
        self.assertEqual(summary['week_seconds'], 0)
        self.assertEqual(summary['completed'], 1)
        self.assertEqual(summary['streak'], 0)

    def test_seven_day_comparison_streak_and_eighty_four_days_are_real(self):
        for offset, seconds in [(0, 90), (1, 60), (2, 59), (7, 120), (84, 600)]:
            StudyDay.objects.create(student=self.student, date=self.today-timedelta(days=offset), seconds=seconds)
        summary = self.summary()
        self.assertEqual(summary['week_seconds'], 209)
        self.assertEqual(summary['previous_seconds'], 120)
        self.assertEqual(summary['difference_seconds'], 89)
        self.assertEqual(summary['streak'], 2)
        self.assertEqual(len(summary['heatmap']), 84)
        self.assertEqual(len(summary['week']), 7)

    def test_other_student_time_and_activity_are_not_exposed(self):
        other = User.objects.create_user(username='other-dashboard')
        StudyDay.objects.create(student=other.student_profile, date=self.today, seconds=9999)
        ActivityEvent.objects.create(student=other.student_profile, kind='lesson_completed', lesson=self.lesson)
        summary = self.summary()
        self.assertEqual(summary['week_seconds'], 0)
        self.assertEqual(summary['activity'], [])

    def test_progress_page_replaces_pending_metrics_and_works_after_plan_end(self):
        from courses.services import create_plan, end_plan_early
        enrollment = Enrollment.objects.get(student=self.student, course=self.course)
        create_plan(enrollment, starts_on=self.today-timedelta(days=5), actor=self.owner)
        end_plan_early(enrollment, end_date=self.today, reason='withdrawal', actor=self.owner)
        response = self.client.get(reverse('member_section', args=['progresso']))
        self.assertContains(response, 'Últimas 12 semanas')
        self.assertNotContains(response, 'Necessita de backend')
        self.assertContains(response, 'Assista sua primeira aula para ver seu ritmo aqui.')
        self.assertContains(response, 'Encerrado')

    def test_next_steps_are_limited_and_continue_precedes_new_course(self):
        Progress.objects.create(student=self.student, lesson=self.lesson, last_position_seconds=20)
        for index in range(5):
            course = Course.objects.create(is_published=True, title=f'Novo {index}', slug=f'next-{index}', creator=self.owner.creator_profile)
            Lesson.objects.create(module=Module.objects.create(course=course, title='M'), title='Primeira')
            Enrollment.objects.create(student=self.student, course=course)
        summary = self.summary()
        self.assertEqual(len(summary['next_steps']), 4)
        self.assertEqual(summary['next_steps'][0]['title'], 'Continuar: A')

    def test_queries_do_not_grow_per_course(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as baseline:
            self.summary()
        for number in range(5):
            course = Course.objects.create(is_published=True, title=f'Extra {number}', slug=f'extra-{number}', creator=self.owner.creator_profile)
            Lesson.objects.create(module=Module.objects.create(course=course, title='M'), title='A')
            Enrollment.objects.create(student=self.student, course=course)
        with CaptureQueriesContext(connection) as expanded:
            self.summary()
        self.assertLessEqual(len(expanded), len(baseline))
