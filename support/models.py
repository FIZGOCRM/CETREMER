from django.conf import settings
from django.db import models

class FaqItem(models.Model):
    category=models.CharField(max_length=80)
    question=models.CharField(max_length=240)
    answer=models.TextField()
    order=models.PositiveIntegerField(default=0)
    is_published=models.BooleanField(default=True)
    class Meta:ordering=['order','pk']

class SupportSubject(models.Model):
    name=models.CharField(max_length=120)
    order=models.PositiveIntegerField(default=0)
    is_active=models.BooleanField(default=True)
    class Meta:ordering=['order','pk']
    def __str__(self):return self.name

class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN='open','Aberto'
        REVIEW='in_review','Em análise'
        RESOLVED='resolved','Resolvido'
    number=models.PositiveIntegerField(unique=True,null=True,editable=False)
    student=models.ForeignKey('users.StudentProfile',on_delete=models.PROTECT,related_name='tickets')
    subject=models.ForeignKey(SupportSubject,on_delete=models.PROTECT)
    title=models.CharField(max_length=200)
    body=models.TextField()
    device=models.CharField(max_length=12,choices=[(x,x) for x in ('Computador','Celular','Tablet')])
    is_private=models.BooleanField(default=False)
    status=models.CharField(max_length=12,choices=Status.choices,default=Status.OPEN)
    answer=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    resolved_at=models.DateTimeField(null=True,blank=True)
    class Meta:ordering=['-created_at']
    @property
    def public_name(self):
        parts=(self.student.full_name or '').split()
        return (parts[0]+(' '+parts[-1][0]+'.' if len(parts)>1 else '')) if parts else 'Aluno'

class TicketEvent(models.Model):
    ticket=models.ForeignKey(Ticket,on_delete=models.PROTECT,related_name='events')
    status=models.CharField(max_length=12,choices=Ticket.Status.choices)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    note=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:ordering=['created_at','pk']

class TicketVote(models.Model):
    ticket=models.ForeignKey(Ticket,on_delete=models.CASCADE,related_name='votes')
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    class Meta:constraints=[models.UniqueConstraint(fields=['ticket','user'],name='support_ticket_vote_unique')]
