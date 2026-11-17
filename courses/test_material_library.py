from tempfile import TemporaryDirectory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from courses import models
from courses.models import Course, Enrollment, Lesson, Module, LessonMaterial
from users.models import User


class MaterialLibraryTests(TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.media = override_settings(MEDIA_ROOT=self.folder.name); self.media.enable(); self.addCleanup(self.media.disable)
        self.owner = User.objects.create_user(username='material-owner', role='CREATOR')
        self.user = User.objects.create_user(username='material-student')
        self.course = Course.objects.create(title='Curso', slug='material-course', creator=self.owner.creator_profile)
        self.lesson = Lesson.objects.create(module=Module.objects.create(course=self.course, title='M'), title='A')
        Enrollment.objects.create(student=self.user.student_profile, course=self.course)
        self.material = LessonMaterial.objects.create(lesson=self.lesson, title='PDF da aula', file=SimpleUploadedFile('aula.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf'))
        self.client.force_login(self.user)

    def test_authenticated_file_response_marks_open_once_and_has_private_cache(self):
        response = self.client.get(f'/materiais/lesson/{self.material.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('no-store', response['Cache-Control'])
        response.close()
        self.client.get(f'/materiais/lesson/{self.material.pk}/').close()
        self.assertEqual(models.MaterialOpen.objects.count(), 1)

    def test_outsider_and_draft_cannot_download_or_see_in_library(self):
        outsider = User.objects.create_user(username='material-outsider')
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(f'/materiais/lesson/{self.material.pk}/').status_code, 403)
        self.client.force_login(self.user)
        self.lesson.status = 'draft'; self.lesson.save()
        self.assertEqual(self.client.get(f'/materiais/lesson/{self.material.pk}/').status_code, 403)
        self.assertNotContains(self.client.get('/dashboard/ebooks/'), 'PDF da aula')

    def test_course_pdf_has_upload_and_authenticated_library_entry(self):
        model = getattr(models, 'CourseMaterial', None)
        self.assertIsNotNone(model, 'Material do curso ainda não implementado')
        material = model.objects.create(course=self.course, title='PDF do curso', file=SimpleUploadedFile('curso.pdf',b'%PDF-1.4\n%%EOF',content_type='application/pdf'))
        response = self.client.get('/dashboard/ebooks/')
        self.assertContains(response, 'PDF do curso')
        self.assertContains(response, f'/materiais/course/{material.pk}/')
        self.assertNotContains(response, '/media/materials/')

    def test_anonymous_is_redirected_to_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(f'/materiais/lesson/{self.material.pk}/').status_code, 302)

    def test_admin_can_preview_draft_pdf_without_student_enrollment(self):
        self.lesson.status='draft';self.lesson.save()
        self.client.force_login(self.owner)
        response = self.client.get(f'/materiais/lesson/{self.material.pk}/')
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_library_opened_filter_and_course_material_removal(self):
        model = getattr(models, 'CourseMaterial', None)
        self.assertIsNotNone(model, 'Material do curso ainda não implementado')
        material = model.objects.create(course=self.course, title='PDF teste já aberto', file=SimpleUploadedFile('curso.pdf',b'%PDF-1.4\n%%EOF',content_type='application/pdf'))
        self.client.get(f'/materiais/course/{material.pk}/').close()
        self.assertContains(self.client.get('/dashboard/ebooks/?kind=opened'), 'PDF teste já aberto')
        self.client.force_login(self.owner)
        self.client.post(f'/painel/cursos/{self.course.pk}/materiais/', {'action':'remove', 'material_id':material.pk})
        self.client.force_login(self.user)
        self.assertNotContains(self.client.get('/dashboard/ebooks/'), 'PDF teste já aberto')

    def test_direct_media_url_does_not_bypass_authentication(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.material.file.url).status_code, 404)

    def test_scheduled_module_cannot_expose_its_pdf(self):
        self.lesson.module.release_month=2;self.lesson.module.save()
        self.assertEqual(self.client.get(f'/materiais/lesson/{self.material.pk}/').status_code, 403)
        self.assertNotContains(self.client.get('/dashboard/ebooks/'), 'PDF da aula')

    def test_upload_with_fake_pdf_mime_is_refused(self):
        from courses.models import CourseMaterial
        from courses.services import save_course_material
        from django.core.exceptions import ValidationError
        material=CourseMaterial(course=self.course,title='Falso',file=SimpleUploadedFile('falso.pdf',b'HTML ou texto',content_type='application/pdf'))
        with self.assertRaises(ValidationError):
            save_course_material(material,actor=self.owner)
        self.assertFalse(CourseMaterial.objects.exists())
