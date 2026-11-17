from datetime import timedelta
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone
from courses.models import Course, Enrollment, AccessPeriod
from users.models import User
from community.models import CommunityPost, Comment

class CommunityV1Tests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user(username='mentor-v1',role='CREATOR')
        self.student=User.objects.create_user(username='student-v1')
        self.other=User.objects.create_user(username='other-v1')
        self.course=Course.objects.create(is_published=True, title='Saúde',slug='saude-v1',creator=self.admin.creator_profile)
        self.enrollment=Enrollment.objects.create(student=self.student.student_profile,course=self.course)
        self.post=CommunityPost.objects.create(author=self.student,course=self.course,title='Dúvida da turma',content='Uma dúvida de demonstração sem dados pessoais.')
        self.client.force_login(self.student)

    def test_outsider_direct_topic_is_forbidden(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f'/community/posts/{self.post.pk}/').status_code,403)

    def test_ended_can_read_owned_topic_but_not_reply_or_create_general(self):
        from community.services import add_reply, create_topic
        self.enrollment.access_policy='PERIODS';self.enrollment.save()
        self.assertEqual(self.client.get(f'/community/posts/{self.post.pk}/').status_code,200)
        with self.assertRaises(PermissionDenied):add_reply(self.student,self.post,'Resposta')
        with self.assertRaises(PermissionDenied):create_topic(self.student,title='Nova dúvida geral',content='Conteúdo com mais de quinze caracteres.')

    def test_hidden_topic_and_comment_are_preserved_but_not_exposed(self):
        from community.services import moderate
        comment=Comment.objects.create(post=self.post,author=self.admin,content='Texto sensível ilustrativo')
        moderate(self.admin,self.post,'hide_comment',comment=comment)
        self.assertNotContains(self.client.get(f'/community/posts/{self.post.pk}/'),'Texto sensível ilustrativo')
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())
        moderate(self.admin,self.post,'hide')
        self.assertEqual(self.client.get(f'/community/posts/{self.post.pk}/').status_code,403)
        self.assertTrue(CommunityPost.objects.filter(pk=self.post.pk).exists())

    def test_author_solution_requires_someone_else_and_same_topic(self):
        from community.services import mark_solution
        own=Comment.objects.create(post=self.post,author=self.student,content='Minha resposta')
        with self.assertRaises(ValidationError):mark_solution(self.student,self.post,own)
        reply=Comment.objects.create(post=self.post,author=self.admin,content='Resposta da equipe')
        mark_solution(self.student,self.post,reply)
        self.post.refresh_from_db();self.assertEqual(self.post.solution_id,reply.pk)
        self.assertEqual(self.post.solution_marked_by,'author')

    def test_team_signature_and_forward_note_stay_private(self):
        from community.services import add_reply, moderate
        moderate(self.admin,self.post,'forward',note='Análise interna reservada')
        add_reply(self.admin,self.post,'Orientação da equipe',display_as='mentor')
        self.post.refresh_from_db();self.assertEqual(self.post.team_status,'answered')
        response=self.client.get(f'/community/posts/{self.post.pk}/')
        self.assertNotContains(response,'Análise interna reservada')
        self.assertContains(response,'Orientação da equipe')

    def test_student_cannot_spoof_signature_or_moderate(self):
        from community.services import add_reply, moderate
        with self.assertRaises(PermissionDenied):add_reply(self.student,self.post,'Falsa equipe',display_as='mentor')
        with self.assertRaises(PermissionDenied):moderate(self.student,self.post,'pin')

    def test_helpful_toggle_is_unique_and_scoped(self):
        from community.services import toggle_helpful
        from community.models import Helpful
        toggle_helpful(self.student,self.post);self.assertEqual(Helpful.objects.count(),1)
        toggle_helpful(self.student,self.post);self.assertEqual(Helpful.objects.count(),0)
        with self.assertRaises(PermissionDenied):toggle_helpful(self.other,self.post)

    def test_topic_validation_and_course_lesson_relation(self):
        from community.services import create_topic
        with self.assertRaises(ValidationError):create_topic(self.student,title='Curto',content='Curto',course=self.course)
        with self.assertRaises(PermissionDenied):create_topic(self.other,title='Título suficiente',content='Texto suficientemente longo.',course=self.course)

    def test_panel_marks_unanswered_over_24h_and_filters_forwarded(self):
        from community.selectors import panel_posts
        from community.services import moderate
        CommunityPost.objects.filter(pk=self.post.pk).update(created_at=timezone.now()-timedelta(hours=25))
        posts,tab=panel_posts({})
        self.assertTrue(posts[0].overdue)
        moderate(self.admin,self.post,'forward',note='Revisar')
        self.assertEqual(panel_posts({'aba':'forwarded'})[0][0].pk,self.post.pk)

    def test_solution_cannot_reference_another_topic_reply(self):
        from community.services import mark_solution
        other_post=CommunityPost.objects.create(author=self.admin,title='Outro tópico',content='Outro conteúdo')
        reply=Comment.objects.create(post=other_post,author=self.admin,content='Resposta')
        with self.assertRaises(ValidationError):mark_solution(self.student,self.post,reply)

