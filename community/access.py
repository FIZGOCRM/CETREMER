"""Community authorization shared by list, detail and all mutations."""
from django.core.exceptions import PermissionDenied
from courses.access import accessible_courses
from courses.models import Enrollment


def is_team(user):
    return user.is_authenticated and user.role in ('ADMIN','CREATOR')


def require_topic_access(user, post):
    if is_team(user): return
    if user.role != 'STUDENT' or post.is_hidden:
        raise PermissionDenied('Sem acesso a este tópico.')
    if post.course_id and not Enrollment.objects.filter(student=user.student_profile,course_id=post.course_id,course__is_published=True).exists():
        raise PermissionDenied('Sem acesso a este curso.')


def can_write(user):
    return is_team(user) or (user.role == 'STUDENT' and accessible_courses(user.student_profile).exists())


def require_write(user):
    if not can_write(user):
        raise PermissionDenied('Seus planos estão encerrados ou aguardam início. A comunidade permanece disponível para leitura.')
