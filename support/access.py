from django.core.exceptions import PermissionDenied
from community.access import is_team

def require_ticket_access(user,ticket):
    if is_team(user):return
    if user.role!='STUDENT' or (ticket.is_private and ticket.student.user_id!=user.pk):
        raise PermissionDenied('Este chamado é privado.')
