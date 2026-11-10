from django.contrib.auth import get_user_model
from django.test import TestCase

from community.models import Comment, CommunityPost

User = get_user_model()


class AnsweredCacheTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='a@example.com', password='x', role=User.Role.ADMIN, is_staff=True)
        self.jane = User.objects.create_user(username='jane', email='j@example.com', password='x')
        self.other = User.objects.create_user(username='other', email='o@example.com', password='x')
        self.post = CommunityPost.objects.create(author=self.jane, title='Dúvida', content='Como?')

    def test_new_post_defaults(self):
        self.assertFalse(self.post.is_answered_cache)
        self.assertFalse(self.post.has_unread_answer)
        self.assertFalse(self.post.is_resolved)
        self.assertFalse(self.post.is_pinned)

    def test_staff_comment_sets_cache_and_unread(self):
        Comment.objects.create(post=self.post, author=self.admin, content='Assim.')
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_answered_cache)
        self.assertTrue(self.post.has_unread_answer)
        self.assertTrue(self.post.is_answered)

    def test_student_comment_does_not_mark_answered(self):
        Comment.objects.create(post=self.post, author=self.other, content='Também quero saber.')
        self.post.refresh_from_db()
        self.assertFalse(self.post.is_answered_cache)
        self.assertFalse(self.post.has_unread_answer)

    def test_staff_replying_to_own_post_is_not_unread_for_author(self):
        own = CommunityPost.objects.create(author=self.admin, title='Aviso', content='x')
        Comment.objects.create(post=own, author=self.admin, content='y')
        own.refresh_from_db()
        self.assertTrue(own.is_answered_cache)
        self.assertFalse(own.has_unread_answer)
