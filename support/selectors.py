from django.db.models import Q,Count
from community.access import is_team
from .models import FaqItem,Ticket

def visible_tickets(user):
    queryset=Ticket.objects.select_related('student__user','subject').annotate(vote_count=Count('votes'))
    if is_team(user):return queryset
    return queryset.filter(Q(is_private=False)|Q(student__user=user))

def support_search(user,params):
    faqs=FaqItem.objects.filter(is_published=True)
    tickets=visible_tickets(user)
    tab=params.get('tab','faq')
    if tab=='mine':tickets=tickets.filter(student__user=user)
    else:tickets=tickets.filter(is_private=False)
    q=params.get('q','').strip()
    if q:
        faqs=faqs.filter(Q(question__icontains=q)|Q(answer__icontains=q))
        tickets=tickets.filter(Q(title__icontains=q)|Q(body__icontains=q)|Q(answer__icontains=q))
    return faqs,tickets,tab
