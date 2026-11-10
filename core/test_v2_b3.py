import json
import tempfile
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from courses.models import Course, Enrollment, Lesson, LessonMaterial, Module, Progress
from courses.services import course_progress
from users.models import SiteSettings

User = get_user_model()
PASSWORD = 'StrongPassword123!'
AJAX = {'HTTP_X_REQUESTED_WITH': 'fetch'}
MEDIA = override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='cetremer-test-'))


class B3Base(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='dono', email='dono@example.com', password=PASSWORD,
                                              role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.inst = User.objects.create_user(username='inst', email='inst@example.com', password=PASSWORD, role=User.Role.CREATOR)
        self.jane = User.objects.create_user(username='jane', email='jane@example.com', password=PASSWORD)
        self.course = Course.objects.create(title='Suporte Básico de Vida', short_name='BLS', slug='bls',
                                            creator=self.owner.creator_profile, status='published', price=150, workload_hours=4)
        self.m1 = Module.objects.create(course=self.course, title='Fundamentos', order=1)
        self.m2 = Module.objects.create(course=self.course, title='Prática', order=2)
        self.l1 = Lesson.objects.create(module=self.m1, title='Introdução', order=1, video_url='https://vimeo.com/76979871', duration_seconds=480)
        self.l2 = Lesson.objects.create(module=self.m1, title='Compressões', order=2, video_url='https://www.youtube.com/watch?v=abcdefghijk')
        self.l3 = Lesson.objects.create(module=self.m1, title='Rascunho sem vídeo', order=3, status='draft')
        self.l4 = Lesson.objects.create(module=self.m2, title='Simulação', order=1, video_url='https://vimeo.com/76979872', duration_seconds=600)
        self.login(self.owner)

    def login(self, user):
        self.client.force_login(user)

    def content(self, **params):
        return self.client.get(reverse('painel:course_content', args=[self.course.id]), params)

    def drawer(self, lesson, **extra):
        return reverse('painel:lesson_drawer', args=[self.course.id, lesson.id])


class ContentPageTests(B3Base):
    def test_header_tabs_and_counts(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.course)
        page = self.content()
        self.assertContains(page, '<h1 class="course-head__title">Suporte Básico de Vida</h1>')
        self.assertContains(page, '2 módulos · 4 aulas · 18 min de vídeo · 1 aluno · R$ 150,00')
        self.assertContains(page, 'Página de venda ao vivo')
        self.assertContains(page, 'Ver como aluno')
        for text in ('Conteúdo', 'Página de venda', 'Configurações', 'Alunos'):
            self.assertContains(page, text)
        self.assertContains(page, 'aria-current="page" href="%s"' % reverse('painel:course_content', args=[self.course.id]))
        self.assertContains(page, reverse('painel:students') + '?curso=bls')
        self.assertContains(page, '<a href="%s">Cursos</a> / Suporte Básico de Vida' % reverse('painel:courses'))

    def test_live_link_only_when_published(self):
        Course.objects.filter(pk=self.course.pk).update(status='draft')
        self.assertNotContains(self.content(), 'Página de venda ao vivo')

    def test_modules_rows_meta_and_badges(self):
        LessonMaterial.objects.create(lesson=self.l1, title='Apostila', url='https://example.com/a.pdf')
        page = self.content()
        self.assertContains(page, 'Módulo 1 · Fundamentos')
        self.assertContains(page, '3 aulas · 2 publicadas')
        self.assertContains(page, '1. Introdução')
        self.assertContains(page, 'Vimeo · 8 min · 1 material')
        self.assertContains(page, 'YouTube · troque pelo Vimeo')
        self.assertContains(page, 'Sem vídeo')
        self.assertContains(page, 'badge--warning">Rascunho')
        self.assertContains(page, 'badge--success">Publicada')
        self.assertContains(page, 'icon-tile--danger')
        self.assertContains(page, 'id="lesson-row-%d"' % self.l1.id)

    def test_row_edit_link_has_drawer_contract(self):
        page = self.content()
        self.assertContains(page, 'href="?aula=%d" data-drawer-url="%s" data-drawer-target="drawer-aula" data-drawer-param="aula" data-drawer-value="%d"'
                            % (self.l1.id, self.drawer(self.l1), self.l1.id))

    def test_inline_create_and_add_module(self):
        page = self.content()
        self.assertContains(page, 'data-inline-create-url="%s"' % reverse('painel:lesson_quick_create', args=[self.m1.id]))
        self.assertContains(page, '+ Nova aula: digite o título e tecle Enter')
        self.assertContains(page, 'Adicionar módulo')
        self.assertContains(page, 'Arraste pela alça para reordenar. A ordem salva sozinha.')
        self.assertContains(page, 'data-reorder-url="%s"' % reverse('painel:course_reorder', args=[self.course.id]))

    def test_module_menu_and_dialogs(self):
        page = self.content()
        for text in ('Renomear', 'Programar liberação', 'Excluir módulo', 'Afeta alunos', 'Novo módulo'):
            self.assertContains(page, text)
        self.assertContains(page, reverse('painel:course_settings', args=[self.course.id]) + '#liberacao')
        self.assertContains(page, 'As 3 aulas do módulo e o progresso dos alunos nelas serão apagados.')

    def test_empty_course_message(self):
        Module.objects.filter(course=self.course).delete()
        self.assertContains(self.content(), 'Adicione o primeiro módulo para organizar as aulas.')

    def test_access_rules(self):
        self.login(self.inst)
        self.assertEqual(self.content().status_code, 200)
        self.login(self.jane)
        self.assertEqual(self.content().status_code, 403)
        self.client.logout()
        self.assertEqual(self.content().status_code, 302)

    def test_old_lessons_route_redirects(self):
        response = self.client.get(reverse('painel:course_lessons', args=[self.course.id]))
        self.assertRedirects(response, reverse('painel:course_content', args=[self.course.id]), status_code=301)

    def test_release_summary(self):
        self.assertContains(self.content(), 'Todas as aulas ficam disponíveis assim que o aluno é matriculado.')
        Course.objects.filter(pk=self.course.pk).update(release_mode='scheduled')
        self.assertContains(self.content(), 'Os módulos são liberados em datas programadas.')


class ReadinessTests(B3Base):
    def items(self, user=None):
        page = self.content()
        return {item['title']: item for item in page.context['ready_items']}, page

    def test_states_and_count(self):
        items, page = self.items()
        self.assertEqual(items['Capa e descrição']['state'], 'todo')
        self.assertEqual(items['Preço e carga horária']['state'], 'ok')
        self.assertEqual(items['Pelo menos uma aula publicada']['state'], 'ok')
        self.assertEqual(items['Vídeos no Vimeo']['state'], 'warn')
        self.assertEqual(items['Vídeos no Vimeo']['sub'], '1 aula ainda usa YouTube')
        self.assertEqual(items['O que o aluno vai aprender']['state'], 'todo')
        self.assertEqual(items['Assinatura do certificado']['state'], 'todo')
        self.assertEqual(page.context['ready_count'], 2)
        self.assertContains(page, '2 de 6')
        self.assertContains(page, 'Aparece na página de venda')
        self.assertContains(page, '1 aula ainda usa YouTube')

    def test_everything_ready(self):
        Lesson.objects.filter(pk=self.l2.pk).update(video_url='https://vimeo.com/76979873', vimeo_id='76979873')
        Lesson.objects.filter(pk=self.l1.pk).update(vimeo_id='76979871')
        Lesson.objects.filter(pk=self.l4.pk).update(vimeo_id='76979872')
        Course.objects.filter(pk=self.course.pk).update(description='Curso completo', learning_objectives='Fazer RCP\nUsar DEA')
        course = Course.objects.get(pk=self.course.pk)
        course.cover_image = 'courses/capa.jpg'
        course.save(update_fields=['cover_image'])
        site = SiteSettings.load()
        site.signer_name = 'Dra. Ana'
        site.save()
        items, page = self.items()
        self.assertEqual(page.context['ready_count'], 6)
        self.assertContains(page, '6 de 6')
        self.assertTrue(all(item['state'] == 'ok' for item in items.values()))

    def test_pending_items_link_to_where_they_are_solved(self):
        page = self.content()
        self.assertContains(page, reverse('painel:course_sales', args=[self.course.id]))
        self.assertContains(page, reverse('painel:settings') + '?secao=certificado')

    def test_signature_link_hidden_for_instructor(self):
        self.login(self.inst)
        page = self.content()
        self.assertNotContains(page, '?secao=certificado')
        self.assertContains(page, 'Assinatura do certificado')

    def test_no_published_lessons_is_pending_not_warning(self):
        Lesson.objects.filter(module__course=self.course).update(status='draft')
        items, _ = self.items()
        self.assertEqual(items['Pelo menos uma aula publicada']['state'], 'todo')
        self.assertEqual(items['Vídeos no Vimeo']['state'], 'todo')


class DrawerTests(B3Base):
    def test_query_opens_drawer_with_row_highlighted(self):
        page = self.content(aula=self.l2.id)
        self.assertContains(page, 'data-autoopen="aula"')
        self.assertContains(page, 'Fundamentos · Aula 2 de 3')
        self.assertContains(page, 'builder-lesson is-editing" id="lesson-row-%d"' % self.l2.id)
        self.assertContains(page, 'value="Compressões"')

    def test_unknown_or_foreign_lesson_ignored(self):
        other = Course.objects.create(title='Outro', slug='outro', creator=self.owner.creator_profile)
        module = Module.objects.create(course=other, title='M', order=1)
        stranger = Lesson.objects.create(module=module, title='Alheia', order=1)
        for value in ('999999', str(stranger.id), 'abc'):
            page = self.content(aula=value)
            self.assertNotContains(page, 'data-autoopen')

    def test_partial_for_fetch_and_redirect_without_js(self):
        page = self.client.get(self.drawer(self.l1), **AJAX)
        self.assertContains(page, 'id="lesson-form"')
        self.assertNotContains(page, '<html')
        response = self.client.get(self.drawer(self.l1))
        self.assertRedirects(response, reverse('painel:course_content', args=[self.course.id]) + '?aula=%d' % self.l1.id, fetch_redirect_response=False)

    def test_drawer_fields_and_contracts(self):
        page = self.client.get(self.drawer(self.l2), **AJAX)
        for text in ('Publicada', 'Rascunho', 'Aula grátis na página de venda', 'Título', 'Vídeo', 'Descrição',
                     'Aparece abaixo do vídeo, para o aluno.', 'Materiais de apoio', 'Adicionar PDF',
                     'Arraste para cá · até 20 MB por arquivo', 'Mais opções', 'Excluir aula', 'Cancelar', 'Salvar aula',
                     '● Alterações não salvas'):
            self.assertContains(page, text)
        self.assertContains(page, 'data-dirty-form data-dirtybar="lesson-dirty"')
        self.assertContains(page, 'data-async')
        self.assertContains(page, 'Este link é do YouTube. A plataforma usa o Vimeo, com restrição de domínio. Troque antes de abrir as vendas.')
        self.assertContains(page, 'data-dirty-msg')

    def test_no_youtube_alert_for_vimeo(self):
        Lesson.objects.filter(pk=self.l1.pk).update(vimeo_id='76979871')
        self.assertNotContains(self.client.get(self.drawer(self.l1), **AJAX), 'Este link é do YouTube')

    def test_prev_next_neighbours_cross_modules(self):
        page = self.client.get(self.drawer(self.l3), **AJAX)
        self.assertContains(page, self.drawer(self.l2))
        self.assertContains(page, self.drawer(self.l4))
        first = self.client.get(self.drawer(self.l1), **AJAX)
        self.assertNotContains(first, 'aria-label="Aula anterior"')
        last = self.client.get(self.drawer(self.l4), **AJAX)
        self.assertNotContains(last, 'aria-label="Próxima aula"')

    def test_missing_duration_hint(self):
        Lesson.objects.filter(pk=self.l1.pk).update(vimeo_id='76979871', duration_seconds=0)
        self.assertContains(self.client.get(self.drawer(self.l1), **AJAX), 'Não foi possível ler a duração do Vimeo')

    def test_lesson_of_another_course_is_404(self):
        other = Course.objects.create(title='Outro', slug='outro', creator=self.owner.creator_profile)
        url = reverse('painel:lesson_drawer', args=[other.id, self.l1.id])
        self.assertEqual(self.client.get(url, **AJAX).status_code, 404)
        self.assertEqual(self.client.post(url, {'title': 'x'}, **AJAX).status_code, 404)

    def test_student_cannot_open_or_save(self):
        self.login(self.jane)
        self.assertEqual(self.client.get(self.drawer(self.l1), **AJAX).status_code, 403)
        self.assertEqual(self.client.post(self.drawer(self.l1), {'title': 'x'}, **AJAX).status_code, 403)

    def test_deleted_lesson_has_no_drawer(self):
        Lesson.all_objects.filter(pk=self.l1.pk).update(deleted_at=timezone.now())
        self.assertEqual(self.client.get(self.drawer(self.l1), **AJAX).status_code, 404)


@MEDIA
class SaveLessonTests(B3Base):
    def save(self, lesson=None, **fields):
        lesson = lesson or self.l1
        data = {'title': lesson.title, 'status': lesson.status, 'video_url': lesson.video_url, 'description': ''}
        data.update(fields)
        return self.client.post(self.drawer(lesson), data, **AJAX)

    def test_saves_fields_and_replaces_row(self):
        response = self.save(title='Nova introdução', description='Texto', status='draft', is_free_preview='1', duration_minutes='12')
        data = response.json()
        self.l1.refresh_from_db()
        self.assertTrue(data['ok'])
        self.assertEqual(data['toast'], 'Aula salva')
        self.assertEqual((self.l1.title, self.l1.description, self.l1.status, self.l1.is_free_preview, self.l1.duration_seconds),
                         ('Nova introdução', 'Texto', 'draft', True, 720))
        html = data['replace']['#lesson-row-%d' % self.l1.id]
        self.assertIn('id="lesson-row-%d"' % self.l1.id, html)
        self.assertIn('1. Nova introdução', html)
        self.assertIn('badge--warning">Rascunho', html)
        self.assertEqual(data['counts']['#module-count-%d' % self.m1.id], '3 aulas · 1 publicada')

    def test_unchecked_free_preview_turns_off(self):
        Lesson.objects.filter(pk=self.l1.pk).update(is_free_preview=True)
        self.save()
        self.l1.refresh_from_db()
        self.assertFalse(self.l1.is_free_preview)

    def test_title_required(self):
        response = self.save(title='   ')
        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.json()['errors'])
        self.l1.refresh_from_db()
        self.assertEqual(self.l1.title, 'Introdução')

    def test_invalid_video_url_and_duration(self):
        response = self.save(video_url='nao e um link', duration_minutes='abc')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()['errors']), {'video_url', 'duration_minutes'})
        self.assertEqual(response.json()['error'], 'Corrija 2 campos para salvar.')

    def test_youtube_link_is_converted_and_not_vimeo(self):
        self.save(self.l1, video_url='https://youtu.be/abcdefghijk')
        self.l1.refresh_from_db()
        self.assertEqual(self.l1.video_url, 'https://www.youtube.com/embed/abcdefghijk')
        self.assertEqual(self.l1.vimeo_id, '')

    def test_vimeo_duration_fetched_when_url_changes_and_no_manual_value(self):
        with mock.patch('painel.content_views.vimeo_duration', return_value=300) as fake:
            self.save(self.l2, video_url='https://vimeo.com/76979999')
        fake.assert_called_once()
        self.l2.refresh_from_db()
        self.assertEqual((self.l2.vimeo_id, self.l2.duration_seconds), ('76979999', 300))

    def test_manual_duration_wins_over_vimeo(self):
        with mock.patch('painel.content_views.vimeo_duration', return_value=300) as fake:
            self.save(self.l2, video_url='https://vimeo.com/76979999', duration_minutes='7')
        fake.assert_not_called()
        self.l2.refresh_from_db()
        self.assertEqual(self.l2.duration_seconds, 420)

    def test_vimeo_not_called_when_url_unchanged(self):
        with mock.patch('painel.content_views.vimeo_duration', return_value=300) as fake:
            self.save(self.l1)
        fake.assert_not_called()

    def test_upload_pdf_and_rename_material(self):
        pdf = SimpleUploadedFile('guia.pdf', b'%PDF-1.4 conteudo', content_type='application/pdf')
        response = self.client.post(self.drawer(self.l1), {'title': 'Introdução', 'status': 'published', 'video_url': self.l1.video_url,
                                                           'materials': pdf}, **AJAX)
        self.assertTrue(response.json()['ok'])
        material = LessonMaterial.objects.get(lesson=self.l1)
        self.assertEqual(material.title, 'guia.pdf')
        self.save(self.l1, **{'material_%d' % material.id: 'Guia rápido'})
        material.refresh_from_db()
        self.assertEqual(material.title, 'Guia rápido')

    def test_rejects_non_pdf_and_big_files(self):
        bad = SimpleUploadedFile('foto.png', b'x', content_type='image/png')
        response = self.client.post(self.drawer(self.l1), {'title': 'Introdução', 'materials': bad}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertIn('materials', response.json()['errors'])
        big = SimpleUploadedFile('grande.pdf', b'0' * (20 * 1024 * 1024 + 1), content_type='application/pdf')
        response = self.client.post(self.drawer(self.l1), {'title': 'Introdução', 'materials': big}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(LessonMaterial.objects.count(), 0)

    def test_without_js_redirects_back_with_toast(self):
        response = self.client.post(self.drawer(self.l1), {'title': 'Sem JS', 'status': 'published'}, follow=True)
        self.assertContains(response, 'Aula salva')
        self.l1.refresh_from_db()
        self.assertEqual(self.l1.title, 'Sem JS')

    def test_without_js_error_toast(self):
        response = self.client.post(self.drawer(self.l1), {'title': ''}, follow=True)
        self.assertContains(response, 'Informe o título da aula.')

    def test_invalid_status_is_ignored(self):
        self.save(status='banana')
        self.l1.refresh_from_db()
        self.assertEqual(self.l1.status, 'published')

    def test_instructor_can_save(self):
        self.login(self.inst)
        self.assertTrue(self.save(title='Do instrutor').json()['ok'])

    def test_delete_material(self):
        material = LessonMaterial.objects.create(lesson=self.l1, title='Apostila', url='https://example.com/a.pdf')
        response = self.client.post(reverse('painel:material_delete', args=[material.id]), **AJAX)
        self.assertEqual(response.json()['remove'], '#material-%d' % material.id)
        self.assertFalse(LessonMaterial.objects.filter(pk=material.pk).exists())


class QuickCreateTests(B3Base):
    def url(self, module=None):
        return reverse('painel:lesson_quick_create', args=[(module or self.m1).id])

    def test_creates_draft_at_the_end_and_returns_row(self):
        data = self.client.post(self.url(), {'title': 'Nova aula'}, **AJAX).json()
        lesson = Lesson.objects.get(title='Nova aula')
        self.assertEqual((lesson.module, lesson.status, lesson.order), (self.m1, 'draft', 4))
        self.assertTrue(data['ok'])
        self.assertIn('id="lesson-row-%d"' % lesson.id, data['html'])
        self.assertIn('is-new', data['html'])
        self.assertIn('4. Nova aula', data['html'])
        self.assertIn('Sem vídeo', data['html'])
        self.assertEqual(data['open_selector'], '#lesson-row-%d [data-drawer-url]' % lesson.id)
        self.assertEqual(data['counts']['#module-count-%d' % self.m1.id], '4 aulas · 2 publicadas')

    def test_order_ignores_deleted_gaps(self):
        Lesson.all_objects.filter(pk=self.l3.pk).update(deleted_at=timezone.now())
        self.client.post(self.url(), {'title': 'Depois'}, **AJAX)
        self.assertEqual(Lesson.objects.get(title='Depois').order, 4)

    def test_blank_title(self):
        response = self.client.post(self.url(), {'title': '  '}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Informe o título da aula.')
        self.assertEqual(Lesson.objects.filter(module=self.m1).count(), 3)

    def test_without_js_opens_drawer_via_query(self):
        response = self.client.post(self.url(), {'title': 'Sem JS'})
        lesson = Lesson.objects.get(title='Sem JS')
        self.assertRedirects(response, reverse('painel:course_content', args=[self.course.id]) + '?aula=%d' % lesson.id,
                             fetch_redirect_response=False)

    def test_get_not_allowed_and_student_forbidden(self):
        self.assertEqual(self.client.get(self.url()).status_code, 405)
        self.login(self.jane)
        self.assertEqual(self.client.post(self.url(), {'title': 'x'}).status_code, 403)

    def test_page_shows_new_draft_in_module(self):
        self.client.post(self.url(self.m2), {'title': 'Aula final'}, **AJAX)
        self.assertContains(self.content(), '2. Aula final')


class DeleteRestoreTests(B3Base):
    def test_soft_delete_returns_undo_and_hides_everywhere(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.course)
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l1, is_completed=True)
        before = course_progress(self.jane, self.course)['total']
        data = self.client.post(reverse('painel:lesson_delete', args=[self.l1.id]), **AJAX).json()
        self.assertEqual(data['toast'], 'Aula excluída')
        self.assertEqual(data['undo_url'], reverse('painel:lesson_restore', args=[self.l1.id]))
        self.assertEqual(data['remove'], '#lesson-row-%d' % self.l1.id)
        self.assertEqual(data['counts']['#module-count-%d' % self.m1.id], '2 aulas · 1 publicada')
        self.assertTrue(Lesson.all_objects.filter(pk=self.l1.pk, deleted_at__isnull=False).exists())
        self.assertNotContains(self.content(), 'id="lesson-row-%d"' % self.l1.id)
        self.assertEqual(course_progress(self.jane, self.course)['total'], before - 1)
        self.assertTrue(Progress.objects.filter(lesson=self.l1).exists())

    def test_restore_brings_everything_back(self):
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l1, is_completed=True)
        self.client.post(reverse('painel:lesson_delete', args=[self.l1.id]), **AJAX)
        data = self.client.post(reverse('painel:lesson_restore', args=[self.l1.id]), **AJAX).json()
        self.assertEqual(data['redirect'], reverse('painel:course_content', args=[self.course.id]))
        self.assertTrue(Lesson.objects.filter(pk=self.l1.pk).exists())
        self.assertContains(self.content(), 'id="lesson-row-%d"' % self.l1.id)
        self.assertTrue(Progress.objects.filter(lesson=self.l1, is_completed=True).exists())

    def test_without_js_toast_with_undo(self):
        response = self.client.post(reverse('painel:lesson_delete', args=[self.l2.id]), follow=True)
        self.assertContains(response, 'Aula excluída')
        self.assertContains(response, 'data-undo-url="%s"' % reverse('painel:lesson_restore', args=[self.l2.id]))

    def test_restore_only_deleted_and_post_only(self):
        self.assertEqual(self.client.post(reverse('painel:lesson_restore', args=[self.l1.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse('painel:lesson_delete', args=[self.l1.id])).status_code, 405)

    def test_student_cannot_delete(self):
        self.login(self.jane)
        self.assertEqual(self.client.post(reverse('painel:lesson_delete', args=[self.l1.id])).status_code, 403)
        self.assertTrue(Lesson.objects.filter(pk=self.l1.pk).exists())

    def test_deleted_lesson_not_playable_by_student(self):
        Enrollment.objects.create(student=self.jane.student_profile, course=self.course)
        self.client.post(reverse('painel:lesson_delete', args=[self.l1.id]))
        self.login(self.jane)
        self.assertEqual(self.client.get(reverse('lesson_detail', args=['bls', self.l1.id])).status_code, 404)

    def test_reorder_still_works_after_delete(self):
        self.client.post(reverse('painel:lesson_delete', args=[self.l3.id]))
        payload = {'modules': [self.m2.id, self.m1.id], 'lessons': {str(self.m1.id): [self.l2.id, self.l1.id], str(self.m2.id): [self.l4.id]}}
        response = self.client.post(reverse('painel:course_reorder', args=[self.course.id]), json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m.id for m in Module.objects.filter(course=self.course)], [self.m2.id, self.m1.id])
        self.assertEqual(list(Lesson.objects.filter(module=self.m1).values_list('id', flat=True)), [self.l2.id, self.l1.id])

    def test_reorder_moves_lesson_between_modules_and_rejects_bad_payload(self):
        payload = {'modules': [self.m1.id, self.m2.id], 'lessons': {str(self.m1.id): [self.l1.id, self.l3.id],
                                                                    str(self.m2.id): [self.l2.id, self.l4.id]}}
        url = reverse('painel:course_reorder', args=[self.course.id])
        self.assertEqual(self.client.post(url, json.dumps(payload), content_type='application/json').status_code, 200)
        self.l2.refresh_from_db()
        self.assertEqual((self.l2.module, self.l2.order), (self.m2, 1))
        payload['lessons'][str(self.m1.id)] = [self.l1.id]
        self.assertEqual(self.client.post(url, json.dumps(payload), content_type='application/json').status_code, 400)


class PurgeCommandTests(B3Base):
    def run_command(self, *args):
        out = StringIO()
        call_command('purge_deleted', *args, stdout=out)
        return out.getvalue()

    def test_purges_only_old_deletions(self):
        now = timezone.now()
        Lesson.all_objects.filter(pk=self.l1.pk).update(deleted_at=now - timedelta(days=8))
        Lesson.all_objects.filter(pk=self.l2.pk).update(deleted_at=now - timedelta(days=2))
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l1, is_completed=True)
        self.assertIn('1 aula(s) apagadas de vez.', self.run_command())
        self.assertFalse(Lesson.all_objects.filter(pk=self.l1.pk).exists())
        self.assertTrue(Lesson.all_objects.filter(pk=self.l2.pk).exists())
        self.assertTrue(Lesson.objects.filter(pk=self.l3.pk).exists())
        self.assertFalse(Progress.objects.filter(lesson_id=self.l1.pk).exists())

    def test_dry_run_and_days_option(self):
        Lesson.all_objects.filter(pk=self.l2.pk).update(deleted_at=timezone.now() - timedelta(days=3))
        self.assertIn('0 aula(s) seriam apagadas.', self.run_command('--dry-run'))
        self.assertIn('1 aula(s) seriam apagadas.', self.run_command('--dry-run', '--days', '2'))
        self.assertTrue(Lesson.all_objects.filter(pk=self.l2.pk).exists())
        self.run_command('--days', '2')
        self.assertFalse(Lesson.all_objects.filter(pk=self.l2.pk).exists())


class ModuleTests(B3Base):
    def test_create_module_at_the_end(self):
        response = self.client.post(reverse('painel:module_create', args=[self.course.id]), {'title': 'Avançado'}, **AJAX)
        self.assertEqual(response.json()['redirect'], reverse('painel:course_content', args=[self.course.id]))
        module = Module.objects.get(title='Avançado')
        self.assertEqual(module.order, 3)
        self.assertContains(self.content(), 'Módulo 3 · Avançado')

    def test_create_requires_title(self):
        response = self.client.post(reverse('painel:module_create', args=[self.course.id]), {'title': ''}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.json()['errors'])

    def test_rename(self):
        self.client.post(reverse('painel:module_rename', args=[self.m1.id]), {'title': 'Base teórica'}, **AJAX)
        self.m1.refresh_from_db()
        self.assertEqual(self.m1.title, 'Base teórica')
        response = self.client.post(reverse('painel:module_rename', args=[self.m1.id]), {'title': ''}, **AJAX)
        self.assertEqual(response.status_code, 400)

    def test_delete_module_cascades_but_keeps_last(self):
        Progress.objects.create(student=self.jane.student_profile, lesson=self.l4, is_completed=True)
        self.client.post(reverse('painel:module_delete', args=[self.m2.id]), **AJAX)
        self.assertFalse(Module.objects.filter(pk=self.m2.pk).exists())
        self.assertFalse(Lesson.all_objects.filter(pk=self.l4.pk).exists())
        self.assertFalse(Progress.objects.filter(lesson_id=self.l4.pk).exists())
        response = self.client.post(reverse('painel:module_delete', args=[self.m1.id]), **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'O curso precisa ter pelo menos um módulo.')
        self.assertTrue(Module.objects.filter(pk=self.m1.pk).exists())

    def test_student_forbidden(self):
        self.login(self.jane)
        for name, arg in (('module_create', self.course.id), ('module_rename', self.m1.id), ('module_delete', self.m1.id)):
            self.assertEqual(self.client.post(reverse('painel:' + name, args=[arg]), {'title': 'x'}).status_code, 403, name)


class JsContractTests(TestCase):
    def read(self, *parts):
        from pathlib import Path
        from django.conf import settings
        return Path(settings.BASE_DIR, *parts).read_text(encoding='utf-8')

    def test_reorder_script_toasts_and_reverts(self):
        source = self.read('static', 'js', 'painel-grade.js')
        self.assertIn('Ordem salva', source)
        self.assertIn('Tentar de novo', source)
        self.assertIn('restore()', source)

    def test_async_save_closes_drawer_through_closeDrawer(self):
        self.assertIn("closeDrawer(dlg, true)", self.read('static', 'js', 'ui.js'))
