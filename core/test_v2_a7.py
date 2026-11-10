from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from community.models import Comment, CommunityPost
from courses.models import Course, Enrollment, Lesson, Module
from users.models import Notification

User = get_user_model()
PASSWORD = 'StrongPassword123!'
PUBLISHED = 'Pergunta publicada. Avisaremos por e-mail quando responderem'


class A7Base(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.jane = User.objects.create_user(username='jane_student', email='jane@example.com', password=PASSWORD)
        self.ana = User.objects.create_user(username='ana', email='ana@example.com', password=PASSWORD)
        self.bls = self.make_course('BLS', 'Suporte Básico de Vida', 'bls', 3)
        self.acls = self.make_course('ACLS', 'Suporte Avançado ACLS', 'acls', 2)
        self.pals = self.make_course('PALS', 'Suporte Avançado PALS', 'pals', 1)
        for user in (self.jane, self.ana):
            Enrollment.objects.create(student=user.student_profile, course=self.bls)
        Enrollment.objects.create(student=self.jane.student_profile, course=self.acls)
        self.client.force_login(self.jane)

    def make_course(self, short, title, slug, lessons):
        course = Course.objects.create(title=title, short_name=short, slug=slug, creator=self.admin.creator_profile, status='published')
        module = Module.objects.create(course=course, title='Módulo', order=1)
        for number in range(1, lessons + 1):
            Lesson.objects.create(module=module, title=f'{short} aula {number}', order=number)
        return course

    def lessons(self, course):
        return list(Lesson.objects.filter(module__course=course).order_by('order'))

    def post(self, title='Dúvida', author=None, course='bls', lesson=None, content='Texto da dúvida', **extra):
        course_obj = {'bls': self.bls, 'acls': self.acls, 'pals': self.pals, None: None}[course]
        return CommunityPost.objects.create(author=author or self.jane, course=course_obj, lesson=lesson, title=title, content=content, **extra)

    def answer(self, post, author=None):
        return Comment.objects.create(post=post, author=author or self.admin, content='Resposta oficial do instrutor.')

    def page(self, **params):
        return self.client.get(reverse('community'), params)

    def titles(self, response):
        return [p.title for p in response.context['posts']]


class ListTests(A7Base):
    def test_default_filters_and_chips(self):
        html = self.page().content.decode()
        self.assertEqual(self.page().context['situation'], 'todas')
        self.assertEqual(self.page().context['course_filter'], '')
        for label in ('Todas', 'Sem resposta', 'Respondidas', 'Minhas', 'Todos os cursos', '>BLS<', '>ACLS<', 'Discussão geral'):
            self.assertIn(label, html)
        self.assertNotIn('>PALS<', html)

    def test_only_enrolled_and_general_posts_are_visible(self):
        self.post('No BLS')
        self.post('No PALS', course='pals', author=self.ana)
        self.post('Geral', course=None)
        self.post('Oculta', is_hidden=True)
        self.assertEqual(sorted(self.titles(self.page())), ['Geral', 'No BLS'])

    def test_inactive_enrollment_hides_course(self):
        self.post('No ACLS', course='acls')
        Enrollment.objects.filter(student=self.jane.student_profile, course=self.acls).update(is_active=False)
        self.assertEqual(self.titles(self.page()), [])
        self.assertNotIn('>ACLS<', self.page().content.decode())

    def test_situation_filters(self):
        waiting = self.post('Sem resposta')
        answered = self.post('Respondida')
        self.answer(answered)
        other = self.post('De outra pessoa', author=self.ana)
        self.assertEqual(set(self.titles(self.page(situacao='sem-resposta'))), {'Sem resposta', 'De outra pessoa'})
        self.assertEqual(self.titles(self.page(situacao='respondidas')), ['Respondida'])
        self.assertEqual(set(self.titles(self.page(situacao='minhas'))), {'Sem resposta', 'Respondida'})
        self.assertEqual(len(self.titles(self.page(situacao='invalida'))), 3)
        self.assertIsNotNone(waiting.pk, other.pk)

    def test_course_filters(self):
        self.post('Do BLS')
        self.post('Do ACLS', course='acls')
        self.post('Geral', course=None)
        self.assertEqual(self.titles(self.page(curso='bls')), ['Do BLS'])
        self.assertEqual(self.titles(self.page(curso='acls')), ['Do ACLS'])
        self.assertEqual(self.titles(self.page(curso='geral')), ['Geral'])
        self.assertEqual(len(self.titles(self.page(curso='pals'))), 3)

    def test_search_in_title_and_content(self):
        self.post('Profundidade da compressão')
        self.post('Outra coisa', content='fala da ventilação com bolsa')
        self.assertEqual(self.titles(self.page(q='compress')), ['Profundidade da compressão'])
        self.assertEqual(self.titles(self.page(q='ventila')), ['Outra coisa'])
        self.assertContains(self.page(q='compress'), 'value="compress"')

    def test_filters_combine(self):
        mine = self.post('Minha do BLS')
        self.post('Minha do ACLS', course='acls')
        self.post('Da Ana', author=self.ana)
        self.assertEqual(self.titles(self.page(situacao='minhas', curso='bls')), [mine.title])

    def test_pinned_first_then_newest(self):
        old = self.post('Antiga')
        new = self.post('Nova')
        pinned = self.post('Fixada', is_pinned=True)
        CommunityPost.objects.filter(pk=pinned.pk).update(created_at=timezone.now() - timedelta(days=9))
        CommunityPost.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=3))
        response = self.page()
        self.assertEqual(self.titles(response), ['Fixada', 'Nova', 'Antiga'])
        self.assertIn('aria-label="Fixada"', response.content.decode())
        self.assertIsNotNone(new.pk)

    def test_row_content(self):
        lesson = self.lessons(self.bls)[1]
        post = self.post('Profundidade', lesson=lesson, content='Em 02:40, qual a profundidade correta?')
        self.answer(post)
        html = self.page().content.decode()
        self.assertIn('Respondida pelo instrutor', html)
        self.assertIn('Em 02:40, qual a profundidade correta?', html)
        self.assertIn('Jane · BLS · Aula 2 · BLS aula 2 ·', html)
        self.assertIn(f'data-drawer-url="?duvida={post.id}&parcial=1"', html)
        self.assertIn('data-drawer-target="drawer-conversa"', html)
        self.assertIn('data-drawer-param="duvida"', html)
        self.assertEqual(self.page().context['posts'][0].replies, 1)
        self.assertNotIn('jane_student', html)

    def test_waiting_badge_and_general_label(self):
        self.post('Geral', course=None)
        html = self.page().content.decode()
        self.assertIn('Aguardando resposta', html)
        self.assertIn('Jane · Discussão geral ·', html)

    def test_unread_and_new_markers(self):
        mine = self.post('Minha')
        self.answer(mine)
        theirs = self.post('Da Ana', author=self.ana, has_unread_answer=True)
        html = self.page(nova_id=theirs.id).content.decode()
        self.assertEqual(html.count('is-unread'), 1)
        self.assertEqual(html.count(' is-new'), 1)
        self.assertIn('thread is-unread', html)

    def test_empty_states(self):
        self.assertContains(self.page(), 'Nenhuma dúvida com esses filtros')
        self.assertNotContains(self.page(), 'Limpar filtros')
        minhas = self.page(situacao='minhas')
        self.assertContains(minhas, 'Você ainda não perguntou nada aqui')
        self.assertContains(minhas, 'Use o botão Nova pergunta ou pergunte direto da aula.')
        self.assertContains(minhas, 'Limpar filtros')
        self.assertContains(self.page(q='zzz'), 'Tente outro curso ou outra situação.')

    def test_side_cards(self):
        html = self.page().content.decode()
        for text in ('Como funciona', 'Pergunte de dentro da aula para a dúvida já ir com o nome da aula.',
                     'Você recebe um e-mail quando o instrutor responder.',
                     'Resposta do instrutor aparece em destaque, no topo da conversa.', 'Combinados',
                     'Sem dados de pacientes, sem prescrição individual e sem divulgação.'):
            self.assertIn(text, html)

    def test_staff_sees_every_course(self):
        self.post('No PALS', course='pals', author=self.ana)
        self.client.force_login(self.admin)
        response = self.page()
        self.assertEqual(self.titles(response), ['No PALS'])
        self.assertIn('>PALS<', response.content.decode())

    def test_requires_login_and_old_routes_are_gone(self):
        self.client.logout()
        self.assertEqual(self.page().status_code, 302)
        for name in ('community_hub', 'create_hub_post', 'create_comment'):
            with self.assertRaises(NoReverseMatch):
                reverse(name)


class ThreadTests(A7Base):
    def url(self, post, **extra):
        params = f'?duvida={post.id}' + ''.join(f'&{k}={v}' for k, v in extra.items())
        return reverse('community') + params

    def test_partial_returns_only_the_inner_markup(self):
        post = self.post('Profundidade')
        html = self.client.get(self.url(post, parcial=1)).content.decode()
        self.assertNotIn('<html', html)
        self.assertIn('id="thread-content"', html)
        self.assertIn('Profundidade', html)
        self.assertIn(reverse('community_reply', args=[post.id]), html)

    def test_partial_is_forbidden_for_invisible_threads(self):
        self.assertEqual(self.client.get(self.url(self.post('Do PALS', course='pals', author=self.ana), parcial=1)).status_code, 403)
        self.assertEqual(self.client.get(self.url(self.post('Oculta', is_hidden=True), parcial=1)).status_code, 403)
        self.assertEqual(self.client.get(reverse('community') + '?duvida=99999&parcial=1').status_code, 403)

    def test_full_page_opens_the_drawer(self):
        post = self.post('Profundidade')
        response = self.client.get(self.url(post))
        self.assertContains(response, 'data-autoopen="duvida"')
        self.assertContains(response, 'id="thread-content"')
        self.assertEqual(response.context['open_post'], post)

    def test_unknown_or_invisible_thread_is_ignored_in_full_page(self):
        response = self.client.get(self.url(self.post('Do PALS', course='pals', author=self.ana)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'data-autoopen="duvida"')
        self.assertIsNone(response.context['open_post'])

    def test_opening_my_thread_clears_unread_answer(self):
        post = self.post('Minha')
        self.answer(post)
        post.refresh_from_db()
        self.assertTrue(post.has_unread_answer)
        self.client.get(self.url(post))
        post.refresh_from_db()
        self.assertFalse(post.has_unread_answer)

    def test_partial_also_clears_unread_but_other_people_do_not(self):
        post = self.post('Minha')
        self.answer(post)
        self.client.force_login(self.ana)
        self.client.get(self.url(post, parcial=1))
        post.refresh_from_db()
        self.assertTrue(post.has_unread_answer)
        self.client.force_login(self.jane)
        self.client.get(self.url(post, parcial=1))
        post.refresh_from_db()
        self.assertFalse(post.has_unread_answer)

    def test_official_answer_block_and_resolve_buttons_for_author(self):
        post = self.post('Minha', lesson=self.lessons(self.bls)[1])
        self.answer(post)
        html = self.client.get(self.url(post, parcial=1)).content.decode()
        self.assertIn('answer-box__by', html)
        self.assertIn('Instrutor CETREMER', html)
        self.assertIn('Resposta oficial', html)
        self.assertIn('Resposta oficial do instrutor.', html)
        self.assertIn('Isso resolveu sua dúvida?', html)
        self.assertIn('Sim, resolveu', html)
        self.assertIn('Ainda tenho dúvida', html)
        self.assertIn('data-focus-target="#reply-content"', html)
        self.assertNotIn('waiting-box', html)
        self.assertIn('BLS · Aula 2 · BLS aula 2', html)

    def test_resolved_state_of_the_button(self):
        post = self.post('Minha', is_resolved=True)
        self.answer(post)
        html = self.client.get(self.url(post, parcial=1)).content.decode()
        self.assertIn('Marcada como resolvida', html)
        self.assertIn('aria-pressed="true"', html)

    def test_other_students_do_not_get_the_resolve_question(self):
        post = self.post('Da Ana', author=self.ana)
        self.answer(post)
        html = self.client.get(self.url(post, parcial=1)).content.decode()
        self.assertIn('Resposta oficial', html)
        self.assertNotIn('Isso resolveu sua dúvida?', html)

    def test_waiting_box_without_official_answer(self):
        post = self.post('Sem resposta')
        Comment.objects.create(post=post, author=self.ana, content='Também quero saber.')
        html = self.client.get(self.url(post, parcial=1)).content.decode()
        self.assertIn('Aguardando o instrutor. A equipe costuma responder em até 1 dia útil, e você recebe um e-mail.', html)
        self.assertIn('Também quero saber.', html)
        self.assertNotIn('Resposta oficial', html)
        self.assertIn('Escreva uma resposta', html)

    def test_general_thread_header(self):
        post = self.post('Geral', course=None)
        self.assertIn('Discussão geral', self.client.get(self.url(post, parcial=1)).content.decode())


class ComposeTests(A7Base):
    def test_drawer_autoopen_and_preselection(self):
        lesson = self.lessons(self.acls)[1]
        response = self.page(nova=1, curso='acls', aula=lesson.id)
        html = response.content.decode()
        self.assertIn('data-autoopen="nova"', html)
        self.assertEqual(response.context['compose_course'], self.acls)
        self.assertEqual(response.context['compose_lesson'], lesson)
        self.assertIn(f'<option value="{self.acls.id}" selected>', html)
        self.assertIn(f'<option value="{lesson.id}" selected>', html)
        self.assertNotIn('data-autoopen="nova"', self.page().content.decode())

    def test_lesson_alone_selects_its_course(self):
        lesson = self.lessons(self.bls)[0]
        self.assertEqual(self.page(nova=1, aula=lesson.id).context['compose_course'], self.bls)

    def test_other_courses_lessons_are_not_offered_or_preselected(self):
        lesson = self.lessons(self.pals)[0]
        response = self.page(nova=1, aula=lesson.id)
        self.assertIsNone(response.context['compose_lesson'])
        self.assertNotContains(response, 'PALS aula 1')

    def test_form_contents(self):
        html = self.page(nova=1).content.decode()
        for text in ('Nova pergunta', 'Curso', 'Aula (opcional)', 'Título', 'Detalhes', 'Publicar pergunta', 'Cancelar',
                     'optgroup label="Suporte Básico de Vida"', 'Aula 1 · BLS aula 1', '<option value="general" selected>Discussão geral',
                     'Conte o contexto. Se for sobre um trecho do vídeo, diga o minuto.',
                     f'data-suggest-url="{reverse("community_suggest")}"', 'data-suggest-box="#suggest-box"', 'id="suggest-box"',
                     f'action="{reverse("community_create")}"', 'data-async'):
            self.assertIn(text, html, text)


class CreateTests(A7Base):
    def create(self, json_mode=True, **data):
        payload = {'course': str(self.bls.id), 'lesson': '', 'title': 'Profundidade', 'content': 'Qual a profundidade?', **data}
        extra = {'HTTP_X_REQUESTED_WITH': 'fetch'} if json_mode else {}
        return self.client.post(reverse('community_create'), payload, **extra)

    def test_success_with_lesson(self):
        lesson = self.lessons(self.bls)[1]
        response = self.create(lesson=str(lesson.id))
        post = CommunityPost.objects.get()
        self.assertEqual((post.author, post.course, post.lesson, post.title), (self.jane, self.bls, lesson, 'Profundidade'))
        data = response.json()
        self.assertEqual(data['toast'], PUBLISHED)
        self.assertEqual(data['undo_url'], reverse('community_delete_own', args=[post.id]))
        self.assertEqual(data['redirect'], reverse('community') + f'?nova_id={post.id}')

    def test_general_question(self):
        self.create(course='general')
        self.assertIsNone(CommunityPost.objects.get().course)
        self.create(course='')
        self.assertEqual(CommunityPost.objects.filter(course__isnull=True).count(), 2)

    def test_required_fields(self):
        data = self.create(title='  ', content='').json()
        self.assertEqual(set(data['errors']), {'title', 'content'})
        self.assertEqual(data['errors']['title'], ['Informe um título para a pergunta.'])
        self.assertEqual(self.create(title='  ', content='').status_code, 400)
        self.assertEqual(CommunityPost.objects.count(), 0)

    def test_course_must_be_one_the_student_has(self):
        data = self.create(course=str(self.pals.id)).json()
        self.assertEqual(data['errors']['course'], ['Escolha um curso em que você está matriculado.'])
        self.assertEqual(CommunityPost.objects.count(), 0)
        Enrollment.objects.filter(student=self.jane.student_profile, course=self.acls).update(is_active=False)
        self.assertEqual(self.create(course=str(self.acls.id)).status_code, 400)

    def test_lesson_must_belong_to_selected_course(self):
        wrong = self.lessons(self.acls)[0]
        data = self.create(lesson=str(wrong.id)).json()
        self.assertEqual(data['errors']['lesson'], ['Escolha uma aula do curso selecionado.'])
        self.assertEqual(self.create(course='general', lesson=str(self.lessons(self.bls)[0].id)).status_code, 400)
        self.assertEqual(self.create(lesson='abc').status_code, 400)
        Lesson.objects.filter(pk=self.lessons(self.bls)[0].pk).update(status='draft')
        self.assertEqual(self.create(lesson=str(self.lessons(self.bls)[0].id)).status_code, 400)
        self.assertEqual(CommunityPost.objects.count(), 0)

    def test_staff_can_post_in_any_course(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.create(course=str(self.pals.id)).status_code, 200)
        self.assertEqual(CommunityPost.objects.get().course, self.pals)

    def test_without_javascript(self):
        response = self.create(json_mode=False)
        post = CommunityPost.objects.get()
        self.assertRedirects(response, reverse('community') + f'?nova_id={post.id}', fetch_redirect_response=False)
        followed = self.client.get(reverse('community') + f'?nova_id={post.id}')
        self.assertContains(followed, PUBLISHED)
        self.assertContains(followed, f'data-undo-url="{reverse("community_delete_own", args=[post.id])}"')
        self.assertContains(followed, ' is-new')

    def test_without_javascript_error_reopens_the_form(self):
        response = self.create(json_mode=False, title='')
        self.assertRedirects(response, reverse('community') + '?nova=1', fetch_redirect_response=False)
        self.assertContains(self.client.get(reverse('community') + '?nova=1'), 'Informe um título para a pergunta.')

    def test_requires_login_and_post(self):
        self.assertEqual(self.client.get(reverse('community_create')).status_code, 405)
        self.client.logout()
        self.assertEqual(self.create().status_code, 302)


class ReplyTests(A7Base):
    def setUp(self):
        super().setUp()
        self.thread = self.post('Profundidade', lesson=self.lessons(self.bls)[1])

    def reply(self, post=None, json_mode=True, content='Obrigada pela ajuda.'):
        extra = {'HTTP_X_REQUESTED_WITH': 'fetch'} if json_mode else {}
        return self.client.post(reverse('community_reply', args=[(post or self.thread).id]), {'content': content}, **extra)

    def test_json_reply_replaces_the_thread(self):
        self.client.force_login(self.ana)
        data = self.reply().json()
        self.assertEqual(data['toast'], 'Resposta publicada')
        self.assertIn('Obrigada pela ajuda.', data['replace']['#thread-content'])
        self.assertIn('id="thread-content"', data['replace']['#thread-content'])
        self.assertEqual(Comment.objects.get().author, self.ana)

    def test_empty_reply_returns_field_error(self):
        response = self.reply(content='  ')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['errors'], {'content': ['Escreva uma resposta.']})
        self.assertEqual(Comment.objects.count(), 0)

    def test_without_javascript(self):
        response = self.reply(json_mode=False)
        self.assertRedirects(response, reverse('community') + f'?duvida={self.thread.id}', fetch_redirect_response=False)
        self.assertContains(self.client.get(reverse('community') + f'?duvida={self.thread.id}'), 'Resposta publicada')

    def test_unenrolled_student_cannot_reply_to_course_thread(self):
        outsider = User.objects.create_user(username='x', email='x@example.com', password=PASSWORD)
        self.client.force_login(outsider)
        self.assertEqual(self.reply().status_code, 403)
        self.assertEqual(Comment.objects.count(), 0)

    def test_general_thread_is_open_to_everyone(self):
        outsider = User.objects.create_user(username='x', email='x@example.com', password=PASSWORD)
        self.client.force_login(outsider)
        self.assertEqual(self.reply(self.post('Geral', course=None)).status_code, 200)

    def test_hidden_thread_is_404(self):
        self.assertEqual(self.reply(self.post('Oculta', is_hidden=True)).status_code, 404)

    def test_staff_reply_notifies_author_and_marks_answered(self):
        self.client.force_login(self.admin)
        self.reply(content='De 5 a 6 cm.')
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_answered_cache)
        self.assertTrue(self.thread.has_unread_answer)
        notification = Notification.objects.get(user=self.jane)
        self.assertEqual(notification.url, f'/community/?duvida={self.thread.id}')
        self.assertEqual(len(mail.outbox), 1)
        html = self.client.get(reverse('community') + f'?duvida={self.thread.id}&parcial=1').content.decode()
        self.assertIn('Instrutor CETREMER', html)

    def test_student_reply_does_not_notify_or_answer(self):
        self.client.force_login(self.ana)
        self.reply()
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_answered_cache)
        self.assertEqual(Notification.objects.count(), 0)


class ResolveAndDeleteTests(A7Base):
    def setUp(self):
        super().setUp()
        self.thread = self.post('Minha')
        self.answer(self.thread)

    def resolve(self, post=None, query='', json_mode=True):
        extra = {'HTTP_X_REQUESTED_WITH': 'fetch'} if json_mode else {}
        return self.client.post(reverse('community_resolve', args=[(post or self.thread).id]) + query, **extra)

    def test_resolve_toasts_with_undo_and_replaces_thread(self):
        data = self.resolve().json()
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_resolved)
        self.assertEqual(data['toast'], 'Obrigado! A dúvida foi marcada como resolvida')
        self.assertEqual(data['undo_url'], reverse('community_resolve', args=[self.thread.id]) + '?desfazer=1')
        self.assertIn('Marcada como resolvida', data['replace']['#thread-content'])

    def test_undo_reverts_and_reloads(self):
        self.resolve()
        data = self.resolve(query='?desfazer=1').json()
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_resolved)
        self.assertEqual(data, {'ok': True, 'reload': True})

    def test_clicking_the_resolved_button_unresolves_without_toast(self):
        self.resolve()
        data = self.resolve().json()
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_resolved)
        self.assertNotIn('toast', data)
        self.assertIn('Sim, resolveu', data['replace']['#thread-content'])

    def test_only_the_author_can_resolve(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.resolve().status_code, 404)
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_resolved)

    def test_without_javascript(self):
        response = self.resolve(json_mode=False)
        self.assertRedirects(response, reverse('community') + f'?duvida={self.thread.id}', fetch_redirect_response=False)
        self.assertContains(self.client.get(reverse('community') + f'?duvida={self.thread.id}'), 'Obrigado! A dúvida foi marcada como resolvida')

    def test_resolve_requires_post(self):
        self.assertEqual(self.client.get(reverse('community_resolve', args=[self.thread.id])).status_code, 405)

    def test_delete_own_without_replies(self):
        fresh = self.post('Recém publicada')
        data = self.client.post(reverse('community_delete_own', args=[fresh.id]), HTTP_X_REQUESTED_WITH='fetch').json()
        self.assertEqual(data, {'ok': True, 'toast': 'Pergunta apagada', 'reload': True})
        self.assertFalse(CommunityPost.objects.filter(pk=fresh.pk).exists())

    def test_cannot_delete_with_replies_or_someone_elses(self):
        self.assertEqual(self.client.post(reverse('community_delete_own', args=[self.thread.id])).status_code, 403)
        self.assertTrue(CommunityPost.objects.filter(pk=self.thread.pk).exists())
        theirs = self.post('Da Ana', author=self.ana)
        self.assertEqual(self.client.post(reverse('community_delete_own', args=[theirs.id])).status_code, 404)
        self.assertTrue(CommunityPost.objects.filter(pk=theirs.pk).exists())

    def test_delete_requires_post_and_login(self):
        fresh = self.post('Recém publicada')
        self.assertEqual(self.client.get(reverse('community_delete_own', args=[fresh.id])).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.post(reverse('community_delete_own', args=[fresh.id])).status_code, 302)


class SuggestTests(A7Base):
    def suggest(self, q):
        return self.client.get(reverse('community_suggest'), {'q': q})

    def test_suggests_up_to_three_similar_visible_questions(self):
        for number in range(4):
            self.post(f'Profundidade da compressão {number}')
        self.post('Compressão oculta', is_hidden=True)
        self.post('Compressão no PALS', course='pals', author=self.ana)
        html = self.suggest('profundidade compressão adulto').content.decode()
        self.assertIn('Talvez já tenha resposta:', html)
        self.assertEqual(html.count('<a '), 3)
        self.assertIn(reverse('community') + '?duvida=', html)
        self.assertNotIn('oculta', html)
        self.assertNotIn('PALS', html)

    def test_short_words_and_no_match_return_nothing(self):
        self.post('Profundidade da compressão')
        self.assertEqual(self.suggest('de do').content.decode().strip(), '')
        self.assertEqual(self.suggest('').content.decode().strip(), '')
        self.assertEqual(self.suggest('inexistente').content.decode().strip(), '')

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.suggest('profundidade').status_code, 302)
