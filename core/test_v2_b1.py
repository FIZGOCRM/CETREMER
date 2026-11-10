from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from courses.models import Course, Enrollment, Lesson, Module
from sales.models import Order

User = get_user_model()
PASSWORD = 'StrongPassword123!'


class B1Base(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='dono', email='dono@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.adm = User.objects.create_user(username='adm', email='adm@example.com', password=PASSWORD, role=User.Role.ADMIN)
        self.inst = User.objects.create_user(username='inst', email='inst@example.com', password=PASSWORD, role=User.Role.CREATOR)
        self.jane = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        profile = self.jane.student_profile
        profile.full_name = 'Jane Souza'
        profile.cpf = '52998224725'
        profile.save()
        self.bls = Course.objects.create(title='Suporte Básico de Vida', short_name='BLS', slug='bls',
                                         creator=self.owner.creator_profile, status='published')
        self.old = Course.objects.create(title='Curso Antigo', short_name='OLD', slug='old',
                                         creator=self.owner.creator_profile, status='archived')
        module = Module.objects.create(course=self.bls, title='Módulo 1', order=1)
        self.lesson = Lesson.objects.create(module=module, title='Ritmos chocáveis', order=1)
        Enrollment.objects.create(student=profile, course=self.bls)
        self.order = Order.objects.create(student=profile, course=self.bls, amount=150)

    def as_user(self, user):
        self.client.force_login(user)
        return self.client


class PermissionTests(B1Base):
    ADMIN_ONLY = ('painel:orders', 'painel:orders_export', 'painel:settings')
    OPEN = ('painel:dashboard', 'painel:courses', 'painel:students', 'painel:community', 'painel:students_import')

    def test_instructor_gets_403_on_admin_only_pages(self):
        self.as_user(self.inst)
        for name in self.ADMIN_ONLY:
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    def test_instructor_post_to_settings_is_403_and_changes_nothing(self):
        from users.models import SiteSettings
        self.as_user(self.inst)
        self.assertEqual(self.client.post(reverse('painel:settings'), {'school_name': 'Hack'}).status_code, 403)
        self.assertNotEqual(SiteSettings.load().school_name, 'Hack')

    def test_admin_owner_and_staff_reach_admin_only_pages(self):
        for user in (self.adm, self.owner):
            self.as_user(user)
            for name in self.ADMIN_ONLY:
                self.assertEqual(self.client.get(reverse(name)).status_code, 200, (user.username, name))

    def test_instructor_reaches_content_pages(self):
        self.as_user(self.inst)
        for name in self.OPEN:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_student_gets_403_and_anonymous_redirects(self):
        self.as_user(self.jane)
        self.assertEqual(self.client.get(reverse('painel:dashboard')).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('painel:orders')).status_code, 302)

    def test_403_uses_the_layout_of_who_asked(self):
        self.as_user(self.inst)
        page = self.client.get(reverse('painel:orders'))
        self.assertContains(page, 'Você não tem acesso a esta página', status_code=403)
        self.assertContains(page, 'app--admin', status_code=403)
        self.assertContains(page, 'Voltar ao início do painel', status_code=403)
        self.as_user(self.jane)
        page = self.client.get(reverse('painel:dashboard'))
        self.assertContains(page, 'Você não tem acesso a esta página', status_code=403)
        self.assertNotContains(page, 'app--admin', status_code=403)

    def test_menu_hides_orders_and_settings_for_instructor(self):
        self.as_user(self.inst)
        page = self.client.get(reverse('painel:dashboard'))
        self.assertNotContains(page, reverse('painel:orders'))
        self.assertNotContains(page, reverse('painel:settings'))
        self.assertNotContains(page, 'sidenav__group">Vendas')
        self.as_user(self.adm)
        page = self.client.get(reverse('painel:dashboard'))
        self.assertContains(page, reverse('painel:orders'))
        self.assertContains(page, reverse('painel:settings'))
        self.assertContains(page, 'sidenav__group">Vendas')


class LayoutTests(B1Base):
    def test_menu_groups_and_top_bar(self):
        page = self.as_user(self.adm).get(reverse('painel:dashboard'))
        for text in ('Visão geral', 'Conteúdo', 'Pessoas', 'Vendas', 'Buscar aluno, curso ou pedido', 'Ctrl K',
                     'Novo curso', 'Matricular aluno', 'Importar alunos', 'Ver como aluno', 'Sair'):
            self.assertContains(page, text)
        self.assertContains(page, 'id="dlg-new-course"')
        self.assertContains(page, 'id="dlg-enroll"')
        self.assertContains(page, 'id="cmdk"')
        self.assertContains(page, 'data-search-url="/painel/busca/"')

    def test_enroll_dialog_lists_no_archived_course(self):
        page = self.as_user(self.adm).get(reverse('painel:dashboard'))
        self.assertContains(page, 'Suporte Básico de Vida')
        self.assertNotContains(page, '>Curso Antigo<')

    def test_pending_questions_badge(self):
        from community.models import CommunityPost
        CommunityPost.objects.create(author=self.jane, title='Dúvida', content='x', course=self.bls)
        page = self.as_user(self.inst).get(reverse('painel:dashboard'))
        self.assertContains(page, 'data-pending-count')
        self.assertContains(page, '1 dúvida sem resposta')

    def test_user_card_shows_email(self):
        page = self.as_user(self.adm).get(reverse('painel:dashboard'))
        self.assertContains(page, 'adm@example.com')


class SearchTests(B1Base):
    def search(self, user, q=''):
        return self.as_user(user).get(reverse('painel:search'), {'q': q})

    def test_requires_painel_access(self):
        self.assertEqual(self.search(self.jane, 'jane').status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('painel:search')).status_code, 302)

    def test_empty_query_lists_actions(self):
        page = self.search(self.adm)
        for text in ('Ações', 'Novo curso', 'Matricular aluno', 'Importar alunos', 'Exportar alunos'):
            self.assertContains(page, text)

    def test_students_by_name_email_and_cpf(self):
        detail = reverse('painel:student_detail', args=[self.jane.id])
        for q in ('Jane', 'jane@example', '529.982', '52998224725'):
            self.assertContains(self.search(self.adm, q), detail, msg_prefix=q)
        self.assertNotContains(self.search(self.adm, 'zzzz'), detail)

    def test_courses_include_archived_and_lessons(self):
        page = self.search(self.adm, 'BLS')
        self.assertContains(page, 'Cursos')
        self.assertContains(page, reverse('painel:course_content', args=[self.bls.id]))
        self.assertContains(self.search(self.adm, 'Antigo'), 'Arquivado')
        page = self.search(self.adm, 'chocáveis')
        self.assertContains(page, 'Aulas')
        self.assertContains(page, f'?aula={self.lesson.id}')
        self.assertContains(page, 'Suporte Básico de Vida · Módulo 1')

    def test_order_by_number_for_admin_only(self):
        for q in (f'#{self.order.id}', str(self.order.id)):
            self.assertContains(self.search(self.adm, q), f'Pedido #{self.order.id}')
        self.assertNotContains(self.search(self.inst, f'#{self.order.id}'), 'Pedido #')

    def test_actions_filtered_by_word(self):
        page = self.search(self.adm, 'importar')
        self.assertContains(page, 'Importar alunos')
        self.assertNotContains(page, 'Exportar alunos')
        self.assertContains(page, reverse('painel:students_import'))

    def test_action_links_open_dialogs(self):
        page = self.search(self.adm, 'matricular')
        self.assertContains(page, reverse('painel:students') + '?abrir=dlg-enroll')
        page = self.search(self.adm, 'novo curso')
        self.assertContains(page, reverse('painel:courses') + '?abrir=dlg-new-course')

    def test_limit_per_group(self):
        module = Module.objects.get(course=self.bls)
        for n in range(8):
            Lesson.objects.create(module=module, title=f'Parada {n}', order=10 + n)
        self.assertEqual(self.search(self.adm, 'Parada').content.decode().count('class="cmdk__item"'), 5)

    def test_deleted_lessons_hidden(self):
        from django.utils import timezone
        Lesson.all_objects.filter(pk=self.lesson.pk).update(deleted_at=timezone.now())
        self.assertNotContains(self.search(self.adm, 'chocáveis'), 'chocáveis')


class JsContractTests(TestCase):
    def test_abrir_param_handled_in_ui_js(self):
        from pathlib import Path
        from django.conf import settings
        source = (Path(settings.BASE_DIR) / 'static' / 'js' / 'ui.js').read_text(encoding='utf-8')
        self.assertIn('abrir=(dlg-', source)
