from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import connection
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from community.models import Comment, CommunityPost
from core.context_processors import student_shell
from courses.models import Certificate, Course, Enrollment, Lesson, LessonMaterial, LiveSession, Module, Progress
from users.models import Notification
from users.notify import notify

User = get_user_model()
PASSWORD = 'StrongPassword123!'


class A2Base(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.jane = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        self.ana = User.objects.create_user(username='ana', email='ana@example.com', password=PASSWORD)
        self.bls = Course.objects.create(title='BLS', slug='bls', creator=self.admin.creator_profile, status='published')
        self.acls = Course.objects.create(title='ACLS', slug='acls', creator=self.admin.creator_profile, status='published')
        self.mod_bls = Module.objects.create(course=self.bls, title='Compressões', order=1)
        self.mod_acls = Module.objects.create(course=self.acls, title='Fármacos', order=1)
        self.l1 = Lesson.objects.create(module=self.mod_bls, title='Compressões torácicas', order=1)
        self.l2 = Lesson.objects.create(module=self.mod_bls, title='Uso do DEA', order=2)
        self.draft = Lesson.objects.create(module=self.mod_bls, title='Compressões em rascunho', order=3, status='draft')
        self.acls_lesson = Lesson.objects.create(module=self.mod_acls, title='Compressões avançadas', order=1)
        self.enroll_bls = Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        Enrollment.objects.create(student=self.ana.student_profile, course=self.acls)

    def complete(self, lesson, user=None):
        user = user or self.jane
        Progress.objects.update_or_create(student=user.student_profile, lesson=lesson, defaults={'is_completed': True})

    def shell(self, user):
        request = RequestFactory().get('/dashboard/')
        request.user = user
        return student_shell(request)


class NotifyTests(A2Base):
    def test_creates_notification_and_sends_email_when_allowed(self):
        notify(self.jane, 'answer', 'O instrutor respondeu sua dúvida', 'BLS · Profundidade', '/community/?duvida=1')
        notification = Notification.objects.get(user=self.jane)
        self.assertEqual((notification.kind, notification.url), ('answer', '/community/?duvida=1'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['jane@example.com'])
        self.assertIn('/community/?duvida=1', mail.outbox[0].body)

    def test_email_respects_student_preference(self):
        profile = self.jane.student_profile
        profile.notify_answers = False
        profile.save()
        notify(self.jane, 'answer', 'Resposta', '', '/community/')
        self.assertEqual(Notification.objects.filter(user=self.jane).count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_email_false_only_creates_notification(self):
        notify(self.jane, 'module', 'Novo módulo liberado', 'BLS · Prática', '/meus-cursos/bls/', email=False)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(ALLOWED_HOSTS=['escola.example.com'])
    def test_absolute_link_when_request_is_given(self):
        request = RequestFactory().get('/', HTTP_HOST='escola.example.com')
        notify(self.jane, 'live', 'Aula ao vivo hoje às 20:00', 'BLS · Encontro', '/ao-vivo/', request=request)
        self.assertIn('http://escola.example.com/ao-vivo/', mail.outbox[0].body)

    def test_email_failure_does_not_break(self):
        from unittest import mock
        with mock.patch('users.notify.send_mail', side_effect=OSError('smtp fora do ar')), self.assertLogs('users.notify', 'ERROR'):
            notify(self.jane, 'answer', 'Resposta', '', '/community/')
        self.assertEqual(Notification.objects.count(), 1)


class StaffAnswerNotificationTests(A2Base):
    def setUp(self):
        super().setUp()
        self.post = CommunityPost.objects.create(author=self.jane, course=self.bls, title='Profundidade', content='Quanto?')

    def test_painel_reply_notifies_author(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('painel:community_action', args=[self.post.id]), {'action': 'reply', 'content': 'De 5 a 6 cm.'})
        notification = Notification.objects.get(user=self.jane)
        self.assertEqual(notification.title, 'O instrutor respondeu sua dúvida')
        self.assertEqual(notification.meta, 'BLS · Profundidade')
        self.assertEqual(notification.url, f'/community/?duvida={self.post.id}')
        self.assertEqual(len(mail.outbox), 1)

    def test_student_reply_does_not_notify(self):
        self.client.force_login(self.ana)
        Enrollment.objects.get_or_create(student=self.ana.student_profile, course=self.bls)
        self.client.post(reverse('community_reply', args=[self.post.id]), {'content': 'Também quero saber.'})
        self.assertEqual(Notification.objects.count(), 0)

    def test_staff_replying_to_own_post_does_not_notify(self):
        own = CommunityPost.objects.create(author=self.admin, title='Aviso', content='x')
        self.client.force_login(self.admin)
        self.client.post(reverse('painel:community'), {'post_id': own.id, 'action': 'reply', 'content': 'y'})
        self.assertEqual(Notification.objects.count(), 0)


class NotificationViewsTests(A2Base):
    def setUp(self):
        super().setUp()
        self.n1 = Notification.objects.create(user=self.jane, kind='answer', title='A', url='/community/?duvida=3')
        self.n2 = Notification.objects.create(user=self.jane, kind='live', title='B', url='/ao-vivo/')
        self.other = Notification.objects.create(user=self.ana, kind='live', title='C', url='/ao-vivo/')

    def test_open_marks_read_and_redirects(self):
        self.client.force_login(self.jane)
        response = self.client.get(reverse('notification_open', args=[self.n1.id]))
        self.assertRedirects(response, '/community/?duvida=3', fetch_redirect_response=False)
        self.n1.refresh_from_db()
        self.assertIsNotNone(self.n1.read_at)
        self.n2.refresh_from_db()
        self.assertIsNone(self.n2.read_at)

    def test_cannot_open_someone_elses_notification(self):
        self.client.force_login(self.jane)
        self.assertEqual(self.client.get(reverse('notification_open', args=[self.other.id])).status_code, 404)
        self.other.refresh_from_db()
        self.assertIsNone(self.other.read_at)

    def test_external_target_is_refused(self):
        self.n1.url = 'https://evil.example.com/'
        self.n1.save()
        self.client.force_login(self.jane)
        self.assertEqual(self.client.get(reverse('notification_open', args=[self.n1.id])).status_code, 404)

    def test_read_all_json_marks_only_own(self):
        self.client.force_login(self.jane)
        response = self.client.post(reverse('notifications_read_all'), HTTP_X_REQUESTED_WITH='fetch')
        self.assertEqual(response.json(), {'ok': True})
        self.assertEqual(Notification.objects.filter(user=self.jane, read_at__isnull=True).count(), 0)
        self.assertEqual(Notification.objects.filter(user=self.ana, read_at__isnull=True).count(), 1)

    def test_read_all_without_js_redirects_with_toast(self):
        self.client.force_login(self.jane)
        response = self.client.post(reverse('notifications_read_all'), follow=True)
        self.assertContains(response, 'Avisos marcados como lidos')

    def test_requires_post_and_login(self):
        self.assertEqual(self.client.post(reverse('notifications_read_all')).status_code, 302)
        self.client.force_login(self.jane)
        self.assertEqual(self.client.get(reverse('notifications_read_all')).status_code, 405)

    def test_bell_lists_notifications_in_layout(self):
        self.client.force_login(self.jane)
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertIn('2 não lidos', html)
        self.assertIn('notif__item is-unread', html)
        self.assertIn(reverse('notification_open', args=[self.n1.id]), html)


class SearchTests(A2Base):
    def get(self, q=None, user=None):
        self.client.force_login(user or self.jane)
        return self.client.get(reverse('search'), {'q': q} if q is not None else {})

    def test_lessons_only_from_enrolled_courses_and_published(self):
        response = self.get('compress')
        self.assertContains(response, 'Compressões torácicas')
        self.assertNotContains(response, 'Compressões avançadas')
        self.assertNotContains(response, 'em rascunho')
        self.assertContains(response, reverse('lesson_detail', args=['bls', self.l1.id]))

    def test_inactive_enrollment_hides_course(self):
        self.enroll_bls.is_active = False
        self.enroll_bls.save()
        self.assertNotContains(self.get('compress'), 'Compressões torácicas')

    def test_questions_exclude_hidden_and_other_courses_but_include_general(self):
        CommunityPost.objects.create(author=self.jane, course=self.bls, title='Dúvida sobre compressão', content='x')
        CommunityPost.objects.create(author=self.ana, course=self.acls, title='Compressão no ACLS', content='x')
        CommunityPost.objects.create(author=self.ana, title='Compressão geral', content='x')
        CommunityPost.objects.create(author=self.ana, title='Compressão oculta', content='x', is_hidden=True)
        response = self.get('compress')
        self.assertContains(response, 'Dúvida sobre compressão')
        self.assertContains(response, 'Compressão geral')
        self.assertNotContains(response, 'Compressão no ACLS')
        self.assertNotContains(response, 'Compressão oculta')

    def test_materials_group(self):
        LessonMaterial.objects.create(lesson=self.l1, title='Algoritmo de PCR', url='https://example.com/a.pdf')
        response = self.get('algoritmo')
        self.assertContains(response, 'Materiais')
        self.assertContains(response, reverse('lesson_detail', args=['bls', self.l1.id]) + '?aba=materiais')

    def test_limit_per_group(self):
        for number in range(8):
            Lesson.objects.create(module=self.mod_bls, title=f'Revisão {number}', order=10 + number)
        html = self.get('revis').content.decode()
        self.assertEqual(html.count('cmdk__item"'), 5)

    def test_no_results_renders_nothing(self):
        self.assertEqual(self.get('zzzzzz').content.decode().strip(), '')

    def test_empty_query_shows_continue_and_shortcuts(self):
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l2, position_seconds=40)
        response = self.get()
        self.assertContains(response, 'Continuar')
        self.assertContains(response, 'Uso do DEA')
        for label in ('Atalhos', 'Aulas ao vivo', 'Certificados', 'Minha conta'):
            self.assertContains(response, label)

    def test_empty_query_without_progress_continues_first_lesson(self):
        self.assertContains(self.get(), 'Compressões torácicas')

    def test_staff_without_student_profile_gets_shortcuts_only(self):
        response = self.get(user=self.admin)
        self.assertContains(response, 'Atalhos')
        self.assertNotContains(response, 'Continuar')

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('search')).status_code, 302)


class StudentShellTests(A2Base):
    def test_neutral_values_for_user_without_courses(self):
        user = User.objects.create_user(username='nova', email='nova@example.com', password=PASSWORD)
        context = self.shell(user)
        self.assertEqual((context['lessons_total'], context['certificates_ready'], context['community_unread']), (0, 0, 0))
        self.assertIsNone(context['live_badge'])

    def test_progress_counts_only_published_lessons_of_active_enrollments(self):
        self.complete(self.l1)
        self.complete(self.draft)
        context = self.shell(self.jane)
        self.assertEqual((context['lessons_done'], context['lessons_total'], context['lessons_pct']), (1, 2, 50))

    def test_progress_of_other_students_is_not_mixed_in(self):
        Enrollment.objects.create(student=self.ana.student_profile, course=self.bls)
        self.complete(self.l1, self.ana)
        self.complete(self.l2, self.ana)
        self.complete(self.l1, self.jane)
        context = self.shell(self.jane)
        self.assertEqual((context['lessons_done'], context['lessons_total']), (1, 2))

    def test_certificates_ready_until_issued(self):
        self.complete(self.l1)
        self.complete(self.l2)
        self.assertEqual(self.shell(self.jane)['certificates_ready'], 1)
        Certificate.objects.create(enrollment=self.enroll_bls, code='ABC123DEF456', student_name='Jane', student_cpf='52998224725',
                                   course_title='BLS', completed_at=timezone.now())
        self.assertEqual(self.shell(self.jane)['certificates_ready'], 0)

    def test_certificates_ready_ignores_courses_with_certificate_disabled(self):
        self.bls.certificate_enabled = False
        self.bls.save()
        self.complete(self.l1)
        self.complete(self.l2)
        self.assertEqual(self.shell(self.jane)['certificates_ready'], 0)

    def test_community_unread_counts_own_posts_with_new_answer(self):
        post = CommunityPost.objects.create(author=self.jane, course=self.bls, title='Dúvida', content='x')
        Comment.objects.create(post=post, author=self.admin, content='Resposta')
        self.assertEqual(self.shell(self.jane)['community_unread'], 1)

    def test_live_badge_states(self):
        now = timezone.now()
        session = LiveSession.objects.create(course=self.bls, title='Encontro', starts_at=now + timedelta(days=3),
                                             ends_at=now + timedelta(days=3, hours=1))
        badge = self.shell(self.jane)['live_badge']
        self.assertFalse(badge['is_live'])
        self.assertIn(badge['label'], ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'])
        session.starts_at, session.ends_at = now - timedelta(minutes=5), now + timedelta(hours=1)
        session.save()
        self.assertEqual(self.shell(self.jane)['live_badge'], {'label': 'Ao vivo', 'is_live': True})
        session.starts_at, session.ends_at = now + timedelta(days=9), now + timedelta(days=9, hours=1)
        session.save()
        self.assertIsNone(self.shell(self.jane)['live_badge'])

    def test_live_badge_ignores_courses_without_enrollment(self):
        now = timezone.now()
        LiveSession.objects.create(course=self.acls, title='Outro', starts_at=now + timedelta(hours=1), ends_at=now + timedelta(hours=2))
        self.assertIsNone(self.shell(self.jane)['live_badge'])

    def test_at_most_eight_queries(self):
        self.complete(self.l1)
        Notification.objects.create(user=self.jane, kind='answer', title='A', url='/')
        request = RequestFactory().get('/dashboard/')
        request.user = User.objects.get(pk=self.jane.pk)
        with CaptureQueriesContext(connection) as queries:
            student_shell(request)
        self.assertLessEqual(len(queries), 8, [q['sql'][:90] for q in queries])

    def test_staff_gets_notifications_but_no_progress(self):
        Notification.objects.create(user=self.admin, kind='access', title='Acesso', url='/painel/')
        context = self.shell(self.admin)
        self.assertEqual(context['unread_count'], 1)
        self.assertEqual(context['lessons_total'], 0)


class LayoutShellTests(A2Base):
    def test_sidebar_and_bottom_nav_show_badges(self):
        self.complete(self.l1)
        self.complete(self.l2)
        post = CommunityPost.objects.create(author=self.jane, course=self.bls, title='Dúvida', content='x')
        Comment.objects.create(post=post, author=self.admin, content='Resposta')
        self.client.force_login(self.jane)
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertIn('2 de 2 aulas concluídas', html)
        self.assertIn('1 pronto para emitir', html)
        self.assertIn('1 resposta nova', html)
        self.assertIn('class="bottom-nav"', html)
        self.assertIn('data-search-url="' + reverse('search') + '"', html)

    def test_singular_labels_in_layout(self):
        Notification.objects.create(user=self.ana, kind='live', title='Aviso', url='/ao-vivo/')
        self.client.force_login(self.ana)
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertIn('Avisos, 1 não lido"', html)
