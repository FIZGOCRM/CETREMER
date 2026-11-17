from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from courses import services
from courses.models import Course, Enrollment, Lesson, Module, Progress
from users.models import User


class PlayerTrackingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='player-admin', role='CREATOR')
        self.user = User.objects.create_user(username='player-student')
        self.student = self.user.student_profile
        self.course = Course.objects.create(is_published=True, title='Curso', slug='player', creator=self.admin.creator_profile)
        self.module = Module.objects.create(course=self.course, title='M')
        self.lesson = Lesson.objects.create(module=self.module, title='A', duration_seconds=100, video_url='https://vimeo.com/76979871')
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.now = timezone.now()
        self.client.force_login(self.user)

    def pulse(self, second, position, playing=True, lesson=None):
        method = getattr(services, 'record_heartbeat', None)
        self.assertTrue(callable(method), 'Telemetria ainda não implementada')
        with patch('courses.services.timezone.now', return_value=self.now+timedelta(seconds=second)):
            return method(self.student, lesson or self.lesson, position=position, playing=playing)

    def test_seek_does_not_grant_time_and_real_elapsed_is_capped_at_twenty(self):
        self.pulse(0, 0)
        self.pulse(15, 95)
        self.pulse(115, 100)
        progress = Progress.objects.get(student=self.student, lesson=self.lesson)
        self.assertEqual(progress.watched_seconds, 35)
        self.assertFalse(progress.is_completed)
        self.assertEqual(progress.last_position_seconds, 100)

    def test_two_devices_share_one_student_clock(self):
        other = Lesson.objects.create(module=self.module, title='Outra', duration_seconds=100)
        self.pulse(0, 0)
        self.pulse(15, 15)
        self.pulse(15, 30, lesson=other)
        self.pulse(30, 45, lesson=other)
        from courses.models import StudyDay
        self.assertEqual(sum(Progress.objects.filter(student=self.student).values_list('watched_seconds', flat=True)), 30)
        self.assertEqual(StudyDay.objects.get(student=self.student).seconds, 30)

    def test_paused_interval_does_not_credit_on_resume(self):
        self.pulse(0, 0)
        self.pulse(15, 15, False)
        self.assertEqual(Progress.objects.get(student=self.student, lesson=self.lesson).watched_seconds, 0)
        self.pulse(200, 15, True)
        self.assertEqual(Progress.objects.get(student=self.student, lesson=self.lesson).watched_seconds, 0)

    def test_ninety_percent_completes_once_and_logs_activity(self):
        for second in range(0, 91, 15):
            result = self.pulse(second, second)
        self.assertTrue(result['completed'])
        self.assertFalse(result['has_quiz'])
        self.pulse(105, 100)
        from courses.models import ActivityEvent
        self.assertEqual(ActivityEvent.objects.filter(student=self.student, kind='lesson_completed').count(), 1)
        self.student.refresh_from_db(); self.assertEqual(self.student.points, 10)

    def test_expired_plan_rejects_next_pulse_without_erasing_prior_position(self):
        services.create_plan(self.enrollment, timezone.localdate()-timedelta(days=5), actor=self.admin)
        self.pulse(0, 10)
        services.end_plan_early(self.enrollment, timezone.localdate(), 'withdrawal', actor=self.admin)
        response = self.client.post(f'/courses/lesson/{self.lesson.pk}/heartbeat/', {'position': 80, 'playing': True}, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['access'], 'ended')
        self.assertEqual(Progress.objects.get(student=self.student, lesson=self.lesson).last_position_seconds, 10)

    def test_heartbeat_requires_csrf_and_student_enrollment(self):
        strict = Client(enforce_csrf_checks=True); strict.force_login(self.user)
        self.assertEqual(strict.post(f'/courses/lesson/{self.lesson.pk}/heartbeat/', '{}', content_type='application/json').status_code, 403)
        outsider = User.objects.create_user(username='other-player')
        self.client.force_login(outsider)
        self.assertEqual(self.client.post(f'/courses/lesson/{self.lesson.pk}/heartbeat/', {'position': 0, 'playing': True}, content_type='application/json').status_code, 403)

    def test_ended_requires_half_of_server_known_duration(self):
        method = getattr(services, 'finish_video', None)
        self.assertTrue(callable(method), 'Conclusão ended ainda não implementada')
        self.pulse(0, 100)
        with self.assertRaises(ValidationError):
            method(self.student, self.lesson)
        for second in (15, 30, 45, 60):
            self.pulse(second, 100)
        self.assertTrue(method(self.student, self.lesson)['is_completed'])

    def test_video_change_resets_position_but_preserves_completion_and_study_time(self):
        self.pulse(0, 20)
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        self.lesson.duration_seconds = 120
        services.save_lesson(self.lesson)
        progress = Progress.objects.get(student=self.student, lesson=self.lesson)
        self.assertEqual(progress.last_position_seconds, 0)
        self.assertTrue(progress.is_completed)

    def test_invalid_position_does_not_change_tracking(self):
        for position in (-1, float('inf'), float('nan')):
            with self.assertRaises(ValidationError):
                self.pulse(0, position)
        self.assertFalse(Progress.objects.exists())

    def test_uncomplete_reduces_progress_without_erasing_actual_study_time(self):
        for second in range(0, 91, 15):
            self.pulse(second, second)
        result = services.set_lesson_progress(self.student, self.lesson, completed=False)
        self.assertEqual(result['completed_count'], 0)
        self.assertFalse(self.pulse(105, 100)['completed'])
        self.assertEqual(Progress.objects.get(student=self.student, lesson=self.lesson).watched_seconds, 105)

    def test_beacon_form_accepts_csrf_and_rejects_forged_credit_fields(self):
        import json
        strict = Client(enforce_csrf_checks=True); strict.force_login(self.user)
        strict.get(reverse('lesson_detail', args=[self.course.slug, self.lesson.pk]))
        token = strict.cookies['csrftoken'].value
        response = strict.post(reverse('lesson_heartbeat', args=[self.lesson.pk]), {'csrfmiddlewaretoken': token,
            'payload': json.dumps({'position': 87, 'playing': True, 'watched_seconds': 9999, 'completed': True})})
        self.assertEqual(response.status_code, 200)
        progress = Progress.objects.get(student=self.student, lesson=self.lesson)
        self.assertEqual(progress.watched_seconds, 0)
        self.assertFalse(progress.is_completed)

    def test_resume_position_is_rendered_without_locale_decimal_comma(self):
        self.pulse(0, 18.5)
        response = self.client.get(reverse('lesson_detail', args=[self.course.slug, self.lesson.pk]))
        self.assertContains(response, 'data-position="18.5"')

    def test_cross_midnight_splits_credit_by_local_day(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from courses.models import StudyDay
        self.now = datetime(2026, 11, 16, 23, 59, 55, tzinfo=ZoneInfo('America/Campo_Grande'))
        self.pulse(0, 0)
        self.pulse(15, 15)
        self.assertEqual(list(StudyDay.objects.order_by('date').values_list('seconds', flat=True)), [5, 10])

    def test_missing_duration_uses_server_vimeo_metadata_for_half_rule(self):
        self.lesson.video_url = 'https://vimeo.com/76979871'; self.lesson.duration_seconds = 0; self.lesson.save()
        self.pulse(0, 0)
        for second in (15, 30, 45, 60):
            self.pulse(second, second)
        with patch('courses.integrations.vimeo.video_duration', return_value=0):
            with self.assertRaises(ValidationError):
                services.finish_video(self.student, self.lesson)
        with patch('courses.integrations.vimeo.video_duration', return_value=100):
            self.assertTrue(services.finish_video(self.student, self.lesson)['is_completed'])
