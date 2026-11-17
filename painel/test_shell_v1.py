from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from users.models import User
from courses.models import Course,Enrollment,AccessPeriod
from community.models import CommunityPost
from support.models import Ticket,SupportSubject

class PanelShellTests(TestCase):
 def setUp(self):
  self.admin=User.objects.create_user(username='shell-admin',role='CREATOR')
  self.student=User.objects.create_user(username='shell-student')
  self.course=Course.objects.create(title='Curso',slug='shell-course',creator=self.admin.creator_profile)
  e=Enrollment.objects.create(student=self.student.student_profile,course=self.course,access_policy='PERIODS')
  AccessPeriod.objects.create(enrollment=e,starts_on=timezone.localdate(),ends_on=timezone.localdate()+timedelta(days=20))
  CommunityPost.objects.create(author=self.student,title='Pergunta',content='Texto',team_status='forwarded')
  Ticket.objects.create(student=self.student.student_profile,subject=SupportSubject.objects.create(name='Acesso'),title='Título',body='Texto',device='Celular')
  self.client.force_login(self.admin)
 def test_dashboard_uses_new_panel_base_and_actual_counts(self):
  r=self.client.get('/painel/')
  self.assertTemplateUsed(r,'base_painel_gomut.html')
  self.assertNotContains(r,'css/cetremer.css')
  self.assertContains(r,'Visualizar como membro')
  self.assertEqual(r.context['panel_counts'],{'community':1,'tickets':1,'expiring':1})
  self.assertNotContains(r,'Vendas no mês')
  self.assertNotContains(r,'href="/painel/pedidos/"')
 def test_staff_flag_alone_does_not_grant_producer_access(self):
  self.student.is_staff=True;self.student.save();self.client.force_login(self.student)
  self.assertEqual(self.client.get('/painel/').status_code,403)

