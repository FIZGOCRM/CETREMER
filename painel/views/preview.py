from django.shortcuts import get_object_or_404,redirect
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from courses.models import Course
from courses.access import has_course_access
from core.decorators import painel_required
from users.models import User
from users.member_preview import SESSION_KEY,begin_preview,finish_preview
from .common import page

@painel_required
@require_GET
def preview_choose(request):
    users=User.objects.filter(role='STUDENT',is_active=True).select_related('student_profile').annotate(
        total_courses=Count('student_profile__enrollments', distinct=True)).order_by('username')
    q=request.GET.get('q','').strip()
    course = get_object_or_404(Course, pk=request.GET['curso']) if request.GET.get('curso','').isdigit() else None
    if course:
        users = users.filter(student_profile__enrollments__course=course).distinct()
    if q:users=users.filter(Q(email__icontains=q)|Q(student_profile__full_name__icontains=q)|Q(username__icontains=q))
    return page(request,'preview_choose',students=Paginator(users,25).get_page(request.GET.get('page')),q=q,course=course)

@painel_required
@require_GET
def preview_start(request,student_id):
    student=get_object_or_404(User,pk=student_id,role='STUDENT',is_active=True)
    target=request.GET.get('next','')
    if target.startswith('/painel/') and url_has_allowed_host_and_scheme(target, {request.get_host()}):
        request.session['preview_return'] = target
    elif SESSION_KEY not in request.session:
        request.session['preview_return'] = reverse('painel:students')
    request.session[SESSION_KEY]=begin_preview(request.user,student,request.session.get(SESSION_KEY))
    course = Course.objects.filter(pk=request.GET['curso']).first() if request.GET.get('curso','').isdigit() else None
    if course and has_course_access(student.student_profile, course):
        return redirect('course_home', course.slug)
    return redirect('dashboard')

@painel_required
@require_GET
def preview_end(request):
    finish_preview(request.user,request.session.get(SESSION_KEY))
    request.session.pop(SESSION_KEY,None)
    return redirect(request.session.pop('preview_return', reverse('painel:students')))
