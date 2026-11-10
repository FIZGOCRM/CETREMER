from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Course, Enrollment, Lesson, LiveSession, Module, Progress
from courses.services import completed_lesson_ids, course_progress, lesson_payload, ordered_lessons

User = get_user_model()
PASSWORD = 'StrongPassword123!'


class V2Base(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.jane = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        self.course = Course.objects.create(title='BLS', slug='bls', creator=self.admin.creator_profile, status='published')
        self.m1 = Module.objects.create(course=self.course, title='Introdução', order=1)
        self.m2 = Module.objects.create(course=self.course, title='Prática', order=2)
        self.l1 = Lesson.objects.create(module=self.m1, title='Aula 1', order=1)
        self.l2 = Lesson.objects.create(module=self.m1, title='Aula 2', order=2)
        self.l3 = Lesson.objects.create(module=self.m2, title='Aula 3', order=1)
        self.draft = Lesson.objects.create(module=self.m2, title='Rascunho', order=2, status='draft')
        self.enrollment = Enrollment.objects.create(student=self.jane.student_profile, course=self.course)

    def mark(self, lesson, completed=True, seconds=0):
        return Progress.objects.update_or_create(student=self.jane.student_profile, lesson=lesson,
                                                 defaults={'is_completed': completed, 'position_seconds': seconds})[0]


class CourseModelTests(V2Base):
    def test_is_published_property_maps_to_status(self):
        self.assertTrue(self.course.is_published)
        self.course.is_published = False
        self.assertEqual(self.course.status, 'draft')
        self.course.is_published = True
        self.assertEqual(self.course.status, 'published')
        self.assertTrue(Course(title='x', slug='x', is_published=True).is_published)

    def test_new_course_starts_as_draft(self):
        course = Course.objects.create(title='Novo', slug='novo', creator=self.admin.creator_profile)
        self.assertEqual(course.status, 'draft')
        self.assertEqual(course.release_mode, 'all')
        self.assertTrue(course.certificate_enabled)

    def test_deleted_lessons_are_hidden_by_default_manager(self):
        self.l2.deleted_at = timezone.now()
        self.l2.save()
        self.assertFalse(Lesson.objects.filter(pk=self.l2.pk).exists())
        self.assertTrue(Lesson.all_objects.filter(pk=self.l2.pk).exists())
        self.assertNotIn(self.l2, self.m1.lessons.all())

    def test_module_release_rules(self):
        self.assertTrue(self.m2.is_released_for(self.enrollment))
        self.course.release_mode = 'scheduled'
        self.m2.release_after_days = 7
        self.assertFalse(self.m2.is_released_for(self.enrollment))
        self.enrollment.enrolled_at = timezone.now() - timedelta(days=8)
        self.assertTrue(self.m2.is_released_for(self.enrollment))
        self.m2.release_date = timezone.localdate() + timedelta(days=3)
        self.assertFalse(self.m2.is_released_for(self.enrollment))

    def test_live_session_states(self):
        now = timezone.now()
        session = LiveSession(course=self.course, title='Encontro', starts_at=now + timedelta(hours=2), ends_at=now + timedelta(hours=3))
        self.assertEqual(session.state(now), 'scheduled')
        self.assertEqual(session.state(now + timedelta(hours=1, minutes=50)), 'soon')
        self.assertEqual(session.state(now + timedelta(hours=2, minutes=30)), 'live')
        self.assertEqual(session.state(now + timedelta(hours=4)), 'ended')

    def test_live_session_join_url_falls_back_to_course(self):
        self.course.live_meet_url = 'https://meet.google.com/aaa'
        session = LiveSession(course=self.course, title='E', starts_at=timezone.now(), ends_at=timezone.now())
        self.assertEqual(session.join_url, 'https://meet.google.com/aaa')
        session.meet_url = 'https://meet.google.com/bbb'
        self.assertEqual(session.join_url, 'https://meet.google.com/bbb')


class ServicesTests(V2Base):
    def test_ordered_lessons_skips_drafts_and_follows_module_order(self):
        self.assertEqual([lesson.title for lesson in ordered_lessons(self.course)], ['Aula 1', 'Aula 2', 'Aula 3'])

    def test_course_progress_counts_only_published_completed(self):
        self.mark(self.l1)
        self.mark(self.draft)
        info = course_progress(self.jane, self.course)
        self.assertEqual((info['done'], info['total'], info['pct'], info['remaining']), (1, 3, 33, 2))
        self.assertEqual(info['next_lesson'], self.l2)

    def test_resume_is_most_recent_uncompleted_with_position(self):
        self.mark(self.l1)
        self.mark(self.l3, completed=False, seconds=192)
        info = course_progress(self.jane, self.course)
        self.assertEqual(info['resume_lesson'], self.l3)
        self.assertEqual(info['resume_seconds'], 192)

    def test_resume_falls_back_to_first_pending_and_none_when_done(self):
        self.mark(self.l1)
        self.assertEqual(course_progress(self.jane, self.course)['resume_lesson'], self.l2)
        self.mark(self.l2)
        self.mark(self.l3)
        info = course_progress(self.jane, self.course)
        self.assertIsNone(info['resume_lesson'])
        self.assertEqual(info['pct'], 100)

    def test_incomplete_progress_records_do_not_count(self):
        self.mark(self.l1, completed=False, seconds=30)
        self.assertEqual(completed_lesson_ids(self.jane, [self.course.id]), set())
        self.assertEqual(course_progress(self.jane, self.course)['done'], 0)

    def test_non_student_has_no_progress(self):
        self.assertEqual(completed_lesson_ids(self.admin, [self.course.id]), set())
        self.assertEqual(course_progress(self.admin, self.course)['done'], 0)

    def test_lesson_payload_shape(self):
        self.mark(self.l1)
        payload = lesson_payload(self.jane, self.l1)
        self.assertTrue(payload['is_completed'])
        self.assertEqual(payload['completed_count'], 1)
        self.assertEqual(payload['total_count'], 3)
        self.assertEqual(payload['percentage'], 33.3)
        self.assertEqual(payload['module'], {'id': self.m1.id, 'done': 1, 'total': 2})
        self.assertEqual(payload['remaining'], 2)
        self.assertFalse(payload['course_done'])
        self.assertEqual(payload['next'], {'url': reverse('lesson_detail', args=['bls', self.l2.id]), 'title': 'Aula 2'})
        self.assertEqual(payload['certificate_url'], '/certificados/?emitir=bls')

    def test_lesson_payload_last_lesson_has_no_next_and_marks_course_done(self):
        for lesson in (self.l1, self.l2, self.l3):
            self.mark(lesson)
        payload = lesson_payload(self.jane, self.l3)
        self.assertIsNone(payload['next'])
        self.assertTrue(payload['course_done'])


class DraftLessonVisibilityTests(V2Base):
    def test_draft_lesson_not_listed_on_public_preview(self):
        response = self.client.get(reverse('course_preview', args=['bls']))
        self.assertContains(response, 'Aula 3')
        self.assertNotContains(response, 'Rascunho')

    def test_student_progress_ignores_draft(self):
        self.client.force_login(self.jane)
        response = self.client.get(reverse('lesson_detail', args=['bls', self.l1.id]))
        self.assertEqual(response.context['total'], 3)
