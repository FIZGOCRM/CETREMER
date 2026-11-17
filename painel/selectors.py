"""Read models for the producer interface; no business mutations."""
from community.models import CommunityPost
from courses.models import Enrollment
from courses.services import plan_status
from support.models import Ticket


def panel_counts():
    expiring=sum(plan_status(e)['state']=='ending_soon' for e in Enrollment.objects.select_related('course').prefetch_related('access_periods','access_changes'))
    return {'community':CommunityPost.objects.filter(is_hidden=False,team_status__in=['new','forwarded']).count(),'tickets':Ticket.objects.exclude(status='resolved').count(),'expiring':expiring}
