import secrets
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from users.validators import validate_cpf
from .models import Certificate, Course, Enrollment, Progress
from .student_views import ordered_lessons, progress_info


@login_required
@require_GET
def certificates(request):
    if request.user.role != 'STUDENT':
        return redirect('painel:dashboard')
    student = request.user.student_profile
    items = []
    for enrollment in Enrollment.objects.filter(student=student).select_related('course').order_by('-enrolled_at'):
        info = progress_info(student, enrollment.course)
        info['remaining'] = info['total'] - info['completed']
        info['certificate'] = Certificate.objects.filter(enrollment=enrollment).first()
        items.append(info)
    return render(request, 'courses/certificates.html', {'items': items, 'data_ok': profile_data_ok(student)})


def profile_data_ok(profile):
    if not profile.full_name:
        return False
    try:
        validate_cpf(profile.cpf)
    except ValidationError:
        return False
    return True


@login_required
@require_GET
def issue_certificate(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    if request.user.role != 'STUDENT':
        return redirect('course_preview', course_slug=course_slug)
    student = request.user.student_profile
    enrollment = Enrollment.objects.filter(student=student, course=course).first()
    if not enrollment:
        return redirect('course_preview', course_slug=course_slug)
    info = progress_info(student, course)
    progress_ok = info['status'] == 'done'
    data_ok = profile_data_ok(student)
    if not progress_ok or not data_ok:
        return render(request, 'courses/certificate_error.html', {'course': course,
            'completed_count': info['completed'], 'total': info['total'],
            'remaining': info['total'] - info['completed'], 'pct': info['pct'],
            'next_lesson': info['next_lesson'], 'progress_ok': progress_ok, 'data_ok': data_ok})
    certificate = Certificate.objects.filter(enrollment=enrollment).first()
    if certificate is None:
        code = secrets.token_hex(6).upper()
        while Certificate.objects.filter(code=code).exists():
            code = secrets.token_hex(6).upper()
        certificate = Certificate.objects.create(enrollment=enrollment, code=code,
            student_name=student.full_name, student_cpf=validate_cpf(student.cpf),
            course_title=course.title, workload_hours=course.workload_hours,
            completed_at=timezone.now())
    verify_url = request.build_absolute_uri(reverse('verify_certificate')) + '?codigo=' + certificate.code
    return render(request, 'courses/certificate.html', {'certificate': certificate, 'verify_url': verify_url})


@require_GET
def verify_certificate(request):
    query = request.GET.get('codigo', '').strip()
    code = ''.join(ch for ch in query.upper() if ch.isalnum())
    certificate = Certificate.objects.filter(code=code).first() if code else None
    return render(request, 'courses/verify_certificate.html', {'query': query,
        'certificate': certificate, 'searched': bool(query)})
