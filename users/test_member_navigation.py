from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from courses.models import Course,Enrollment,Module,Lesson
from users.models import User,SiteSettings

class MemberNavigationTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user(username='nav-admin',role='CREATOR')
        self.user=User.objects.create_user(username='nav-student',email='nav@example.org',password='StrongPassword123!')
        self.course=Course.objects.create(is_published=True, title='Curso próprio',slug='nav-course',creator=self.admin.creator_profile)
        Enrollment.objects.create(student=self.user.student_profile,course=self.course,plan_started_on=timezone.localdate())
        self.module=Module.objects.create(course=self.course,title='Módulo pesquisável')
        self.lesson=Lesson.objects.create(module=self.module,title='ECG da demonstração')
        self.client.force_login(self.user)

    def test_student_pages_use_only_member_styles_and_v1_navigation(self):
        for path in ['/dashboard/','/dashboard/meus-cursos/','/settings/','/community/','/ao-vivo/','/certificados/','/suporte/','/notificacoes/']:
            response=self.client.get(path)
            self.assertEqual(response.status_code,200,path)
            self.assertNotContains(response,'css/cetremer.css')
            self.assertNotContains(response,'Minha lista')
            self.assertNotContains(response,'>Trilhas<')
            self.assertContains(response,'Suporte')

    def test_search_owns_courses_and_excludes_drafts_but_marks_scheduled(self):
        other=Course.objects.create(is_published=True, title='Alheio',slug='nav-other',creator=self.admin.creator_profile)
        Lesson.objects.create(module=Module.objects.create(course=other,title='Outro'),title='ECG secreto')
        Lesson.objects.create(module=self.module,title='ECG rascunho',status='draft')
        self.module.release_month=2;self.module.save()
        response=self.client.get('/buscar/?q=ECG')
        self.assertContains(response,self.lesson.title)
        self.assertContains(response,'Libera em')
        self.assertNotContains(response,'ECG secreto');self.assertNotContains(response,'ECG rascunho')
        self.assertNotContains(response,f'/courses/{self.course.slug}/lessons/{self.lesson.pk}/')

    def test_search_by_module_and_brand_from_settings(self):
        site=SiteSettings.load();site.school_name='Escola de demonstração';site.save()
        response=self.client.get('/buscar/?q=pesquisável')
        self.assertContains(response,self.lesson.title);self.assertContains(response,site.school_name)
        self.assertNotContains(response,'Emergensimples')

    def test_preferences_persist_and_expiry_cannot_be_disabled(self):
        response=self.client.post('/settings/',{'action':'preferences','email_live_events':'on','email_expiry':''})
        self.assertEqual(response.status_code,200)
        self.user.student_profile.refresh_from_db()
        self.assertFalse(self.user.student_profile.email_new_lessons)
        self.assertTrue(self.user.student_profile.email_live_events)
        self.assertContains(response,'vencimento são obrigatórios')

    def test_account_rejects_invalid_email_and_keeps_data(self):
        self.client.post('/settings/',{'action':'profile_account','email':'inválido'})
        self.user.refresh_from_db();self.assertEqual(self.user.email,'nav@example.org')

    def test_login_has_student_brand_and_real_recovery_links(self):
        self.client.logout();response=self.client.get('/login/')
        self.assertContains(response,'Treinamento para quem')
        self.assertContains(response,'/senha/esqueci/')
        self.assertContains(response,'/primeiro-acesso/')
        self.assertNotContains(response,'css/cetremer.css')
        self.assertContains(self.client.get('/login/?acesso=admin'),'GoMut')

    def test_old_sections_redirect_to_real_features_and_outside_v1_is_404(self):
        self.assertRedirects(self.client.get('/dashboard/recursos/notificacoes/'),'/notificacoes/')
        self.assertRedirects(self.client.get('/dashboard/recursos/ajuda/'),'/suporte/')
        self.assertEqual(self.client.get('/dashboard/recursos/trilhas/').status_code,404)
        self.assertEqual(self.client.get('/dashboard/recursos/minha-lista/').status_code,404)

    def test_old_public_catalog_routes_no_longer_expose_sales_ui(self):
        self.assertRedirects(self.client.get('/'),'/dashboard/')
        self.assertRedirects(self.client.get(f'/courses/{self.course.slug}/'),f'/dashboard/cursos/{self.course.slug}/')
        self.client.logout()
        self.assertRedirects(self.client.get('/'),'/login/')
        self.assertRedirects(self.client.get(f'/courses/{self.course.slug}/'),'/login/')
