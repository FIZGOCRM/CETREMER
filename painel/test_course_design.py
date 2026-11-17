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
