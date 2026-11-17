from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from users.models import User,SiteSettings
from courses.models import Course,Enrollment,Certificate,LiveEvent

class PanelSettingsDesignTests(TestCase):
 def setUp(self):
  self.owner=User.objects.create_user(username='configuration-owner',role='CREATOR');self.student=User.objects.create_user(username='configuration-student')
  self.course=Course.objects.create(title='Curso certificado',slug='cert-settings',creator=self.owner.creator_profile)
  self.client.force_login(self.owner)
 def test_settings_save_mentor_school_and_support_with_validation(self):
  self.assertTemplateUsed(self.client.get('/painel/configuracoes/?aba=mentoria'),'base_painel_gomut.html')
  response=self.client.post('/painel/configuracoes/',{'school_name':'Escola de teste','mentor_display_name':'Mentor Exemplo','mentor_label':'Mentor','team_display_name':'Equipe Exemplo','support_email':'ajuda@example.org'})
  self.assertEqual(response.status_code,302);site=SiteSettings.load();self.assertEqual(site.mentor_display_name,'Mentor Exemplo');self.assertEqual(site.support_email,'ajuda@example.org')
  self.client.post('/painel/configuracoes/',{'school_name':'Não pode salvar','support_email':'inválido'})
  self.assertEqual(SiteSettings.load().school_name,'Escola de teste')
 def test_certificate_management_shows_snapshot_and_code_without_cpf(self):
  enrollment=Enrollment.objects.create(student=self.student.student_profile,course=self.course)
  certificate=Certificate.objects.create(enrollment=enrollment,code='CERT-DEMO-ONLY',student_name='Aluno do Certificado',student_cpf='52998224725',course_title='Curso emitido',completed_at=timezone.now())
  response=self.client.get('/painel/certificados/')
  self.assertEqual(response.status_code,200);self.assertTemplateUsed(response,'base_painel_gomut.html')
  self.assertContains(response,'Curso emitido');self.assertContains(response,certificate.code);self.assertNotContains(response,'52998224725')
 def test_live_course_context_and_help_settings_use_new_base(self):
  event=LiveEvent.objects.create(course=self.course,title='Encontro do curso',starts_at=timezone.now()+timedelta(days=1))
  response=self.client.get(f'/painel/ao-vivo/?curso={self.course.pk}')
  self.assertTemplateUsed(response,'base_painel_gomut.html');self.assertContains(response,event.title)
  self.assertEqual(response.context['form'].initial['course'],self.course.pk)
  self.assertTemplateUsed(self.client.get('/painel/ajuda/faq/'),'base_painel_gomut.html')
 def test_email_configuration_never_renders_password(self):
  self.client.post('/painel/configuracoes/',{'email_password':'OnlyTestSecret-NotReal','email_host':'smtp.example.org'})
  response=self.client.get('/painel/configuracoes/?aba=email')
  self.assertNotContains(response,'OnlyTestSecret-NotReal')
  self.assertTrue(SiteSettings.load().email_password_encrypted)
