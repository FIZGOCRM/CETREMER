import tempfile
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import ActivityLog
from courses.models import Category, Course, CourseFAQ, CourseSlugRedirect, Enrollment, Lesson, LiveSession, Module
from painel.course_views import format_price, parse_price
from sales.models import Order
from users.models import SiteSettings

User = get_user_model()
PASSWORD = 'StrongPassword123!'
AJAX = {'HTTP_X_REQUESTED_WITH': 'fetch'}
MEDIA = override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='cetremer-test-'))
GIF = (b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')


class PriceParsingTests(TestCase):
    def test_accepted_formats(self):
        cases = {'150': '150', '150,00': '150.00', '1.234,56': '1234.56', 'R$ 150,00': '150.00', '150.50': '150.50',
                 '1.234': '1234', '0': '0', '  99,9 ': '99.9', '0,5': '0.5'}
        for text, expected in cases.items():
            self.assertEqual(parse_price(text), Decimal(expected), text)

    def test_rejected_formats(self):
        for text in ('', '   ', 'abc', '-5', '1,234,56', '12,345', '150,001', '1e3', '999999999,00', 'R$'):
            with self.assertRaises(ValueError, msg=text):
                parse_price(text)

    def test_format_round_trip(self):
        for value in ('0.00', '150.00', '1234.56', '99999999.99'):
            self.assertEqual(parse_price(format_price(Decimal(value))), Decimal(value))
        self.assertEqual(format_price(Decimal('1234.5')), '1.234,50')
        self.assertEqual(format_price(None), '0,00')


class B4Base(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='dono', email='dono@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.inst = User.objects.create_user(username='inst', email='inst@example.com', password=PASSWORD, role=User.Role.CREATOR)
        self.jane = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        self.cat = Category.objects.create(name='Essenciais', slug='essenciais')
        self.course = Course.objects.create(title='Suporte Básico de Vida', short_name='BLS', slug='bls', category=self.cat,
                                            creator=self.owner.creator_profile, status='published', price=Decimal('150.00'), workload_hours=4)
        self.m1 = Module.objects.create(course=self.course, title='Fundamentos', order=1)
        self.m2 = Module.objects.create(course=self.course, title='Prática', order=2)
        self.lesson = Lesson.objects.create(module=self.m1, title='Introdução', order=1, is_free_preview=True)
        self.client.force_login(self.owner)

    def login(self, user):
        self.client.force_login(user)


class SalesPageTests(B4Base):
    url = property(lambda self: reverse('painel:course_sales', args=[self.course.id]))

    def test_page_renders_all_cards(self):
        CourseFAQ.objects.create(course=self.course, question='Tem certificado?', answer='Sim.')
        Course.objects.filter(pk=self.course.pk).update(tagline='Aprenda RCP', learning_objectives='Fazer RCP\nUsar DEA',
                                                       target_audience='Profissionais de saúde')
        page = self.client.get(self.url)
        for text in ('Apresentação', 'Chamada curta', '11 de 160 caracteres', 'Descrição completa', 'Capa', 'Trocar imagem',
                     '3:2, mínimo 1200 × 800 px. Você ajusta o enquadramento depois de enviar.', 'O que o aluno vai aprender',
                     '2 itens · ideal entre 4 e 6', '+ Adicionar item', 'Para quem é', 'Se ficar vazio, a seção não aparece no site.',
                     'Perguntas frequentes', '+ Pergunta', 'Tem certificado?', 'Aulas grátis', 'Introdução', 'Escolher aula',
                     'Pré-visualização', 'Computador', 'Celular', 'A prévia atualiza quando você salva.',
                     'Abrir página completa em nova aba', 'Você tem alterações não salvas na página de venda.'):
            self.assertContains(page, text)
        self.assertContains(page, 'data-dirty-form data-dirtybar="dirtybar"')
        self.assertContains(page, 'aria-current="page" href="%s"' % self.url)

    def test_free_lessons_empty_state(self):
        Lesson.objects.update(is_free_preview=False)
        self.assertContains(self.client.get(self.url), 'Nenhuma aula grátis')

    def test_preview_modes(self):
        self.assertNotContains(self.client.get(self.url), 'preview-frame--mobile')
        self.assertContains(self.client.get(self.url, {'previa': 'celular'}), 'preview-frame--mobile')

    def test_save_everything(self):
        data = {'tagline': 'Aprenda RCP em 4 horas', 'description': 'Curso completo.', 'target_audience': 'Equipe de saúde',
                'objectives': ['Fazer RCP', '  ', 'Usar o DEA'], 'faq_question': ['Tem certificado?', ''], 'faq_answer': ['Sim.', '']}
        response = self.client.post(self.url, data, **AJAX)
        body = response.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['toast'], 'Alterações salvas')
        self.assertEqual(body['counts']['#tagline-count'], '22 de 160 caracteres')
        self.assertIn('Aprenda RCP em 4 horas', body['replace']['#sales-preview'])
        self.course.refresh_from_db()
        self.assertEqual((self.course.tagline, self.course.description, self.course.target_audience),
                         ('Aprenda RCP em 4 horas', 'Curso completo.', 'Equipe de saúde'))
        self.assertEqual(self.course.objectives_list, ['Fazer RCP', 'Usar o DEA'])
        self.assertEqual([(f.question, f.answer, f.order) for f in self.course.faqs.all()], [('Tem certificado?', 'Sim.', 1)])
        self.assertTrue(ActivityLog.objects.filter(course=self.course, verb='course_updated').exists())

    def test_saving_does_not_touch_price_or_status(self):
        self.client.post(self.url, {'tagline': 'x'}, **AJAX)
        self.course.refresh_from_db()
        self.assertEqual((self.course.price, self.course.status, self.course.slug), (Decimal('150.00'), 'published', 'bls'))

    def test_faq_replaced_not_duplicated(self):
        data = {'faq_question': ['A?'], 'faq_answer': ['B.']}
        self.client.post(self.url, data, **AJAX)
        self.client.post(self.url, data, **AJAX)
        self.assertEqual(self.course.faqs.count(), 1)

    def test_validation_errors(self):
        response = self.client.post(self.url, {'tagline': 'x' * 161, 'faq_question': ['Só pergunta'], 'faq_answer': ['']}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()['errors']), {'tagline', 'faq_question'})
        self.assertEqual(response.json()['error'], 'Corrija 2 campos para salvar.')
        self.course.refresh_from_db()
        self.assertEqual(self.course.tagline, '')

    def test_without_js_redirects_with_toast(self):
        response = self.client.post(self.url, {'tagline': 'Sem JS'}, follow=True)
        self.assertContains(response, 'Alterações salvas')
        self.assertContains(response, 'value="Sem JS"')

    @MEDIA
    def test_cover_upload_and_remove(self):
        image = SimpleUploadedFile('capa.gif', GIF, content_type='image/gif')
        self.assertTrue(self.client.post(self.url, {'cover_image': image}, **AJAX).json()['ok'])
        self.course.refresh_from_db()
        self.assertTrue(self.course.cover_image)
        self.assertContains(self.client.get(self.url), 'Remover')
        self.client.post(self.url, {'remove_cover': '1'}, **AJAX)
        self.course.refresh_from_db()
        self.assertFalse(self.course.cover_image)

    @MEDIA
    def test_cover_must_be_image(self):
        bad = SimpleUploadedFile('capa.pdf', b'%PDF', content_type='application/pdf')
        response = self.client.post(self.url, {'cover_image': bad}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertIn('cover_image', response.json()['errors'])

    def test_instructor_can_edit_student_cannot(self):
        self.login(self.inst)
        self.assertTrue(self.client.post(self.url, {'tagline': 'Do instrutor'}, **AJAX).json()['ok'])
        self.login(self.jane)
        self.assertEqual(self.client.post(self.url, {'tagline': 'x'}).status_code, 403)
        self.assertEqual(self.client.get(self.url).status_code, 403)


class SettingsPageTests(B4Base):
    url = property(lambda self: reverse('painel:course_settings', args=[self.course.id]))

    def form(self, **overrides):
        data = {'title': 'Suporte Básico de Vida', 'category': self.cat.id, 'short_name': 'BLS', 'slug': 'bls', 'price': '150,00',
                'workload_hours': '4', 'access_months': '', 'release_mode': 'all', 'notify_module_release': '1',
                'live_meet_url': '', 'certificate_enabled': '1'}
        data.update(overrides)
        return data

    def save(self, **overrides):
        return self.client.post(self.url, self.form(**overrides), **AJAX)

    def test_page_sections_and_values(self):
        page = self.client.get(self.url)
        for text in ('Geral', 'Preço e acesso', 'Liberação do conteúdo', 'Encontros ao vivo', 'Certificado', 'Zona de risco',
                     'Nome e identificação do curso no site e no painel.', 'cetremer.com.br/cursos/',
                     'Trocar o endereço quebra links já divulgados. O antigo redireciona por 90 dias.',
                     'Usado no checkout e no certificado.', 'Alunos importados contam o prazo a partir da importação.',
                     'Tudo na matrícula', 'Programada por módulo', 'Avisar o aluno por e-mail quando um módulo for liberado',
                     'Emitir certificado neste curso', 'Ver certificado de exemplo', 'Ações que mudam o acesso dos alunos.',
                     'Mover para rascunho', 'Arquivar curso', 'Excluir definitivamente', 'Adicionar encontro'):
            self.assertContains(page, text)
        self.assertContains(page, 'value="150,00"')
        self.assertContains(page, 'id="geral"')
        self.assertContains(page, 'href="#risco"')
        self.assertContains(page, 'data-dirty-form data-dirtybar="dirtybar"')

    def test_price_with_comma_is_kept(self):
        """HANDOFF-v2 seção 10, item 1: "150,00" não pode zerar o preço."""
        Course.objects.filter(pk=self.course.pk).update(price=Decimal('99.00'))
        self.assertTrue(self.save(price='150,00').json()['ok'])
        self.course.refresh_from_db()
        self.assertEqual(self.course.price, Decimal('150.00'))
        self.save(price='1.234,56')
        self.course.refresh_from_db()
        self.assertEqual(self.course.price, Decimal('1234.56'))
        self.save(price='200')
        self.course.refresh_from_db()
        self.assertEqual(self.course.price, Decimal('200.00'))

    def test_invalid_price_is_an_error_and_keeps_old_value(self):
        response = self.save(price='abc')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['errors']['price'], ['Informe o preço em reais, por exemplo 150,00.'])
        self.assertEqual(self.save(price='').status_code, 400)
        self.course.refresh_from_db()
        self.assertEqual(self.course.price, Decimal('150.00'))

    def test_price_field_is_text_not_number(self):
        page = self.client.get(self.url).content.decode()
        self.assertNotIn('type="number"', page)
        self.assertIn('inputmode="decimal"', page)

    def test_general_fields(self):
        other = Category.objects.create(name='Leigos', slug='leigos')
        self.save(title='BLS Novo', category=other.id, short_name='BLS2', workload_hours='6', access_months='12')
        self.course.refresh_from_db()
        self.assertEqual((self.course.title, self.course.category, self.course.short_name, self.course.workload_hours, self.course.access_months),
                         ('BLS Novo', other, 'BLS2', 6, 12))
        self.save(access_months='', category='', workload_hours='')
        self.course.refresh_from_db()
        self.assertEqual((self.course.access_months, self.course.category, self.course.workload_hours), (None, None, None))

    def test_field_validation(self):
        cases = {'title': {'title': ' '}, 'short_name': {'short_name': 'x' * 13}, 'workload': {'workload_hours': 'quatro'},
                 'access': {'access_months': '7'}, 'meet': {'live_meet_url': 'meet.google.com/x'}, 'category': {'category': '9999'},
                 'slug': {'slug': 'Com Espaço'}}
        for name, overrides in cases.items():
            response = self.save(**overrides)
            self.assertEqual(response.status_code, 400, name)
        self.course.refresh_from_db()
        self.assertEqual((self.course.title, self.course.slug), ('Suporte Básico de Vida', 'bls'))

    def test_slug_change_creates_redirect_for_public_page(self):
        self.save(slug='suporte-basico')
        self.course.refresh_from_db()
        self.assertEqual(self.course.slug, 'suporte-basico')
        self.assertTrue(CourseSlugRedirect.objects.filter(old_slug='bls', course=self.course).exists())
        self.client.logout()
        old = self.client.get(reverse('course_preview', args=['bls']))
        self.assertRedirects(old, reverse('course_preview', args=['suporte-basico']), status_code=301, fetch_redirect_response=False)
        CourseSlugRedirect.objects.filter(old_slug='bls').update(created_at=timezone.now() - timedelta(days=91))
        self.assertEqual(self.client.get(reverse('course_preview', args=['bls'])).status_code, 404)

    def test_slug_conflicts(self):
        Course.objects.create(title='Outro', slug='outro', creator=self.owner.creator_profile)
        self.assertEqual(self.save(slug='outro').status_code, 400)
        self.save(slug='novo-endereco')
        other = Course.objects.create(title='Terceiro', slug='terceiro', creator=self.owner.creator_profile)
        response = self.client.post(reverse('painel:course_settings', args=[other.id]), self.form(title='Terceiro', slug='bls'), **AJAX)
        self.assertEqual(response.status_code, 400)

    def test_returning_to_old_slug_drops_its_redirect(self):
        self.save(slug='novo')
        self.save(slug='bls')
        self.assertFalse(CourseSlugRedirect.objects.filter(old_slug='bls').exists())
        self.assertTrue(CourseSlugRedirect.objects.filter(old_slug='novo').exists())

    def test_unknown_slug_is_404(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('course_preview', args=['nao-existe'])).status_code, 404)

    def test_scheduled_release_per_module(self):
        response = self.save(release_mode='scheduled', **{
            'release_type_%d' % self.m1.id: 'now',
            'release_type_%d' % self.m2.id: 'days', 'release_days_%d' % self.m2.id: '7', 'release_date_%d' % self.m2.id: ''})
        self.assertTrue(response.json()['ok'])
        self.course.refresh_from_db()
        self.m1.refresh_from_db()
        self.m2.refresh_from_db()
        self.assertEqual(self.course.release_mode, 'scheduled')
        self.assertEqual((self.m1.release_after_days, self.m1.release_date), (None, None))
        self.assertEqual((self.m2.release_after_days, self.m2.release_date), (7, None))
        self.save(release_mode='scheduled', **{'release_type_%d' % self.m1.id: 'date', 'release_date_%d' % self.m1.id: '2027-03-01',
                                               'release_type_%d' % self.m2.id: 'now'})
        self.m1.refresh_from_db()
        self.m2.refresh_from_db()
        self.assertEqual((self.m1.release_after_days, self.m1.release_date), (None, date(2027, 3, 1)))
        self.assertEqual((self.m2.release_after_days, self.m2.release_date), (None, None))

    def test_release_validation(self):
        response = self.save(release_mode='scheduled', **{'release_type_%d' % self.m1.id: 'days', 'release_days_%d' % self.m1.id: 'x',
                                                          'release_type_%d' % self.m2.id: 'date', 'release_date_%d' % self.m2.id: 'ontem'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()['errors']), {'release_days_%d' % self.m1.id, 'release_date_%d' % self.m2.id})

    def test_all_mode_ignores_module_fields(self):
        Module.objects.filter(pk=self.m1.pk).update(release_after_days=5)
        self.save(release_mode='all', **{'release_type_%d' % self.m1.id: 'date', 'release_date_%d' % self.m1.id: 'lixo'})
        self.m1.refresh_from_db()
        self.assertEqual(self.m1.release_after_days, 5)

    def test_switches_and_meet_link(self):
        post = self.form(live_meet_url='https://meet.google.com/abc-defg-hij', certificate_enabled='0')
        post['notify_module_release'] = ['0']
        self.client.post(self.url, post, **AJAX)
        self.course.refresh_from_db()
        self.assertEqual((self.course.live_meet_url, self.course.certificate_enabled, self.course.notify_module_release),
                         ('https://meet.google.com/abc-defg-hij', False, False))

    def test_signer_alert_and_sample_certificate(self):
        page = self.client.get(self.url)
        self.assertContains(page, 'Responsável técnico ainda não definido.')
        self.assertContains(page, reverse('painel:settings') + '?secao=certificado')
        site = SiteSettings.load()
        site.signer_name = 'Dra. Ana'
        site.save()
        self.assertNotContains(self.client.get(self.url), 'Responsável técnico ainda não definido.')
        self.login(self.inst)
        site.signer_name = ''
        site.save()
        page = self.client.get(self.url)
        self.assertContains(page, 'Responsável técnico ainda não definido.')
        self.assertNotContains(page, '?secao=certificado')

    def test_certificate_sample_is_marked_example(self):
        sample = self.client.get(reverse('painel:course_certificate_sample', args=[self.course.id]))
        self.assertContains(sample, 'EXEMPLO')
        self.assertContains(sample, 'Suporte Básico de Vida')
        self.assertEqual(sample.status_code, 200)

    def test_old_edit_route_redirects(self):
        response = self.client.get(reverse('painel:course_edit', args=[self.course.id]))
        self.assertRedirects(response, self.url, status_code=301, fetch_redirect_response=False)

    def test_save_without_js(self):
        response = self.client.post(self.url, self.form(title='Sem JS'), follow=True)
        self.assertContains(response, 'Alterações salvas')
        self.assertContains(response, 'Sem JS')

    def test_activity_logged(self):
        self.save(short_name='SBV')
        self.assertTrue(ActivityLog.objects.filter(text='Curso SBV foi atualizado', course=self.course).exists())

    def test_student_forbidden(self):
        self.login(self.jane)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, self.form()).status_code, 403)


class LiveSessionTests(B4Base):
    save_url = property(lambda self: reverse('painel:live_session_save', args=[self.course.id]))

    def data(self, **overrides):
        data = {'title': 'Plantão de dúvidas', 'date': '2027-05-10', 'start': '19:00', 'end': '20:30', 'host_name': 'Dra. Ana',
                'meet_url': '', 'recording_url': ''}
        data.update(overrides)
        return data

    def test_create_in_brasilia_time(self):
        response = self.client.post(self.save_url, self.data(), **AJAX)
        self.assertEqual(response.json()['redirect'], reverse('painel:course_settings', args=[self.course.id]) + '#ao-vivo')
        session = LiveSession.objects.get()
        self.assertEqual((session.title, session.host_name, session.course), ('Plantão de dúvidas', 'Dra. Ana', self.course))
        self.assertEqual(session.starts_at.isoformat(), '2027-05-10T22:00:00+00:00')
        self.assertEqual(session.ends_at.isoformat(), '2027-05-10T23:30:00+00:00')

    def test_list_and_dialogs_on_settings(self):
        self.client.post(self.save_url, self.data(recording_url='https://vimeo.com/123'), **AJAX)
        page = self.client.get(reverse('painel:course_settings', args=[self.course.id]))
        self.assertContains(page, '2027-05-10')
        self.assertContains(page, '19:00 às 20:30')
        self.assertContains(page, 'Plantão de dúvidas')
        self.assertContains(page, 'Ver gravação')
        self.assertContains(page, 'Horários de Brasília.')
        self.assertContains(page, 'id="dlg-session-%d"' % LiveSession.objects.get().id)
        self.assertContains(page, 'id="dlg-session-new"')

    def test_empty_list_message(self):
        self.assertContains(self.client.get(reverse('painel:course_settings', args=[self.course.id])), 'Nenhum encontro marcado.')

    def test_edit_existing(self):
        self.client.post(self.save_url, self.data(), **AJAX)
        session = LiveSession.objects.get()
        LiveSession.objects.filter(pk=session.pk).update(reminder_sent_at=timezone.now())
        self.client.post(self.save_url, self.data(session_id=session.id, title='Novo título', start='10:00', end='11:00'), **AJAX)
        session.refresh_from_db()
        self.assertEqual(session.title, 'Novo título')
        self.assertEqual(session.starts_at.isoformat(), '2027-05-10T13:00:00+00:00')
        self.assertIsNone(session.reminder_sent_at)
        self.assertEqual(LiveSession.objects.count(), 1)

    def test_validation(self):
        bad = {'title': {'title': ''}, 'date': {'date': ''}, 'end': {'end': '18:00'}, 'meet': {'meet_url': 'meet'},
               'recording': {'recording_url': 'x'}}
        for name, overrides in bad.items():
            response = self.client.post(self.save_url, self.data(**overrides), **AJAX)
            self.assertEqual(response.status_code, 400, name)
        self.assertEqual(LiveSession.objects.count(), 0)

    def test_cannot_edit_session_of_another_course(self):
        other = Course.objects.create(title='Outro', slug='outro', creator=self.owner.creator_profile)
        session = LiveSession.objects.create(course=other, title='Alheio', starts_at=timezone.now(), ends_at=timezone.now() + timedelta(hours=1))
        response = self.client.post(self.save_url, self.data(session_id=session.id), **AJAX)
        self.assertEqual(response.status_code, 404)

    def test_delete(self):
        self.client.post(self.save_url, self.data(), **AJAX)
        session = LiveSession.objects.get()
        self.client.post(reverse('painel:live_session_delete', args=[session.id]), **AJAX)
        self.assertEqual(LiveSession.objects.count(), 0)

    def test_student_forbidden(self):
        self.login(self.jane)
        self.assertEqual(self.client.post(self.save_url, self.data()).status_code, 403)


class DeleteCourseTests(B4Base):
    def url(self, course=None):
        return reverse('painel:course_delete', args=[(course or self.course).id])

    def test_blocked_with_students_or_orders(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.course)
        response = self.client.post(self.url(), {'confirmar': 'BLS'}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())
        Enrollment.objects.all().delete()
        Order.objects.create(student=self.jane.student_profile, course=self.course, amount=150)
        self.assertEqual(self.client.post(self.url(), {'confirmar': 'BLS'}, **AJAX).status_code, 400)
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())

    def test_requires_acronym(self):
        response = self.client.post(self.url(), {'confirmar': 'errado'}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertIn('confirmar', response.json()['errors'])
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())

    def test_deletes_empty_course_with_content(self):
        data = self.client.post(self.url(), {'confirmar': 'bls'}, **AJAX).json()
        self.assertEqual(data['redirect'], reverse('painel:courses'))
        self.assertFalse(Course.objects.filter(pk=self.course.pk).exists())
        self.assertFalse(Lesson.all_objects.filter(module__title='Fundamentos').exists())
        self.assertTrue(ActivityLog.objects.filter(text='Curso BLS foi excluído').exists())

    def test_without_js_goes_to_list_with_toast(self):
        response = self.client.post(self.url(), {'confirmar': 'BLS'}, follow=True)
        self.assertContains(response, 'Curso excluído')

    def test_button_disabled_when_course_has_students(self):
        page = self.client.get(reverse('painel:course_settings', args=[self.course.id]))
        self.assertNotContains(page, 'aria-describedby="delete-why"')
        self.assertContains(page, 'id="dlg-delete"')
        Enrollment.objects.create(student=self.jane.student_profile, course=self.course)
        page = self.client.get(reverse('painel:course_settings', args=[self.course.id]))
        self.assertContains(page, 'aria-describedby="delete-why"')
        self.assertContains(page, 'Este curso tem alunos ou pedidos. Arquive o curso em vez de excluir.')
        self.assertNotContains(page, 'id="dlg-delete"')

    def test_get_and_student(self):
        self.assertEqual(self.client.get(self.url()).status_code, 405)
        self.login(self.jane)
        self.assertEqual(self.client.post(self.url(), {'confirmar': 'BLS'}).status_code, 403)


class RiskZoneTests(B4Base):
    def test_move_to_draft_and_archive_from_settings(self):
        status_url = reverse('painel:course_status', args=[self.course.id])
        page = self.client.get(reverse('painel:course_settings', args=[self.course.id]))
        self.assertContains(page, 'Sai do site.')
        self.assertContains(page, 'id="dlg-archive"')
        self.assertContains(page, 'action="%s"' % status_url)
        self.client.post(status_url, {'para': 'draft'}, **AJAX)
        self.course.refresh_from_db()
        self.assertEqual(self.course.status, 'draft')
        page = self.client.get(reverse('painel:course_settings', args=[self.course.id]))
        self.assertNotContains(page, 'Sai do site.')

    def test_archived_course_hides_archive_action(self):
        Course.objects.filter(pk=self.course.pk).update(status='archived')
        page = self.client.get(reverse('painel:course_settings', args=[self.course.id]))
        self.assertNotContains(page, 'id="dlg-archive"')
        self.assertNotContains(page, 'data-dialog-open="dlg-archive"')

    def test_students_count_wording(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.course)
        self.assertContains(self.client.get(reverse('painel:course_settings', args=[self.course.id])), 'O aluno matriculado continua assistindo.')


class JsContractTests(TestCase):
    def test_repeater_notifies_dirty_bar(self):
        from pathlib import Path
        from django.conf import settings
        source = Path(settings.BASE_DIR, 'static', 'js', 'ui.js').read_text(encoding='utf-8')
        self.assertIn('data-repeater-add], [data-repeater-remove]', source)
