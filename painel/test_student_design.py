from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from users.models import User,SiteSettings
from courses.models import Course,Enrollment,AccessPeriod

class StudentPanelDesignTests(TestCase):
 def setUp(self):
  self.owner=User.objects.create_user(username='students-owner',role='CREATOR');self.student=User.objects.create_user(username='students-member',email='member@example.org')
  self.course=Course.objects.create(title='Curso dos alunos',slug='students-design',creator=self.owner.creator_profile)
  self.enrollment=Enrollment.objects.create(student=self.student.student_profile,course=self.course,access_policy='PERIODS',plan_started_on=timezone.localdate())
  AccessPeriod.objects.create(enrollment=self.enrollment,starts_on=timezone.localdate(),ends_on=timezone.localdate()+timedelta(days=20))
  self.client.force_login(self.owner)
 def test_table_and_expirations_use_new_base_and_plan_modal(self):
  r=self.client.get('/painel/alunos/');self.assertTemplateUsed(r,'base_painel_gomut.html')
  self.assertContains(self.client.get(f'/painel/alunos/?aluno={self.student.pk}'), 'data-gp-drawer')
  self.assertNotContains(r,'Período quitado')
  self.assertTemplateUsed(self.client.get('/painel/vencimentos/'),'base_painel_gomut.html')
  r=self.client.get(f'/painel/planos/{self.enrollment.pk}/?embed=1');self.assertTemplateUsed(r,'base_panel_embed.html')
  self.assertNotContains(r,'producer-sidebar')
  self.assertEqual(r['X-Frame-Options'],'SAMEORIGIN')
 def test_manual_new_enrollment_requires_dates_and_creates_audited_plan(self):
  data={'action':'enroll','email':'new-member@example.org','full_name':'Novo Aluno','course_id':self.course.pk}
  self.client.post('/painel/alunos/',data);self.assertFalse(User.objects.filter(email=data['email']).exists())
  data['starts_on']='2026-11-01';data['last_day']='2027-10-31'
  self.client.post('/painel/alunos/',data)
  e=Enrollment.objects.get(student__user__email=data['email'])
  self.assertEqual(e.plan_started_on.isoformat(),'2026-11-01');self.assertEqual(e.access_periods.get().ends_on.isoformat(),'2027-11-01')
  self.assertEqual(e.access_changes.count(),1)
 def test_existing_plan_is_not_replaced_by_new_enrollment_form(self):
  period=self.enrollment.access_periods.get()
  self.client.post('/painel/alunos/',{'action':'enroll','email':self.student.email,'course_id':self.course.pk,'starts_on':'2020-01-01'})
  self.assertEqual(self.enrollment.access_periods.get().ends_on,period.ends_on)
 def test_access_email_without_smtp_is_logged_unsent_without_token(self):
  from users.services import send_access_link
  from users.models import EmailLog
  with patch('users.services.send_mail') as send:
   sent=send_access_link(self.student,'https://example.org/senha/nova/private-token/')
   self.assertEqual(sent,0);send.assert_not_called()
  log=EmailLog.objects.get();self.assertEqual(log.status,'not_sent');self.assertNotIn('private-token',log.body)
 def test_access_email_records_actual_delivery_date_without_saving_token(self):
  from users.services import send_access_link
  from users.models import EmailLog
  site=SiteSettings.load();site.email_host='smtp.example.org';site.save()
  with patch('users.services.send_mail',return_value=1):self.assertEqual(send_access_link(self.student,'https://example.org/secret/'),1)
  log=EmailLog.objects.get();self.assertEqual(log.status,'sent');self.assertIsNotNone(log.created_at);self.assertNotIn('secret',log.body)
