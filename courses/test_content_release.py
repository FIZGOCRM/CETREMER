from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses import access, services
from courses.models import Course, Enrollment, Lesson, Module, Progress
from courses.selectors import progress_info
from users.models import User


class ContentReleaseTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='release-admin', role='CREATOR')
        self.user = User.objects.create_user(username='release-student')
        self.course = Course.objects.create(title='Curso', slug='release', creator=self.admin.creator_profile)
        self.module = Module.objects.create(course=self.course, title='Módulo')
        self.lesson = Lesson.objects.create(module=self.module, title='Aula')
        self.enrollment = Enrollment.objects.create(student=self.user.student_profile, course=self.course)
        services.create_plan(self.enrollment, starts_on=date(2024, 1, 31), actor=self.admin)
        self.enrollment.refresh_from_db()
        self.client.force_login(self.user)

    def availability(self, on):
        method = getattr(access, 'lesson_availability', None)
        self.assertTrue(callable(method), 'Liberação de conteúdo ainda não implementada')
        return method(self.enrollment, self.lesson, on=on)

    def test_calendar_release_clamps_day_31_and_uses_original_anchor(self):
        self.module.release_month = 2
        self.module.save()
        self.assertEqual(self.availability(date(2024, 2, 28)).state, 'scheduled')
        self.assertEqual(self.availability(date(2024, 2, 28)).release_date, date(2024, 2, 29))
        self.assertEqual(self.availability(date(2024, 2, 29)).state, 'available')
        self.module.release_month = 3; self.module.save()
        self.assertEqual(self.availability(date(2024, 3, 30)).state, 'scheduled')
        self.assertEqual(self.availability(date(2024, 3, 31)).state, 'available')

    def test_direct_url_and_completion_reject_scheduled_lesson(self):
        services.correct_plan_dates(self.enrollment, timezone.localdate(), services.add_calendar_months(timezone.localdate(), 12), 'Teste', actor=self.admin)
        self.enrollment.refresh_from_db()
        self.module.release_month = 2; self.module.save()
        response = self.client.get(reverse('lesson_detail', args=[self.course.slug, self.lesson.pk]))
        self.assertContains(response, 'Libera em', status_code=403)
        self.assertNotContains(response, 'data-vimeo', status_code=403)
        self.assertEqual(self.client.post(reverse('complete_lesson', args=[self.lesson.pk])).status_code, 403)
        self.assertFalse(Progress.objects.exists())

    def test_draft_is_hidden_and_excluded_from_progress(self):
        self.lesson.status = 'draft'; self.lesson.save()
        self.assertEqual(progress_info(self.user.student_profile, self.course)['total'], 0)
        self.assertEqual(self.availability(date(2024, 2, 1)).state, 'draft')
        self.module.status = 'draft'; self.module.save()
        self.assertEqual(progress_info(self.user.student_profile, self.course)['total'], 0)

    def test_release_month_must_be_positive(self):
        self.module.release_month = 0
        with self.assertRaises(ValidationError):
            self.module.full_clean()

    def test_postponing_requires_confirmation_for_affected_active_students(self):
        services.correct_plan_dates(self.enrollment, timezone.localdate()-timedelta(days=3), services.add_calendar_months(timezone.localdate(), 12), 'Teste', actor=self.admin)
        self.enrollment.refresh_from_db()
        method = getattr(services, 'save_module', None)
        self.assertTrue(callable(method), 'Serviço save_module ainda não implementado')
        self.module.release_month = 3
        with self.assertRaisesMessage(ValidationError, '1 aluno'):
            method(self.module, actor=self.admin)
        self.module.refresh_from_db(); self.assertEqual(self.module.release_month, 1)
        self.module.release_month = 3
        method(self.module, actor=self.admin, confirm_impact=True)
        self.assertEqual(self.availability(timezone.localdate()).state, 'scheduled')

    def test_completed_lesson_stays_completed_after_postponing(self):
        services.correct_plan_dates(self.enrollment, timezone.localdate(), services.add_calendar_months(timezone.localdate(), 12), 'Teste', actor=self.admin)
        self.enrollment.refresh_from_db()
        Progress.objects.create(student=self.user.student_profile, lesson=self.lesson, is_completed=True)
        self.module.release_month = 3; self.module.save()
        self.assertEqual(self.availability(timezone.localdate()).state, 'available')
        self.assertEqual(progress_info(self.user.student_profile, self.course)['completed'], 1)

    def test_panel_refuses_deleting_lesson_with_progress(self):
        Progress.objects.create(student=self.user.student_profile, lesson=self.lesson, is_completed=True)
        self.client.force_login(self.admin)
        response = self.client.post(reverse('painel:course_lessons', args=[self.course.pk]), {'action': 'delete_lesson', 'lesson_id': self.lesson.pk}, follow=True)
        self.assertTrue(Lesson.objects.filter(pk=self.lesson.pk).exists())
        self.assertContains(response, 'despublicar')

    def test_publishing_draft_in_released_module_appears_immediately(self):
        services.correct_plan_dates(self.enrollment, timezone.localdate(), services.add_calendar_months(timezone.localdate(), 12), 'Teste', actor=self.admin)
        self.lesson.status = 'draft'; self.lesson.save()
        url = reverse('lesson_detail', args=[self.course.slug, self.lesson.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.lesson.status = 'published'; self.lesson.save()
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_panel_preview_does_not_postpone_until_confirmed(self):
        services.correct_plan_dates(self.enrollment, timezone.localdate(), services.add_calendar_months(timezone.localdate(), 12), 'Teste', actor=self.admin)
        self.client.force_login(self.admin)
        url = reverse('painel:course_lessons', args=[self.course.pk])
        payload = {'action': 'save_module', 'module_id': self.module.pk, 'title': self.module.title, 'status': 'published', 'release_month': 3}
        response = self.client.post(url, payload)
        self.assertContains(response, '1 aluno(s)')
        self.module.refresh_from_db(); self.assertEqual(self.module.release_month, 1)
        self.assertEqual(self.client.post(url, dict(payload, confirm_impact='on')).status_code, 302)
        self.module.refresh_from_db(); self.assertEqual(self.module.release_month, 3)

    def test_module_with_progress_cannot_be_deleted(self):
        Progress.objects.create(student=self.user.student_profile, lesson=self.lesson)
        self.client.force_login(self.admin)
        self.client.post(reverse('painel:course_lessons', args=[self.course.pk]), {'action': 'delete_module', 'module_id': self.module.pk})
        self.assertTrue(Module.objects.filter(pk=self.module.pk).exists())

    def test_two_courses_release_by_their_own_original_start(self):
        other = Course.objects.create(title='Outro', slug='other-release', creator=self.admin.creator_profile)
        other_module = Module.objects.create(course=other, title='M2', release_month=3)
        other_lesson = Lesson.objects.create(module=other_module, title='A2')
        second = Enrollment.objects.create(student=self.user.student_profile, course=other)
        services.create_plan(second, starts_on=date(2024, 3, 10), actor=self.admin)
        second.refresh_from_db()
        self.module.release_month = 3; self.module.save()
        self.assertEqual(self.availability(date(2024, 4, 10)).state, 'available')
        self.assertEqual(access.lesson_availability(second, other_lesson, on=date(2024, 4, 10)).state, 'scheduled')
