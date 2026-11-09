from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import StudentProfile, CreatorProfile
from courses.models import Course, Module, Lesson, Progress, Enrollment
from sales.models import Order

User = get_user_model()

class PlatformTestCase(TestCase):
    def setUp(self):
        # Create creator
        self.creator_user = User.objects.create_user(
            username="test_creator",
            email="creator@test.com",
            password="testpassword",
            role=User.Role.CREATOR
        )
        self.creator_profile = self.creator_user.creator_profile
        
        # Create student
        self.student_user = User.objects.create_user(
            username="test_student",
            email="student@test.com",
            password="testpassword",
            role=User.Role.STUDENT
        )
        self.student_profile = self.student_user.student_profile
        
        # Create course
        self.course = Course.objects.create(
            title="BLS - Suporte Básico de Vida",
            slug="suporte-basico-vida-bls",
            description="AHA course.",
            creator=self.creator_profile,
            price=150.00,
            is_published=True
        )
        
        # Create module & lesson
        self.module = Module.objects.create(
            course=self.course,
            title="Módulo 1",
            order=1
        )
        self.lesson = Lesson.objects.create(
            module=self.module,
            title="Aula 1",
            description="Descrição da aula 1.",
            video_url="https://youtube.com/embed/placeholder",
            duration_seconds=120,
            order=1
        )

    def test_profile_creation_signal(self):
        """Verifies that signals automatically instantiate profiles upon user creation."""
        self.assertIsNotNone(self.student_user.student_profile)
        self.assertIsNotNone(self.creator_user.creator_profile)
        self.assertEqual(self.student_profile.points, 0)
        self.assertEqual(self.student_profile.level, 1)

    def test_anonymous_checkout_enrollment(self):
        """Verifies that a guest user can checkout directly, creating their account and enrollment."""
        # Process checkout POST without being logged in
        checkout_url = reverse('process_checkout', kwargs={'course_slug': self.course.slug})
        response = self.client.post(checkout_url, {
            'payment_method': 'CREDIT_CARD',
            'name': 'Novo Aluno',
            'email': 'novo_aluno@test.com'
        })
        self.assertEqual(response.status_code, 200)  # Returns JSON response
        
        # Verify a new student account is generated
        user_exists = User.objects.filter(email='novo_aluno@test.com').exists()
        self.assertTrue(user_exists)
        
        new_user = User.objects.get(email='novo_aluno@test.com')
        new_profile = new_user.student_profile
        
        # Verify enrollment is created for new student
        enrolled = Enrollment.objects.filter(student=new_profile, course=self.course).exists()
        self.assertTrue(enrolled)

    def test_checkout_generates_temporary_password_and_sends_email(self):
        """Verifies that guest checkout generates a temporary password, sends it via email, and the user can log in with it."""
        from django.core import mail
        
        # Setup creator SMTP configs
        self.creator_profile.email_host = 'smtp.test.com'
        self.creator_profile.email_port = 587
        self.creator_profile.email_username = 'creator_sender@test.com'
        self.creator_profile.email_password = 'secretpassword'
        self.creator_profile.save()
        
        # Clear outbox
        mail.outbox = []
        
        checkout_url = reverse('process_checkout', kwargs={'course_slug': self.course.slug})
        response = self.client.post(checkout_url, {
            'payment_method': 'CREDIT_CARD',
            'name': 'Estudante Teste',
            'email': 'estudante_teste@test.com'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.from_email, 'creator_sender@test.com')
        self.assertIn('estudante_teste@test.com', sent_email.to)
        
        # Extract temporary password from email body
        body = sent_email.body
        self.assertIn("Senha Temporária:", body)
        
        # Find password line
        password_line = [line for line in body.split('\n') if "Senha Temporária:" in line][0]
        temp_password = password_line.split("Senha Temporária:")[1].strip()
        
        # Verify student can authenticate using this temporary password
        login_success = self.client.login(username="estudante_teste", password=temp_password)
        self.assertTrue(login_success)

    def test_lesson_toggle_progress(self):
        """Verifies that completing a lesson increments student points, updates rank, and saves progress."""
        # Create enrollment directly
        Enrollment.objects.create(
            student=self.student_profile,
            course=self.course
        )
        
        self.client.login(username="test_student", password="testpassword")
        
        # Post request to toggle progress
        toggle_url = reverse('toggle_progress', kwargs={'lesson_id': self.lesson.id})
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['is_completed'])
        self.assertEqual(data['percentage'], 100.0)
        
        # Check student points updated
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.points, 10)

    def test_profile_settings_update(self):
        """Verifies that an authenticated student can edit their username, email, and password."""
        self.client.login(username="test_student", password="testpassword")
        
        # Test Profile Update
        settings_url = reverse('settings')
        response = self.client.post(settings_url, {
            'action': 'profile_account',
            'username': 'updated_student',
            'email': 'updated@student.com'
        })
        self.assertEqual(response.status_code, 200)
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.username, 'updated_student')
        self.assertEqual(self.student_user.email, 'updated@student.com')

        # Test Password Change
        response = self.client.post(settings_url, {
            'action': 'password',
            'password_old': 'testpassword',
            'password_new': 'newpassword123',
            'password_confirm': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.check_password('newpassword123'))

    def test_community_hub_interaction(self):
        """Verifies that a student can browse the community hub and create discussions."""
        self.client.login(username="test_student", password="testpassword")
        
        hub_url = reverse('community_hub')
        response = self.client.get(hub_url)
        self.assertEqual(response.status_code, 200)

        # Create hub post
        create_url = reverse('create_hub_post')
        response = self.client.post(create_url, {
            'title': 'Dúvida Geral',
            'content': 'Como funciona o ACLS?',
            'course_id': 'general'
        })
        self.assertEqual(response.status_code, 302)
        from community.models import CommunityPost
        self.assertEqual(CommunityPost.objects.count(), 1)
        post = CommunityPost.objects.first()
        self.assertEqual(post.title, 'Dúvida Geral')
        self.assertIsNone(post.course)

    def test_creator_portal_access_and_forms(self):
        """Verifies that only creators can access the creator panel, create courses and update keys."""
        from decimal import Decimal
        # 1. Access without login redirects
        creator_dashboard_url = reverse('creator_dashboard')
        response = self.client.get(creator_dashboard_url)
        self.assertEqual(response.status_code, 302)

        # 2. Student cannot access creator dashboard
        self.client.login(username="test_student", password="testpassword")
        response = self.client.get(creator_dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.client.logout()

        # 3. Creator can access
        self.client.login(username="test_creator", password="testpassword")
        response = self.client.get(creator_dashboard_url)
        self.assertEqual(response.status_code, 200)

        # 4. Creator can create course
        create_url = reverse('course_create')
        response = self.client.post(create_url, {
            'title': 'Novo Curso Emergência',
            'description': 'Resgate de alta montanha.',
            'price': '220.00',
            'is_published': 'on'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Course.objects.filter(title='Novo Curso Emergência').count(), 1)
        new_course = Course.objects.get(title='Novo Curso Emergência')
        self.assertEqual(new_course.price, Decimal('220.00'))

        # 5. Creator can edit payments
        payments_url = reverse('creator_payments')
        response = self.client.post(payments_url, {
            'bank_name': 'Itau',
            'pix_key': '123456789',
            'gateway_name': 'STRIPE',
            'gateway_api_key': 'sk_test_secret_key'
        })
        self.assertEqual(response.status_code, 200)
        self.creator_profile.refresh_from_db()
        self.assertEqual(self.creator_profile.bank_name, 'Itau')
        self.assertEqual(self.creator_profile.gateway_name, 'STRIPE')

        # 6. Test course builder safe int parsing with empty values
        builder_url = reverse('course_builder', kwargs={'course_id': new_course.id})
        response = self.client.post(builder_url, {
            'action': 'add_module',
            'module_title': 'Módulo Teórico',
            'module_order': ''
        })
        self.assertEqual(response.status_code, 302)
        module = Module.objects.get(course=new_course, title='Módulo Teórico')
        self.assertEqual(module.order, 0)

        response = self.client.post(builder_url, {
            'action': 'add_lesson',
            'module_id': module.id,
            'lesson_title': 'Aula Prática',
            'lesson_desc': 'Uso do desfibrilador',
            'lesson_video': 'https://youtube.com',
            'lesson_duration': '',
            'lesson_order': ''
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Lesson.objects.filter(module=module, title='Aula Prática').count(), 1)

    def test_landing_page_with_hero(self):
        """Verifies that the landing page renders successfully and passes the active HeroBanner."""
        from courses.models import HeroBanner
        HeroBanner.objects.create(
            title="Custom Banner Title",
            subtitle="Custom description text",
            is_active=True
        )
        
        landing_url = reverse('landing')
        response = self.client.get(landing_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Custom Banner Title")
        self.assertContains(response, "Custom description text")

    def test_settings_page_saves_extended_profile(self):
        """Verifies that the settings profile form saves Name, CPF, and Address for students."""
        self.client.login(username="test_student", password="testpassword")
        settings_url = reverse('settings')
        
        # 1. Update account details
        response = self.client.post(settings_url, {
            'action': 'profile_account',
            'username': 'test_student_mod',
            'email': 'mod@test.com'
        })
        self.assertEqual(response.status_code, 200)
        
        # 2. Update personal certification details
        response = self.client.post(settings_url, {
            'action': 'profile_personal',
            'full_name': 'Márcio Hirade Filho',
            'cpf': '111.222.333-44'
        })
        self.assertEqual(response.status_code, 200)
        
        # 3. Update residential address details
        response = self.client.post(settings_url, {
            'action': 'profile_address',
            'address': 'Rua Principal, 123 - Campo Grande'
        })
        self.assertEqual(response.status_code, 200)
        
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.full_name, 'Márcio Hirade Filho')
        self.assertEqual(self.student_profile.cpf, '111.222.333-44')
        self.assertEqual(self.student_profile.address, 'Rua Principal, 123 - Campo Grande')

    def test_certificate_blocked_if_incomplete(self):
        """Verifies that a student cannot generate a certificate if they haven't finished 100% of the lessons."""
        Enrollment.objects.create(student=self.student_profile, course=self.course)
        self.client.login(username="test_student", password="testpassword")
        cert_url = reverse('issue_certificate', kwargs={'course_slug': self.course.slug})
        response = self.client.get(cert_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Certificado Bloqueado")

    def test_certificate_allowed_if_complete(self):
        """Verifies that a student gets their certificate once they hit 100% completion progress."""
        Enrollment.objects.create(student=self.student_profile, course=self.course)
        self.client.login(username="test_student", password="testpassword")
        
        # Complete all lessons
        Progress.objects.create(student=self.student_profile, lesson=self.lesson, is_completed=True)
        
        # Save StudentProfile full_name and CPF first to validate template renders
        self.student_profile.full_name = "Aluno Certificado"
        self.student_profile.cpf = "000.000.000-00"
        self.student_profile.save()
        
        cert_url = reverse('issue_certificate', kwargs={'course_slug': self.course.slug})
        response = self.client.get(cert_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CERTIFICADO")
        self.assertContains(response, "Aluno Certificado")

    def test_creator_integrations_saving(self):
        """Verifies that creators can save Asaas credentials, AI API keys, and custom signatures."""
        self.client.login(username="test_creator", password="testpassword")
        integrations_url = reverse('creator_integrations')
        response = self.client.post(integrations_url, {
            'asaas_token': 'asaas_key_123',
            'asaas_sandbox': 'on',
            'ai_provider': 'GEMINI',
            'ai_api_key': 'gemini_api_key_456',
            'ai_tutor_enabled': 'on',
            'certificate_signature_name': 'Dr. Hirade',
            'certificate_signature_role': 'Diretor de Ensino'
        })
        self.assertEqual(response.status_code, 200)
        self.creator_profile.refresh_from_db()
        self.assertEqual(self.creator_profile.asaas_token, 'asaas_key_123')
        self.assertTrue(self.creator_profile.asaas_sandbox)
        self.assertEqual(self.creator_profile.ai_api_key, 'gemini_api_key_456')
        self.assertTrue(self.creator_profile.ai_tutor_enabled)
        self.assertEqual(self.creator_profile.certificate_signature_name, 'Dr. Hirade')
        self.assertEqual(self.creator_profile.certificate_signature_role, 'Diretor de Ensino')

    def test_youtube_link_embed_conversion(self):
        """Verifies that watch, youtu.be, and shorts YouTube links are automatically converted to embed format on save."""
        from courses.models import get_embed_url
        self.assertEqual(get_embed_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "https://www.youtube.com/embed/dQw4w9WgXcQ")
        self.assertEqual(get_embed_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=4s"), "https://www.youtube.com/embed/dQw4w9WgXcQ")
        self.assertEqual(get_embed_url("https://youtu.be/dQw4w9WgXcQ"), "https://www.youtube.com/embed/dQw4w9WgXcQ")
        self.assertEqual(get_embed_url("https://www.youtube.com/shorts/dQw4w9WgXcQ"), "https://www.youtube.com/embed/dQw4w9WgXcQ")
