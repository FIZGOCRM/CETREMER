from django.test import TestCase
from users.models import User
from courses.models import Course,Module,Lesson

class ContentDesignTests(TestCase):
 def setUp(self):
  self.owner=User.objects.create_user(username='content-designer',role='CREATOR')
  self.course=Course.objects.create(title='Conteúdo',slug='content-design',creator=self.owner.creator_profile)
  self.module=Module.objects.create(course=self.course,title='Fundamentos')
  self.client.force_login(self.owner)
 def test_content_has_new_base_and_final_section_after_modules(self):
  r=self.client.get(f'/painel/cursos/{self.course.pk}/aulas/')
  self.assertTemplateUsed(r,'base_painel_gomut.html')
  self.assertContains(r,'data-quick-lesson')
  self.assertContains(r,'Avaliação final')
  text=r.content.decode();self.assertGreater(text.index('data-final-assessment'),text.index('data-module-id'))
 def test_quick_creation_always_creates_draft_and_requires_owned_module(self):
  r=self.client.post(f'/painel/cursos/{self.course.pk}/aulas/',{'action':'quick_lesson','module_id':self.module.pk,'title':'Nova aula rápida','status':'published'})
  self.assertEqual(r.status_code,302)
  lesson=Lesson.objects.get(title='Nova aula rápida');self.assertEqual(lesson.status,'draft');self.assertFalse(lesson.video_url)
  other=Course.objects.create(title='Outro',slug='content-other',creator=self.owner.creator_profile)
  module=Module.objects.create(course=other,title='Outro módulo')
  self.client.post(f'/painel/cursos/{self.course.pk}/aulas/',{'action':'quick_lesson','module_id':module.pk,'title':'Não pode entrar'})
  self.assertFalse(Lesson.objects.filter(title='Não pode entrar').exists())
