from django.test import TestCase
from django.urls import reverse

from courses.models import Course, Enrollment, Lesson, Module, Certificate
from courses.services import set_lesson_progress
from users.models import User


class CertificateExperienceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='cert-experience-owner', role='CREATOR')
        self.user = User.objects.create_user(username='cert-experience-student')
        self.course = Course.objects.create(is_published=True, title='Curso com certificado', slug='cert-experience', creator=self.owner.creator_profile)
        self.lesson = Lesson.objects.create(module=Module.objects.create(course=self.course, title='M'), title='A')
        self.enrollment = Enrollment.objects.create(student=self.user.student_profile, course=self.course)
        set_lesson_progress(self.user.student_profile, self.lesson, completed=True)
        self.client.force_login(self.user)

    def test_list_uses_member_layout_and_inline_personal_data(self):
        response = self.client.get(reverse('certificates'))
        self.assertTemplateUsed(response, 'base_membros.html')
        self.assertContains(response, 'Nome completo')
        self.assertContains(response, 'CPF')
        self.assertNotContains(response, 'css/cetremer.css')

    def test_valid_inline_data_saves_and_issues_without_exposing_full_cpf(self):
        response = self.client.post(reverse('issue_certificate', args=[self.course.slug]), {
            'action':'save_and_issue', f'enrollment-{self.enrollment.pk}-full_name':'Aluno Completo', f'enrollment-{self.enrollment.pk}-cpf':'529.982.247-25'})
        self.assertEqual(response.status_code, 302)
        cert = Certificate.objects.get(enrollment=self.enrollment)
        response = self.client.get(response.url)
        self.assertContains(response, '***.***.***-25')
        self.assertNotContains(response, '52998224725')
        self.assertNotContains(response, '529.982.247-25')
        self.assertContains(response, 'Copiar código')
        self.assertContains(response, 'Baixar PDF')
        self.assertContains(response, cert.code)

    def test_invalid_cpf_does_not_issue_or_change_profile(self):
        response = self.client.post(reverse('issue_certificate', args=[self.course.slug]), {
            'action':'save_and_issue', f'enrollment-{self.enrollment.pk}-full_name':'Aluno Completo', f'enrollment-{self.enrollment.pk}-cpf':'111.111.111-11'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Certificate.objects.exists())
        self.user.student_profile.refresh_from_db()
        self.assertFalse(self.user.student_profile.cpf)

    def test_public_verification_has_no_cpf(self):
        self.client.post(reverse('issue_certificate', args=[self.course.slug]), {
            'action':'save_and_issue', f'enrollment-{self.enrollment.pk}-full_name':'Aluno Completo', f'enrollment-{self.enrollment.pk}-cpf':'52998224725'})
        cert = Certificate.objects.get(enrollment=self.enrollment)
        self.client.logout()
        response = self.client.get(reverse('verify_certificate'), {'codigo':cert.code})
        self.assertContains(response, 'Certificado válido')
        self.assertNotContains(response, '52998224725')

    def test_linkedin_uses_static_link_and_copyable_credential_data_without_cpf(self):
        from users.models import SiteSettings
        site = SiteSettings.load(); site.school_name = 'Escola de Demonstração'; site.save()
        self.client.post(reverse('issue_certificate', args=[self.course.slug]), {
            'action':'save_and_issue', f'enrollment-{self.enrollment.pk}-full_name':'Aluno Completo', f'enrollment-{self.enrollment.pk}-cpf':'52998224725'})
        response = self.client.get(reverse('issue_certificate', args=[self.course.slug]))
        self.assertContains(response, 'Copiar dados para o LinkedIn')
        self.assertEqual(response.context['linkedin_url'], 'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME')
        details = response.context['linkedin_details']
        self.assertIn('Nome: Curso com certificado', details)
        self.assertIn('Instituição: Escola de Demonstração', details)
        self.assertIn('Código: '+Certificate.objects.get(enrollment=self.enrollment).code, details)
        self.assertNotIn('52998224725', details)
