from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction
from django.utils import timezone
from community.access import is_team
from .models import Ticket,TicketEvent,TicketVote

@transaction.atomic
def create_ticket(user,*,subject,title,body,device,is_private=False):
    if user.role!='STUDENT':raise PermissionDenied
    if not subject.is_active:raise ValidationError('Escolha um assunto ativo.')
    ticket=Ticket(student=user.student_profile,subject=subject,title=title.strip(),body=body.strip(),device=device,is_private=is_private)
    if len(ticket.title)<8 or len(ticket.body)<15:raise ValidationError('Título: pelo menos 8 caracteres. Descrição: pelo menos 15.')
    ticket.full_clean();ticket.save()
    # PK is allocated by SQLite itself. No SELECT MAX race between concurrent requests.
    ticket.number=1023+ticket.pk;ticket.save(update_fields=['number'])
    TicketEvent.objects.create(ticket=ticket,status='open',actor=user,note='Chamado aberto.')
    return ticket

@transaction.atomic
def update_ticket(user,ticket,*,status,answer=None,note=''):
    if not is_team(user):raise PermissionDenied
    if status not in Ticket.Status.values:raise ValidationError('Situação inválida.')
    if status=='resolved' and not (answer if answer is not None else ticket.answer).strip():
        raise ValidationError('Escreva uma resposta antes de resolver.')
    previous=ticket.status;previous_answer=ticket.answer
    ticket.status=status
    if answer is not None:ticket.answer=answer.strip()
    ticket.resolved_at=(ticket.resolved_at or timezone.now()) if status=='resolved' else None
    ticket.full_clean();ticket.save()
    if previous!=status or previous_answer!=ticket.answer:
        event=TicketEvent.objects.create(ticket=ticket,status=status,actor=user,note=note.strip() or (ticket.answer if previous_answer!=ticket.answer else ticket.get_status_display()))
        from users.notifications import notify
        from django.urls import reverse
        notify(ticket.student.user,'ticket_update',event.pk,f'Chamado #{ticket.number}: {ticket.get_status_display()}',ticket.title,reverse('support_ticket',args=[ticket.pk]))
    return ticket

@transaction.atomic
def toggle_vote(user,ticket):
    if user.role!='STUDENT' or ticket.is_private:raise PermissionDenied
    vote,created=TicketVote.objects.get_or_create(user=user,ticket=ticket)
    if not created:vote.delete()
    return created


def save_setting(user,instance):
    if not is_team(user):raise PermissionDenied
    instance.full_clean();instance.save();return instance
