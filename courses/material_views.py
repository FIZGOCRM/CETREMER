from urllib.parse import urlparse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET
from .access import access_decision, require_lesson_access
from .forms import MaterialFilterForm
from .models import Course, CourseMaterial, Enrollment, LessonMaterial
from .selectors import library_items
from .services import mark_material_open


def deny_direct_material(request, *args, **kwargs):
    raise Http404


@login_required
@require_GET
def open_material(request, kind, material_id):
    if kind == 'lesson':
        material = get_object_or_404(LessonMaterial.objects.select_related('lesson__module__course'),pk=material_id)
    elif kind == 'course':
        material = get_object_or_404(CourseMaterial.objects.select_related('course'),pk=material_id)
    else:
        raise Http404
    student = None
    if request.user.role == 'STUDENT':
        student = request.user.student_profile
        try:
            if kind == 'lesson':
                require_lesson_access(student, material.lesson)
            else:
                enrollment = Enrollment.objects.filter(student=student,course=material.course).prefetch_related('access_periods').first()
                if not material.course.is_published or not material.is_active or not access_decision(enrollment).allowed:
                    raise PermissionDenied('Este material não está disponível para seu plano.')
        except PermissionDenied as exc:
            return render(request,'courses/material_unavailable.html',{'message':str(exc)},status=403)
    elif request.user.role not in ('ADMIN','CREATOR'):
        raise PermissionDenied
    if material.file:
        try:
            stream = material.file.open('rb')
        except (FileNotFoundError, OSError):
            raise Http404('O arquivo ainda não está disponível.')
        response = FileResponse(stream, content_type='application/pdf', as_attachment=request.GET.get('download') == '1')
    elif kind == 'lesson' and material.url and urlparse(material.url).scheme in ('http','https'):
        response = redirect(material.url)
    else:
        raise Http404('A equipe precisa enviar o arquivo deste material.')
    if student and not getattr(request, 'member_preview', False):
        mark_material_open(student,kind,material.pk)
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@login_required
@require_GET
def ebooks(request):
    if request.user.role != 'STUDENT':
        return redirect('painel:dashboard')
    student = request.user.student_profile
    form = MaterialFilterForm(request.GET)
    valid = form.is_valid()
    filters = form.cleaned_data if valid else {}
    return render(request, 'courses/ebooks.html', {'items':library_items(student, **filters) if valid else [],
        'form':form,'courses':Course.objects.filter(enrollments__student=student,is_published=True).order_by('title'), 'selected_course':filters.get('course')},status=200 if valid else 400)
