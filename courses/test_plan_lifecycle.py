from datetime import date, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses import services
from courses.access import access_decision
from courses.models import Course, Enrollment, Lesson, Module, Progress
from users.models import User


class PlanLifecycleTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='plan-admin', role='CREATOR')
        self.user = User.objects.create_user(username='plan-student')
        self.course = Course.objects.create(is_published=True, title='Curso', slug='plan-course', creator=self.admin.creator_profile)
        self.enrollment = Enrollment.objects.create(student=self.user.student_profile, course=self.course)
        self.today = timezone.localdate()

    def call(self, name, *args, **kwargs):
        method = getattr(services, name, None)
        self.assertTrue(callable(method), f'Serviço {name} ainda não implementado')
        return method(*args, actor=self.admin, **kwargs)

    def create(self, **kwargs):
        return self.call('create_plan', self.enrollment, starts_on=self.today - timedelta(days=30), **kwargs)

    def test_default_uses_calendar_months_and_records_creation(self):
        period = self.call('create_plan', self.enrollment, starts_on=date(2024, 2, 29))
        self.assertEqual(period.ends_on, date(2025, 2, 28))
        self.assertEqual(period.grace_days, 3)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.plan_started_on, date(2024, 2, 29))
        change = self.enrollment.access_changes.get()
        self.assertEqual((change.action, change.actor_id), ('created', self.admin.pk))

    def test_end_on_start_day_creates_empty_interval_without_grace(self):
        self.call('create_plan', self.enrollment, starts_on=self.today)
        self.call('end_plan_early', self.enrollment, end_date=self.today, reason='withdrawal')
        self.enrollment.refresh_from_db()
        period = self.enrollment.access_periods.get()
        self.assertEqual((period.starts_on, period.ends_on, period.grace_days), (self.today, self.today, 0))
        self.assertFalse(access_decision(self.enrollment).allowed)
        self.assertEqual(self.enrollment.access_changes.count(), 2)

    def test_creation_cannot_have_empty_interval(self):
        with self.assertRaises(ValidationError):
            self.call('create_plan', self.enrollment, starts_on=self.today, ends_on=self.today)
        self.assertFalse(self.enrollment.access_periods.exists())

    def test_early_end_blocks_today_without_grace_and_preserves_progress(self):
        self.create()
        lesson = Lesson.objects.create(module=Module.objects.create(course=self.course, title='M'), title='A')
        progress = Progress.objects.create(student=self.user.student_profile, lesson=lesson, is_completed=True)
        self.call('end_plan_early', self.enrollment, end_date=self.today, reason='withdrawal')
        self.enrollment.refresh_from_db()
        self.assertFalse(access_decision(self.enrollment).allowed)
        self.assertTrue(Progress.objects.get(pk=progress.pk).is_completed)
        self.assertEqual(self.enrollment.access_changes.last().reason_code, 'withdrawal')
        self.assertEqual(self.enrollment.access_periods.get().grace_days, 0)

    def test_reactivation_is_limited_to_corrected_contract_end(self):
        self.create()
        limit = self.today + timedelta(days=60)
        self.call('correct_plan_dates', self.enrollment, new_start=self.today-timedelta(days=30), new_end=limit, reason='Correção contratual')
        self.call('end_plan_early', self.enrollment, end_date=self.today, reason='student_request')
        with self.assertRaises(ValidationError):
            self.call('reactivate_plan', self.enrollment, until_date=limit+timedelta(days=1))
        self.call('reactivate_plan', self.enrollment, until_date=limit)
        self.enrollment.refresh_from_db()
        self.assertTrue(access_decision(self.enrollment).allowed)
        self.assertEqual(self.enrollment.access_periods.count(), 1)
        self.assertEqual(list(self.enrollment.access_changes.values_list('action', flat=True)), ['created', 'corrected', 'ended_early', 'reactivated'])

    def test_correction_requires_reason_and_invalid_dates_do_not_write(self):
        self.create()
        for reason in ('', '   '):
            with self.assertRaises(ValidationError):
                self.call('correct_plan_dates', self.enrollment, new_start=self.today, new_end=self.today+timedelta(days=10), reason=reason)
        self.assertEqual(self.enrollment.access_changes.count(), 1)

    def test_student_cannot_change_plan(self):
        method = getattr(services, 'create_plan', None)
        self.assertTrue(callable(method), 'Serviço create_plan ainda não implementado')
        with self.assertRaises(PermissionDenied):
            method(self.enrollment, starts_on=self.today, actor=self.user)

    def test_two_courses_keep_independent_dates_and_natural_grace(self):
        first = self.create(ends_on=self.today)
        other = Course.objects.create(is_published=True, title='Outro', slug='other-plan', creator=self.admin.creator_profile)
        second = Enrollment.objects.create(student=self.user.student_profile, course=other)
        self.call('create_plan', second, starts_on=self.today)
        self.enrollment.refresh_from_db(); second.refresh_from_db()
        self.assertEqual(access_decision(self.enrollment).state, 'grace')
        self.assertEqual(access_decision(second).state, 'active')
        self.assertEqual(first.ends_on, self.today)

    def test_panel_can_end_plan_and_student_sees_support(self):
        self.create()
        self.client.force_login(self.admin)
        response = self.client.post(f'/painel/planos/{self.enrollment.pk}/', {'action': 'end', 'end_date': self.today.isoformat(), 'reason_code': 'withdrawal'})
        self.assertEqual(response.status_code, 302)
        self.enrollment.refresh_from_db()
        self.assertFalse(access_decision(self.enrollment).allowed)
        lesson = Lesson.objects.create(module=Module.objects.create(course=self.course, title='M'), title='A')
        self.client.force_login(self.user)
        response = self.client.get(reverse('lesson_detail', args=[self.course.slug, lesson.pk]))
        self.assertContains(response, 'Abrir chamado', status_code=403)

    def test_dismissal_is_per_notice_milestone(self):
        self.create(ends_on=self.today+timedelta(days=7))
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Seu acesso a')
        response = self.client.post(f'/dashboard/planos/{self.enrollment.pk}/dispensar/', {'milestone': '7'})
        self.assertEqual(response.status_code, 302)
        self.assertNotContains(self.client.get(reverse('dashboard')), 'data-plan-notice')

    def test_student_cannot_manage_plan_or_dismiss_another_students_notice(self):
        self.create()
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(f'/painel/planos/{self.enrollment.pk}/', {'action': 'note', 'admin_note': 'indevido'}).status_code, 403)
        outsider = User.objects.create_user(username='outsider-plan')
        self.client.force_login(outsider)
        self.assertEqual(self.client.post(f'/dashboard/planos/{self.enrollment.pk}/dispensar/').status_code, 404)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.admin_note, '')

    def test_manual_end_other_requires_explanation_and_rolls_back(self):
        self.create()
        with self.assertRaises(ValidationError):
            self.call('end_plan_early', self.enrollment, end_date=self.today, reason='other')
        self.assertEqual(self.enrollment.access_changes.count(), 1)

    def test_status_distinguishes_natural_end_and_exact_grace_boundary(self):
        from courses.services import plan_status
        self.create(ends_on=self.today)
        self.enrollment.refresh_from_db()
        self.assertEqual(plan_status(self.enrollment, on=self.today)['state'], 'grace')
        self.assertEqual(plan_status(self.enrollment, on=self.today+timedelta(days=2))['days'], 1)
        self.assertEqual(plan_status(self.enrollment, on=self.today+timedelta(days=3))['state'], 'ended')
