from django.contrib import messages
from django.core.exceptions import PermissionDenied,ValidationError
from django.shortcuts import get_object_or_404,redirect
from community.access import is_team
from core.decorators import painel_required
from support.models import FaqItem,SupportSubject,Ticket
from support.forms import FaqForm,SubjectForm
from support.services import update_ticket,save_setting
from support.selectors import visible_tickets
from .common import page

@painel_required
def tickets(request):
    if not is_team(request.user):raise PermissionDenied
    if request.method=='POST':
        ticket=get_object_or_404(Ticket,pk=request.POST.get('ticket_id'))
        try:
            update_ticket(request.user,ticket,status=request.POST.get('status'),answer=request.POST.get('answer'),note=request.POST.get('note',''))
            messages.success(request,'Chamado atualizado com histórico.')
        except ValidationError as exc:messages.error(request,' '.join(exc.messages))
        return redirect(request.get_full_path())
    tickets=visible_tickets(request.user).prefetch_related('events')
    status=request.GET.get('status','active')
    tickets=tickets.filter(status='resolved') if status=='resolved' else tickets.exclude(status='resolved')
    return page(request,'tickets',tickets=tickets,tab=status)

@painel_required
def support_settings(request,kind):
    if not is_team(request.user):raise PermissionDenied
    model,form_class=(FaqItem,FaqForm) if kind=='faq' else (SupportSubject,SubjectForm)
    instance=get_object_or_404(model,pk=request.GET['id']) if request.GET.get('id') else None
    form=form_class(request.POST or None,instance=instance)
    if request.method=='POST' and form.is_valid():
        save_setting(request.user,form.save(commit=False));messages.success(request,'Configuração salva.')
        return redirect('painel:support_settings',kind=kind)
    return page(request,'support_settings',items=model.objects.all(),form=form,kind=kind)
