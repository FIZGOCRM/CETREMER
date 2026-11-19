"""Regressions from QA-GM-20261117-105209, using an isolated test database."""
from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from courses import services
from courses.models import Certificate, Course, Enrollment, Lesson, Module
from users.models import User


def text(response):
    return ' '.join(strip_tags(response.content.decode()).split())


class Qa105209Tests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='qa-owner', role='CREATOR')
        self.user = User.objects.create_user(username='qa-member')
        self.course = Course.objects.create(title='Curso QA', slug='qa-regression',
            is_published=True, creator=self.owner.creator_profile, workload_hours=1)
        self.lesson = Lesson.objects.create(module=Module.objects.create(course=self.course, title='M'), title='A')
        self.enrollment = Enrollment.objects.create(student=self.user.student_profile, course=self.course)
        self.today = timezone.localdate()
        self.client.force_login(self.user)

    def test_access_until_matches_account_before_and_on_last_grace_day_then_blocks(self):
        period = services.create_plan(self.enrollment, self.today-timedelta(days=10), self.today+timedelta(days=1), actor=self.owner)
        last_day = period.ends_on+timedelta(days=2)
        expected = last_day.strftime('%d/%m/%Y')
        for day in (self.today, last_day):
            time = datetime.max.time() if day == last_day else datetime.min.time()
            now = timezone.make_aware(datetime.combine(day, time))
            with self.subTest(day=day), patch('django.utils.timezone.now', return_value=now):
                detail = self.client.get(reverse('member_course', args=[self.course.slug]))
                account = self.client.get(reverse('settings'))
                self.assertEqual(detail.status_code, 200)
                self.assertIn('Acesso até '+expected, text(detail))
                self.assertIn('Acesso até: '+expected, text(account))
                self.assertEqual(self.client.get(reverse('lesson_detail', args=[self.course.slug, self.lesson.pk])).status_code, 200)
        next_day = timezone.make_aware(datetime.combine(last_day+timedelta(days=1), datetime.min.time()))
        with patch('django.utils.timezone.now', return_value=next_day):
            self.assertEqual(self.client.get(reverse('member_course', args=[self.course.slug])).status_code, 403)
            self.assertEqual(self.client.get(reverse('lesson_detail', args=[self.course.slug, self.lesson.pk])).status_code, 403)
            self.assertEqual(self.client.post(reverse('lesson_heartbeat', args=[self.lesson.pk]),
                {'position': 20, 'playing': True}, content_type='application/json').status_code, 403)
            self.assertIn('Acesso até: '+expected, text(self.client.get(reverse('settings'))))

    def test_unrestricted_access_does_not_display_an_invented_deadline(self):
        response = self.client.get(reverse('member_course', args=[self.course.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Acesso até', text(response))

    def test_certificate_workload_singular_and_plural_on_member_and_public_views(self):
        services.set_lesson_progress(self.user.student_profile, self.lesson, completed=True)
        self.client.post(reverse('issue_certificate', args=[self.course.slug]), {
            'action': 'save_and_issue', f'enrollment-{self.enrollment.pk}-full_name': 'Aluno Fictício',
            f'enrollment-{self.enrollment.pk}-cpf': '52998224725'})
        certificate = Certificate.objects.get(enrollment=self.enrollment)
        for hours, label in ((1, '1 hora'), (2, '2 horas')):
            certificate.workload_hours = hours; certificate.save(update_fields=['workload_hours'])
            for url in (reverse('issue_certificate', args=[self.course.slug]), reverse('verify_certificate')+'?codigo='+certificate.code):
                with self.subTest(hours=hours, url=url):
                    response = self.client.get(url)
                    self.assertIn(label, text(response))
                    self.assertNotIn('1 horas', text(response))

    def test_plan_days_singular_and_plural_in_active_and_grace_states(self):
        services.create_plan(self.enrollment, self.today-timedelta(days=10), self.today+timedelta(days=2), actor=self.owner)
        self.enrollment.refresh_from_db()
        for offset, expected in ((0, 'Termina em 2 dias'), (1, 'Termina em 1 dia'),
                                 (3, 'Seu acesso termina em 2 dias'), (4, 'Seu acesso termina em 1 dia')):
            day = self.today+timedelta(days=offset)
            now = timezone.make_aware(datetime.combine(day, datetime.min.time())+timedelta(hours=12))
            with self.subTest(day=day), patch('django.utils.timezone.now', return_value=now):
                self.assertEqual(services.plan_status(self.enrollment)['label'], expected)
                self.client.force_login(self.owner)
                response = self.client.get(f'/painel/planos/{self.enrollment.pk}/', follow=True)
                self.assertIn(expected, text(response))
                self.assertNotIn('1 dias', text(response))
