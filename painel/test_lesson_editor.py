from tempfile import TemporaryDirectory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase,override_settings
from users.models import User
from courses.models import Course,Module,Lesson,Enrollment,Progress,LessonMaterial

class LessonEditorTests(TestCase):
 def setUp(self):
  self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.media=override_settings(MEDIA_ROOT=self.temp.name);self.media.enable();self.addCleanup(self.media.disable)
  self.owner=User.objects.create_user(username='editor-owner',role='CREATOR');self.student=User.objects.create_user(username='editor-student')
  self.course=Course.objects.create(title='Curso editor',slug='lesson-editor',creator=self.owner.creator_profile)
  self.module=Module.objects.create(course=self.course,title='M1');self.other_module=Module.objects.create(course=self.course,title='M2')
  self.lesson=Lesson.objects.create(module=self.module,title='Aula',video_url='https://vimeo.com/76979871',duration_seconds=62)
  Enrollment.objects.create(student=self.student.student_profile,course=self.course)
  self.progress=Progress.objects.create(student=self.student.student_profile,lesson=self.lesson,last_position_seconds=30)
  self.client.force_login(self.owner);self.url=f'/painel/aulas/{self.lesson.pk}/editar/'
 def data(self,**extra):
  data={'module':self.other_module.pk,'title':'Aula editada','description':'Texto','video_url':self.lesson.video_url,'duration_text':'2:05','status':'draft'};data.update(extra);return data
 def test_editor_has_preview_quiz_and_precise_duration(self):
  r=self.client.get(self.url);self.assertEqual(r.status_code,200)
  self.assertTemplateUsed(r,'base_painel_gomut.html');self.assertContains(r,'https://player.vimeo.com/video/76979871')
  self.assertContains(r,'1:02');self.assertContains(r,f'/painel/aulas/{self.lesson.pk}/quiz/')
 def test_save_moves_module_and_resets_position_with_duration_change(self):
  r=self.client.post(self.url,self.data());self.assertEqual(r.status_code,302)
  self.lesson.refresh_from_db();self.progress.refresh_from_db()
  self.assertEqual(self.lesson.module_id,self.other_module.pk);self.assertEqual(self.lesson.duration_seconds,125);self.assertEqual(self.progress.last_position_seconds,0)
 def test_pdf_replacement_keeps_material_identity(self):
  material=LessonMaterial.objects.create(lesson=self.lesson,title='Anterior',file=SimpleUploadedFile('old.pdf',b'%PDF-1.4\n%%EOF',content_type='application/pdf'))
  r=self.client.post(self.url,self.data(ebook=SimpleUploadedFile('new.pdf',b'%PDF-1.4\n%%EOF',content_type='application/pdf')))
  self.assertEqual(r.status_code,302);self.assertEqual(LessonMaterial.objects.get().pk,material.pk)
 def test_invalid_upload_or_foreign_module_does_not_save_any_changes(self):
  response=self.client.post(self.url,self.data(ebook=SimpleUploadedFile('fake.pdf',b'not-pdf',content_type='application/pdf')))
  self.assertEqual(response.status_code,200);self.lesson.refresh_from_db();self.assertEqual(self.lesson.title,'Aula')
  other=Course.objects.create(title='Outro',slug='editor-outsider',creator=self.owner.creator_profile);module=Module.objects.create(course=other,title='Alheio')
  self.client.post(self.url,self.data(module=module.pk));self.lesson.refresh_from_db();self.assertEqual(self.lesson.module_id,self.module.pk)
