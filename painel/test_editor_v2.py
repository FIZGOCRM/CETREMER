from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from courses.models import Course, Lesson, Module
from users.models import User


def cover_file():
    content = BytesIO()
    Image.new('RGB', (12, 12), 'navy').save(content, format='PNG')
    return SimpleUploadedFile('capa.png', content.getvalue(), content_type='image/png')


class ContentEditorV2Tests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.enterContext(override_settings(MEDIA_ROOT=directory.name))
        self.owner = User.objects.create_user(username='mentor', role='CREATOR')
        self.course = Course.objects.create(title='Mentoria', slug='mentoria', creator=self.owner.creator_profile)
        self.client.force_login(self.owner)
        self.url = f'/painel/cursos/{self.course.pk}/aulas/nova/'
        self.grade = f'/painel/cursos/{self.course.pk}/aulas/'
        self.data = {'new_module_title': 'Vertigem', 'title': 'Caso inicial', 'duration_text': '10:00', 'status': 'draft'}

    def test_new_lesson_and_module_can_be_created_together_with_uploads(self):
        self.assertContains(self.client.get(self.grade), self.url)
        self.assertContains(self.client.get(self.url), 'new_module_title')
        ebook = SimpleUploadedFile('caso.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf')
        response = self.client.post(self.url, {**self.data, 'cover': cover_file(), 'ebook': ebook})
        lesson = Lesson.objects.get()
        self.assertRedirects(response, f'/painel/aulas/{lesson.pk}/editar/')
        self.assertEqual(lesson.module.course, self.course)
        self.assertEqual(lesson.module.title, 'Vertigem')
        self.assertTrue(lesson.cover.name.endswith('.png'))
        self.assertEqual(lesson.materials.get().title, 'caso.pdf')

    def test_saving_lesson_failure_rolls_back_new_module(self):
        with patch('painel.views.lessons.save_lesson_editor', side_effect=ValidationError('Falha ao salvar')):
            response = self.client.post(self.url, self.data)
        self.assertContains(response, 'Falha ao salvar')
        self.assertFalse(Module.objects.exists())
        self.assertFalse(Lesson.objects.exists())

    def test_exclusive_module_choices_and_invalid_image(self):
        module = Module.objects.create(course=self.course, title='Existente')
        response = self.client.post(self.url, {**self.data, 'module': module.pk})
        self.assertContains(response, 'Escolha um módulo existente ou informe')
        invalid_cover = SimpleUploadedFile('capa.png', b'bad', content_type='image/png')
        self.assertEqual(self.client.post(self.url, {**self.data, 'cover': invalid_cover}).status_code, 200)
        self.assertEqual(Module.objects.count(), 1)
        self.assertFalse(Lesson.objects.exists())
        self.client.post(self.url, {**self.data, 'module': module.pk, 'new_module_title': ''})
        self.assertEqual(Lesson.objects.get().module, module)

    def test_module_image_uses_upload_validation_and_can_be_cleared(self):
        self.client.post(self.grade, {'action': 'new_module', 'title': 'GECA', 'cover': cover_file()})
        module = Module.objects.get()
        self.assertTrue(module.cover.name.endswith('.png'))
        invalid_cover = SimpleUploadedFile('foto.png', b'invalid', content_type='image/png')
        update = {'action': 'save_module', 'module_id': module.pk, 'title': 'Atualizado'}
        self.client.post(self.grade, {**update, 'cover': invalid_cover})
        module.refresh_from_db()
        self.assertEqual(module.title, 'GECA')
        self.client.post(self.grade, {**update, 'cover-clear': 'on'})
        module.refresh_from_db()
        self.assertFalse(module.cover)
