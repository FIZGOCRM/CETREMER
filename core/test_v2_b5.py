import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import ActivityLog
from courses.models import Certificate, Course, Enrollment, Lesson, Module, Progress
from painel import import_views, students_stats
from sales.models import Order
from users.models import FirstAccessCode

User = get_user_model()
PASSWORD = 'StrongPassword123!'
AJAX = {'HTTP_X_REQUESTED_WITH': 'fetch'}
CPF = '52998224725'


class B5Base(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='dono', email='dono@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.inst = User.objects.create_user(username='inst', email='inst@example.com', password=PASSWORD, role=User.Role.CREATOR)
        self.bls = Course.objects.create(title='Suporte Básico de Vida', short_name='BLS', slug='bls',
                                         creator=self.owner.creator_profile, status='published')
        self.acls = Course.objects.create(title='ACLS', short_name='ACLS', slug='acls', creator=self.owner.creator_profile, status='published')
        module = Module.objects.create(course=self.bls, title='M1', order=1)
        self.l1 = Lesson.objects.create(module=module, title='Aula 1', order=1)
        self.l2 = Lesson.objects.create(module=module, title='Aula 2', order=2)
        self.l3 = Lesson.objects.create(module=module, title='Rascunho', order=3, status='draft')
        self.jane = self.student('jane', 'Jane Souza', CPF)
        self.ana = self.student('ana', 'Ana Lima', '')
        self.nunca = self.student('nunca', '', '')
        self.login(self.owner)

    def student(self, username, name, cpf, password=True):
        user = User.objects.create_user(username=username, email=f'{username}@example.com', password=PASSWORD if password else None)
        if not password:
            user.set_unusable_password()
            user.save()
        profile = user.student_profile
        profile.full_name = name
        profile.cpf = cpf or None
        profile.save()
        return user

    def login(self, user):
        self.client.force_login(user)

    def enroll(self, user, course=None, **kwargs):
        return Enrollment.objects.create(student=user.student_profile, course=course or self.bls, **kwargs)

    def done(self, user, *lessons):
        for lesson in lessons:
            Progress.objects.create(student=user.student_profile, lesson=lesson, is_completed=True)


class ListTests(B5Base):
    def get(self, **params):
        return self.client.get(reverse('painel:students'), params)

    def test_header_line_and_empty_state(self):
        self.enroll(self.jane)
        self.enroll(self.jane, self.acls)
        self.enroll(self.ana)
        page = self.get()
        self.assertContains(page, '3 alunos · 3 matrículas em 2 cursos')
        self.assertContains(page, 'Importar CSV')
        self.assertContains(page, 'Matricular aluno')
        User.objects.filter(role=User.Role.STUDENT).delete()
        page = self.get()
        self.assertContains(page, 'Nenhum aluno ainda')
        self.assertContains(page, 'Importe a lista da Eduzz ou da Hotmart, ou matricule alguém manualmente.')

    def test_row_content(self):
        self.enroll(self.jane)
        self.done(self.jane, self.l1)
        User.objects.filter(pk=self.jane.pk).update(last_login=timezone.now() - timedelta(hours=1))
        page = self.get()
        self.assertContains(page, 'Jane Souza')
        self.assertContains(page, 'jane@example.com')
        self.assertContains(page, 'aria-valuenow="50"')
        self.assertContains(page, 'Ativo')
        self.assertContains(page, '<span class="text-danger">Nunca acessou</span>')
        self.assertContains(page, reverse('painel:student_detail', args=[self.jane.id]))
        self.assertContains(page, 'Mostrando 3 de 3 alunos')

    def test_status_labels(self):
        self.enroll(self.ana)
        rows = {row['user'].username: row for row in self.get().context['rows']}
        self.assertEqual(rows['ana']['status'], 'waiting')
        self.assertEqual(rows['jane']['status'], 'none')
        self.assertContains(self.get(), 'Aguardando 1º acesso')
        self.assertContains(self.get(), 'Sem cursos')
        Progress.objects.create(student=self.ana.student_profile, lesson=self.l1)
        rows = {row['user'].username: row for row in self.get().context['rows']}
        self.assertEqual(rows['ana']['status'], 'active')

    def test_filters_and_counts(self):
        self.enroll(self.jane)
        self.enroll(self.ana)
        self.done(self.jane, self.l1, self.l2)
        Progress.objects.filter(student=self.jane.student_profile).update(updated_at=timezone.now())
        counts = students_stats.filter_counts()
        self.assertEqual(counts, {'todos': 3, 'ativos': 1, 'nunca': 2, 'concluiram': 1, 'sem-dados': 2, 'importados-hoje': 0})
        names = lambda name: sorted(r['user'].username for r in self.get(filtro=name).context['rows'])
        self.assertEqual(names('ativos'), ['jane'])
        self.assertEqual(names('nunca'), ['ana', 'nunca'])
        self.assertEqual(names('concluiram'), ['jane'])
        self.assertEqual(names('sem-dados'), ['ana', 'nunca'])
        self.assertEqual(names('todos'), ['ana', 'jane', 'nunca'])
        self.assertEqual(names('invalido'), ['ana', 'jane', 'nunca'])

    def test_active_filter_ignores_old_activity(self):
        self.enroll(self.jane)
        self.done(self.jane, self.l1)
        Progress.objects.update(updated_at=timezone.now() - timedelta(days=40))
        self.assertEqual(students_stats.filter_counts()['ativos'], 0)

    def test_imported_today_chip_only_after_import(self):
        self.assertNotContains(self.get(), 'Importados hoje')
        self.enroll(self.jane, source='import')
        self.assertContains(self.get(), 'Importados hoje 1')
        self.assertEqual([r['user'].username for r in self.get(filtro='importados-hoje').context['rows']], ['jane'])
        Enrollment.objects.update(enrolled_at=timezone.now() - timedelta(days=2))
        self.assertNotContains(self.get(), 'Importados hoje')

    def test_completed_ignores_removed_access(self):
        self.enroll(self.jane, is_active=False)
        self.done(self.jane, self.l1, self.l2)
        self.assertEqual(students_stats.filter_counts()['concluiram'], 0)

    def test_search_by_name_email_and_cpf(self):
        for q, expected in (('jane', ['jane']), ('Souza', ['jane']), ('ana@exam', ['ana']), ('529.982.247-25', ['jane']), ('52998', ['jane']), ('zzz', [])):
            self.assertEqual([r['user'].username for r in self.get(q=q).context['rows']], expected, q)
        self.assertContains(self.get(q='zzz'), 'Nenhum aluno com "zzz"')
        self.assertContains(self.get(q='zzz'), 'Limpar filtros')

    def test_course_filter_by_slug_or_id_only_active(self):
        self.enroll(self.jane)
        self.enroll(self.ana, is_active=False)
        for value in ('bls', str(self.bls.id)):
            self.assertEqual([r['user'].username for r in self.get(curso=value).context['rows']], ['jane'], value)
        self.assertContains(self.get(curso='acls', q='x'), 'no curso ACLS')

    def test_pagination_25_per_page(self):
        for n in range(30):
            self.student(f's{n:02d}', f'Aluno {n:02d}', '')
        first = self.get()
        self.assertEqual(len(first.context['rows']), 25)
        self.assertContains(first, 'Mostrando 25 de 33 alunos')
        self.assertContains(first, 'Próxima')
        self.assertNotContains(first, 'Anterior')
        second = self.get(pagina=2)
        self.assertEqual(len(second.context['rows']), 8)
        self.assertContains(second, 'Anterior')

    def test_query_count_does_not_grow(self):
        self.get()
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as small:
            self.get()
        for n in range(12):
            user = self.student(f'x{n}', f'X {n}', '')
            self.enroll(user)
        with CaptureQueriesContext(connection) as big:
            self.get()
        self.assertLessEqual(len(big), len(small) + 4)

    def test_access_rules(self):
        self.login(self.inst)
        self.assertEqual(self.get().status_code, 200)
        self.login(self.jane)
        self.assertEqual(self.get().status_code, 403)

    def test_bulk_bar_contract(self):
        self.enroll(self.jane)
        page = self.get()
        for text in ('data-bulk data-bulkbar="bulkbar-alunos"', 'id="bulkbar-alunos"', 'Liberar curso', 'Reenviar acesso', 'Exportar',
                     'Remover de um curso', 'Limpar seleção', 'data-bulk-item', 'data-bulk-all', 'Digite REMOVER para confirmar'):
            self.assertContains(page, text)


class BulkTests(B5Base):
    def post(self, action, *users, **extra):
        data = {'action': action, 'ids': [u.id for u in users], 'next': reverse('painel:students') + '?filtro=nunca'}
        data.update(extra)
        return self.client.post(reverse('painel:students'), data, follow=True)

    def test_enroll_toast_with_real_total(self):
        response = self.post('enroll', self.jane, self.ana, course=self.bls.id)
        self.assertContains(response, '2 alunos receberam o BLS')
        self.assertEqual(Enrollment.objects.filter(course=self.bls, is_active=True).count(), 2)
        self.assertEqual(response.request['QUERY_STRING'], 'filtro=nunca')
        self.assertEqual(ActivityLog.objects.filter(verb='enrolled').count(), 2)
        self.assertContains(self.post('enroll', self.nunca, course=self.bls.id), '1 aluno recebeu o BLS')

    def test_enroll_reactivates_removed_access_keeping_progress(self):
        self.enroll(self.jane, is_active=False)
        self.done(self.jane, self.l1)
        self.post('enroll', self.jane, course=self.bls.id)
        self.assertTrue(Enrollment.objects.get(student=self.jane.student_profile).is_active)
        self.assertEqual(Progress.objects.filter(student=self.jane.student_profile).count(), 1)

    def test_resend_counts_and_reports_failures(self):
        response = self.post('resend', self.jane, self.ana)
        self.assertContains(response, 'Acesso reenviado para 2 alunos')
        self.assertEqual(len(mail.outbox), 2)
        self.jane.student_profile.refresh_from_db()
        self.assertIsNotNone(self.jane.student_profile.access_email_sent_at)
        with patch('painel.access.send_mail', side_effect=OSError('smtp')):
            response = self.post('resend', self.jane, self.ana)
        self.assertContains(response, '2 alunos falharam.')
        self.assertContains(response, 'Baixar relatório')
        report = self.client.get(reverse('painel:students_report'))
        self.assertIn('jane@example.com,E-mail de acesso não enviado', report.content.decode())

    def test_export_selected_only(self):
        self.enroll(self.jane)
        response = self.client.post(reverse('painel:students'), {'action': 'export', 'ids': [self.jane.id]})
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        body = response.content.decode()
        self.assertIn('Jane Souza,jane@example.com,52998224725,Suporte Básico de Vida', body)
        self.assertNotIn('ana@example.com', body)

    def test_unenroll_requires_confirmation_word(self):
        self.enroll(self.jane)
        response = self.post('unenroll', self.jane, remove_course=self.bls.id, confirmar='x')
        self.assertContains(response, 'Digite REMOVER para confirmar a remoção de acesso.')
        self.assertTrue(Enrollment.objects.get(student=self.jane.student_profile).is_active)

    def test_unenroll_keeps_progress_and_can_notify(self):
        self.enroll(self.jane)
        self.enroll(self.ana)
        self.done(self.jane, self.l1)
        response = self.post('unenroll', self.jane, self.ana, self.nunca, remove_course=self.bls.id, confirmar='remover', notify='1')
        self.assertContains(response, '2 alunos perderam o acesso ao BLS. O progresso foi guardado.')
        self.assertContains(response, '1 aluno falhou.')
        self.assertFalse(Enrollment.objects.get(student=self.jane.student_profile).is_active)
        self.assertEqual(Progress.objects.filter(student=self.jane.student_profile).count(), 1)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('foi removido', mail.outbox[0].subject)

    def test_enroll_uses_its_own_course_field(self):
        self.enroll(self.jane)
        self.post('enroll', self.ana, course=self.acls.id, remove_course=self.bls.id)
        self.assertTrue(Enrollment.objects.filter(student=self.ana.student_profile, course=self.acls).exists())
        self.assertFalse(Enrollment.objects.filter(student=self.ana.student_profile, course=self.bls).exists())

    def test_no_selection_and_bad_action(self):
        self.assertContains(self.client.post(reverse('painel:students'), {'action': 'enroll'}, follow=True), 'Selecione pelo menos um aluno.')
        self.assertContains(self.post('apagar', self.jane), 'Ação inválida.')

    def test_next_must_stay_in_students(self):
        response = self.client.post(reverse('painel:students'), {'action': 'resend', 'ids': [self.jane.id], 'next': 'https://evil.example/'})
        self.assertRedirects(response, reverse('painel:students'), fetch_redirect_response=False)

    def test_ignores_staff_ids(self):
        self.post('enroll', self.owner, course=self.bls.id)
        self.assertEqual(Enrollment.objects.count(), 0)

    def test_student_cannot_bulk(self):
        self.login(self.jane)
        self.assertEqual(self.client.post(reverse('painel:students'), {'action': 'enroll', 'ids': [self.ana.id], 'course': self.bls.id}).status_code, 403)


class EnrollDialogTests(B5Base):
    url = property(lambda self: reverse('painel:student_enroll'))

    def test_creates_student_enrolls_and_opens_detail(self):
        data = self.client.post(self.url, {'email': 'Nova@Example.com', 'full_name': 'Nova Aluna', 'course': self.bls.id, 'send_email': '1'}, **AJAX).json()
        user = User.objects.get(email='nova@example.com')
        self.assertEqual(data['redirect'], reverse('painel:student_detail', args=[user.id]))
        self.assertEqual((user.role, user.student_profile.full_name, user.has_usable_password()), ('STUDENT', 'Nova Aluna', False))
        enrollment = Enrollment.objects.get(student=user.student_profile)
        self.assertEqual((enrollment.course, enrollment.source, enrollment.is_active), (self.bls, 'manual', True))
        self.assertEqual(len(mail.outbox), 1)
        page = self.client.get(data['redirect'])
        self.assertContains(page, 'Curso liberado. E-mail enviado para nova@example.com')
        self.assertTrue(ActivityLog.objects.filter(text='Nova Aluna foi matriculado em BLS', actor=self.owner).exists())

    def test_without_email_message_and_first_access_code(self):
        response = self.client.post(self.url, {'email': 'sem@example.com', 'course': self.bls.id}, follow=True)
        self.assertContains(response, 'Curso liberado')
        self.assertNotContains(response, 'E-mail enviado')
        self.assertRegex(response.content.decode(), r'\b\d{10}\b')
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(FirstAccessCode.objects.filter(user__email='sem@example.com').exists())

    def test_existing_student_with_access_gets_info(self):
        self.enroll(self.jane)
        response = self.client.post(self.url, {'email': 'jane@example.com', 'course': self.bls.id}, follow=True)
        self.assertContains(response, 'Jane Souza já tem acesso ao BLS.')
        self.assertEqual(Enrollment.objects.filter(student=self.jane.student_profile).count(), 1)

    def test_reactivates_removed_access(self):
        self.enroll(self.jane, is_active=False)
        self.client.post(self.url, {'email': 'jane@example.com', 'course': self.bls.id}, follow=True)
        self.assertTrue(Enrollment.objects.get(student=self.jane.student_profile).is_active)

    def test_validation(self):
        for data, field in (({'email': 'nao-e-email', 'course': self.bls.id}, 'email'), ({'email': 'a@example.com', 'course': ''}, 'course'),
                            ({'email': 'inst@example.com', 'course': self.bls.id}, 'email')):
            response = self.client.post(self.url, data, **AJAX)
            self.assertEqual(response.status_code, 400, data)
            self.assertIn(field, response.json()['errors'])
        self.assertFalse(User.objects.filter(email='a@example.com').exists())

    def test_access_rules(self):
        self.login(self.inst)
        self.assertEqual(self.client.post(self.url, {'email': 'novo@example.com', 'course': self.bls.id}, **AJAX).status_code, 200)
        self.login(self.jane)
        self.assertEqual(self.client.post(self.url, {'email': 'x@example.com', 'course': self.bls.id}).status_code, 403)


class DetailTests(B5Base):
    def url(self, user=None, **params):
        return reverse('painel:student_detail', args=[(user or self.jane).id])

    def get(self, user=None, **params):
        return self.client.get(self.url(user), params)

    def action(self, user=None, **data):
        return self.client.post(reverse('painel:student_action', args=[(user or self.jane).id]), data, **AJAX)

    def test_header_and_tabs(self):
        self.enroll(self.jane, source='manual')
        Order.objects.create(student=self.jane.student_profile, course=self.bls, amount=150)
        page = self.get()
        self.assertContains(page, 'Jane Souza')
        self.assertContains(page, 'jane@example.com · aluno desde')
        self.assertContains(page, 'liberado pelo admin')
        for text in ('Reenviar e-mail de acesso', 'Liberar curso', 'Editar dados', 'Enviar link para criar nova senha'):
            self.assertContains(page, text)
        for aba in ('Cursos', 'Pedidos', 'Certificados', 'Atividade'):
            self.assertContains(page, aba)
        self.assertEqual(page.context['counts'], {'cursos': 1, 'pedidos': 1, 'certificados': 0, 'atividade': 0})
        self.assertContains(page, '<a href="%s">Alunos</a> / Jane Souza' % reverse('painel:students'))

    def test_courses_tab_lessons_and_progress(self):
        self.enroll(self.jane)
        self.done(self.jane, self.l1)
        page = self.get()
        self.assertContains(page, '1 de 2 aulas')
        self.assertContains(page, 'Ver aulas')
        self.assertContains(page, 'concluída hoje')
        self.assertContains(page, 'não assistida')
        self.assertContains(page, 'rascunho, não visível')
        self.assertContains(page, 'Desmarcar')
        self.assertContains(page, 'Marcar concluída')
        self.assertContains(page, 'Zerar progresso do curso')
        self.assertContains(page, 'Remover acesso a este curso')

    def test_empty_courses(self):
        self.assertContains(self.get(), 'Nenhum curso liberado')

    def test_orders_certificates_activity_tabs(self):
        enrollment = self.enroll(self.jane)
        self.assertContains(self.get(aba='pedidos'), 'Nenhum pedido deste aluno')
        self.assertContains(self.get(aba='certificados'), 'Nenhum certificado emitido')
        self.assertContains(self.get(aba='atividade'), 'Nenhuma atividade registrada')
        Order.objects.create(student=self.jane.student_profile, course=self.bls, amount=150)
        Certificate.objects.create(enrollment=enrollment, code='CERT01', student_name='Jane', student_cpf=CPF, course_title='BLS', completed_at=timezone.now())
        ActivityLog.objects.create(verb='enrolled', text='Jane Souza foi matriculado em BLS', student=self.jane)
        self.assertContains(self.get(aba='pedidos'), '#')
        self.assertContains(self.get(aba='certificados'), 'CERT01')
        self.assertContains(self.get(aba='atividade'), 'Jane Souza foi matriculado em BLS')

    def test_personal_data_alerts(self):
        page = self.get(self.nunca)
        self.assertContains(page, 'Não informado')
        self.assertContains(page, 'Sem CPF o certificado fica bloqueado.')
        self.assertContains(page, 'Pedir ao aluno por e-mail')
        self.assertNotContains(self.get(), 'Sem CPF o certificado fica bloqueado.')

    def test_access_card_and_notes(self):
        page = self.get()
        self.assertContains(page, 'Nunca acessou')
        self.assertContains(page, 'ainda não')
        self.assertContains(page, 'ainda não enviado')
        self.assertContains(page, 'data-autosave-url="%s"' % reverse('painel:student_notes', args=[self.jane.id]))
        self.assertContains(page, 'Salva automaticamente.')
        profile = self.jane.student_profile
        profile.first_access_at = timezone.now()
        profile.access_email_sent_at = timezone.now()
        profile.save()
        page = self.get()
        self.assertContains(page, 'feito em')
        self.assertContains(page, 'enviado em')

    def test_notes_autosave(self):
        response = self.client.post(reverse('painel:student_notes', args=[self.jane.id]), {'notes': 'Pediu certificado por WhatsApp'}, **AJAX)
        self.assertTrue(response.json()['ok'])
        self.jane.student_profile.refresh_from_db()
        self.assertEqual(self.jane.student_profile.staff_notes, 'Pediu certificado por WhatsApp')
        self.assertContains(self.get(), 'Pediu certificado por WhatsApp')

    def test_only_students_have_a_detail(self):
        self.assertEqual(self.client.get(reverse('painel:student_detail', args=[self.owner.id])).status_code, 404)
        self.login(self.jane)
        self.assertEqual(self.get().status_code, 403)
        self.login(self.inst)
        self.assertEqual(self.get().status_code, 200)

    def test_toggle_lesson_with_undo(self):
        self.enroll(self.jane)
        data = self.action(action='toggle_lesson', lesson=self.l1.id).json()
        self.assertEqual(data['toast'], 'Aula marcada como concluída para Jane Souza')
        self.assertTrue(Progress.objects.get(student=self.jane.student_profile, lesson=self.l1).is_completed)
        self.assertIn('1 de 2 aulas', data['replace']['#scourse-progress-%d' % self.bls.id])
        self.assertIn('aria-expanded="true"', data['replace']['#scourse-progress-%d' % self.bls.id])
        undo = data['undo_url']
        self.assertIn('desfazer=1', undo)
        self.client.post(undo, **AJAX)
        self.assertFalse(Progress.objects.get(student=self.jane.student_profile, lesson=self.l1).is_completed)
        data = self.action(action='toggle_lesson', lesson=self.l1.id).json()
        self.action(action='toggle_lesson', lesson=self.l1.id)
        self.assertEqual(self.action(action='toggle_lesson', lesson=self.l1.id).json()['toast'], 'Aula marcada como concluída para Jane Souza')

    def test_toggle_message_when_unmarking(self):
        self.enroll(self.jane)
        self.done(self.jane, self.l1)
        self.assertEqual(self.action(action='toggle_lesson', lesson=self.l1.id).json()['toast'], 'Aula desmarcada para Jane Souza')

    def test_toggle_rejects_draft_or_missing_enrollment(self):
        self.enroll(self.jane)
        self.assertEqual(self.action(action='toggle_lesson', lesson=self.l3.id).status_code, 400)
        self.assertEqual(self.action(self.ana, action='toggle_lesson', lesson=self.l1.id).status_code, 400)

    def test_unenroll_keeps_progress_and_certificate(self):
        enrollment = self.enroll(self.jane)
        self.done(self.jane, self.l1)
        Certificate.objects.create(enrollment=enrollment, code='KEEP', student_name='Jane', student_cpf=CPF, course_title='BLS', completed_at=timezone.now())
        response = self.client.post(reverse('painel:student_action', args=[self.jane.id]), {'action': 'unenroll', 'course_id': self.bls.id, 'notify': '1'}, follow=True)
        self.assertContains(response, 'Acesso removido. O progresso foi mantido.')
        enrollment.refresh_from_db()
        self.assertFalse(enrollment.is_active)
        self.assertEqual(Progress.objects.filter(student=self.jane.student_profile).count(), 1)
        self.assertTrue(Certificate.objects.filter(code='KEEP').exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertContains(response, 'Acesso removido')
        self.assertNotContains(response, 'Remover acesso a este curso')
        self.assertEqual(self.action(action='unenroll', course_id=self.bls.id).status_code, 400)

    def test_removed_student_no_longer_sees_course(self):
        self.enroll(self.jane)
        self.action(action='unenroll', course_id=self.bls.id)
        self.login(self.jane)
        self.assertNotEqual(self.client.get(reverse('course_home', args=['bls'])).status_code, 200)
        self.assertNotEqual(self.client.get(reverse('lesson_detail', args=['bls', self.l1.id])).status_code, 200)

    def test_reset_progress(self):
        self.enroll(self.jane)
        self.done(self.jane, self.l1, self.l2)
        other = Course.objects.create(title='Outro', slug='outro', creator=self.owner.creator_profile)
        module = Module.objects.create(course=other, title='M', order=1)
        keep = Lesson.objects.create(module=module, title='Fica', order=1)
        self.done(self.jane, keep)
        response = self.client.post(reverse('painel:student_action', args=[self.jane.id]), {'action': 'reset_progress', 'course_id': self.bls.id}, follow=True)
        self.assertContains(response, 'Progresso de Jane Souza zerado no BLS')
        self.assertEqual(Progress.objects.filter(student=self.jane.student_profile).count(), 1)
        self.assertContains(self.get(), 'As 0 aulas concluídas voltam')

    def test_resend_and_reset_password_toasts(self):
        response = self.client.post(reverse('painel:student_action', args=[self.jane.id]), {'action': 'resend_access'}, follow=True)
        self.assertContains(response, 'E-mail de acesso enviado para jane@example.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/senha/nova/', mail.outbox[0].body)
        response = self.client.post(reverse('painel:student_action', args=[self.jane.id]), {'action': 'reset_password'}, follow=True)
        self.assertContains(response, 'Link para criar nova senha enviado para jane@example.com')

    def test_request_data_email(self):
        response = self.client.post(reverse('painel:student_action', args=[self.nunca.id]), {'action': 'request_data'}, follow=True)
        self.assertContains(response, 'Pedido enviado para nunca@example.com')
        self.assertIn('/settings/?secao=certificado', mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['nunca@example.com'])

    def test_edit_data(self):
        self.assertTrue(self.action(self.nunca, action='edit', full_name='Maria Nova', cpf='529.982.247-25', email='MARIA@example.com').json()['ok'])
        self.nunca.refresh_from_db()
        profile = self.nunca.student_profile
        profile.refresh_from_db()
        self.assertEqual((profile.full_name, profile.cpf, self.nunca.email), ('Maria Nova', CPF, 'maria@example.com'))
        self.action(self.nunca, action='edit', full_name='', cpf='', email='maria@example.com')
        profile.refresh_from_db()
        self.assertEqual(profile.full_name, '')
        self.assertFalse(profile.cpf)

    def test_edit_validation(self):
        response = self.action(action='edit', full_name='Jane', cpf='111.111.111-11', email='ana@example.com')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()['errors']), {'cpf', 'email'})
        self.assertEqual(self.action(action='edit', email='invalido').status_code, 400)
        self.jane.refresh_from_db()
        self.assertEqual(self.jane.email, 'jane@example.com')

    def test_generate_first_access_only_without_password(self):
        pending = self.student('pend', 'Pendente', '', password=False)
        response = self.client.post(reverse('painel:student_action', args=[pending.id]), {'action': 'generate_first_access'}, follow=True)
        self.assertRegex(response.content.decode(), r'\b\d{10}\b')
        self.assertContains(self.get(pending), 'Gerar código de primeiro acesso')
        self.assertNotContains(self.get(), 'Gerar código de primeiro acesso')
        response = self.client.post(reverse('painel:student_action', args=[self.jane.id]), {'action': 'generate_first_access'}, follow=True)
        self.assertContains(response, 'Este aluno já tem senha.')

    def test_invalid_action_and_get(self):
        self.assertEqual(self.action(action='explodir').status_code, 400)
        self.assertEqual(self.client.get(reverse('painel:student_action', args=[self.jane.id])).status_code, 405)

    def test_enroll_dialog_prefilled_with_open_courses_only(self):
        self.enroll(self.jane)
        page = self.get()
        self.assertContains(page, 'Liberar curso para Jane Souza')
        self.assertContains(page, 'name="email" value="jane@example.com"')
        options = page.content.decode().split('id="es-course"')[1].split('</select>')[0]
        self.assertIn('ACLS', options)
        self.assertNotIn('Suporte Básico de Vida', options)

    def test_first_login_is_recorded_once(self):
        self.assertIsNone(self.jane.student_profile.first_access_at)
        self.client.logout()
        self.assertTrue(self.client.login(username='jane', password=PASSWORD))
        self.jane.student_profile.refresh_from_db()
        first = self.jane.student_profile.first_access_at
        self.assertIsNotNone(first)
        self.client.logout()
        self.client.login(username='jane', password=PASSWORD)
        self.jane.student_profile.refresh_from_db()
        self.assertEqual(self.jane.student_profile.first_access_at, first)


class ImportParsingTests(TestCase):
    def upload(self, content, name='alunos.csv'):
        data = content.encode('utf-8') if isinstance(content, str) else content
        return SimpleUploadedFile(name, data, content_type='text/csv')

    def test_comma_semicolon_and_latin1(self):
        for text in ('Nome,Email,CPF\nAna,ana@x.com,1\n', 'Nome;Email;CPF\nAna;ana@x.com;1\n'):
            headers, rows = import_views.parse_upload(self.upload(text))
            self.assertEqual((headers, rows[0][:2]), (['Nome', 'Email', 'CPF'], ['Ana', 'ana@x.com']))
        headers, rows = import_views.parse_upload(self.upload('Nome;Email\nJosé;jose@x.com\n'.encode('latin-1')))
        self.assertEqual(rows[0][0], 'José')

    def test_rejections(self):
        for content in ('', '   \n', 'Nome,Email\n'):
            with self.assertRaises(ValueError):
                import_views.parse_upload(self.upload(content))
        with self.assertRaises(ValueError):
            import_views.parse_upload(self.upload('a,b\n' + 'x,y\n' * (5 * 1024 * 1024 // 4 + 10)))

    def test_pads_short_rows_and_skips_blank_lines(self):
        headers, rows = import_views.parse_upload(self.upload('Nome,Email,CPF\nAna,ana@x.com\n,,\n\nBia,bia@x.com,2\n'))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ['Ana', 'ana@x.com', ''])

    def test_guess_mapping(self):
        mapping = import_views.guess_mapping(['Nome do Comprador', 'E-mail', 'CPF/CNPJ', 'Código do pedido', 'Valor'])
        self.assertEqual(mapping, {'0': 'name', '1': 'email', '2': 'cpf', '3': 'order', '4': 'ignore'})
        self.assertEqual(import_views.guess_mapping(['Email', 'Email do cliente'])['1'], 'ignore')

    def test_evaluate_statuses(self):
        owner = User.objects.create_user(username='s', email='staff@x.com', password=PASSWORD, role=User.Role.ADMIN)
        old = User.objects.create_user(username='old', email='old@x.com', password=PASSWORD)
        rows = [['A', 'novo@x.com', CPF, 'P1'], ['B', 'OLD@x.com', '', ''], ['C', 'sem-arroba', '', ''], ['D', 'novo@x.com', '', ''],
                ['E', 'staff@x.com', '', ''], ['F', 'cpf@x.com', '123', ''], ['G', '', '', '']]
        parsed = import_views.evaluate(rows, {'0': 'name', '1': 'email', '2': 'cpf', '3': 'order'})
        self.assertEqual([r['status'] for r in parsed], ['new', 'existing', 'invalid', 'duplicate', 'other_account', 'new', 'invalid'])
        self.assertEqual(parsed[0]['cpf'], CPF)
        self.assertEqual(parsed[0]['order'], 'P1')
        self.assertEqual(parsed[5]['cpf'], '')
        self.assertEqual(parsed[5]['note'], 'CPF inválido, não será importado')
        summary = import_views.summarize(parsed)
        self.assertEqual((summary['new'], summary['existing'], summary['ignored'], summary['total_ok']), (2, 1, 4, 3))
        self.assertEqual(summary['problems_total'], 5)
        self.assertEqual(old.email, 'old@x.com')
        self.assertEqual(owner.role, 'ADMIN')


class ImportFlowTests(B5Base):
    url = property(lambda self: reverse('painel:students_import'))
    CSV = ('Nome,Email,CPF,Pedido\nAna Nova,ana.nova@x.com,52998224725,#9001\nBia Nova,bia.nova@x.com,,#9002\n'
           'Jane Souza,jane@example.com,,#9003\nRuim,sem-arroba,,\nBia Nova,bia.nova@x.com,,\n')

    def upload(self, text=None, origin='hotmart'):
        file = SimpleUploadedFile('alunos.csv', (text or self.CSV).encode('utf-8'), content_type='text/csv')
        return self.client.post(self.url, {'origin': origin, 'file': file})

    def to_step(self, step, **overrides):
        self.upload()
        if step >= 3:
            self.client.post(self.url + '?passo=2', {'col_0': 'name', 'col_1': 'email', 'col_2': 'cpf', 'col_3': 'order'})
        if step >= 4:
            data = {'courses': [self.bls.id, self.acls.id]}
            data.update(overrides)
            self.client.post(self.url + '?passo=3', data)

    def test_step_one_page(self):
        page = self.client.get(self.url)
        for text in ('Nada é importado até você confirmar no último passo.', 'Arquivo', 'Colunas', 'Cursos', 'Revisar', 'Eduzz', 'Hotmart',
                     'Outra planilha', 'Envie o CSV exportado', 'Como exportar da Eduzz', 'Como exportar da Hotmart'):
            self.assertContains(page, text)
        self.assertContains(page, 'stepper__item is-current')

    def test_upload_moves_to_columns_with_recognition(self):
        response = self.upload()
        self.assertRedirects(response, self.url + '?passo=2', fetch_redirect_response=False)
        page = self.client.get(self.url + '?passo=2')
        self.assertContains(page, 'Reconhecemos 4 de 4 colunas. Ajuste se algo estiver errado.')
        self.assertContains(page, 'Código do pedido')
        self.assertContains(page, 'Ana Nova')
        self.assertContains(page, 'E-mail é obrigatório. Nome e CPF são opcionais, mas o certificado só sai com os dois.')
        self.assertContains(page, 'Passo 2 de 4')
        self.assertContains(page, 'stepper__item is-done')

    def test_step_guard_without_state(self):
        for step in (2, 3, 4):
            self.assertContains(self.client.get(self.url + '?passo=%d' % step), 'Envie o CSV exportado')

    def test_step_guard_cannot_skip_ahead(self):
        self.upload()
        self.assertContains(self.client.get(self.url + '?passo=4'), 'Reconhecemos')

    def test_upload_errors(self):
        response = self.client.post(self.url, {'origin': 'eduzz'}, follow=True)
        self.assertContains(response, 'Escolha o arquivo CSV para continuar.')
        empty = SimpleUploadedFile('vazio.csv', b'', content_type='text/csv')
        self.assertContains(self.client.post(self.url, {'file': empty}, follow=True), 'O arquivo está vazio.')

    def test_columns_validation(self):
        self.upload()
        response = self.client.post(self.url + '?passo=2', {'col_0': 'name', 'col_1': 'ignore', 'col_2': 'cpf', 'col_3': 'ignore'}, follow=True)
        self.assertContains(response, 'Escolha qual coluna é o e-mail.')
        response = self.client.post(self.url + '?passo=2', {'col_0': 'email', 'col_1': 'email', 'col_2': 'cpf', 'col_3': 'ignore'}, follow=True)
        self.assertContains(response, 'Cada tipo de coluna só pode ser usado uma vez.')
        self.assertContains(self.client.get(self.url + '?passo=3'), 'Reconhecemos')

    def test_courses_step(self):
        self.to_step(3)
        page = self.client.get(self.url + '?passo=3')
        self.assertContains(page, 'Liberar acesso a')
        self.assertContains(page, 'Enviar e-mail de acesso agora')
        self.assertContains(page, 'Passo 3 de 4')
        self.assertContains(self.client.post(self.url + '?passo=3', {}, follow=True), 'Escolha pelo menos um curso.')
        Course.objects.filter(pk=self.acls.pk).update(status='archived')
        self.client.post(self.url + '?passo=3', {'courses': [self.acls.id, self.bls.id]})
        self.assertEqual(self.client.session['student_import']['course_ids'], [self.bls.id])

    def test_review_numbers_and_problem_rows(self):
        self.to_step(4)
        page = self.client.get(self.url + '?passo=4')
        summary = page.context['summary']
        self.assertEqual((summary['new'], summary['existing'], summary['ignored']), (2, 1, 2))
        self.assertContains(page, 'Importar 3 alunos')
        self.assertContains(page, 'E-mail inválido')
        self.assertContains(page, 'E-mail repetido no arquivo')
        self.assertContains(page, 'data-busy-label="Importando 3 alunos…"')
        self.assertContains(page, 'Passo 4 de 4')
        self.assertEqual(User.objects.filter(email='ana.nova@x.com').count(), 0)

    def confirm(self, **overrides):
        self.to_step(4, **overrides)
        return self.client.post(self.url + '?passo=4', {}, follow=True)

    def test_confirm_imports_enrolls_and_redirects(self):
        response = self.confirm()
        self.assertEqual(response.request['QUERY_STRING'], 'filtro=importados-hoje')
        self.assertContains(response, '2 novos, 1 já existia e recebeu os cursos, 2 ignorados')
        ana = User.objects.get(email='ana.nova@x.com')
        self.assertEqual((ana.role, ana.has_usable_password(), ana.student_profile.full_name, ana.student_profile.cpf), ('STUDENT', False, 'Ana Nova', CPF))
        enrollments = Enrollment.objects.filter(student=ana.student_profile)
        self.assertEqual({(e.course_id, e.source, e.external_ref) for e in enrollments}, {(self.bls.id, 'import', '#9001'), (self.acls.id, 'import', '#9001')})
        self.assertEqual(Enrollment.objects.filter(student=self.jane.student_profile).count(), 2)
        self.assertTrue(ActivityLog.objects.filter(verb='imported', text='3 alunos importados').exists())
        self.assertNotIn('student_import', self.client.session)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_does_not_overwrite_existing_data(self):
        self.to_step(2)
        text = 'Nome,Email,CPF\nOutro Nome,jane@example.com,111.444.777-35\nNome Novo,ana@example.com,111.444.777-35\n'
        self.upload(text)
        self.client.post(self.url + '?passo=2', {'col_0': 'name', 'col_1': 'email', 'col_2': 'cpf'})
        self.client.post(self.url + '?passo=3', {'courses': [self.bls.id]})
        self.client.post(self.url + '?passo=4', {})
        self.jane.student_profile.refresh_from_db()
        self.ana.student_profile.refresh_from_db()
        self.assertEqual((self.jane.student_profile.full_name, self.jane.student_profile.cpf), ('Jane Souza', CPF))
        self.assertEqual((self.ana.student_profile.full_name, self.ana.student_profile.cpf), ('Ana Lima', '11144477735'))

    def test_confirm_with_email_only_for_new_or_passwordless(self):
        self.confirm(send_email='1')
        recipients = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(recipients, ['ana.nova@x.com', 'bia.nova@x.com'])

    def test_confirm_reactivates_removed_access(self):
        self.enroll(self.jane, is_active=False)
        self.confirm()
        self.assertTrue(Enrollment.objects.get(student=self.jane.student_profile, course=self.bls).is_active)

    def test_singular_toast(self):
        self.upload('Email\nsozinho@x.com\n')
        self.client.post(self.url + '?passo=2', {'col_0': 'email'})
        self.client.post(self.url + '?passo=3', {'courses': [self.bls.id]})
        response = self.client.post(self.url + '?passo=4', {}, follow=True)
        self.assertContains(response, '1 novo, 0 já existiam e receberam os cursos, 0 ignorados')

    def test_confirm_without_state_goes_to_start(self):
        self.assertRedirects(self.client.post(self.url + '?passo=4', {}), self.url, fetch_redirect_response=False)

    def test_restart_clears_state(self):
        self.upload()
        self.client.post(self.url, {'action': 'restart'})
        self.assertNotIn('student_import', self.client.session)

    def test_access_rules(self):
        self.login(self.inst)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.login(self.jane)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url + '?passo=4', {}).status_code, 403)


class JsContractTests(TestCase):
    def test_new_ui_hooks_exist(self):
        from pathlib import Path
        from django.conf import settings
        source = Path(settings.BASE_DIR, 'static', 'js', 'ui.js').read_text(encoding='utf-8')
        for hook in ('data-toggle-target', 'form[data-busy-label]'):
            self.assertIn(hook, source)
        json.loads('{}')
