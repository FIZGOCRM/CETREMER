"""Read-only member preview lifecycle. Authentication identity is never replaced in session."""
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from .models import MemberPreviewLog

SESSION_KEY='member_preview'


def valid_payload(payload):
    return isinstance(payload,dict) and all(type(payload.get(key)) is int and 0<payload[key]<2**63 for key in ('admin_id','student_id','log_id'))

@transaction.atomic
def finish_preview(actor,payload):
    if valid_payload(payload) and payload['admin_id']==actor.pk:
        MemberPreviewLog.objects.filter(pk=payload['log_id'],admin=actor,student__user_id=payload['student_id'],ended_at__isnull=True).update(ended_at=timezone.now())

@transaction.atomic
def begin_preview(actor,student,previous=None):
    if actor.role not in ('ADMIN','CREATOR') or student.role!='STUDENT' or not student.is_active:raise PermissionDenied('Prévia disponível apenas para administradores e alunos ativos.')
    finish_preview(actor,previous)
    log=MemberPreviewLog.objects.create(admin=actor,student=student.student_profile)
    return {'admin_id':actor.pk,'student_id':student.pk,'log_id':log.pk}
