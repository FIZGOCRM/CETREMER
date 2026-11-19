from django.test import TestCase
from django.urls import reverse

from courses.models import Course, Enrollment, Lesson, Module
from users.models import User


class LessonExperienceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='notes-owner', role='CREATOR')
        self.user = User.objects.create_user(username='notes-user')
        self.other = User.objects.create_user(username='notes-other')
        self.course = Course.objects.create(is_published=True, title='Curso', slug='notes', creator=self.owner.creator_profile)
        self.lesson = Lesson.objects.create(module=Module.objects.create(course=self.course, title='M'), title='A', duration_seconds=100)
        for user in (self.user, self.other):
            Enrollment.objects.create(student=user.student_profile, course=self.course)
        self.url = f'/courses/lesson/{self.lesson.pk}/notes/'
        self.client.force_login(self.user)

    def test_lesson_without_quiz_has_empty_quiz_tab_and_has_notes(self):
        response = self.client.get(reverse('lesson_detail', args=[self.course.slug, self.lesson.pk]))
        self.assertContains(response, 'id="tab-quiz"')
        self.assertContains(response, 'Esta aula ainda não tem quiz.')
        self.assertNotContains(response, 'Esta aula tem um quiz')
        self.assertContains(response, 'Anotações')
        self.assertContains(response, 'conclui com 90% assistido')

    def test_note_is_saved_at_minute_and_only_owner_can_list_or_delete(self):
        response = self.client.post(self.url, {'position_seconds': 42, 'text': 'Rever este ponto'}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 201)
        note_id = response.json()['id']
        self.assertEqual(self.client.get(self.url).json()['notes'][0]['position_seconds'], 42)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).json()['notes'], [])
        self.assertEqual(self.client.post(f'{self.url}{note_id}/delete/').status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(f'{self.url}{note_id}/delete/', HTTP_ACCEPT='application/json').status_code, 200)
        self.assertEqual(self.client.get(self.url).json()['notes'], [])

    def test_lesson_navigation_uses_global_number_and_personal_reactions(self):
        from courses.models import LessonLike, SavedLesson
        self.lesson.order = 2
        self.lesson.save(update_fields=['order'])
        first = Lesson.objects.create(module=self.lesson.module, order=1, title='Primeira')
        following = Lesson.objects.create(module=Module.objects.create(course=self.course, title='M2'), order=1, title='Seguinte')
        Lesson.objects.create(module=self.lesson.module, title='Rascunho', status='draft')
        url = reverse('lesson_detail', args=[self.course.slug, self.lesson.pk])
        LessonLike.objects.create(student=self.user.student_profile, lesson=self.lesson)
        SavedLesson.objects.create(student=self.other.student_profile, lesson=self.lesson)
        response = self.client.get(url)
        self.assertContains(response, 'Aula 2 de 3')
        self.assertEqual(response.context['prev_lesson'], first)
        self.assertEqual(response.context['next_lesson_nav'], following)
        self.assertTrue(response.context['is_liked'])
        self.assertFalse(response.context['is_saved'])

    def test_unenrolled_student_cannot_read_or_create_notes(self):
        outsider = User.objects.create_user(username='notes-outsider')
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, {'position_seconds': 0, 'text': 'x'}).status_code, 403)

    def test_note_rejects_empty_text_and_time_outside_video(self):
        for data in ({'position_seconds': -1, 'text': 'x'}, {'position_seconds': 101, 'text': 'x'}, {'position_seconds': 1, 'text': '  '}):
            self.assertEqual(self.client.post(self.url, data, HTTP_ACCEPT='application/json').status_code, 400)

    def test_notes_require_csrf_and_expired_plan_cannot_write(self):
        from datetime import timedelta
        from django.test import Client
        from django.utils import timezone
        from courses.services import create_plan, end_plan_early
        strict = Client(enforce_csrf_checks=True); strict.force_login(self.user)
        self.assertEqual(strict.post(self.url, {'position_seconds': 1, 'text': 'x'}).status_code, 403)
        enrollment = Enrollment.objects.get(student=self.user.student_profile, course=self.course)
        create_plan(enrollment, starts_on=timezone.localdate()-timedelta(days=2), actor=self.owner)
        end_plan_early(enrollment, end_date=timezone.localdate(), reason='withdrawal', actor=self.owner)
        self.assertEqual(self.client.post(self.url, {'position_seconds': 1, 'text': 'x'}).status_code, 403)

    def test_note_text_is_escaped_when_rendered(self):
        self.client.post(self.url, {'position_seconds': 1, 'text': '<script>alert(1)</script>'})
        response = self.client.get(reverse('lesson_detail', args=[self.course.slug, self.lesson.pk]))
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
