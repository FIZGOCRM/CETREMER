"""Compatibility URLs for the private V1; public sales are outside this release."""
from django.shortcuts import get_object_or_404,redirect
from .models import Course


def landing(request):
    if not request.user.is_authenticated:return redirect('login')
    return redirect('dashboard' if request.user.role=='STUDENT' else 'painel:dashboard')


def course_preview(request,course_slug):
    course=get_object_or_404(Course,slug=course_slug)
    if not request.user.is_authenticated:return redirect('login')
    if request.user.role=='STUDENT':return redirect('member_course',course_slug=course.slug)
    return redirect('painel:course_edit',course_id=course.pk)
