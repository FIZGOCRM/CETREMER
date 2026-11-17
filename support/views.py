from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError,PermissionDenied
from django.shortcuts import get_object_or_404,render,redirect
from django.views.decorators.http import require_POST
from .access import require_ticket_access,can_view_cohort
from .forms import TicketForm
from .models import Ticket
from .selectors import support_search
from .services import create_ticket,toggle_vote

@login_required
def hub(request):
    if request.user.role!='STUDENT':return redirect('painel:tickets')
    faqs,tickets,tab=support_search(request.user,request.GET)
    return render(request,'support/hub.html',{'faqs':faqs,'tickets':tickets,'tab':tab})

@login_required
def new_ticket(request):
    if request.user.role!='STUDENT':raise PermissionDenied
    form=TicketForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        try:
            ticket=create_ticket(request.user,**form.cleaned_data)
            return redirect('support_ticket',ticket_id=ticket.pk)
        except ValidationError as exc:form.add_error(None,exc)
    return render(request,'support/new_ticket.html',{'form':form})

@login_required
def ticket_detail(request,ticket_id):
    ticket=get_object_or_404(Ticket.objects.select_related('student__user','subject'),pk=ticket_id)
    require_ticket_access(request.user,ticket)
    return render(request,'support/ticket.html',{'ticket':ticket,'events':ticket.events.all(),'can_vote':not ticket.is_private and can_view_cohort(request.user)})

@login_required
@require_POST
def vote(request,ticket_id):
    ticket=get_object_or_404(Ticket,pk=ticket_id);toggle_vote(request.user,ticket)
    return redirect('support_ticket',ticket_id=ticket.pk)
