from django.shortcuts import get_object_or_404,redirect
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.db.models import Q
from core.decorators import painel_required
from users.models import User
from users.member_preview import SESSION_KEY,begin_preview,finish_preview
from .common import page

@painel_required
@require_GET
def preview_choose(request):
    users=User.objects.filter(role='STUDENT',is_active=True).select_related('student_profile').order_by('username')
    q=request.GET.get('q','').strip()
    if q:users=users.filter(Q(email__icontains=q)|Q(student_profile__full_name__icontains=q)|Q(username__icontains=q))
    return page(request,'preview_choose',students=Paginator(users,25).get_page(request.GET.get('page')),q=q)

@painel_required
@require_GET
def preview_start(request,student_id):
    student=get_object_or_404(User,pk=student_id,role='STUDENT',is_active=True)
    request.session[SESSION_KEY]=begin_preview(request.user,student,request.session.get(SESSION_KEY))
    return redirect('dashboard')

@painel_required
@require_GET
def preview_end(request):
    finish_preview(request.user,request.session.get(SESSION_KEY))
    request.session.pop(SESSION_KEY,None)
    return redirect('painel:students')
