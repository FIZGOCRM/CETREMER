from users.display import first_name

from .models import CommunityPost, is_staff_user


def lesson_questions(lesson):
    """Dúvidas visíveis de uma aula, prontas para o template (HANDOFF-v2 7.3, aba Dúvidas)."""
    posts = list(CommunityPost.objects.filter(lesson=lesson, is_hidden=False)
                 .select_related('author__student_profile').prefetch_related('comments__author')
                 .order_by('-created_at'))
    for post in posts:
        comments = list(post.comments.all())
        post.replies_count = len(comments)
        post.official = next((c for c in comments if is_staff_user(c.author)), None)
        post.author_name = first_name(post.author)
    return posts
