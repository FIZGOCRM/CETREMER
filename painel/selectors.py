"""Read models for the producer interface; no business mutations."""
from community.models import CommunityPost
from courses.models import Enrollment
from courses.services import plan_status
from support.models import Ticket


def panel_counts():
    expiring=sum(plan_status(e)['state']=='ending_soon' for e in Enrollment.objects.select_related('course').prefetch_related('access_periods','access_changes'))
    return {'community':CommunityPost.objects.filter(is_hidden=False,team_status__in=['new','forwarded']).count(),'tickets':Ticket.objects.exclude(status='resolved').count(),'expiring':expiring}

def course_overview(course):
    from django.utils import timezone
    from courses.access import access_decision,module_release_date
    from courses.models import Lesson,Module
    from users.models import User
    today=timezone.localdate()
    enrollments=list(Enrollment.objects.filter(course=course).select_related('course','student__user').prefetch_related('access_periods','access_changes'))
    active=[e for e in enrollments if access_decision(e).allowed]
    published=Lesson.objects.filter(module__course=course,status='published',module__status='published').count()
    releases=[]
    for module in Module.objects.filter(course=course,status='published').order_by('order','pk'):
        dates=[module_release_date(e,module) for e in active]
        future=[value for value in dates if value and value>today]
        if future:releases.append({'module':module,'date':min(future),'students':len(future)})
    releases.sort(key=lambda item:item['date'])
    return {'active_students':len(active),'published':published,'draft':Lesson.objects.filter(module__course=course).count()-published,
        'questions':CommunityPost.objects.filter(course=course,is_hidden=False,team_status__in=['new','forwarded']).count(),
        'tickets':Ticket.objects.filter(student_id__in=[e.student_id for e in enrollments]).exclude(status='resolved').count(),
        'missing_vimeo':Lesson.objects.filter(module__course=course,vimeo_id='').count(),
        'expiring':sum(plan_status(e)['state']=='ending_soon' for e in enrollments),'releases':releases}
