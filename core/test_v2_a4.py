from datetime import datetime, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from community.models import Comment, CommunityPost
from courses.home_views import greeting
from courses.models import Certificate, Course, Enrollment, Lesson, LessonMaterial, LiveSession, Module, Progress
from users import steps

User = get_user_model()
PASSWORD = 'StrongPassword123!'


class A4Base(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.jane = User.objects.create_user(username='jane_student', email='jane@example.com', password=PASSWORD)
        self.profile = self.jane.student_profile
        self.bls = self.make_course('BLS', 'Suporte Básico de Vida', 'bls', 4)
        self.plantao = self.make_course('Plantão', 'Plantão Sem GPT', 'plantao', 1)
        self.enroll_bls = Enrollment.objects.create(student=self.profile, course=self.bls)
        self.client.force_login(self.jane)

    def make_course(self, short, title, slug, lessons):
        course = Course.objects.create(title=title, short_name=short, slug=slug, creator=self.admin.creator_profile, status='published')
        module = Module.objects.create(course=course, title='Introdução', order=1)
        for number in range(1, lessons + 1):
            Lesson.objects.create(module=module, title=f'{short} aula {number}', order=number, duration_seconds=420)
        return course

    def lessons(self, course):
        return list(Lesson.objects.filter(module__course=course).order_by('order'))

    def mark(self, lesson, completed=True, seconds=0):
        return Progress.objects.update_or_create(student=self.profile, lesson=lesson,
                                                 defaults={'is_completed': completed, 'position_seconds': seconds})[0]

    def finish(self, course):
        for lesson in self.lessons(course):
            self.mark(lesson)

    def fill_data(self):
        self.profile.full_name, self.profile.cpf = 'Jane Silva', '52998224725'
        self.profile.save()

    def home(self, **params):
        return self.client.get(reverse('dashboard'), params)


class GreetingTests(A4Base):
    def test_greeting_by_hour(self):
        for hour, expected in ((4, 'Boa noite'), (5, 'Bom dia'), (11, 'Bom dia'), (12, 'Boa tarde'), (17, 'Boa tarde'), (18, 'Boa noite'), (23, 'Boa noite')):
            with mock.patch('courses.home_views.timezone.localtime', return_value=datetime(2026, 11, 10, hour, 30)):
                self.assertEqual(greeting(), expected, hour)

    def test_uses_first_name_never_username(self):
        html = self.home().content.decode()
        self.assertIn(', Jane</h2>', html)
        self.assertNotIn('jane_student', html)
        self.profile.display_name = 'Janinha'
        self.profile.save()
        self.assertIn(', Janinha</h2>', self.home().content.decode())

    def test_staff_is_sent_to_painel(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.home(), reverse('painel:dashboard'), fetch_redirect_response=False)


class SummaryTests(A4Base):
    def test_summary_parts_and_plurals(self):
        self.assertContains(self.home(), '1 curso na sua conta')
        Enrollment.objects.create(student=self.profile, course=self.plantao)
        self.finish(self.plantao)
        now = timezone.now()
        LiveSession.objects.create(course=self.plantao, title='Encontro', starts_at=now + timedelta(days=2), ends_at=now + timedelta(days=2, hours=1))
        self.assertContains(self.home(), '2 cursos na sua conta · 1 concluído · 1 aula ao vivo esta semana')

    def test_zero_parts_are_omitted(self):
        html = self.home().content.decode()
        self.assertNotIn('concluído', html.split('page-intro')[1].split('</p>')[0])
        self.assertNotIn('ao vivo esta semana', html)


class EmptyAndShopTests(A4Base):
    def test_student_without_courses(self):
        Enrollment.objects.all().delete()
        response = self.home()
        self.assertContains(response, 'Você ainda não tem cursos')
        self.assertContains(response, 'Quando sua compra for confirmada, o curso aparece aqui na hora.')
        self.assertNotContains(response, 'Meus cursos</h2>')
        self.assertContains(response, 'Outros treinamentos CETREMER')

    def test_shop_excludes_owned_and_unpublished(self):
        draft = Course.objects.create(title='Rascunho X', slug='rx', creator=self.admin.creator_profile, status='draft')
        html = self.home().content.decode()
        self.assertIn('Plantão Sem GPT', html)
        self.assertIn('Não adquirido', html)
        self.assertIn('Veja o conteúdo completo antes de comprar.', html)
        self.assertNotIn(draft.title, html)
        shop_html = html.split('Outros treinamentos CETREMER')[1]
        self.assertNotIn('Suporte Básico de Vida', shop_html)

    def test_shop_hidden_when_everything_is_owned(self):
        Enrollment.objects.create(student=self.profile, course=self.plantao)
        self.assertNotContains(self.home(), 'Outros treinamentos CETREMER')

    def test_archived_and_inactive_courses_are_not_listed(self):
        Enrollment.objects.create(student=self.profile, course=self.plantao, is_active=False)
        self.bls.status = 'archived'
        self.bls.save()
        response = self.home()
        self.assertEqual(response.context['all_courses'], [])
        self.assertContains(response, 'Você ainda não tem cursos')


class ResumeCardTests(A4Base):
    def test_no_card_without_activity(self):
        self.assertNotContains(self.home(), 'Continue de onde parou')

    def test_card_with_position(self):
        lesson = self.lessons(self.bls)[1]
        self.mark(self.lessons(self.bls)[0])
        self.mark(lesson, completed=False, seconds=192)
        response = self.home()
        html = response.content.decode()
        self.assertContains(response, 'Continue de onde parou')
        self.assertIn('Parou em 03:12 de 07:00', html)
        self.assertIn('BLS aula 2', html)
        self.assertIn('Suporte Básico de Vida · Módulo 1 · Aula 2 de 4', html)
        self.assertIn('25% do curso · 1 de 4 aulas', html)
        self.assertIn('style="width: 46%"', html)
        self.assertIn(reverse('lesson_detail', args=['bls', lesson.id]), html)
        self.assertIn('Continuar aula', html)
        self.assertIn('Ver conteúdo do curso', html)

    def test_short_position_hides_time_chip(self):
        self.mark(self.lessons(self.bls)[0], completed=False, seconds=10)
        html = self.home().content.decode()
        self.assertIn('Continue de onde parou', html)
        self.assertNotIn('Parou em', html)

    def test_most_recent_course_wins_and_finished_courses_are_skipped(self):
        Enrollment.objects.create(student=self.profile, course=self.plantao)
        old = self.mark(self.lessons(self.bls)[0], completed=False, seconds=60)
        Progress.objects.filter(pk=old.pk).update(updated_at=timezone.now() - timedelta(days=3))
        self.mark(self.lessons(self.plantao)[0], completed=False, seconds=90)
        self.assertEqual(self.home().context['resume']['course'], self.plantao)
        self.finish(self.plantao)
        self.assertEqual(self.home().context['resume']['course'], self.bls)


class CourseListTests(A4Base):
    def setUp(self):
        super().setUp()
        self.extra = self.make_course('ACLS', 'Suporte Avançado ACLS', 'acls', 2)
        self.pals = self.make_course('PALS', 'Suporte Avançado PALS', 'pals', 1)
        Enrollment.objects.create(student=self.profile, course=self.extra)
        Enrollment.objects.create(student=self.profile, course=self.pals)
        self.mark(self.lessons(self.bls)[0])
        self.finish(self.pals)

    def test_counts_and_filters(self):
        response = self.home()
        self.assertEqual(response.context['filter_counts'], {'todos': 3, 'andamento': 1, 'nao_iniciados': 1, 'concluidos': 1})
        for label in ('Todos (3)', 'Em andamento (1)', 'Não iniciados (1)', 'Concluídos (1)'):
            self.assertContains(response, label)
        titles = lambda r: [i['course'].slug for i in r.context['courses']]
        self.assertEqual(titles(self.home(filtro='andamento')), ['bls'])
        self.assertEqual(titles(self.home(filtro='nao_iniciados')), ['acls'])
        self.assertEqual(titles(self.home(filtro='concluidos')), ['pals'])
        self.assertEqual(len(titles(self.home(filtro='qualquer'))), 3)
        self.assertEqual(self.home(filtro='qualquer').context['filter'], 'todos')

    def test_current_filter_is_marked(self):
        self.assertIn('aria-current="page" href="?filtro=concluidos"', self.home(filtro='concluidos').content.decode())

    def test_card_labels_and_actions(self):
        html = self.home().content.decode()
        self.assertIn('1 de 4 aulas · visto há', html)
        self.assertIn('Não iniciado · 2 aulas', html)
        self.assertIn('Concluído · 1 aula<', html)
        self.assertNotIn('1 aulas', html)
        by_slug = {i['course'].slug: i for i in self.home().context['courses']}
        self.assertEqual((by_slug['bls']['action'], by_slug['acls']['action'], by_slug['pals']['action']),
                         ('Continuar', 'Começar curso', 'Rever aulas'))
        self.assertEqual(by_slug['bls']['url'], reverse('lesson_detail', args=['bls', self.lessons(self.bls)[1].id]))
        self.assertEqual(by_slug['acls']['url'], reverse('lesson_detail', args=['acls', self.lessons(self.extra)[0].id]))
        self.assertEqual(by_slug['pals']['url'], reverse('lesson_detail', args=['pals', self.lessons(self.pals)[0].id]))

    def test_empty_filter_messages(self):
        Progress.objects.all().delete()
        Progress.objects.create(student=self.profile, lesson=self.lessons(self.extra)[0])
        Progress.objects.create(student=self.profile, lesson=self.lessons(self.bls)[0])
        Progress.objects.create(student=self.profile, lesson=self.lessons(self.pals)[0])
        self.assertContains(self.home(filtro='nao_iniciados'), 'Nenhum curso por começar')
        self.assertContains(self.home(filtro='concluidos'), 'Nenhum curso concluído ainda')
        self.assertContains(self.home(filtro='concluidos'), 'Ver todos')

    def test_no_courses_empty_in_progress_filter(self):
        Progress.objects.all().delete()
        self.assertContains(self.home(filtro='andamento'), 'Nenhum curso em andamento')

    def test_draft_lessons_do_not_count(self):
        Lesson.objects.create(module=self.bls.modules.first(), title='Rascunho', order=9, status='draft')
        self.assertContains(self.home(), '1 de 4 aulas')

    def test_query_count_does_not_grow_with_courses(self):
        self.home()  # a primeira chamada cria SiteSettings e distorce a contagem
        with CaptureQueriesContext(connection) as few:
            self.home()
        for index in range(4):
            course = self.make_course(f'C{index}', f'Curso {index}', f'c{index}', 3)
            Enrollment.objects.create(student=self.profile, course=course)
        with CaptureQueriesContext(connection) as many:
            self.home()
        self.assertEqual(len(few), len(many))


class StepsTests(A4Base):
    def keys(self, **params):
        return [s['key'] for s in self.home(**params).context['steps']]

    def test_cpf_step_when_data_missing(self):
        response = self.home()
        self.assertEqual([s['key'] for s in response.context['steps']], ['cpf'])
        self.assertContains(response, 'Próximos passos')
        self.assertContains(response, 'Informe nome completo e CPF')
        self.assertContains(response, 'Sem isso o certificado não pode ser emitido. Leva 1 minuto.')
        self.assertContains(response, 'Completar dados')
        self.assertContains(response, reverse('settings') + '?secao=certificado')
        self.assertContains(response, 'data-dismiss-url="/passos/cpf/dispensar/"')
        self.assertContains(response, 'data-dismiss-target="#step-cpf"')

    def test_no_steps_card_when_everything_is_ok(self):
        self.fill_data()
        response = self.home()
        self.assertEqual(response.context['steps'], [])
        self.assertNotContains(response, 'Próximos passos')

    def test_certificate_ready_step(self):
        self.fill_data()
        self.finish(self.plantao)
        Enrollment.objects.create(student=self.profile, course=self.plantao)
        response = self.home()
        self.assertEqual([s['key'] for s in response.context['steps']], ['cert:plantao'])
        self.assertContains(response, 'Seu certificado do Plantão está pronto')
        self.assertContains(response, reverse('certificates') + '?emitir=plantao')

    def test_certificate_step_disappears_after_issue_or_when_disabled(self):
        self.fill_data()
        enrollment = Enrollment.objects.create(student=self.profile, course=self.plantao)
        self.finish(self.plantao)
        self.assertEqual(self.keys(), ['cert:plantao'])
        Certificate.objects.create(enrollment=enrollment, code='ABC123DEF456', student_name='Jane', student_cpf='52998224725',
                                   course_title='Plantão', completed_at=timezone.now())
        self.assertEqual(self.keys(), [])
        self.plantao.certificate_enabled = False
        self.plantao.save()
        Certificate.objects.all().delete()
        self.assertEqual(self.keys(), [])

    def test_live_step_texts_and_states(self):
        self.fill_data()
        now = timezone.now()
        session = LiveSession.objects.create(course=self.bls, title='Encontro', starts_at=now + timedelta(days=2, hours=1),
                                             ends_at=now + timedelta(days=2, hours=2))
        step = self.home().context['steps'][0]
        self.assertEqual(step['key'], f'live:{session.id}')
        self.assertEqual(step['title'], 'Aula ao vivo · BLS')
        self.assertEqual(step['badge'], 'Em 2 dias')
        self.assertIn('(horário de Brasília). O botão de entrar libera 15 min antes.', step['meta'])
        self.assertRegex(step['meta'], r'^(Segunda|Terça|Quarta|Quinta|Sexta|Sábado|Domingo), \d\d/\d\d, das \d{1,2}h(\d\d)? às \d{1,2}h(\d\d)? ')
        session.starts_at, session.ends_at = now - timedelta(minutes=10), now + timedelta(hours=1)
        session.save()
        step = self.home().context['steps'][0]
        self.assertEqual((step['badge'], step['badge_class']), ('● Ao vivo agora', 'badge--live'))
        session.starts_at, session.ends_at = now + timedelta(days=9), now + timedelta(days=9, hours=1)
        session.save()
        self.assertEqual(self.keys(), [])

    def test_live_step_ignores_other_courses(self):
        self.fill_data()
        other = self.make_course('Outro', 'Outro curso', 'outro', 1)
        now = timezone.now()
        LiveSession.objects.create(course=other, title='X', starts_at=now + timedelta(hours=3), ends_at=now + timedelta(hours=4))
        self.assertEqual(self.keys(), [])

    def test_answer_step(self):
        self.fill_data()
        post = CommunityPost.objects.create(author=self.jane, course=self.bls, title='Profundidade', content='x')
        Comment.objects.create(post=post, author=self.admin, content='Resposta')
        response = self.home()
        self.assertEqual([s['key'] for s in response.context['steps']], [f'resp:{post.id}'])
        self.assertContains(response, 'O instrutor respondeu sua dúvida')
        self.assertContains(response, 'Suporte Básico de Vida · Profundidade')
        self.assertContains(response, reverse('community') + f'?duvida={post.id}')

    def test_order_and_limit_of_four(self):
        self.finish(self.plantao)
        Enrollment.objects.create(student=self.profile, course=self.plantao)
        now = timezone.now()
        LiveSession.objects.create(course=self.bls, title='E', starts_at=now + timedelta(days=1), ends_at=now + timedelta(days=1, hours=1))
        posts = [CommunityPost.objects.create(author=self.jane, course=self.bls, title=f'D{n}', content='x') for n in range(3)]
        for post in posts:
            Comment.objects.create(post=post, author=self.admin, content='r')
        keys = self.keys()
        self.assertEqual(len(keys), 4)
        self.assertEqual([k.split(':')[0] for k in keys][:3], ['cpf', 'cert', 'live'])
        self.assertEqual(keys[3].split(':')[0], 'resp')

    def test_dismiss_restore_and_persistence(self):
        self.assertEqual(self.client.post(reverse('step_dismiss', args=['cpf'])).json(), {'ok': True})
        self.assertEqual(self.keys(), [])
        self.assertEqual(self.client.post(reverse('step_restore', args=['cpf'])).json(), {'ok': True})
        self.assertEqual(self.keys(), ['cpf'])

    def test_dismissed_non_cpf_step_never_returns(self):
        self.fill_data()
        self.finish(self.plantao)
        Enrollment.objects.create(student=self.profile, course=self.plantao)
        self.client.post(reverse('step_dismiss', args=['cert:plantao']))
        self.assertEqual(self.keys(), [])
        self.assertIn('cert:plantao', self.profile.__class__.objects.get(pk=self.profile.pk).dismissed_steps)

    def test_cpf_dismissal_returns_after_seven_days(self):
        self.profile.dismissed_steps = [f'cpf@{(timezone.localdate() - timedelta(days=6)).isoformat()}']
        self.profile.save()
        self.assertEqual(self.keys(), [])
        self.profile.dismissed_steps = [f'cpf@{(timezone.localdate() - timedelta(days=7)).isoformat()}']
        self.profile.save()
        self.assertEqual(self.keys(), ['cpf'])

    def test_step_endpoints_validate_method_user_and_key(self):
        self.assertEqual(self.client.get(reverse('step_dismiss', args=['cpf'])).status_code, 405)
        self.assertEqual(self.client.post(reverse('step_dismiss', args=['invalida'])).status_code, 404)
        self.assertEqual(self.client.post('/passos/live:abc/dispensar/').status_code, 404)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(reverse('step_dismiss', args=['cpf'])).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.post(reverse('step_dismiss', args=['cpf'])).status_code, 302)

    def test_colon_keys_are_routable(self):
        self.assertEqual(reverse('step_dismiss', args=['cert:bls']), '/passos/cert:bls/dispensar/')
        self.assertEqual(self.client.post('/passos/cert:bls/dispensar/').json(), {'ok': True})


class StepStoreTests(A4Base):
    def test_valid_keys(self):
        for key in ('cpf', 'cert:bls', 'cert:plantao-sem-gpt', 'live:12', 'resp:3'):
            self.assertTrue(steps.is_valid_key(key), key)
        for key in ('', 'cpf:1', 'live:x', 'resp:', 'cert:', 'outro'):
            self.assertFalse(steps.is_valid_key(key), key)

    def test_dismiss_is_idempotent(self):
        steps.dismiss(self.profile, 'resp:1')
        steps.dismiss(self.profile, 'resp:1')
        self.assertEqual(self.profile.dismissed_steps, ['resp:1'])
        steps.restore(self.profile, 'resp:1')
        self.assertEqual(self.profile.dismissed_steps, [])


class CourseHomeTests(A4Base):
    def url(self, slug='bls', **params):
        return reverse('course_home', args=[slug]) + ('?' + '&'.join(f'{k}={v}' for k, v in params.items()) if params else '')

    def test_access_rules(self):
        self.assertEqual(self.client.get(self.url()).status_code, 200)
        self.assertEqual(self.client.get(self.url('plantao')).status_code, 404)
        self.enroll_bls.is_active = False
        self.enroll_bls.save()
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.enroll_bls.is_active = True
        self.enroll_bls.save()
        self.bls.status = 'archived'
        self.bls.save()
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(self.url('plantao')), reverse('course_preview', args=['plantao']), fetch_redirect_response=False)
        self.client.logout()
        self.assertEqual(self.client.get(self.url()).status_code, 302)

    def test_public_preview_redirects_enrolled_students_unless_preview_flag(self):
        preview = reverse('course_preview', args=['bls'])
        self.assertRedirects(self.client.get(preview), self.url(), fetch_redirect_response=False)
        self.assertEqual(self.client.get(preview + '?preview=1').status_code, 200)
        self.assertEqual(self.client.get(reverse('course_preview', args=['plantao'])).status_code, 200)
        self.client.logout()
        self.assertEqual(self.client.get(preview).status_code, 200)

    def test_hero_texts_and_action(self):
        html = self.client.get(self.url()).content.decode()
        self.assertIn('1 módulo · 4 aulas · 28 min', html)
        self.assertIn('Certificado verificável', html)
        self.assertIn('Começar curso', html)
        self.assertIn('Requisitos do certificado', html)
        self.assertIn('Acesso vitalício · liberado em ', html)
        self.assertIn('0% · 0 de 4 aulas', html)
        self.mark(self.lessons(self.bls)[0])
        self.mark(self.lessons(self.bls)[1], completed=False, seconds=30)
        html = self.client.get(self.url()).content.decode()
        self.assertIn('Continuar: Aula 2 · BLS aula 2', html)
        self.finish(self.bls)
        self.assertIn('Rever aulas', self.client.get(self.url()).content.decode())

    def test_access_line_with_expiry_and_origin(self):
        self.enroll_bls.expires_at = timezone.now() + timedelta(days=30)
        self.enroll_bls.source = 'import'
        self.enroll_bls.external_ref = 'HP1234'
        self.enroll_bls.save()
        html = self.client.get(self.url()).content.decode()
        self.assertIn(f'Acesso até {self.enroll_bls.expires_at:%d/%m/%Y}', html)
        self.assertIn('por importação (HP1234)', html)

    def test_certificate_badge_follows_course_flag(self):
        self.bls.certificate_enabled = False
        self.bls.save()
        html = self.client.get(self.url()).content.decode()
        self.assertNotIn('Certificado verificável', html)
        self.assertNotIn('Seu certificado', html)
        self.assertNotIn('Requisitos do certificado', html)

    def test_lesson_marks_and_meta(self):
        first, second, third, fourth = self.lessons(self.bls)
        self.mark(first)
        self.mark(second, completed=False, seconds=192)
        html = self.client.get(self.url()).content.decode()
        self.assertIn('mark-done', html)
        self.assertIn('mark-current', html)
        self.assertIn('mark-todo', html)
        self.assertIn('Concluída', html)
        self.assertIn('Você parou em 03:12', html)
        self.assertIn('Não assistida', html)
        self.assertIn('4 aulas · 1 concluída', html)
        self.assertIn('Em andamento', html)
        self.assertNotIn('1 aulas', html)

    def test_module_states(self):
        html = self.client.get(self.url()).content.decode()
        self.assertIn('badge badge--gray">Não iniciado', html)
        self.finish(self.bls)
        self.assertIn('badge badge--success">Concluído', self.client.get(self.url()).content.decode())

    def test_locked_module_shows_release_date_and_no_links(self):
        self.bls.release_mode = 'scheduled'
        self.bls.save()
        module = self.bls.modules.first()
        module.release_date = timezone.localdate() + timedelta(days=5)
        module.save()
        html = self.client.get(self.url()).content.decode()
        self.assertIn(f'Libera em {module.release_date:%d/%m}', html)
        self.assertIn('aria-disabled="true"', html)
        self.assertNotIn(reverse('lesson_detail', args=['bls', self.lessons(self.bls)[0].id]), html)

    def test_draft_lessons_hidden_everywhere(self):
        Lesson.objects.create(module=self.bls.modules.first(), title='Aula secreta', order=9, status='draft')
        html = self.client.get(self.url()).content.decode()
        self.assertNotIn('Aula secreta', html)
        self.assertIn('4 aulas', html)

    def test_lesson_material_count_and_materials_tab(self):
        lesson = self.lessons(self.bls)[0]
        LessonMaterial.objects.create(lesson=lesson, title='Algoritmo de PCR', url='https://example.com/a.pdf')
        html = self.client.get(self.url(aba='materiais')).content.decode()
        self.assertIn('1 material', html)
        self.assertIn('Materiais (1)', html)
        self.assertIn('Todos os materiais do curso em um lugar.', html)
        self.assertIn('PDF · Aula 1', html)
        self.assertIn('https://example.com/a.pdf', html)

    def test_empty_materials_text(self):
        self.assertContains(self.client.get(self.url()), 'Este curso não tem materiais de apoio')

    def test_tabs_follow_parameter(self):
        html = self.client.get(self.url(aba='duvidas')).content.decode()
        self.assertIn('data-tab="duvidas" aria-selected="true"', html)
        self.assertIn('id="panel-conteudo" aria-labelledby="tab-conteudo" hidden', html)
        self.assertEqual(self.client.get(self.url(aba='x')).context['aba'], 'conteudo')

    def test_questions_tab(self):
        lesson = self.lessons(self.bls)[1]
        answered = CommunityPost.objects.create(author=self.jane, course=self.bls, lesson=lesson, title='Com resposta', content='x')
        Comment.objects.create(post=answered, author=self.admin, content='r')
        CommunityPost.objects.create(author=self.jane, course=self.bls, title='Sem resposta', content='y')
        CommunityPost.objects.create(author=self.jane, course=self.bls, title='Oculta', content='z', is_hidden=True)
        html = self.client.get(self.url(aba='duvidas')).content.decode()
        self.assertIn('Dúvidas (2)', html)
        self.assertIn('Respondida', html)
        self.assertIn('Aguardando resposta', html)
        self.assertIn('Aula 2 · Jane', html)
        self.assertNotIn('Oculta', html)
        self.assertIn('Nova pergunta', html)
        self.assertIn('Ver todas na comunidade', html)

    def test_empty_questions_text(self):
        self.assertContains(self.client.get(self.url(aba='duvidas')), 'Ninguém perguntou nada neste curso ainda.')

    def test_live_tab(self):
        self.assertContains(self.client.get(self.url(aba='ao-vivo')), 'Este curso não tem encontros ao vivo')
        now = timezone.now()
        LiveSession.objects.create(course=self.bls, title='Encontro 3', starts_at=now + timedelta(days=2), ends_at=now + timedelta(days=2, hours=1))
        LiveSession.objects.create(course=self.bls, title='Encontro velho', starts_at=now - timedelta(days=5), ends_at=now - timedelta(days=5, hours=-1))
        html = self.client.get(self.url(aba='ao-vivo')).content.decode()
        self.assertIn('Encontro 3', html)
        self.assertNotIn('Encontro velho', html)
        self.assertIn('(horário de Brasília)', html)
        self.assertIn('Ver agenda completa', html)

    def test_certificate_requirements_card(self):
        html = self.client.get(self.url()).content.decode()
        self.assertIn('Concluir as 4 aulas', html)
        self.assertIn('0 de 4 · faltam 4 aulas.', html)
        self.assertIn('Completar agora', html)
        self.assertIn('Ter acesso ativo ao curso', html)
        self.assertIn('Vitalício', html)
        self.fill_data()
        self.finish(self.bls)
        html = self.client.get(self.url()).content.decode()
        self.assertNotIn('Completar agora', html)
        self.assertIn('Nome e CPF informados', html)
        self.assertIn('Concluídas', html)

    def test_help_card_and_support_link(self):
        from users.models import SiteSettings
        site = SiteSettings.load()
        site.whatsapp = '5567999999999'
        site.save()
        html = self.client.get(self.url()).content.decode()
        self.assertIn('Falar com o suporte', html)
        self.assertIn('https://wa.me/5567999999999', html)

    def test_breadcrumb_and_title(self):
        html = self.client.get(self.url()).content.decode()
        self.assertIn('<nav class="crumbs"', html)
        self.assertIn('Meus cursos', html)

    def test_lesson_unreleased_redirect_now_lands_on_course_home(self):
        self.bls.release_mode = 'scheduled'
        self.bls.save()
        module = self.bls.modules.first()
        module.release_after_days = 3
        module.save()
        lesson = self.lessons(self.bls)[0]
        response = self.client.get(reverse('lesson_detail', args=['bls', lesson.id]), follow=True)
        self.assertEqual(response.redirect_chain[-1][0], self.url())
        self.assertContains(response, 'Este módulo libera em')
