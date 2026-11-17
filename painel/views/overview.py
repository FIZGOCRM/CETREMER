from django.contrib.auth import get_user_model
from core.decorators import painel_required
from courses.models import Course,Enrollment
from courses.access import access_decision
from .common import page

@painel_required
def dashboard(request):
    enrollments=Enrollment.objects.select_related('course','student__user').prefetch_related('access_periods')
    return page(request,'dashboard',courses_count=Course.objects.count(),students_count=get_user_model().objects.filter(role='STUDENT',student_profile__enrollments__isnull=False).distinct().count(),active_enrollments=sum(access_decision(e).allowed for e in enrollments),recent_enrollments=enrollments.order_by('-enrolled_at')[:5])
