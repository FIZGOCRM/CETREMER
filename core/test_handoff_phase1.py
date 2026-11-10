from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone


User = get_user_model()


class HandoffPhaseOneTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username='creator1', role=User.Role.CREATOR)
        self.student = User.objects.create_user(username='student1', role=User.Role.STUDENT)

    def test_category_course_and_material_fields(self):
        from courses.models import Category, Course, Lesson, LessonMaterial, Module

        category = Category.objects.create(name='Essenciais AHA', slug='essenciais', color='blue', order=1)
        course = Course.objects.create(
            creator=self.creator.creator_profile, title='BLS', slug='bls', category=category,
            short_name='BLS', cover_color='teal', workload_hours=8,
            learning_objectives='RCP\n\nDEA\n', target_audience='Alunos',
        )
        self.assertEqual(category.badge_class, 'badge--blue')
        self.assertEqual(course.cover_class, 'cover--teal')
        self.assertEqual(course.objectives_list, ['RCP', 'DEA'])
        lesson = Lesson.objects.create(module=Module.objects.create(course=course, title='M1'), title='Aula')
        material = LessonMaterial.objects.create(lesson=lesson, title='Manual', url='https://example.com/manual.pdf')
        self.assertEqual(list(lesson.materials.all()), [material])

    def test_vimeo_fields_and_player_url(self):
        from courses.models import Course, Lesson, Module

        course = Course.objects.create(creator=self.creator.creator_profile, title='Video', slug='video')
        module = Module.objects.create(course=course, title='M1')
        lesson = Lesson.objects.create(module=module, title='Aula', video_url='https://vimeo.com/123456789/abcdef1234')
        self.assertEqual(lesson.vimeo_id, '123456789')
        self.assertEqual(lesson.vimeo_hash, 'abcdef1234')
        self.assertIn('h=abcdef1234', lesson.player_url)
        lesson.video_url = 'https://player.vimeo.com/video/987654321?h=feed1234'
        lesson.save()
        self.assertEqual((lesson.vimeo_id, lesson.vimeo_hash), ('987654321', 'feed1234'))

    def test_material_rejects_non_pdf_upload(self):
        from courses.models import Course, Lesson, LessonMaterial, Module

        course = Course.objects.create(creator=self.creator.creator_profile, title='Material', slug='material')
        lesson = Lesson.objects.create(module=Module.objects.create(course=course, title='M1'), title='Aula')
        material = LessonMaterial(
            lesson=lesson, title='Arquivo',
            file=SimpleUploadedFile('arquivo.pdf', b'texto', content_type='text/plain'),
        )
        with self.assertRaises(ValidationError):
            material.full_clean()

    def test_enrollment_certificate_and_post_status(self):
        from community.models import Comment, CommunityPost
        from courses.models import Certificate, Course, Enrollment
        from sales.models import Order

        course = Course.objects.create(creator=self.creator.creator_profile, title='BLS', slug='bls')
        enrollment = Enrollment.objects.create(student=self.student.student_profile, course=course, source='manual')
        self.assertIsNone(enrollment.last_accessed_at)
        certificate = Certificate.objects.create(
            enrollment=enrollment, code='ABCDEF123456', student_name='Aluno Teste',
            student_cpf='52998224725', course_title='BLS', workload_hours=8,
            completed_at=timezone.now(),
        )
        self.assertEqual(enrollment.certificate, certificate)
        post = CommunityPost.objects.create(author=self.student, course=course, title='Dúvida', content='Conteúdo')
        self.assertFalse(post.is_answered)
        Comment.objects.create(post=post, author=self.creator, content='Resposta')
        self.assertTrue(post.is_answered)
        self.assertEqual(Order.Status.REFUNDED, 'REFUNDED')

    def test_cpf_normalization_and_site_settings(self):
        from users.models import SiteSettings

        profile = self.student.student_profile
        profile.cpf = '529.982.247-25'
        profile.save()
        self.assertEqual(profile.cpf, '52998224725')
        profile.cpf = '111.111.111-11'
        with self.assertRaises(ValidationError):
            profile.save()
        site = SiteSettings.load()
        self.assertEqual(site.school_name, 'CETREMER')

    def test_crypto_round_trip(self):
        from core.crypto import decrypt, encrypt

        token = encrypt('segredo de teste')
        self.assertNotIn('segredo de teste', token)
        self.assertEqual(decrypt(token), 'segredo de teste')
