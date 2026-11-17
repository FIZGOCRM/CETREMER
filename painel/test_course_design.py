from django.test import TestCase
from users.models import User
from courses.models import Course

class ProducerCoursesTests(TestCase):
 def setUp(self):
  self.owner=User.objects.create_user(username='course-designer',role='CREATOR')
  self.course=Course.objects.create(title='Curso de demonstração',slug='course-design',creator=self.owner.creator_profile)
  self.client.force_login(self.owner)
 def test_cards_and_create_page_use_gomut_without_sale_fields(self):
  response=self.client.get('/painel/cursos/')
  self.assertTemplateUsed(response,'base_painel_gomut.html')
  self.assertContains(response,'gp-course-card')
  self.assertContains(response,'Criar curso')
  self.assertNotContains(response,'<th>Preço</th>')
  response=self.client.get('/painel/cursos/novo/')
  self.assertTemplateUsed(response,'painel/course_create.html')
  self.assertNotContains(response,'name="price"')
  self.assertNotContains(response,'Página de venda')
 def test_create_persists_draft_and_uses_existing_service(self):
  response=self.client.post('/painel/cursos/novo/',{'title':'Novo curso V1','description':'Descrição ilustrativa','plan_months':12})
  self.assertEqual(response.status_code,302)
  course=Course.objects.get(title='Novo curso V1')
  self.assertFalse(course.is_published);self.assertEqual(course.plan_months,12)

class ProducerCourseOverviewTests(TestCase):
 setUp=ProducerCoursesTests.setUp
 def test_overview_uses_real_counts_and_future_release(self):
  from datetime import timedelta
  from django.utils import timezone
  from courses.models import Module,Lesson,Enrollment,AccessPeriod
  student=User.objects.create_user(username='overview-student')
  enrollment=Enrollment.objects.create(student=student.student_profile,course=self.course,plan_started_on=timezone.localdate(),access_policy='PERIODS')
  AccessPeriod.objects.create(enrollment=enrollment,starts_on=timezone.localdate(),ends_on=timezone.localdate()+timedelta(days=20))
  module=Module.objects.create(course=self.course,title='Mês dois',release_month=2)
  Lesson.objects.create(module=module,title='Sem vídeo')
  Lesson.objects.create(module=module,title='Rascunho',status='draft')
  response=self.client.get(f'/painel/cursos/{self.course.pk}/visao-geral/')
  self.assertEqual(response.status_code,200)
  stats=response.context['overview']
  self.assertEqual(stats['active_students'],1);self.assertEqual(stats['published'],1);self.assertEqual(stats['draft'],1)
  self.assertEqual(stats['missing_vimeo'],2);self.assertEqual(stats['expiring'],1)
  self.assertEqual(stats['releases'][0]['module'],module)
 def test_basic_hides_sale_fields_and_preserves_legacy_values(self):
  self.course.price=99;self.course.live_meet_url='https://example.org/sala-legada';self.course.save()
  response=self.client.get(f'/painel/cursos/{self.course.pk}/')
  self.assertTemplateUsed(response,'base_painel_gomut.html')
  self.assertNotContains(response,'name="price"');self.assertNotContains(response,'Página de venda')
  self.client.post(f'/painel/cursos/{self.course.pk}/',{'title':self.course.title,'description':'Nova descrição','plan_months':12})
  self.course.refresh_from_db();self.assertEqual(self.course.price,99);self.assertEqual(self.course.live_meet_url,'https://example.org/sala-legada')
