from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from courses.models import Course, Enrollment
from .models import CommunityPost


User = get_user_model()


class CommunityEnrollmentTests(TestCase):
    def setUp(self):
        creator = User.objects.create_user(username='creator', password='CreatorPassword123!', role=User.Role.CREATOR)
        self.student = User.objects.create_user(username='student', password='StudentPassword123!', role=User.Role.STUDENT)
        self.course = Course.objects.create(title='Paid course', slug='paid-course', creator=creator.creator_profile)
        self.client.force_login(self.student)

    def test_hub_rejects_unenrolled_course_but_allows_general(self):
        response = self.client.post(reverse('create_hub_post'), {
            'title': 'Topic', 'content': 'Post', 'course_id': str(self.course.id),
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(CommunityPost.objects.exists())
        response = self.client.post(reverse('create_hub_post'), {
            'title': 'Topic', 'content': 'Post', 'course_id': 'general',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(CommunityPost.objects.get().course)

    def test_course_post_requires_enrollment(self):
        url = reverse('create_post', kwargs={'course_slug': self.course.slug})
        response = self.client.post(url, {'title': 'Topic', 'content': 'Post'})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(CommunityPost.objects.exists())
        Enrollment.objects.create(student=self.student.student_profile, course=self.course)
        self.assertEqual(self.client.post(url, {'title': 'Topic', 'content': 'Post'}).status_code, 302)
        self.assertEqual(CommunityPost.objects.get().course, self.course)

    def test_comment_on_course_post_requires_enrollment(self):
        post = CommunityPost.objects.create(course=self.course, author=self.student, title='Topic', content='Post')
        response = self.client.post(reverse('create_comment', kwargs={'post_id': post.id}), {'content': 'Reply'})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(post.comments.exists())
