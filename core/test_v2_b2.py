from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from community.models import CommunityPost
from core.models import ActivityLog
from courses.models import Category, Certificate, Course, Enrollment, Lesson, Module, Progress
from painel import stats
from sales.models import Order
from users.models import SiteSettings

User = get_user_model()
PASSWORD = 'StrongPassword123!'
AJAX = {'HTTP_X_REQUESTED_WITH': 'fetch'}


class B2Base(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='dono', email='dono@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.inst = User.objects.create_user(username='inst', email='inst@example.com', password=PASSWORD, role=User.Role.CREATOR)
        self.jane = self.student('jane', 'Jane Souza')
        self.ana = self.student('ana', 'Ana Lima')
        self.cat = Category.objects.create(name='Essenciais AHA', slug='essenciais')
        self.bls = self.course('BLS', 'Suporte Básico de Vida', 'bls', 'published', self.cat)
        self.draft = self.course('DEA', 'DEA para leigos', 'dea', 'draft')
        self.arch = self.course('OLD', 'Curso Antigo', 'old', 'archived')
        self.module = Module.objects.get(course=self.bls)
        self.l1 = Lesson.objects.create(module=self.module, title='Aula 1', order=1, video_url='https://vimeo.com/76979871', duration_seconds=600)
        self.l2 = Lesson.objects.create(module=self.module, title='Aula 2', order=2, video_url='https://www.youtube.com/watch?v=abcdefghijk', duration_seconds=1200)
        SiteSettings.load()

    def student(self, username, name):
        user = User.objects.create_user(username=username, email=f'{username}@example.com', password=PASSWORD)
        user.student_profile.full_name = name
        user.student_profile.save()
        return user

    def course(self, short, title, slug, status, category=None):
        course = Course.objects.create(title=title, short_name=short, slug=slug, creator=self.owner.creator_profile,
                                       status=status, category=category, workload_hours=4, price=150)
        Module.objects.create(course=course, title='Módulo 1', order=1)
        return course

    def login(self, user):
        self.client.force_login(user)
        return self.client


class AgoTests(TestCase):
    def test_ago_pt(self):
        from core.templatetags.ui import ago_pt
        now = timezone.now()
        cases = ((5, 'agora mesmo'), (25 * 60, 'há 25 min'), (3600, 'há 1 h'), (3 * 3600 + 10, 'há 3 h'),
                 (86400, 'há 1 dia'), (2 * 86400 + 3600, 'há 2 dias'))
        for seconds, text in cases:
            self.assertEqual(ago_pt(now - timedelta(seconds=seconds)), text)
        self.assertEqual(ago_pt(None), '')


class GreetingTests(TestCase):
    def test_greeting_by_hour(self):
        for hour, text in ((5, 'Bom dia'), (11, 'Bom dia'), (12, 'Boa tarde'), (17, 'Boa tarde'), (18, 'Boa noite'), (23, 'Boa noite')):
            moment = timezone.make_aware(timezone.datetime(2026, 5, 4, hour, 30))
            self.assertEqual(stats.greeting(moment), text, hour)

    def test_period_parsing(self):
        self.assertEqual([stats.parse_period(v) for v in ('7', '30', '90', '15', 'x', None)], [7, 30, 90, 30, 30, 30])


class DashboardTests(B2Base):
    def get(self, user=None, **params):
        return (self.login(user or self.owner)).get(reverse('painel:dashboard'), params)

    def test_greeting_uses_first_name_never_username(self):
        self.owner.first_name = 'Marina'
        self.owner.save()
        page = self.get()
        self.assertRegex(page.content.decode(), r'page-title">(Bom dia|Boa tarde|Boa noite), ')
        self.assertNotContains(page, ', dono<')
        self.assertContains(page, 'Resumo da escola e o que precisa da sua atenção hoje.')

    def test_period_switch(self):
        for days in (7, 30, 90):
            self.assertContains(self.get(periodo=days), f'últimos {days} dias')
        page = self.get(periodo=7)
        self.assertContains(page, 'aria-current="page" href="?periodo=7"')
        self.assertContains(self.get(periodo='abc'), 'últimos 30 dias')

    def test_revenue_counts_only_paid_orders_in_period(self):
        profile = self.jane.student_profile
        Order.objects.create(student=profile, course=self.bls, amount=150, status=Order.Status.COMPLETED)
        Order.objects.create(student=profile, course=self.bls, amount=100, status=Order.Status.PENDING)
        Order.objects.create(student=profile, course=self.bls, amount=70, status=Order.Status.REFUNDED)
        old = Order.objects.create(student=profile, course=self.bls, amount=900, status=Order.Status.COMPLETED)
        Order.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=45))
        page = self.get(periodo=30)
        self.assertContains(page, 'R$ 150,00')
        self.assertContains(page, '1 pedido pago · últimos 30 dias')
        self.assertContains(self.get(periodo=90), '2 pedidos pagos · últimos 90 dias')

    def test_instructor_does_not_see_revenue(self):
        Order.objects.create(student=self.jane.student_profile, course=self.bls, amount=150, status=Order.Status.COMPLETED)
        page = self.get(self.inst)
        self.assertNotContains(page, 'Receita')
        self.assertNotContains(page, 'pedido pago')
        self.assertContains(page, 'Novos alunos')

    def test_new_students_active_students_and_certificates(self):
        old = self.student('velha', 'Velha')
        User.objects.filter(pk=old.pk).update(date_joined=timezone.now() - timedelta(days=200))
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l1)
        stale = Progress.objects.create(student=self.ana.student_profile, lesson=self.l1)
        Progress.objects.filter(pk=stale.pk).update(updated_at=timezone.now() - timedelta(days=60))
        numbers = stats.dashboard_numbers(30)
        self.assertEqual(numbers['new_students'], 2)
        self.assertEqual(numbers['students_total'], 3)
        self.assertEqual(numbers['active_students'], 1)
        page = self.get()
        self.assertContains(page, '+2 no período')
        self.assertContains(page, '1 de 3')
        self.assertContains(page, 'nenhuma conclusão ainda')
        enrollment = Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        Certificate.objects.create(enrollment=enrollment, code='ABC123', student_name='Jane', student_cpf='52998224725',
                                   course_title='BLS', completed_at=timezone.now())
        self.assertNotContains(self.get(), 'nenhuma conclusão ainda')
        self.assertEqual(stats.dashboard_numbers(30)['certificates'], 1)

    def test_attention_empty_state(self):
        Lesson.objects.filter(pk=self.l2.pk).update(video_url='https://vimeo.com/76979872', vimeo_id='76979872')
        Lesson.objects.filter(pk=self.l1.pk).update(vimeo_id='76979871')
        site = SiteSettings.load()
        site.signer_name = 'Dra. Ana'
        site.save()
        User.objects.filter(role=User.Role.STUDENT).update(last_login=timezone.now())
        page = self.get()
        self.assertContains(page, 'Nada pendente. Tudo em dia.')
        self.assertContains(page, '0 pendências')

    def test_attention_items_each_appear_only_when_positive(self):
        old = CommunityPost.objects.create(author=self.jane, title='Dúvida antiga', content='x', course=self.bls)
        CommunityPost.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=2, hours=1))
        CommunityPost.objects.create(author=self.ana, title='Outra', content='y', course=self.bls)
        hidden = CommunityPost.objects.create(author=self.ana, title='Oculta', content='y', course=self.bls)
        CommunityPost.objects.filter(pk=hidden.pk).update(is_hidden=True)
        page = self.get()
        self.assertContains(page, '2 dúvidas sem resposta')
        self.assertContains(page, 'A mais antiga está esperando há 2 dias')
        self.assertContains(page, reverse('painel:community'))
        self.assertContains(page, '1 aula publicada ainda usa vídeo do YouTube')
        self.assertContains(page, reverse('painel:course_content', args=[self.bls.id]))
        self.assertContains(page, 'Certificado sem responsável técnico')
        self.assertContains(page, reverse('painel:settings') + '?secao=certificado')
        self.assertContains(page, '4 pendências')

    def test_never_accessed_students_item(self):
        page = self.get()
        self.assertContains(page, '2 alunos nunca acessaram')
        self.assertContains(page, reverse('painel:students') + '?filtro=nunca')
        User.objects.filter(pk=self.jane.pk).update(last_login=timezone.now())
        Progress.objects.create(student=self.ana.student_profile, lesson=self.l1)
        self.assertNotContains(self.get(), 'nunca acessaram')

    def test_signer_item_hidden_for_instructor(self):
        self.assertContains(self.get(), 'Certificado sem responsável técnico')
        self.assertNotContains(self.get(self.inst), 'Certificado sem responsável técnico')

    def test_youtube_item_points_to_course_with_most_cases(self):
        other = self.course('ACL', 'ACLS', 'acls', 'published')
        module = Module.objects.get(course=other)
        for n in range(3):
            Lesson.objects.create(module=module, title=f'Y{n}', order=n + 1, video_url=f'https://www.youtube.com/watch?v=abcdefghij{n}')
        page = self.get()
        self.assertContains(page, '4 aulas publicadas ainda usam vídeo do YouTube')
        self.assertContains(page, reverse('painel:course_content', args=[other.id]))

    def test_youtube_ignores_drafts_and_deleted_lessons(self):
        Lesson.objects.filter(pk=self.l2.pk).update(status='draft')
        self.assertEqual(stats.non_vimeo_by_course(), {})
        Lesson.objects.filter(pk=self.l2.pk).update(status='published', deleted_at=timezone.now())
        self.assertEqual(stats.non_vimeo_by_course(), {})

    def test_activity_lists_eight_latest_with_links_and_actor(self):
        for n in range(10):
            ActivityLog.objects.create(verb='enrolled', text=f'Jane Souza foi matriculado {n}', student=self.jane, actor=self.owner)
        page = self.get()
        text = page.content.decode()
        self.assertEqual(text.count('class="timeline__item"'), 8)
        self.assertIn(f'<a class="fw-600" href="{reverse("painel:student_detail", args=[self.jane.id])}">Jane Souza</a>', text)
        self.assertIn('foi matriculado 9', text)
        self.assertNotIn('foi matriculado 0<', text)
        self.assertContains(page, 'por ')

    def test_activity_course_link_and_empty_state(self):
        self.assertContains(self.get(), 'Matrículas, aulas concluídas e certificados aparecem neste lugar.')
        ActivityLog.objects.create(verb='course_updated', text='Curso BLS foi atualizado', course=self.bls)
        page = self.get()
        self.assertContains(page, f'Curso <a class="fw-600" href="{reverse("painel:course_content", args=[self.bls.id])}">BLS</a> foi atualizado')

    def test_courses_table_published_only_with_stats(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        Enrollment.objects.create(student=self.ana.student_profile, course=self.bls)
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l1, is_completed=True)
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l2, is_completed=True)
        Progress.objects.create(student=self.ana.student_profile, lesson=self.l1, is_completed=True)
        Order.objects.create(student=self.jane.student_profile, course=self.bls, amount=150, status=Order.Status.COMPLETED)
        row = stats.course_stats([self.bls.id])[self.bls.id]
        self.assertEqual(row['students'], 2)
        self.assertEqual(row['avg_pct'], 75)
        self.assertEqual(row['completed'], 1)
        self.assertEqual(row['revenue'], 150)
        page = self.get()
        self.assertContains(page, 'BLS · Suporte Básico de Vida')
        self.assertEqual([row['course'].title for row in page.context['courses_table']], ['Suporte Básico de Vida'])
        self.assertContains(page, 'aria-valuenow="75"')
        self.assertContains(page, 'Gerenciar cursos')

    def test_average_is_dash_without_students_and_ignores_drafts(self):
        self.assertIsNone(stats.course_stats([self.bls.id])[self.bls.id]['avg_pct'])
        Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        Lesson.objects.create(module=self.module, title='Rascunho', order=3, status='draft')
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l1, is_completed=True)
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l2, is_completed=True)
        self.assertEqual(stats.course_stats([self.bls.id])[self.bls.id]['avg_pct'], 100)

    def test_inactive_enrollment_does_not_count(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.bls, is_active=False)
        self.assertEqual(stats.course_stats([self.bls.id])[self.bls.id]['students'], 0)

    def test_topbar_has_view_as_student(self):
        self.assertContains(self.get(), 'target="_blank"')


class ActivityHookTests(B2Base):
    def test_complete_lesson_logs_once_with_position(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        self.login(self.jane)
        url = reverse('complete_lesson', args=[self.l2.id])
        self.client.post(url)
        self.client.post(url)
        entries = ActivityLog.objects.filter(verb='completed_lesson')
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].text, 'Jane Souza concluiu a aula 2 de BLS')
        self.assertEqual(entries[0].student, self.jane)

    def test_toggle_logs_only_when_completing(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        self.login(self.jane)
        url = reverse('toggle_progress', args=[self.l1.id])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(ActivityLog.objects.filter(verb='completed_lesson').count(), 1)

    def test_manual_enrollment_logs_with_actor(self):
        self.login(self.owner)
        post = {'email': 'jane@example.com', 'course': self.bls.id}
        self.client.post(reverse('painel:student_enroll'), post)
        self.client.post(reverse('painel:student_enroll'), post)
        entries = ActivityLog.objects.filter(verb='enrolled')
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].text, 'Jane Souza foi matriculado em BLS')
        self.assertEqual(entries[0].actor, self.owner)
        self.assertEqual(entries[0].student, self.jane)

    def test_log_helpers_text(self):
        from core import activity
        self.assertEqual(activity.log_enrolled(self.ana, self.bls).text, 'Ana Lima foi matriculado em BLS')
        self.assertEqual(activity.log_certificate(self.ana, self.bls).text, 'Ana Lima recebeu o certificado de BLS')

    def test_course_edit_logs_update(self):
        self.login(self.owner)
        self.client.post(reverse('painel:course_settings', args=[self.bls.id]), {'title': 'Suporte Básico de Vida', 'short_name': 'BLS', 'slug': 'bls', 'price': '150,00'})
        self.assertTrue(ActivityLog.objects.filter(verb='course_updated', course=self.bls, text='Curso BLS foi atualizado').exists())


class CoursesListTests(B2Base):
    def get(self, user=None, **params):
        return self.login(user or self.owner).get(reverse('painel:courses'), params)

    def titles(self, page):
        return [card['course'].title for card in page.context['cards']]

    def test_counts_and_default_hides_archived(self):
        page = self.get()
        self.assertEqual(page.context['counts'], {'all': 2, 'published': 1, 'draft': 1, 'archived': 1})
        self.assertEqual(self.titles(page), ['DEA para leigos', 'Suporte Básico de Vida'])

    def test_status_filters(self):
        self.assertEqual(self.titles(self.get(status='publicados')), ['Suporte Básico de Vida'])
        self.assertEqual(self.titles(self.get(status='rascunhos')), ['DEA para leigos'])
        page = self.get(status='arquivados')
        self.assertEqual(self.titles(page), ['Curso Antigo'])
        self.assertContains(page, 'Arquivado')

    def test_search_and_category_filters(self):
        self.assertEqual(self.titles(self.get(q='bls')), ['Suporte Básico de Vida'])
        self.assertEqual(self.titles(self.get(categoria='essenciais')), ['Suporte Básico de Vida'])
        self.assertEqual(self.titles(self.get(q='dea', categoria='essenciais')), [])

    def test_card_meta_numbers_and_alerts(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l1, is_completed=True)
        page = self.get()
        self.assertContains(page, 'Essenciais AHA · 1 módulo · 2 aulas · 30 min')
        self.assertContains(page, '1 aula ainda usa YouTube')
        self.assertContains(page, '50%')
        self.assertContains(page, 'R$ 150,00')
        self.assertNotContains(page, 'Carga horária não informada')
        Course.objects.filter(pk=self.bls.pk).update(workload_hours=None)
        self.assertContains(self.get(), 'Carga horária não informada')

    def test_progress_dash_without_students(self):
        page = self.get(status='rascunhos')
        self.assertContains(page, '<dd class="fw-600">–</dd>')

    def test_card_menu_items_and_sales_link(self):
        page = self.get()
        for text in ('Abrir curso', 'Ver como aluno', 'Abrir página de venda', 'Copiar link de venda', 'Duplicar curso',
                     'Mover para rascunho', 'Arquivar curso'):
            self.assertContains(page, text)
        self.assertContains(page, 'data-copy="http://testserver/courses/bls/"')
        self.assertContains(page, 'data-copy-toast="Link de venda copiado"')
        self.assertContains(page, 'Começa como rascunho, só você vê')

    def test_archive_dialog_per_course_asks_for_acronym(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        page = self.get()
        self.assertContains(page, 'id="dlg-archive-%d"' % self.bls.id)
        self.assertContains(page, 'data-confirm-text="BLS"')
        self.assertContains(page, 'Digite BLS para confirmar')
        self.assertContains(page, 'Arquivar BLS · Suporte Básico de Vida?')
        self.assertContains(page, 'do aluno matriculado')
        self.assertNotContains(page, 'id="dlg-archive-%d"' % self.arch.id)

    def test_archived_card_offers_restore(self):
        page = self.get(status='arquivados')
        self.assertContains(page, 'Restaurar como rascunho')
        self.assertNotContains(page, 'Arquivar curso')

    def test_empty_states(self):
        Course.objects.filter(status='archived').delete()
        self.assertContains(self.get(status='arquivados'), 'Nenhum curso arquivado')
        self.assertContains(self.get(status='arquivados'), 'Limpar filtros')
        self.assertContains(self.get(q='zzz'), 'Nenhum curso encontrado')
        Course.objects.all().delete()
        page = self.get()
        self.assertContains(page, 'Crie seu primeiro curso')
        self.assertNotContains(page, 'Limpar filtros')
        Course.objects.create(title='X', slug='x', creator=self.owner.creator_profile, status='archived')
        self.assertContains(self.get(status='rascunhos'), 'Nenhum curso em rascunho')

    def test_instructor_can_use_list(self):
        self.assertEqual(self.get(self.inst).status_code, 200)

    def test_list_query_count_does_not_grow_with_courses(self):
        self.get()
        with self.assertNumQueries(self._count()):
            self.get()
        for n in range(6):
            self.course('C%d' % n, 'Curso %d' % n, 'c%d' % n, 'published')
        with self.assertNumQueries(self._count()):
            self.get()

    def _count(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as ctx:
            self.get()
        return len(ctx)


class CourseCreateTests(B2Base):
    url = property(lambda self: reverse('painel:course_create'))

    def test_creates_draft_with_first_module_and_opens_content(self):
        self.login(self.owner)
        response = self.client.post(self.url, {'title': 'Novo Curso', 'category': self.cat.id})
        course = Course.objects.get(title='Novo Curso')
        self.assertRedirects(response, reverse('painel:course_content', args=[course.id]), fetch_redirect_response=False)
        self.assertEqual(course.status, 'draft')
        self.assertEqual(course.category, self.cat)
        self.assertEqual(list(course.modules.values_list('title', 'order')), [('Módulo 1', 1)])
        self.assertEqual(course.slug, 'novo-curso')
        self.assertTrue(ActivityLog.objects.filter(course=course, verb='course_updated').exists())

    def test_toast_after_create(self):
        self.login(self.owner)
        response = self.client.post(self.url, {'title': 'Outro'}, follow=True)
        self.assertContains(response, 'Curso criado como rascunho')

    def test_json_response_redirects(self):
        self.login(self.owner)
        data = self.client.post(self.url, {'title': 'Via JS'}, **AJAX).json()
        course = Course.objects.get(title='Via JS')
        self.assertTrue(data['ok'])
        self.assertEqual(data['redirect'], reverse('painel:course_content', args=[course.id]))

    def test_blank_title_error_keeps_dialog_open(self):
        self.login(self.owner)
        response = self.client.post(self.url, {'title': '   '}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.json()['errors'])
        self.assertEqual(Course.objects.count(), 3)

    def test_blank_title_without_js_goes_back_with_error_toast(self):
        self.login(self.owner)
        response = self.client.post(self.url, {'title': ''}, follow=True)
        self.assertContains(response, 'Informe o título do curso.')
        self.assertEqual(Course.objects.count(), 3)

    def test_slug_is_unique(self):
        self.login(self.owner)
        self.client.post(self.url, {'title': 'Repetido'})
        self.client.post(self.url, {'title': 'Repetido'})
        self.assertEqual(sorted(Course.objects.filter(title='Repetido').values_list('slug', flat=True)), ['repetido', 'repetido-2'])

    def test_get_opens_the_dialog_on_the_list(self):
        self.login(self.owner)
        self.assertRedirects(self.client.get(self.url), reverse('painel:courses') + '?abrir=dlg-new-course', fetch_redirect_response=False)

    def test_student_cannot_create(self):
        self.login(self.jane)
        self.assertEqual(self.client.post(self.url, {'title': 'Hack'}).status_code, 403)
        self.assertFalse(Course.objects.filter(title='Hack').exists())

    def test_instructor_can_create(self):
        self.login(self.inst)
        self.client.post(self.url, {'title': 'Do instrutor'})
        self.assertTrue(Course.objects.filter(title='Do instrutor').exists())


class CourseDuplicateTests(B2Base):
    def test_copy_has_modules_lessons_materials_and_is_draft(self):
        from courses.models import CourseFAQ, LessonMaterial
        CourseFAQ.objects.create(course=self.bls, question='Q?', answer='A.')
        LessonMaterial.objects.create(lesson=self.l1, title='Apostila', url='https://example.com/a.pdf')
        Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l1, is_completed=True)
        self.login(self.owner)
        response = self.client.post(reverse('painel:course_duplicate', args=[self.bls.id]))
        copy = Course.objects.get(title='Suporte Básico de Vida (cópia)')
        self.assertRedirects(response, reverse('painel:course_content', args=[copy.id]), fetch_redirect_response=False)
        self.assertEqual(copy.status, 'draft')
        self.assertNotEqual(copy.slug, self.bls.slug)
        self.assertEqual(list(Lesson.objects.filter(module__course=copy).order_by('order').values_list('title', flat=True)), ['Aula 1', 'Aula 2'])
        self.assertEqual(LessonMaterial.objects.filter(lesson__module__course=copy).count(), 1)
        self.assertEqual(copy.faqs.count(), 1)
        self.assertEqual(copy.enrollments.count(), 0)
        self.assertEqual(Progress.objects.filter(lesson__module__course=copy).count(), 0)
        self.assertEqual(Lesson.objects.filter(module__course=self.bls).count(), 2)
        self.assertEqual(self.bls.modules.count(), 1)

    def test_toast_and_json(self):
        self.login(self.owner)
        data = self.client.post(reverse('painel:course_duplicate', args=[self.bls.id]), **AJAX).json()
        self.assertTrue(data['ok'])
        self.assertContains(self.client.get(data['redirect'], follow=True), 'Cópia criada como rascunho')

    def test_get_not_allowed(self):
        self.login(self.owner)
        self.assertEqual(self.client.get(reverse('painel:course_duplicate', args=[self.bls.id])).status_code, 405)

    def test_copying_twice_gets_distinct_slugs(self):
        self.login(self.owner)
        for _ in range(2):
            self.client.post(reverse('painel:course_duplicate', args=[self.bls.id]))
        self.assertEqual(Course.objects.filter(title__startswith='Suporte Básico de Vida (cópia)').count(), 2)
        self.assertEqual(Course.objects.values('slug').distinct().count(), Course.objects.count())


class CourseStatusTests(B2Base):
    def url(self, course=None):
        return reverse('painel:course_status', args=[(course or self.bls).id])

    def test_move_to_draft_with_undo(self):
        self.login(self.owner)
        response = self.client.post(self.url(), {'para': 'draft'}, follow=True)
        self.bls.refresh_from_db()
        self.assertEqual(self.bls.status, 'draft')
        self.assertContains(response, 'Curso movido para rascunho')
        self.assertContains(response, 'data-undo-url="%s?para=published&amp;desfazer=1"' % self.url())
        self.client.post(self.url() + '?para=published&desfazer=1')
        self.bls.refresh_from_db()
        self.assertEqual(self.bls.status, 'published')

    def test_archive_requires_acronym(self):
        self.login(self.owner)
        response = self.client.post(self.url(), {'para': 'archived', 'confirmar': 'errado'}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertIn('confirmar', response.json()['errors'])
        self.bls.refresh_from_db()
        self.assertEqual(self.bls.status, 'published')
        self.assertIsNone(self.bls.archived_at)

    def test_archive_sends_to_archived_tab_with_undo(self):
        self.login(self.owner)
        response = self.client.post(self.url(), {'para': 'archived', 'confirmar': 'bls'}, follow=True)
        self.bls.refresh_from_db()
        self.assertEqual(self.bls.status, 'archived')
        self.assertIsNotNone(self.bls.archived_at)
        self.assertEqual(response.request['QUERY_STRING'], 'status=arquivados')
        self.assertContains(response, 'Curso arquivado')
        self.assertContains(response, 'para=published&amp;desfazer=1')
        self.client.post(self.url() + '?para=published&desfazer=1')
        self.bls.refresh_from_db()
        self.assertEqual((self.bls.status, self.bls.archived_at), ('published', None))

    def test_undo_of_archiving_a_draft_goes_back_to_draft(self):
        self.login(self.owner)
        response = self.client.post(self.url(self.draft), {'para': 'archived', 'confirmar': 'DEA'}, follow=True)
        self.assertContains(response, 'para=draft&amp;desfazer=1')
        self.client.post(self.url(self.draft) + '?para=draft&desfazer=1')
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, 'draft')

    def test_archive_without_acronym_uses_title(self):
        course = Course.objects.create(title='Sem sigla', slug='sem-sigla', creator=self.owner.creator_profile)
        self.login(self.owner)
        self.client.post(self.url(course), {'para': 'archived', 'confirmar': 'Sem sigla'})
        course.refresh_from_db()
        self.assertEqual(course.status, 'archived')

    def test_restore_archived_as_draft(self):
        self.login(self.owner)
        self.client.post(self.url(self.arch), {'para': 'draft'})
        self.arch.refresh_from_db()
        self.assertEqual((self.arch.status, self.arch.archived_at), ('draft', None))

    def test_invalid_status_rejected(self):
        self.login(self.owner)
        self.assertEqual(self.client.post(self.url(), {'para': 'xyz'}, **AJAX).status_code, 400)

    def test_archiving_keeps_enrollments_orders_and_certificates(self):
        enrollment = Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        order = Order.objects.create(student=self.jane.student_profile, course=self.bls, amount=150, status=Order.Status.COMPLETED)
        Certificate.objects.create(enrollment=enrollment, code='KEEP01', student_name='Jane', student_cpf='52998224725',
                                   course_title='BLS', completed_at=timezone.now())
        self.login(self.owner)
        self.client.post(self.url(), {'para': 'archived', 'confirmar': 'BLS'})
        self.assertTrue(Enrollment.objects.filter(pk=enrollment.pk).exists())
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())
        self.assertTrue(Certificate.objects.filter(code='KEEP01').exists())

    def test_archived_course_leaves_the_student_area(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.bls)
        self.login(self.owner)
        self.client.post(self.url(), {'para': 'archived', 'confirmar': 'BLS'})
        self.login(self.jane)
        self.assertNotContains(self.client.get(reverse('dashboard')), 'Suporte Básico de Vida')

    def test_student_cannot_change_status(self):
        self.login(self.jane)
        self.assertEqual(self.client.post(self.url(), {'para': 'draft'}).status_code, 403)

    def test_get_not_allowed(self):
        self.login(self.owner)
        self.assertEqual(self.client.get(self.url()).status_code, 405)

    def test_activity_logged(self):
        self.login(self.owner)
        self.client.post(self.url(), {'para': 'draft'})
        self.assertTrue(ActivityLog.objects.filter(text='Curso BLS foi movido para rascunho', actor=self.owner).exists())
