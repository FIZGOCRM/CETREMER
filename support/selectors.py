from django.db.models import Q,Count
from community.access import is_team
from .models import FaqItem,Ticket
from .access import can_view_cohort

def visible_tickets(user):
    queryset=Ticket.objects.select_related('student__user','subject').annotate(vote_count=Count('votes'))
    if is_team(user):return queryset
    if user.role != 'STUDENT':return queryset.none()
    own=Q(student__user=user)
    return queryset.filter(own|Q(is_private=False)) if can_view_cohort(user) else queryset.filter(own)

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
