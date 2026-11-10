import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core import mail, signing
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from courses.models import Certificate, Course, Enrollment, Lesson, Module
from sales.models import Order
from users.account import EMAIL_SALT

User = get_user_model()
PASSWORD = 'SenhaForte2026'
NEW_PASSWORD = 'NovaSenha2026x'
CPF = '529.982.247-25'
HEADERS = {'HTTP_X_REQUESTED_WITH': 'fetch'}


def image_file(name='foto.png', fmt='PNG', content_type='image/png', size=(20, 20)):
    buffer = io.BytesIO()
    Image.new('RGB', size, 'blue').save(buffer, fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


class A8Base(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.jane = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        self.ana = User.objects.create_user(username='ana', email='ana@example.com', password=PASSWORD)
        self.profile = self.jane.student_profile
        self.bls = self.make_course('BLS', 'Suporte Básico de Vida', 'bls')
        self.acls = self.make_course('ACLS', 'Suporte Avançado ACLS', 'acls')
        self.enroll_bls = Enrollment.objects.create(student=self.profile, course=self.bls)
        self.enroll_acls = Enrollment.objects.create(student=self.profile, course=self.acls)
        self.client.force_login(self.jane)

    def make_course(self, short, title, slug):
        course = Course.objects.create(title=title, short_name=short, slug=slug, creator=self.admin.creator_profile, status='published')
        Lesson.objects.create(module=Module.objects.create(course=course, title='Módulo', order=1), title=f'{short} aula', order=1)
        return course

    def fill_data(self):
        self.profile.full_name, self.profile.cpf = 'Jane Silva', '52998224725'
        self.profile.save()

    def page(self, **params):
        return self.client.get(reverse('settings'), params)

    def save(self, section, json_mode=True, files=None, **data):
        payload = {'section': section, **data, **(files or {})}
        return self.client.post(reverse('settings'), payload, **(HEADERS if json_mode else {}))


class LayoutTests(A8Base):
    def test_default_section_is_profile_when_data_is_complete(self):
        self.fill_data()
        self.assertEqual(self.page().context['section'], 'perfil')

    def test_default_section_is_certificate_when_name_or_cpf_is_missing(self):
        self.assertEqual(self.page().context['section'], 'certificado')
        self.profile.full_name = 'Jane Silva'
        self.profile.save()
        self.assertEqual(self.page().context['section'], 'certificado')

    def test_section_parameter_and_fallback(self):
        self.fill_data()
        for section in ('perfil', 'certificado', 'senha', 'pedidos', 'avisos'):
            self.assertEqual(self.page(secao=section).context['section'], section)
        self.assertEqual(self.page(secao='x').context['section'], 'perfil')

    def test_tabs_badges_and_current(self):
        html = self.page(secao='senha').content.decode()
        self.assertIn('aria-label="Seções da conta"', html)
        self.assertIn('aria-current="page">Senha e acesso', html)
        self.assertIn('Dados do certificado <span class="badge badge--warning">Pendente</span>', html)
        self.assertIn('Pedidos e acessos <span class="badge badge--gray">2</span>', html)
        self.fill_data()
        self.assertNotIn('badge--warning">Pendente', self.page().content.decode())

    def test_only_the_active_section_is_rendered(self):
        self.fill_data()
        html = self.page(secao='avisos').content.decode()
        self.assertIn('id="form-avisos"', html)
        for other in ('form-perfil', 'form-certificado', 'form-senha'):
            self.assertNotIn(f'id="{other}"', html)

    def test_dirty_bar_and_no_loose_save_buttons(self):
        self.fill_data()
        for section in ('perfil', 'certificado', 'avisos'):
            html = self.page(secao=section).content.decode()
            self.assertIn('id="dirtybar"', html)
            self.assertIn(f'data-dirtybar="dirtybar"', html)
            self.assertIn(f'form="form-{section}">Salvar alterações', html)
            self.assertEqual(html.count('Salvar alterações'), 1)
        html = self.page(secao='senha').content.decode()
        self.assertNotIn('id="dirtybar"', html)
        self.assertIn('Atualizar senha', html)
        self.assertNotIn('id="dirtybar"', self.page(secao='pedidos').content.decode())

    def test_staff_gets_only_profile_and_password(self):
        self.client.force_login(self.admin)
        html = self.page().content.decode()
        tabs = html.split('aria-label="Seções da conta"')[1].split('</nav>')[0]
        self.assertIn('Perfil', tabs)
        self.assertIn('Senha e acesso', tabs)
        for hidden in ('Dados do certificado', 'Pedidos e acessos', 'Avisos por e-mail'):
            self.assertNotIn(hidden, tabs)
        self.assertNotIn('Como prefere ser chamada(o)', html)
        self.assertEqual(self.page(secao='certificado').context['section'], 'perfil')
        self.assertEqual(self.save('avisos').status_code, 302)

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.page().status_code, 302)


class ProfileTests(A8Base):
    def test_texts(self):
        self.fill_data()
        html = self.page().content.decode()
        for text in ('Como prefere ser chamada(o)', 'Usado nas saudações e na comunidade.', 'E-mail de acesso',
                     'Trocar o e-mail pede confirmação no endereço novo.', 'WhatsApp', 'Só para avisos de aula ao vivo, se você permitir.',
                     'Trocar foto', 'JPG ou PNG até 2 MB. Aparece na comunidade.', 'enctype="multipart/form-data"', 'data-async'):
            self.assertIn(text, html, text)

    def test_save_name_and_whatsapp(self):
        response = self.save('perfil', email='jane@example.com', display_name='  Janinha  ', whatsapp='(67) 99999-0000')
        self.assertEqual(response.json(), {'ok': True, 'toast': 'Alterações salvas'})
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.display_name, self.profile.whatsapp), ('Janinha', '67999990000'))

    def test_invalid_whatsapp(self):
        data = self.save('perfil', email='jane@example.com', whatsapp='123').json()
        self.assertEqual(data['errors']['whatsapp'], ['Informe o WhatsApp com DDD, só números.'])

    def test_email_change_waits_for_confirmation(self):
        response = self.save('perfil', email='Nova@Example.com')
        self.jane.refresh_from_db()
        self.assertEqual((self.jane.email, self.jane.pending_email), ('jane@example.com', 'Nova@Example.com'))
        self.assertIn('Enviamos um link de confirmação para Nova@Example.com.', response.json()['toast'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['Nova@Example.com'])
        self.assertIn('/settings/email/', mail.outbox[0].body)
        self.assertIn('Aguardando confirmação de Nova@Example.com.', self.page(secao='perfil').content.decode())

    def test_same_email_does_not_send_anything_and_clears_pending(self):
        self.jane.pending_email = 'outro@example.com'
        self.jane.save()
        self.save('perfil', email='JANE@example.com')
        self.jane.refresh_from_db()
        self.assertEqual(self.jane.pending_email, '')
        self.assertEqual(len(mail.outbox), 0)

    def test_email_already_used_or_invalid(self):
        data = self.save('perfil', email='ANA@example.com').json()
        self.assertEqual(data['errors']['email'], ['Este e-mail já está em uso em outra conta.'])
        self.assertEqual(self.save('perfil', email='nao-e-email').json()['errors']['email'], ['Informe um e-mail válido.'])
        self.assertEqual(self.save('perfil', email='').json()['errors']['email'], ['Informe o e-mail de acesso.'])
        self.assertEqual(len(mail.outbox), 0)

    def test_photo_upload(self):
        response = self.save('perfil', email='jane@example.com', files={'avatar': image_file()})
        self.assertEqual(response.status_code, 200)
        self.jane.refresh_from_db()
        self.assertTrue(self.jane.avatar.name.startswith('avatars/'))
        self.assertIn('avatars/', self.page().content.decode())
        self.jane.avatar.delete(save=False)

    def test_photo_rejects_wrong_type_size_and_non_image(self):
        gif = image_file('foto.gif', 'GIF', 'image/gif')
        self.assertEqual(self.save('perfil', email='jane@example.com', files={'avatar': gif}).json()['errors']['avatar'], ['Envie uma imagem JPG ou PNG.'])
        big = SimpleUploadedFile('grande.png', image_file().read() + b'0' * (2 * 1024 * 1024 + 1), content_type='image/png')
        self.assertEqual(self.save('perfil', email='jane@example.com', files={'avatar': big}).json()['errors']['avatar'], ['A foto deve ter no máximo 2 MB.'])
        text = SimpleUploadedFile('a.png', b'nao sou imagem', content_type='image/png')
        self.assertEqual(self.save('perfil', email='jane@example.com', files={'avatar': text}).json()['errors']['avatar'], ['Envie uma imagem JPG ou PNG.'])
        self.jane.refresh_from_db()
        self.assertFalse(self.jane.avatar)

    def test_without_javascript(self):
        response = self.save('perfil', json_mode=False, email='jane@example.com', display_name='Jane')
        self.assertRedirects(response, reverse('settings') + '?secao=perfil', fetch_redirect_response=False)
        self.assertContains(self.page(secao='perfil'), 'Alterações salvas')

    def test_without_javascript_errors_are_rendered(self):
        response = self.save('perfil', json_mode=False, email='ana@example.com')
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Este e-mail já está em uso em outra conta.', status_code=400)
        self.assertContains(response, 'Corrija 1 campo para salvar.', status_code=400)
        self.assertContains(response, 'aria-invalid="true"', status_code=400)

    def test_json_summary(self):
        data = self.save('perfil', email='ana@example.com', whatsapp='1').json()
        self.assertEqual(data['error'], 'Corrija 2 campos para salvar.')

    def test_staff_can_change_email_and_photo(self):
        self.client.force_login(self.admin)
        response = self.save('perfil', email='admin@example.com', files={'avatar': image_file()})
        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.avatar)
        self.admin.avatar.delete(save=False)


class EmailConfirmTests(A8Base):
    def token(self, user=None, email='nova@example.com'):
        return signing.dumps({'u': (user or self.jane).pk, 'e': email}, salt=EMAIL_SALT)

    def confirm(self, token):
        return self.client.get(reverse('email_confirm', args=[token]), follow=True)

    def test_confirmation_updates_the_email(self):
        self.jane.pending_email = 'nova@example.com'
        self.jane.save()
        response = self.confirm(self.token())
        self.jane.refresh_from_db()
        self.assertEqual((self.jane.email, self.jane.pending_email), ('nova@example.com', ''))
        self.assertContains(response, 'E-mail de acesso atualizado')
        self.assertEqual(response.redirect_chain[-1][0], reverse('settings') + '?secao=perfil')

    def test_new_email_can_be_used_to_log_in(self):
        self.jane.pending_email = 'nova@example.com'
        self.jane.save()
        self.confirm(self.token())
        self.client.logout()
        self.assertTrue(self.client.login(username='nova@example.com', password=PASSWORD))

    def test_invalid_expired_or_mismatched_links(self):
        self.jane.pending_email = 'nova@example.com'
        self.jane.save()
        for token in ('lixo', self.token(self.ana), self.token(email='outra@example.com')):
            self.assertContains(self.confirm(token), 'Este link de confirmação não vale mais.')
        self.jane.refresh_from_db()
        self.assertEqual(self.jane.email, 'jane@example.com')

    def test_expired_token(self):
        self.jane.pending_email = 'nova@example.com'
        self.jane.save()
        token = self.token()
        with override_settings():
            from unittest import mock
            with mock.patch('users.account.EMAIL_MAX_AGE', -1):
                self.assertContains(self.confirm(token), 'Este link de confirmação não vale mais.')

    def test_email_taken_in_the_meantime(self):
        self.jane.pending_email = 'ana@example.com'
        self.jane.save()
        self.assertContains(self.confirm(self.token(email='ana@example.com')), 'Este e-mail já está em uso em outra conta.')

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('email_confirm', args=[self.token()])).status_code, 302)


class CertificateDataTests(A8Base):
    def test_page_texts_and_prefill(self):
        self.fill_data()
        html = self.page(secao='certificado').content.decode()
        for text in ('Dados do certificado', 'Esses dados vão impressos em todos os seus certificados. Depois de emitir um certificado, só o suporte consegue corrigir.',
                     'Com acentos, sem abreviar.', 'Só números ou com pontos, como preferir.', 'value="Jane Silva"', 'value="529.982.247-25"', 'data-cpf', 'CPF válido'):
            self.assertIn(text, html, text)
        self.assertNotIn('readonly', html)

    def test_pending_badge_counts_certificates(self):
        html = self.page(secao='certificado').content.decode()
        self.assertIn('Pendente para 2 certificados', html)
        Certificate.objects.create(enrollment=self.enroll_bls, code='ABC123DEF456', student_name='X', student_cpf=CPF.replace('.', '').replace('-', ''),
                                   course_title='BLS', completed_at=timezone.now())
        self.assertIn('Pendente para 1 certificado<', self.page(secao='certificado').content.decode().replace('</span>', '<'))

    def test_pending_badge_hidden_when_data_is_complete(self):
        self.fill_data()
        self.assertNotIn('Pendente para', self.page(secao='certificado').content.decode())

    def test_save(self):
        response = self.save('certificado', full_name='  Márcio   Hirade  ', cpf=CPF)
        self.assertEqual(response.json(), {'ok': True, 'toast': 'Alterações salvas'})
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.full_name, self.profile.cpf), ('Márcio Hirade', '52998224725'))

    def test_invalid_cpf(self):
        data = self.save('certificado', full_name='Márcio', cpf='111.111.111-11').json()
        self.assertEqual(data['errors']['cpf'], ['CPF inválido. Confira os números.'])
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.cpf)

    def test_fields_can_be_cleared_before_any_certificate(self):
        self.fill_data()
        self.save('certificado', full_name='', cpf='')
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.full_name)
        self.assertFalse(self.profile.cpf)

    def test_locked_after_a_certificate_was_issued(self):
        self.fill_data()
        Certificate.objects.create(enrollment=self.enroll_bls, code='ABC123DEF456', student_name='Jane Silva', student_cpf='52998224725',
                                   course_title='BLS', completed_at=timezone.now())
        html = self.page(secao='certificado').content.decode()
        self.assertEqual(html.count('readonly'), 2)
        self.assertIn('Já usado em certificado emitido. Para corrigir, fale com o suporte.', html)
        self.save('certificado', full_name='Outro Nome', cpf='111.444.777-35')
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.full_name, self.profile.cpf), ('Jane Silva', '52998224725'))

    def test_support_link_when_locked(self):
        from users.models import SiteSettings
        site = SiteSettings.load()
        site.whatsapp = '5567999999999'
        site.save()
        self.fill_data()
        Certificate.objects.create(enrollment=self.enroll_bls, code='ABC123DEF456', student_name='Jane', student_cpf='52998224725',
                                   course_title='BLS', completed_at=timezone.now())
        self.assertIn('https://wa.me/5567999999999', self.page(secao='certificado').content.decode())


class PasswordTests(A8Base):
    def change(self, json_mode=True, **overrides):
        data = {'password_old': PASSWORD, 'password_new': NEW_PASSWORD, 'password_confirm': NEW_PASSWORD, **overrides}
        return self.save('senha', json_mode=json_mode, **data)

    def test_page_markup(self):
        html = self.page(secao='senha').content.decode()
        for text in ('Senha atual', 'Nova senha', 'Confirmar nova senha', 'data-reveal="old_password"', 'data-reveal="new_password1"',
                     'data-pw-rules="new_password1"', 'Pelo menos 8 caracteres', 'Letras e números', 'Diferente da senha atual',
                     'data-diff-from="old_password"', 'Sair de todos os aparelhos', 'Use se você entrou em um computador que não é seu.',
                     'Sair dos outros aparelhos', reverse('logout_others'), 'Atualizar senha'):
            self.assertIn(text, html, text)

    def test_success_keeps_the_session_and_reloads(self):
        response = self.change()
        self.assertEqual(response.json(), {'ok': True, 'toast': 'Senha atualizada. Use a nova senha no próximo acesso', 'reload': True})
        self.jane.refresh_from_db()
        self.assertTrue(self.jane.check_password(NEW_PASSWORD))
        self.assertEqual(self.page(secao='senha').status_code, 200)

    def test_wrong_current_password(self):
        self.assertEqual(self.change(password_old='errada').json()['errors']['password_old'], ['Senha atual incorreta.'])
        self.jane.refresh_from_db()
        self.assertTrue(self.jane.check_password(PASSWORD))

    def test_new_password_rules(self):
        cases = {'curta1': 'A nova senha precisa ter pelo menos 8 caracteres.',
                 'somenteletras': 'Use letras e números na nova senha.',
                 PASSWORD: 'A nova senha precisa ser diferente da atual.'}
        for value, message in cases.items():
            data = self.change(password_new=value, password_confirm=value).json()
            self.assertEqual(data['errors']['password_new'], [message], value)

    def test_django_validators_still_apply(self):
        data = self.change(password_new='password123', password_confirm='password123').json()
        self.assertIn('password_new', data['errors'])

    def test_confirmation_must_match(self):
        data = self.change(password_confirm='Diferente2026').json()
        self.assertEqual(data['errors']['password_confirm'], ['A confirmação não é igual à nova senha.'])

    def test_required_fields(self):
        data = self.save('senha').json()
        self.assertEqual(set(data['errors']), {'password_old', 'password_new', 'password_confirm'})
        self.assertEqual(data['error'], 'Corrija 3 campos para salvar.')

    def test_without_javascript(self):
        response = self.change(json_mode=False)
        self.assertRedirects(response, reverse('settings') + '?secao=senha', fetch_redirect_response=False)
        self.assertContains(self.page(secao='senha'), 'Senha atualizada. Use a nova senha no próximo acesso')

    def test_without_javascript_errors_are_rendered(self):
        response = self.change(json_mode=False, password_old='errada')
        self.assertContains(response, 'Senha atual incorreta.', status_code=400)
        self.assertContains(response, 'Corrija 1 campo para salvar.', status_code=400)

    def test_logout_other_devices(self):
        other = Client()
        other.force_login(self.jane)
        stranger = Client()
        stranger.force_login(self.ana)
        self.assertEqual(Session.objects.count(), 3)
        response = self.client.post(reverse('logout_others'), **HEADERS)
        self.assertEqual(response.json(), {'ok': True, 'toast': 'Você saiu dos outros aparelhos. Este continua conectado'})
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        self.assertEqual(other.get(reverse('dashboard')).status_code, 302)
        self.assertEqual(stranger.get(reverse('dashboard')).status_code, 200)
        self.assertEqual(Session.objects.count(), 2)

    def test_logout_other_devices_without_javascript(self):
        response = self.client.post(reverse('logout_others'))
        self.assertRedirects(response, reverse('settings') + '?secao=senha', fetch_redirect_response=False)
        self.assertContains(self.page(secao='senha'), 'Você saiu dos outros aparelhos. Este continua conectado')

    def test_logout_others_requires_post_and_login(self):
        self.assertEqual(self.client.get(reverse('logout_others')).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.post(reverse('logout_others')).status_code, 302)


class AccessAndOrdersTests(A8Base):
    def rows(self):
        return {r['course'].slug: r for r in self.page(secao='pedidos').context['access_rows']}

    def test_origins(self):
        order = Order.objects.create(student=self.profile, course=self.bls, amount='150.00', status=Order.Status.COMPLETED)
        Enrollment.objects.filter(pk=self.enroll_bls.pk).update(source='purchase')
        Enrollment.objects.filter(pk=self.enroll_acls.pk).update(source='import', external_ref='HP1234')
        rows = self.rows()
        self.assertEqual(rows['bls']['origin'], f'Compra no site · #{order.id}')
        self.assertEqual(rows['acls']['origin'], 'Importado · HP1234')
        for source, expected in (('manual', 'Liberado pela equipe'), ('signup', 'Cadastro no site'), ('import', 'Importado')):
            Enrollment.objects.filter(pk=self.enroll_bls.pk).update(source=source, external_ref='')
            self.assertEqual(self.rows()['bls']['origin'], expected)

    def test_purchase_without_order_shows_plain_label(self):
        Enrollment.objects.filter(pk=self.enroll_bls.pk).update(source='purchase')
        self.assertEqual(self.rows()['bls']['origin'], 'Compra no site')

    def test_table_texts_and_access_badges(self):
        Enrollment.objects.filter(pk=self.enroll_acls.pk).update(expires_at=timezone.now() + timedelta(days=30))
        html = self.page(secao='pedidos').content.decode()
        for text in ('De onde veio cada curso da sua conta.', 'Curso', 'Origem', 'Liberado em', 'Acesso', 'Vitalício',
                     'Algum curso que você comprou não aparece?', 'Suporte Básico de Vida', 'table--w640'):
            self.assertIn(text, html, text)
        self.assertIn(f'Até {(timezone.now() + timedelta(days=30)).astimezone(timezone.get_current_timezone()):%d/%m/%Y}', html)

    def test_support_link(self):
        from users.models import SiteSettings
        site = SiteSettings.load()
        site.whatsapp = '5567999999999'
        site.save()
        html = self.page(secao='pedidos').content.decode()
        self.assertIn('Avisar o suporte', html)
        self.assertIn('https://wa.me/5567999999999', html)

    def test_inactive_and_archived_courses_are_not_listed(self):
        self.enroll_acls.is_active = False
        self.enroll_acls.save()
        self.bls.status = 'archived'
        self.bls.save()
        self.assertEqual(self.rows(), {})
        self.assertContains(self.page(secao='pedidos'), 'Você ainda não tem cursos.')

    def test_orders_table(self):
        self.assertContains(self.page(secao='pedidos'), 'Você ainda não tem pedidos.')
        Order.objects.create(student=self.profile, course=self.bls, amount='150.00', status=Order.Status.COMPLETED)
        html = self.page(secao='pedidos').content.decode()
        self.assertIn('Meus pedidos', html)
        self.assertIn('R$ 150,00', html)
        self.assertNotIn('Você ainda não tem pedidos.', html)

    def test_other_students_orders_are_not_shown(self):
        Order.objects.create(student=self.ana.student_profile, course=self.bls, amount='999.00', status=Order.Status.COMPLETED)
        self.assertNotContains(self.page(secao='pedidos'), '999,00')

    def test_this_section_has_no_form_to_post(self):
        self.assertEqual(self.save('pedidos').status_code, 302)


class NoticesTests(A8Base):
    def test_switches_reflect_profile(self):
        self.profile.notify_marketing = False
        self.profile.notify_live = False
        self.profile.save()
        html = self.page(secao='avisos').content.decode()
        for text in ('Respostas às minhas dúvidas', 'Quando o instrutor ou outro aluno responder.', 'Lembrete de aula ao vivo',
                     '1 hora antes, com o link do Google Meet.', 'Certificado pronto', 'Quando você concluir um curso.',
                     'Novos cursos e condições especiais', 'No máximo 2 por mês.'):
            self.assertIn(text, html, text)
        self.assertIn('aria-labelledby="lbl-answers" data-switch-input="notify_answers"', html)
        self.assertEqual(html.count('role="switch" aria-checked="true"'), 2)
        self.assertEqual(html.count('role="switch" aria-checked="false"'), 2)
        self.assertIn('name="notify_live" id="notify_live" value="0"', html)
        self.assertIn('name="notify_answers" id="notify_answers" value="1"', html)

    def test_save(self):
        response = self.save('avisos', notify_answers='0', notify_live='1', notify_certificate='0', notify_marketing='1')
        self.assertEqual(response.json(), {'ok': True, 'toast': 'Alterações salvas'})
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.notify_answers, self.profile.notify_live, self.profile.notify_certificate, self.profile.notify_marketing),
                         (False, True, False, True))

    def test_missing_values_turn_everything_off(self):
        self.save('avisos')
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.notify_answers or self.profile.notify_live or self.profile.notify_certificate or self.profile.notify_marketing)

    def test_preferences_drive_email_sending(self):
        from users.notify import notify
        self.save('avisos', notify_answers='0', notify_live='1', notify_certificate='1', notify_marketing='0')
        jane = User.objects.get(pk=self.jane.pk)
        notify(jane, 'answer', 'Resposta', '', '/community/')
        self.assertEqual(len(mail.outbox), 0)
        notify(jane, 'live', 'Aula', '', '/ao-vivo/')
        self.assertEqual(len(mail.outbox), 1)
