import json
import re
import shutil
import subprocess
from datetime import timedelta
from pathlib import Path
from unittest import mock, skipUnless

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Certificate, Course, Enrollment, Lesson, Module, Progress
from users.models import SiteSettings

User = get_user_model()
PASSWORD = 'StrongPassword123!'
CPF = '529.982.247-25'


class A6Base(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.jane = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        self.profile = self.jane.student_profile
        self.bls = self.make_course('BLS', 'Suporte Básico de Vida', 'bls', 3, workload=4)
        self.acls = self.make_course('ACLS', 'Suporte Avançado ACLS', 'acls', 2)
        self.enroll_bls = Enrollment.objects.create(student=self.profile, course=self.bls)
        self.enroll_acls = Enrollment.objects.create(student=self.profile, course=self.acls)
        self.client.force_login(self.jane)

    def make_course(self, short, title, slug, lessons, workload=None):
        course = Course.objects.create(title=title, short_name=short, slug=slug, creator=self.admin.creator_profile,
                                       status='published', workload_hours=workload)
        module = Module.objects.create(course=course, title='Módulo', order=1)
        for number in range(1, lessons + 1):
            Lesson.objects.create(module=module, title=f'{short} aula {number}', order=number)
        return course

    def lessons(self, course):
        return list(Lesson.objects.filter(module__course=course).order_by('order'))

    def mark(self, lesson, completed=True):
        return Progress.objects.update_or_create(student=self.profile, lesson=lesson, defaults={'is_completed': completed})[0]

    def finish(self, course, upto=None):
        for lesson in self.lessons(course)[:upto]:
            self.mark(lesson)

    def fill_data(self):
        self.profile.full_name, self.profile.cpf = 'Jane Silva', '52998224725'
        self.profile.save()

    def listing(self, **params):
        return self.client.get(reverse('certificates'), params)

    def issue(self, course=None, json_mode=True, **data):
        course = course or self.bls
        payload = {'full_name': 'Jane da Silva', 'cpf': CPF, 'confirm': '1', **data}
        payload = {k: v for k, v in payload.items() if v is not None}
        extra = {'HTTP_X_REQUESTED_WITH': 'fetch'} if json_mode else {}
        return self.client.post(reverse('certificate_issue', args=[course.slug]), payload, **extra)


class ListTests(A6Base):
    def test_stats_and_ordering(self):
        self.finish(self.bls)
        self.fill_data()
        done = self.make_course('PALS', 'Suporte Avançado PALS', 'pals', 1)
        enrollment = Enrollment.objects.create(student=self.profile, course=done)
        self.mark(self.lessons(done)[0])
        Certificate.objects.create(enrollment=enrollment, code='ABC123DEF456', student_name='Jane', student_cpf='52998224725',
                                   course_title='PALS', completed_at=timezone.now())
        response = self.listing()
        self.assertEqual(response.context['stats'], {'issued': 1, 'ready': 1, 'in_progress': 1})
        self.assertEqual([i['state'] for i in response.context['items']], ['ready', 'issued', 'progress'])
        html = response.content.decode()
        self.assertIn('Emitidos', html)
        self.assertIn('Prontos para emitir', html)
        self.assertIn('Em andamento', html)
        self.assertIn('text-success">1<', html)

    def test_ready_number_is_not_green_when_zero(self):
        self.assertNotIn('text-success">0<', self.listing().content.decode())

    def test_empty_state(self):
        Enrollment.objects.all().delete()
        self.assertContains(self.listing(), 'Você ainda não tem certificados')

    def test_hidden_courses(self):
        self.acls.certificate_enabled = False
        self.acls.save()
        self.enroll_bls.is_active = False
        self.enroll_bls.save()
        self.assertEqual(self.listing().context['items'], [])
        self.enroll_bls.is_active = True
        self.enroll_bls.save()
        self.bls.status = 'archived'
        self.bls.save()
        self.assertEqual(self.listing().context['items'], [])

    def test_staff_goes_to_painel(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.listing(), reverse('painel:dashboard'), fetch_redirect_response=False)

    def test_verification_card(self):
        html = self.listing().content.decode()
        self.assertIn('Qualquer pessoa pode conferir se um certificado CETREMER é verdadeiro pelo código, sem precisar de login.', html)
        self.assertIn('Página de verificação', html)

    def test_progress_card_texts(self):
        self.mark(self.lessons(self.bls)[0])
        html = self.listing().content.decode()
        self.assertIn('badge badge--blue">Em andamento', html)
        self.assertIn('badge badge--gray">Não iniciado', html)
        self.assertIn('Concluir as 3 aulas · faltam 2 aulas.', html)
        self.assertIn('Informar nome completo e CPF · <a class="link-strong"', html)
        self.assertIn('completar agora', html)
        self.assertIn('1 de 3 aulas', html)
        self.assertIn('Continuar curso', html)
        self.assertNotIn('Conferir dados e emitir', html)
        self.fill_data()
        self.assertIn('Nome e CPF informados', self.listing().content.decode())

    def test_progress_card_links_to_resume_lesson(self):
        second = self.lessons(self.bls)[1]
        self.mark(self.lessons(self.bls)[0])
        Progress.objects.create(student=self.profile, lesson=second, position_seconds=50)
        self.assertContains(self.listing(), reverse('lesson_detail', args=['bls', second.id]))

    def test_draft_lessons_do_not_block_readiness(self):
        Lesson.objects.create(module=self.bls.modules.first(), title='Rascunho', order=9, status='draft')
        self.finish(self.bls)
        self.assertEqual(self.listing().context['stats']['ready'], 1)

    def test_query_count_does_not_grow(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        self.listing()
        with CaptureQueriesContext(connection) as few:
            self.listing()
        for index in range(4):
            course = self.make_course(f'C{index}', f'Curso {index}', f'c{index}', 2)
            Enrollment.objects.create(student=self.profile, course=course)
        with CaptureQueriesContext(connection) as many:
            self.listing()
        self.assertEqual(len(few), len(many))


class ReadyCardAndDrawerTests(A6Base):
    def setUp(self):
        super().setUp()
        self.finish(self.bls)

    def test_ready_card(self):
        html = self.listing().content.decode()
        self.assertIn('Pronto para emitir', html)
        self.assertIn('cert-row is-ready', html)
        self.assertIn('3 de 3 aulas concluídas', html)
        self.assertIn('Confira nome e CPF antes de emitir', html)
        self.assertIn('data-drawer-open="drawer-emitir-bls"', html)
        self.assertIn('Conferir dados e emitir', html)

    def test_no_data_warning_when_profile_is_complete(self):
        self.fill_data()
        self.assertNotIn('Confira nome e CPF antes de emitir', self.listing().content.decode())

    def test_only_ready_courses_get_a_drawer(self):
        html = self.listing().content.decode()
        self.assertIn('id="drawer-emitir-bls"', html)
        self.assertNotIn('id="drawer-emitir-acls"', html)

    def test_autoopen_only_for_matching_ready_course(self):
        self.assertIn('data-autoopen="emitir"', self.listing(emitir='bls').content.decode())
        self.assertNotIn('data-autoopen', self.listing().content.decode())
        self.assertNotIn('data-autoopen', self.listing(emitir='acls').content.decode())
        self.assertNotIn('data-autoopen', self.listing(emitir='nao-existe').content.decode())
        self.assertEqual(self.listing(emitir='bls').context['open_issue'], 'bls')

    def test_drawer_contents(self):
        html = self.listing().content.decode()
        for text in ('Emitir certificado', 'Esses dados vão impressos no certificado. Depois de emitido, só o suporte consegue corrigir.',
                     'Do jeito que está no seu documento, com acentos.', 'Prévia do texto', 'Conferi meu nome e CPF',
                     'Cancelar', 'CPF válido', f'action="{reverse("certificate_issue", args=["bls"])}"', 'data-async',
                     'data-cpf', 'data-mirror="#preview-cpf-bls"', 'data-mirror-cpf', 'data-mirror="#preview-name-bls"',
                     'data-mirror-upper', 'name="confirm"', 'NOME COMPLETO', '***.***.***-**',
                     'com carga horária de 4 horas'):
            self.assertIn(text, html, text)

    def test_drawer_is_prefilled_and_preview_masks_cpf(self):
        self.fill_data()
        html = self.listing().content.decode()
        self.assertIn('value="Jane Silva"', html)
        self.assertIn('value="529.982.247-25"', html)
        self.assertIn('>JANE SILVA</strong>', html)
        self.assertIn('***.982.247-**', html)
        self.assertNotIn('529.982.247-25</span>', html)

    def test_preview_has_no_workload_clause_when_missing(self):
        self.finish(self.acls)
        html = self.listing().content.decode()
        drawer = html.split('id="drawer-emitir-acls"')[1].split('</dialog>')[0]
        self.assertNotIn('carga horária', drawer)


class IssuedCardTests(A6Base):
    def setUp(self):
        super().setUp()
        self.finish(self.bls)
        self.fill_data()
        self.certificate = Certificate.objects.create(enrollment=self.enroll_bls, code='2A0E307CF993', student_name='Jane Silva',
                                                      student_cpf='52998224725', course_title='Suporte Básico de Vida',
                                                      workload_hours=4, completed_at=timezone.now())

    def test_issued_card(self):
        html = self.listing().content.decode()
        self.assertIn('badge badge--success">', html)
        self.assertIn('Emitido', html)
        self.assertIn(f'Emitido em {timezone.localtime(self.certificate.issued_at):%d/%m/%Y} · código 2A0E-307C-F993 · carga horária 4h', html)
        self.assertIn(reverse('issue_certificate', args=['bls']) + '?imprimir=1', html)
        self.assertIn('Baixar PDF', html)
        self.assertIn('Certificado de conclusão', html)
        self.assertNotIn('Conferir dados e emitir', html)
        self.assertNotIn('id="drawer-emitir-bls"', html)

    def test_copy_link_and_linkedin(self):
        html = self.listing().content.decode()
        verify = 'http://testserver/certificado/verificar/?codigo=2A0E307CF993'
        self.assertIn(f'data-copy="{verify}" data-copy-toast="Link de verificação copiado"', html)
        self.assertIn('Copiar link de verificação', html)
        self.assertIn('https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME', html)
        self.assertIn('name=Suporte+B%C3%A1sico+de+Vida', html)
        self.assertIn('organizationName=CETREMER', html)
        self.assertIn('certId=2A0E307CF993', html)
        self.assertIn('certUrl=http%3A%2F%2Ftestserver%2Fcertificado%2Fverificar%2F%3Fcodigo%3D2A0E307CF993', html)
        self.assertIn(f'issueYear={timezone.localtime(self.certificate.issued_at).year}', html)
        self.assertIn('Adicionar ao LinkedIn', html)

    def test_linkedin_uses_school_name(self):
        site = SiteSettings.load()
        site.school_name = 'Escola X'
        site.save()
        self.assertIn('organizationName=Escola+X', self.listing().content.decode())


class IssueTests(A6Base):
    def setUp(self):
        super().setUp()
        self.finish(self.bls)

    def test_success_creates_certificate_updates_profile_and_sends_email(self):
        response = self.issue()
        self.assertEqual(response.json(), {'ok': True, 'toast': 'Certificado emitido. Enviamos o link para seu e-mail', 'reload': True})
        certificate = Certificate.objects.get(enrollment=self.enroll_bls)
        self.assertEqual((certificate.student_name, certificate.student_cpf, certificate.course_title, certificate.workload_hours),
                         ('Jane da Silva', '52998224725', 'Suporte Básico de Vida', 4))
        self.assertRegex(certificate.code, r'^[0-9A-F]{12}$')
        self.profile.refresh_from_db()
        self.assertEqual((self.profile.full_name, self.profile.cpf), ('Jane da Silva', '52998224725'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['jane@example.com'])
        self.assertIn('http://testserver/courses/bls/certificate/', mail.outbox[0].body)
        self.assertIn(f'codigo={certificate.code}', mail.outbox[0].body)

    def test_completion_date_comes_from_progress(self):
        last = Progress.objects.filter(student=self.profile).order_by('-updated_at').first()
        past = timezone.now() - timedelta(days=9)
        Progress.objects.filter(student=self.profile).update(updated_at=past)
        self.issue()
        self.assertEqual(Certificate.objects.get().completed_at.date(), past.date())
        self.assertIsNotNone(last)

    def test_name_is_normalized(self):
        self.issue(full_name='  Jane    da   Silva ')
        self.assertEqual(Certificate.objects.get().student_name, 'Jane da Silva')

    def test_second_post_does_not_duplicate_or_resend(self):
        self.issue()
        again = self.issue(full_name='Outro Nome')
        self.assertEqual(again.json()['toast'], 'Certificado emitido. Enviamos o link para seu e-mail')
        self.assertEqual(Certificate.objects.count(), 1)
        self.assertEqual(Certificate.objects.get().student_name, 'Jane da Silva')
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_cpf_returns_field_error_and_creates_nothing(self):
        response = self.issue(cpf='529.982.247-26')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['ok'])
        self.assertEqual(data['errors']['cpf'], ['CPF inválido. Confira os números.'])
        self.assertEqual(Certificate.objects.count(), 0)
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.cpf)

    def test_required_fields(self):
        data = self.issue(full_name='', cpf='', confirm=None).json()
        self.assertEqual(set(data['errors']), {'full_name', 'cpf', 'confirm'})
        self.assertEqual(data['errors']['confirm'], ['Confirme que conferiu seu nome e CPF.'])
        self.assertEqual(data['errors']['full_name'], ['Informe seu nome completo.'])
        self.assertEqual(data['error'], 'Corrija 3 campos para salvar.')

    def test_course_must_be_finished(self):
        Progress.objects.filter(student=self.profile).delete()
        response = self.issue()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Conclua todas as aulas para emitir o certificado.')
        self.assertEqual(Certificate.objects.count(), 0)

    def test_draft_lessons_do_not_block_issue(self):
        Lesson.objects.create(module=self.bls.modules.first(), title='Rascunho', order=9, status='draft')
        self.assertEqual(self.issue().status_code, 200)

    def test_access_rules(self):
        self.assertEqual(self.client.get(reverse('certificate_issue', args=['bls'])).status_code, 405)
        self.assertEqual(self.issue(self.make_course('X', 'Outro', 'outro', 1)).status_code, 404)
        self.enroll_bls.is_active = False
        self.enroll_bls.save()
        self.assertEqual(self.issue().status_code, 404)
        self.enroll_bls.is_active = True
        self.enroll_bls.save()
        self.bls.certificate_enabled = False
        self.bls.save()
        self.assertEqual(self.issue().status_code, 404)
        self.bls.certificate_enabled = True
        self.bls.save()
        self.client.force_login(self.admin)
        self.assertEqual(self.issue(json_mode=False).status_code, 302)
        self.assertEqual(Certificate.objects.count(), 0)
        self.client.logout()
        self.assertEqual(self.issue().status_code, 302)

    def test_without_javascript_success_redirects_with_toast(self):
        response = self.issue(json_mode=False)
        self.assertRedirects(response, reverse('certificates'), fetch_redirect_response=False)
        self.assertContains(self.client.get(reverse('certificates')), 'Certificado emitido. Enviamos o link para seu e-mail')
        self.assertEqual(Certificate.objects.count(), 1)

    def test_without_javascript_error_reopens_the_panel(self):
        response = self.issue(json_mode=False, cpf='111.111.111-11')
        self.assertRedirects(response, reverse('certificates') + '?emitir=bls', fetch_redirect_response=False)
        page = self.client.get(reverse('certificates') + '?emitir=bls')
        self.assertContains(page, 'CPF inválido. Confira os números.')
        self.assertContains(page, 'data-autoopen="emitir"')
        self.assertEqual(Certificate.objects.count(), 0)

    def test_email_failure_does_not_break_issue(self):
        with mock.patch('courses.certificate_views.send_mail', side_effect=OSError('smtp fora do ar')), \
                self.assertLogs('courses.certificate_views', 'ERROR'):
            response = self.issue()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Certificate.objects.count(), 1)

    def test_listing_shows_issued_after_issue(self):
        self.issue()
        self.assertEqual(self.listing().context['stats']['issued'], 1)
        self.assertEqual(self.listing().context['stats']['ready'], 0)


class CertificatePageTests(A6Base):
    def url(self, course=None):
        return reverse('issue_certificate', args=[(course or self.bls).slug])

    def test_opening_the_page_never_issues(self):
        self.finish(self.bls)
        self.fill_data()
        response = self.client.get(self.url())
        self.assertEqual(Certificate.objects.count(), 0)
        self.assertContains(response, 'Certificado Bloqueado')
        self.assertContains(response, 'Conferir dados e emitir')
        self.assertContains(response, reverse('certificates') + '?emitir=bls')

    def test_pending_requirements_have_no_check_icon(self):
        html = self.client.get(self.url()).content.decode()
        self.assertEqual(html.count('req-item__mark'), 2)
        self.assertNotIn('icon--check', html)
        self.assertNotIn('is-ok', html)
        self.assertIn('Concluir 100% das aulas · 0 de 3 aulas · faltam 3 aulas.', html)
        self.assertIn('Completar em Minha conta', html)
        self.assertNotIn('Conferir dados e emitir', html)
        self.assertIn('Continuar o curso', html)

    def test_ok_requirement_shows_check_only_there(self):
        self.finish(self.bls)
        html = self.client.get(self.url()).content.decode()
        self.assertEqual(html.count('icon--check'), 1)
        self.assertEqual(html.count('req-item is-ok'), 1)
        self.assertIn('Conferir dados e emitir', html)
        self.assertNotIn('Continuar o curso', html)
        self.fill_data()
        html = self.client.get(self.url()).content.decode()
        self.assertEqual(html.count('icon--check'), 2)

    def test_issued_certificate_is_shown(self):
        self.finish(self.bls)
        self.client.post(reverse('certificate_issue', args=['bls']), {'full_name': 'Jane Silva', 'cpf': CPF, 'confirm': '1'})
        response = self.client.get(self.url())
        self.assertContains(response, 'CERTIFICADO')
        self.assertContains(response, 'Jane Silva')
        self.assertContains(response, 'codigo=')

    def test_access_rules(self):
        other = self.make_course('X', 'Outro', 'outro', 1)
        self.assertRedirects(self.client.get(self.url(other)), reverse('course_preview', args=['outro']))
        self.bls.certificate_enabled = False
        self.bls.save()
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(self.url()), reverse('course_preview', args=['bls']), fetch_redirect_response=False)


@skipUnless(shutil.which('node'), 'node não está instalado')
class CpfScriptTests(TestCase):
    def test_client_side_check_matches_server_rules(self):
        source = (Path(settings.BASE_DIR) / 'static' / 'js' / 'ui.js').read_text(encoding='utf-8')
        function = re.search(r'function validCpf[\s\S]*?\n  }\n', source).group(0)
        values = ['529.982.247-25', '52998224725', '111.111.111-11', '52998224726', '', '123', '000.000.000-00']
        script = function + '\nconsole.log(JSON.stringify(' + json.dumps(values) + '.map(validCpf)));'
        output = subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(output), [True, True, False, False, False, False, False])
