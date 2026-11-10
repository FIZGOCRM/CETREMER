from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse

from community.models import CommunityPost
from core.toasts import toast
from courses.models import Course, Enrollment, Lesson, Module

User = get_user_model()
PASSWORD = 'StrongPassword123!'


def request_with_messages():
    request = RequestFactory().get('/')
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


class ToastTests(TestCase):
    def render(self, request):
        return render_to_string('partials/toasts.html', {'messages': get_messages(request)}, request)

    def test_toast_renders_template_with_undo_and_action(self):
        request = request_with_messages()
        toast(request, 'Aula excluída', undo_url='/painel/aulas/1/restaurar/', action=('Ver aluno', '/painel/alunos/3/'))
        html = self.render(request)
        self.assertIn('id="toast-stack"', html)
        self.assertIn('data-kind="ok"', html)
        self.assertIn('data-undo-url="/painel/aulas/1/restaurar/"', html)
        self.assertIn('data-action-label="Ver aluno"', html)
        self.assertIn('Aula excluída', html)

    def test_error_toast_uses_error_kind(self):
        request = request_with_messages()
        toast(request, 'Falhou', level='error')
        self.assertIn('data-kind="error"', self.render(request))


class FilterTests(TestCase):
    def test_plural_and_falta(self):
        from core.templatetags.ui import falta_pt, plural_pt
        self.assertEqual(plural_pt(1, 'aula,aulas'), '1 aula')
        self.assertEqual(plural_pt(3, 'aula,aulas'), '3 aulas')
        self.assertEqual(falta_pt(0), '')
        self.assertEqual(falta_pt(1), 'Falta 1 aula.')
        self.assertEqual(falta_pt(3), 'Faltam 3 aulas.')


class LayoutV2SmokeTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.student = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        self.course = Course.objects.create(title='BLS', slug='bls', creator=self.admin.creator_profile, is_published=True)
        self.module = Module.objects.create(course=self.course, title='Introdução', order=1)
        self.lesson = Lesson.objects.create(module=self.module, title='Aula 1', order=1)
        Enrollment.objects.create(student=self.student.student_profile, course=self.course)

    def test_student_pages_use_v2_shell(self):
        self.client.force_login(self.student)
        pages = [reverse('dashboard'), reverse('live_classes'), reverse('certificates'), reverse('community'),
                 reverse('settings'), reverse('course_preview', args=['bls']) + '?preview=1']
        for url in pages:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
        html = self.client.get(reverse('dashboard')).content.decode()
        for marker in ('id="toast-stack"', 'class="bottom-nav"', 'id="cmdk"', 'data-cmdk-open', 'user-btn'):
            self.assertIn(marker, html)
        self.assertNotIn('class="messages"', html)

    def test_lesson_page_still_opens(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('lesson_detail', args=['bls', self.lesson.id]))
        self.assertEqual(response.status_code, 200)

    def test_painel_pages_use_v2_shell_and_keep_titles(self):
        self.client.force_login(self.admin)
        pages = {
            reverse('painel:courses'): 'Cursos',
            reverse('painel:students'): 'Alunos', reverse('painel:students_import'): 'Importar alunos',
            reverse('painel:orders'): 'Pedidos', reverse('painel:community'): 'Comunidade',
            reverse('painel:settings'): 'Configurações',
        }
        for url, title in pages.items():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, '<h1 class="page-title">' + title + '</h1>', msg_prefix=url)
            self.assertContains(response, 'id="dlg-new-course"', msg_prefix=url)
            self.assertContains(response, 'id="dlg-enroll"', msg_prefix=url)
            self.assertContains(response, 'id="toast-stack"', msg_prefix=url)

    def test_dashboard_has_greeting_title_and_new_course_url_redirects(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('painel:dashboard'))
        self.assertContains(response, '<h1 class="page-title">')
        self.assertRegex(response.content.decode(), r'page-title">(Bom dia|Boa tarde|Boa noite), ')
        self.assertEqual(self.client.get(reverse('painel:course_new')).status_code, 302)

    def test_course_content_page_and_old_lessons_route(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('painel:course_content', args=[self.course.id]))
        self.assertContains(response, 'class="course-head__title"')
        old = self.client.get(reverse('painel:course_lessons', args=[self.course.id]))
        self.assertRedirects(old, reverse('painel:course_content', args=[self.course.id]), status_code=301)

    def test_provisional_routes_exist_and_do_not_break(self):
        self.client.force_login(self.admin)
        for name, args in (('painel:student_detail', [self.student.id]),):
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)
        for name in ('painel:course_sales', 'painel:course_settings'):
            self.assertEqual(self.client.get(reverse(name, args=[self.course.id])).status_code, 200, name)
        self.assertEqual(self.client.post(reverse('painel:student_enroll')).status_code, 302)  # sem e-mail: volta com aviso
        self.assertEqual(self.client.get(reverse('painel:search') + '?q=bls').status_code, 200)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('search') + '?q=bls').status_code, 200)
        self.assertEqual(self.client.post(reverse('notifications_read_all'), HTTP_X_REQUESTED_WITH='fetch').status_code, 200)

    def test_instructor_cannot_open_painel_without_login(self):
        self.assertEqual(self.client.get(reverse('painel:search')).status_code, 302)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('painel:search')).status_code, 403)

    def test_django_messages_become_toasts_in_logged_layout(self):
        post = CommunityPost.objects.create(author=self.student, title='Dúvida', content='Como faço?')
        self.client.force_login(self.admin)
        response = self.client.post(reverse('painel:community_action', args=[post.id]), {'action': 'reply', 'content': 'Assim.'}, follow=True)
        self.assertContains(response, '<template data-toast data-kind="ok">Resposta publicada</template>')
        self.assertNotContains(response, 'class="messages"')

    def test_settings_success_is_a_toast(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('settings'), {'section': 'avisos', 'notify_answers': '1'}, follow=True)
        self.assertContains(response, 'data-toast data-kind="ok"')
        self.assertNotContains(response, 'class="messages"')

    def test_public_auth_page_shows_message_once(self):
        request = request_with_messages()
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()
        toast(request, 'Senha criada. Entre com seu e-mail e a nova senha.')
        html = render_to_string('login.html', {'next': '/'}, request)
        self.assertEqual(html.count('data-toast'), 1)
        self.assertNotIn('alert--success', html)

    def test_login_error_still_inline(self):
        response = self.client.post(reverse('login'), {'username': 'x@example.com', 'password': 'errada'})
        self.assertContains(response, 'alert--error')
