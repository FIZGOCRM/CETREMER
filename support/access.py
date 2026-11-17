from django.core.exceptions import PermissionDenied
from community.access import is_team

def can_view_cohort(user):
    from courses.access import accessible_courses
    return user.role == 'STUDENT' and accessible_courses(user.student_profile).exists()

def require_ticket_access(user,ticket):
    if is_team(user):return
    if user.role == 'STUDENT' and ticket.student.user_id == user.pk:return
    if ticket.is_private or not can_view_cohort(user):
        raise PermissionDenied('Este chamado está disponível apenas ao autor e à turma com acesso ativo.')
