from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from community.models import Comment, CommunityPost
from courses.models import Certificate, Course, Enrollment, Lesson, LessonMaterial, Module, Progress
from users.models import Notification

User = get_user_model()
PASSWORD = 'StrongPassword123!'
VIMEO = 'https://vimeo.com/76979871'


class A3Base(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.jane = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        self.ana = User.objects.create_user(username='ana', email='ana@example.com', password=PASSWORD)
        self.course = Course.objects.create(title='Suporte Básico de Vida', short_name='BLS', slug='bls',
                                            creator=self.admin.creator_profile, status='published')
        self.m1 = Module.objects.create(course=self.course, title='Introdução', order=1)
        self.m2 = Module.objects.create(course=self.course, title='Prática', order=2)
        self.l1 = Lesson.objects.create(module=self.m1, title='Aula 1', order=1, video_url=VIMEO, duration_seconds=300)
        self.l2 = Lesson.objects.create(module=self.m1, title='Aula 2', order=2, video_url=VIMEO, duration_seconds=420)
        self.l3 = Lesson.objects.create(module=self.m2, title='Aula 3', order=1, description='Texto da aula três.')
        self.draft = Lesson.objects.create(module=self.m2, title='Rascunho', order=2, status='draft')
        self.enrollment = Enrollment.objects.create(student=self.jane.student_profile, course=self.course)
        self.client.force_login(self.jane)

    def url(self, lesson, **params):
        base = reverse('lesson_detail', args=['bls', lesson.id])
        return base + ('?' + '&'.join(f'{k}={v}' for k, v in params.items()) if params else '')

    def post(self, name, lesson, **data):
        return self.client.post(reverse(name, args=[lesson.id]), data, HTTP_X_REQUESTED_WITH='fetch')

    def progress(self, lesson):
        return Progress.objects.filter(student=self.jane.student_profile, lesson=lesson).first()

    def complete_all_but(self, *skip):
        for lesson in (self.l1, self.l2, self.l3):
            if lesson not in skip:
                Progress.objects.update_or_create(student=self.jane.student_profile, lesson=lesson, defaults={'is_completed': True})


class PlayerPageTests(A3Base):
    def test_page_exposes_contract_for_player_js(self):
        html = self.client.get(self.url(self.l2)).content.decode()
        for marker in ('id="lesson-page"', f'data-lesson-id="{self.l2.id}"', f'data-module-id="{self.m1.id}"',
                       reverse('toggle_progress', args=[self.l2.id]), reverse('complete_lesson', args=[self.l2.id]),
                       reverse('save_position', args=[self.l2.id]), 'data-resume="0"', 'data-completed="false"',
                       'data-vimeo', 'id="resume-chip"', 'data-resume-restart', 'data-complete-toggle', 'id="done-banner"',
                       'data-next-link', 'data-done-stay', 'id="celebrate"', 'data-course-progress', 'data-progress-text',
                       'data-progress-count', 'data-cert-mini', 'data-cert-text', 'data-cert-link', 'data-focus-toggle',
                       f'id="status-dot-{self.l2.id}"', f'data-lesson-meta="{self.l2.id}"', f'data-module-count="{self.m1.id}"',
                       'data-nav-next', 'id="cmdk"'):
            self.assertIn(marker, html, marker)
        self.assertIn('js/player.js', html)
        self.assertNotIn('aluno.js', html)

    def test_public_preview_does_not_load_removed_script(self):
        self.client.logout()
        self.assertNotContains(self.client.get(reverse('course_preview', args=['bls'])), 'aluno.js')

    def test_header_texts(self):
        html = self.client.get(self.url(self.l2)).content.decode()
        self.assertIn('Módulo 1 · Introdução · Aula 2 de 3', html)
        self.assertNotIn('Módulo 1 · Módulo', html)
        self.assertIn('0% · 0 de 3 aulas', html)
        self.assertIn('Marcar como concluída', html)
        self.assertIn('A aula também é marcada sozinha quando você assiste 90% do vídeo.', html)
        self.assertIn('Faltam 3 aulas.', html)

    def test_draft_lesson_is_excluded_from_totals_and_list(self):
        response = self.client.get(self.url(self.l1))
        self.assertEqual(response.context['total'], 3)
        self.assertNotContains(response, 'Rascunho')

    def test_progress_record_is_created_on_open_without_completing(self):
        self.client.get(self.url(self.l2))
        record = self.progress(self.l2)
        self.assertIsNotNone(record)
        self.assertFalse(record.is_completed)

    def test_saved_position_is_passed_as_resume(self):
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l2, position_seconds=192)
        self.assertContains(self.client.get(self.url(self.l2)), 'data-resume="192"')

    def test_completed_lesson_state(self):
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l1, is_completed=True)
        html = self.client.get(self.url(self.l1)).content.decode()
        self.assertIn('data-completed="true"', html)
        self.assertIn('aria-pressed="true"', html)
        self.assertIn('Concluída', html)

    def test_prev_next_and_last_lesson_navigation(self):
        middle = self.client.get(self.url(self.l2)).content.decode()
        self.assertIn('Aula anterior', middle)
        self.assertIn(reverse('lesson_detail', args=['bls', self.l3.id]), middle)
        first = self.client.get(self.url(self.l1)).content.decode()
        self.assertNotIn('Aula anterior', first)
        last = self.client.get(self.url(self.l3)).content.decode()
        self.assertIn('Última aula do curso', last)
        self.assertIn('Ver requisitos do certificado', last)
        self.assertNotIn('id="done-banner"', last)
        self.assertNotIn('data-nav-next', last)

    def test_non_vimeo_lesson_has_no_resume_or_auto_note(self):
        html = self.client.get(self.url(self.l3)).content.decode()
        self.assertNotIn('data-vimeo', html)
        self.assertNotIn('id="resume-chip"', html)
        self.assertNotIn('marcada sozinha', html)

    def test_lesson_without_video_shows_unavailable_message_and_logs(self):
        with self.assertLogs('courses.student_views', 'WARNING') as logs:
            response = self.client.get(self.url(self.l3))
        self.assertContains(response, 'Este vídeo está indisponível agora. A equipe já foi avisada.')
        self.assertIn(str(self.l3.id), logs.output[0])

    def test_tabs_follow_aba_parameter(self):
        html = self.client.get(self.url(self.l1, aba='materiais')).content.decode()
        self.assertIn('id="tab-materiais" aria-controls="panel-materiais" data-tab="materiais" aria-selected="true"', html)
        self.assertIn('id="panel-sobre" aria-labelledby="tab-sobre" hidden', html)
        self.assertNotIn('id="panel-materiais" aria-labelledby="tab-materiais" hidden', html)
        self.assertEqual(self.client.get(self.url(self.l1, aba='x')).context['aba'], 'sobre')

    def test_about_and_empty_materials_texts(self):
        html = self.client.get(self.url(self.l3)).content.decode()
        self.assertIn('Texto da aula três.', html)
        self.assertIn('Esta aula não tem material de apoio.', html)
        self.assertIn('O instrutor não escreveu uma descrição para esta aula.', self.client.get(self.url(self.l1)).content.decode())

    def test_materials_tab_counts_and_links(self):
        LessonMaterial.objects.create(lesson=self.l1, title='Algoritmo', url='https://example.com/a.pdf')
        html = self.client.get(self.url(self.l1)).content.decode()
        self.assertIn('Materiais (1)', html)
        self.assertIn('https://example.com/a.pdf', html)

    def test_certificate_card_states(self):
        self.assertIn('Liberado ao concluir 100% das aulas.', self.client.get(self.url(self.l1)).content.decode())
        self.complete_all_but()
        html = self.client.get(self.url(self.l1)).content.decode()
        self.assertIn('cert-mini is-ready', html)
        self.assertIn('Todas as aulas concluídas. Confira seus dados e emita.', html)
        self.assertIn('Emitir certificado', html)

    def test_celebrate_dialog_text_depends_on_profile_data(self):
        html = self.client.get(self.url(self.l1)).content.decode()
        self.assertIn('Você concluiu o BLS', html)
        self.assertIn('Todas as 3 aulas foram concluídas. Falta só conferir nome e CPF para emitir o certificado.', html)
        profile = self.jane.student_profile
        profile.full_name, profile.cpf = 'Jane Silva', '52998224725'
        profile.save()
        self.assertIn('Seu certificado já pode ser emitido.', self.client.get(self.url(self.l1)).content.decode())

    def test_module_not_released_redirects_with_info_toast(self):
        self.course.release_mode = 'scheduled'
        self.course.save()
        self.m2.release_after_days = 10
        self.m2.save()
        response = self.client.get(self.url(self.l3), follow=True)
        expected = (self.enrollment.enrolled_at + timedelta(days=10)).astimezone(timezone.get_current_timezone())
        self.assertContains(response, f'Este módulo libera em {expected:%d/%m}.')
        self.assertContains(response, 'data-kind="info"')

    def test_draft_lesson_is_404_and_inactive_enrollment_cannot_open(self):
        self.assertEqual(self.client.get(self.url(self.draft)).status_code, 404)
        self.enrollment.is_active = False
        self.enrollment.save()
        self.assertRedirects(self.client.get(self.url(self.l1)), reverse('course_preview', args=['bls']))


class ProgressEndpointsTests(A3Base):
    def test_toggle_marks_then_unmarks_with_full_payload(self):
        first = self.post('toggle_progress', self.l1).json()
        self.assertTrue(first['is_completed'])
        for key in ('completed_count', 'total_count', 'percentage', 'module', 'remaining', 'course_done', 'next', 'certificate_url'):
            self.assertIn(key, first)
        self.assertEqual((first['completed_count'], first['total_count'], first['remaining']), (1, 3, 2))
        self.assertEqual(first['module'], {'id': self.m1.id, 'done': 1, 'total': 2})
        self.assertEqual(first['next']['title'], 'Aula 2')
        second = self.post('toggle_progress', self.l1).json()
        self.assertFalse(second['is_completed'])
        self.assertEqual(second['completed_count'], 0)
        self.assertFalse(self.progress(self.l1).is_completed)

    def test_toggle_keeps_points_behaviour(self):
        self.post('toggle_progress', self.l1)
        profile = self.jane.student_profile
        profile.refresh_from_db()
        self.assertEqual(profile.points, 10)
        self.post('toggle_progress', self.l1)
        profile.refresh_from_db()
        self.assertEqual(profile.points, 0)

    def test_toggle_requires_post_login_enrollment_student_and_published(self):
        self.assertEqual(self.client.get(reverse('toggle_progress', args=[self.l1.id])).status_code, 405)
        self.assertEqual(self.post('toggle_progress', self.draft).status_code, 404)
        self.client.force_login(self.ana)
        self.assertEqual(self.post('toggle_progress', self.l1).status_code, 403)
        self.assertEqual(self.post('complete_lesson', self.l1).status_code, 403)
        self.assertEqual(self.post('save_position', self.l1, seconds=10).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.post('toggle_progress', self.l1).status_code, 403)
        self.client.logout()
        self.assertEqual(self.post('toggle_progress', self.l1).status_code, 302)

    def test_inactive_enrollment_cannot_change_progress(self):
        self.enrollment.is_active = False
        self.enrollment.save()
        self.assertEqual(self.post('toggle_progress', self.l1).status_code, 403)

    def test_complete_is_idempotent_and_never_unmarks(self):
        first = self.post('complete_lesson', self.l1).json()
        second = self.post('complete_lesson', self.l1).json()
        self.assertEqual(first, second)
        self.assertTrue(second['is_completed'])

    def test_last_lesson_has_no_next_and_marks_course_done(self):
        self.complete_all_but(self.l3)
        payload = self.post('complete_lesson', self.l3).json()
        self.assertIsNone(payload['next'])
        self.assertTrue(payload['course_done'])
        self.assertEqual(payload['certificate_url'], '/certificados/?emitir=bls')

    def test_certificate_notification_only_when_course_becomes_done(self):
        self.post('complete_lesson', self.l1)
        self.assertEqual(Notification.objects.filter(kind='certificate').count(), 0)
        self.complete_all_but(self.l3)
        self.post('complete_lesson', self.l3)
        notification = Notification.objects.get(kind='certificate')
        self.assertEqual(notification.user, self.jane)
        self.assertEqual(notification.title, 'Seu certificado está pronto para emitir')
        self.assertEqual(notification.url, '/certificados/?emitir=bls')
        self.assertEqual(len(mail.outbox), 1)
        self.post('complete_lesson', self.l3)
        self.assertEqual(Notification.objects.filter(kind='certificate').count(), 1)

    def test_certificate_notification_not_repeated_after_unmark_and_mark(self):
        self.complete_all_but(self.l3)
        self.post('toggle_progress', self.l3)
        self.post('toggle_progress', self.l3)
        self.post('toggle_progress', self.l3)
        self.assertEqual(Notification.objects.filter(kind='certificate').count(), 1)

    def test_no_certificate_notification_when_disabled_or_already_issued(self):
        self.course.certificate_enabled = False
        self.course.save()
        self.complete_all_but(self.l3)
        self.post('complete_lesson', self.l3)
        self.assertEqual(Notification.objects.count(), 0)

    def test_no_notification_when_certificate_already_issued(self):
        Certificate.objects.create(enrollment=self.enrollment, code='ABC123DEF456', student_name='Jane', student_cpf='52998224725',
                                   course_title='BLS', completed_at=timezone.now())
        self.complete_all_but(self.l3)
        self.post('complete_lesson', self.l3)
        self.assertEqual(Notification.objects.count(), 0)

    def test_save_position_stores_seconds_without_completing(self):
        self.assertEqual(self.post('save_position', self.l2, seconds=192).json(), {'ok': True})
        record = self.progress(self.l2)
        self.assertEqual(record.position_seconds, 192)
        self.assertFalse(record.is_completed)

    def test_save_position_keeps_completion_and_clamps(self):
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l2, is_completed=True)
        self.post('save_position', self.l2, seconds=999999)
        record = self.progress(self.l2)
        self.assertTrue(record.is_completed)
        self.assertEqual(record.position_seconds, 86400)
        self.post('save_position', self.l2, seconds=-5)
        self.assertEqual(self.progress(self.l2).position_seconds, 0)

    def test_save_position_rejects_invalid_values(self):
        self.assertEqual(self.post('save_position', self.l2, seconds='abc').status_code, 400)
        self.assertEqual(self.post('save_position', self.l2).status_code, 400)

    def test_save_position_updates_resume_choice(self):
        self.post('save_position', self.l1, seconds=40)
        self.post('save_position', self.l2, seconds=90)
        from courses.services import course_progress
        info = course_progress(self.jane, self.course)
        self.assertEqual((info['resume_lesson'], info['resume_seconds']), (self.l2, 90))

    def test_save_position_accepts_beacon_with_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.jane)
        client.get(self.url(self.l2))
        token = client.cookies['csrftoken'].value
        denied = client.post(reverse('save_position', args=[self.l2.id]), {'seconds': 30})
        self.assertEqual(denied.status_code, 403)
        allowed = client.post(reverse('save_position', args=[self.l2.id]), {'seconds': 30, 'csrfmiddlewaretoken': token})
        self.assertEqual(allowed.json(), {'ok': True})


class LessonQuestionsTests(A3Base):
    ASKED = 'Dúvida publicada. Avisaremos por e-mail quando responderem'

    def ask(self, content='Em 02:40, qual a posição das mãos?', json_mode=True):
        extra = {'HTTP_X_REQUESTED_WITH': 'fetch'} if json_mode else {}
        return self.client.post(reverse('create_post', args=['bls']), {'lesson_id': self.l2.id, 'content': content}, **extra)

    def test_json_publish_replaces_list_and_toasts(self):
        data = self.ask().json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['toast'], self.ASKED)
        self.assertIn('Em 02:40', data['replace']['#lesson-questions'])
        self.assertIn('Aguardando resposta', data['replace']['#lesson-questions'])
        post = CommunityPost.objects.get()
        self.assertEqual((post.lesson, post.course, post.author), (self.l2, self.course, self.jane))

    def test_without_js_redirects_to_questions_tab_with_toast(self):
        response = self.ask(json_mode=False)
        self.assertRedirects(response, self.url(self.l2, aba='duvidas'), fetch_redirect_response=False)
        self.assertContains(self.client.get(self.url(self.l2, aba='duvidas')), self.ASKED)

    def test_empty_question_returns_field_error(self):
        response = self.ask(content='   ')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['errors'], {'content': ['Escreva sua dúvida.']})
        self.assertEqual(CommunityPost.objects.count(), 0)

    def test_list_shows_badges_counts_and_official_answer(self):
        waiting = CommunityPost.objects.create(author=self.jane, course=self.course, lesson=self.l2, title='Sem resposta', content='x')
        answered = CommunityPost.objects.create(author=self.jane, course=self.course, lesson=self.l2, title='Com resposta', content='y')
        Comment.objects.create(post=answered, author=self.admin, content='Mantenha 5 a 6 cm.')
        html = self.client.get(self.url(self.l2, aba='duvidas')).content.decode()
        self.assertIn('Dúvidas (2)', html)
        self.assertIn('Respondida pelo instrutor', html)
        self.assertIn('Aguardando resposta', html)
        self.assertIn('<strong>Instrutor CETREMER:</strong> Mantenha 5 a 6 cm.', html)
        self.assertIn('1 resposta', html)
        self.assertIn('0 respostas', html)
        self.assertIn(f'?duvida={waiting.id}', html)
        self.assertNotIn('jane_student', html)

    def test_hidden_and_other_lesson_questions_are_not_listed(self):
        CommunityPost.objects.create(author=self.jane, course=self.course, lesson=self.l2, title='Oculta', content='x', is_hidden=True)
        CommunityPost.objects.create(author=self.jane, course=self.course, lesson=self.l1, title='De outra aula', content='x')
        html = self.client.get(self.url(self.l2, aba='duvidas')).content.decode()
        self.assertNotIn('Oculta', html)
        self.assertNotIn('De outra aula', html)
        self.assertIn('Ninguém perguntou nada nesta aula ainda.', html)

    def test_unenrolled_student_cannot_post(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.ask().status_code, 403)
