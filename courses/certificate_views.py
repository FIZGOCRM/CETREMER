"""Certificados do aluno (HANDOFF-v2 7.5): lista, emissão no painel lateral, certificado e verificação pública."""
import logging
import secrets
from urllib.parse import urlencode

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from core.ajax import json_errors, json_ok, wants_json
from core.activity import log_certificate
from core.toasts import toast
from users.models import SiteSettings
from users.validators import validate_cpf
from .home_views import _bulk_progress
from .models import Certificate, Course, Enrollment, Progress

logger = logging.getLogger(__name__)
ISSUED_TOAST = 'Certificado emitido. Enviamos o link para seu e-mail'


def profile_data_ok(profile):
    if not profile.full_name:
        return False
    try:
        validate_cpf(profile.cpf)
    except ValidationError:
        return False
    return True


def verify_link(request, certificate):
    return request.build_absolute_uri(reverse('verify_certificate')) + '?codigo=' + certificate.code


def linkedin_url(request, certificate, school_name):
    issued = timezone.localtime(certificate.issued_at)
    params = {'startTask': 'CERTIFICATION_NAME', 'name': certificate.course_title, 'organizationName': school_name,
              'issueYear': issued.year, 'issueMonth': issued.month, 'certUrl': verify_link(request, certificate),
              'certId': certificate.code}
    return 'https://www.linkedin.com/profile/add?' + urlencode(params)


def _eligible_enrollments(student):
    return (Enrollment.objects.filter(student=student, is_active=True, course__certificate_enabled=True)
            .exclude(course__status='archived').select_related('course__category').order_by('-enrolled_at'))


@login_required
@require_GET
def certificates(request):
    if request.user.role != 'STUDENT':
        return redirect('painel:dashboard')
    student = request.user.student_profile
    enrollments = list(_eligible_enrollments(student))
    progress = _bulk_progress(request.user, student, [e.course_id for e in enrollments])
    issued = {c.enrollment_id: c for c in Certificate.objects.filter(enrollment__in=enrollments)}
    data_ok = profile_data_ok(student)
    school_name = SiteSettings.load().school_name

    items = []
    for enrollment in enrollments:
        info = progress[enrollment.course_id]
        certificate = issued.get(enrollment.id)
        done = bool(info['total']) and info['done'] == info['total']
        state = 'issued' if certificate else 'ready' if done else 'progress'
        item = {'course': enrollment.course, 'enrollment': enrollment, 'state': state, 'done': info['done'], 'total': info['total'],
                'remaining': info['remaining'], 'pct': info['pct'], 'certificate': certificate, 'data_ok': data_ok,
                'started': info['started'] or info['done'] > 0, 'next_lesson': info['resume_lesson'],
                'completed_on': info['last_seen_at']}
        if certificate:
            item['verify_url'] = verify_link(request, certificate)
            item['linkedin_url'] = linkedin_url(request, certificate, school_name)
        items.append(item)
    order = {'ready': 0, 'issued': 1, 'progress': 2}
    items.sort(key=lambda item: order[item['state']])
    stats = {'issued': sum(i['state'] == 'issued' for i in items), 'ready': sum(i['state'] == 'ready' for i in items),
             'in_progress': sum(i['state'] == 'progress' for i in items)}
    wanted = request.GET.get('emitir')
    open_issue = wanted if any(i['state'] == 'ready' and i['course'].slug == wanted for i in items) else ''
    return render(request, 'courses/certificates.html', {
        'stats': stats, 'items': items, 'open_issue': open_issue,
        'profile_name': student.full_name or '', 'profile_cpf': student.cpf or '',
        'profile_cpf_masked': f'***.{student.cpf[3:6]}.{student.cpf[6:9]}-**' if student.cpf and len(student.cpf) == 11 else '***.***.***-**',
    })


@login_required
@require_GET
def issue_certificate(request, course_slug):
    """Mostra o certificado emitido. Nunca emite ao abrir a URL: a emissão é o POST de `certificate_issue`."""
    course = get_object_or_404(Course, slug=course_slug)
    if request.user.role != 'STUDENT':
        return redirect('course_preview', course_slug=course_slug)
    student = request.user.student_profile
    enrollment = Enrollment.objects.filter(student=student, course=course).first()
    if not enrollment:
        return redirect('course_preview', course_slug=course_slug)
    certificate = Certificate.objects.filter(enrollment=enrollment).first()
    if certificate:
        return render(request, 'courses/certificate.html', {'certificate': certificate, 'verify_url': verify_link(request, certificate)})
    if not course.certificate_enabled:
        raise Http404
    info = _bulk_progress(request.user, student, [course.id])[course.id]
    progress_ok = bool(info['total']) and info['done'] == info['total']
    return render(request, 'courses/certificate_error.html', {
        'course': course, 'completed_count': info['done'], 'total': info['total'], 'remaining': info['remaining'],
        'pct': info['pct'], 'next_lesson': info['resume_lesson'], 'progress_ok': progress_ok, 'data_ok': profile_data_ok(student)})


class CertificateIssueForm(forms.Form):
    full_name = forms.CharField(max_length=255, error_messages={'required': 'Informe seu nome completo.'})
    cpf = forms.CharField(error_messages={'required': 'CPF inválido. Confira os números.'})
    confirm = forms.BooleanField(error_messages={'required': 'Confirme que conferiu seu nome e CPF.'})

    def clean_full_name(self):
        return ' '.join(self.cleaned_data['full_name'].split())

    def clean_cpf(self):
        return validate_cpf(self.cleaned_data['cpf'])


def _send_issued_email(request, certificate):
    link = request.build_absolute_uri(reverse('issue_certificate', args=[certificate.enrollment.course.slug]))
    body = (f'Seu certificado do curso {certificate.course_title} foi emitido.\n\n'
            f'Para ver e baixar: {link}\n'
            f'Para conferir a autenticidade: {verify_link(request, certificate)}')
    try:
        send_mail(f'Seu certificado do {certificate.course_title}', body, None, [request.user.email], fail_silently=False)
    except Exception:
        logger.exception('Falha ao enviar o e-mail do certificado %s', certificate.code)


@login_required
@require_POST
def certificate_issue(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    if request.user.role != 'STUDENT':
        return redirect('course_preview', course_slug=course_slug)
    student = request.user.student_profile
    enrollment = Enrollment.objects.filter(student=student, course=course, is_active=True).first()
    if enrollment is None or not course.certificate_enabled:
        raise Http404
    back = reverse('certificates') + '?emitir=' + course.slug
    info = _bulk_progress(request.user, student, [course.id])[course.id]
    if not info['total'] or info['done'] != info['total']:
        message = 'Conclua todas as aulas para emitir o certificado.'
        if wants_json(request):
            return JsonResponse({'ok': False, 'errors': {}, 'error': message}, status=400)
        toast(request, message, level='error')
        return redirect(back)

    if Certificate.objects.filter(enrollment=enrollment).exists():
        if wants_json(request):
            return json_ok(toast=ISSUED_TOAST, reload=True)
        toast(request, ISSUED_TOAST)
        return redirect('certificates')

    form = CertificateIssueForm(request.POST)
    if not form.is_valid():
        if wants_json(request):
            return json_errors(form)
        toast(request, next(iter(form.errors.values()))[0], level='error')
        return redirect(back)

    student.full_name = form.cleaned_data['full_name']
    student.cpf = form.cleaned_data['cpf']
    student.save(update_fields=['full_name', 'cpf'])
    code = secrets.token_hex(6).upper()
    while Certificate.objects.filter(code=code).exists():
        code = secrets.token_hex(6).upper()
    finished = Progress.objects.filter(student=student, is_completed=True, lesson__module__course=course).order_by('-updated_at').first()
    certificate = Certificate.objects.create(
        enrollment=enrollment, code=code, student_name=student.full_name, student_cpf=student.cpf,
        course_title=course.title, workload_hours=course.workload_hours,
        completed_at=finished.updated_at if finished else timezone.now())
    _send_issued_email(request, certificate)
    log_certificate(request.user, course)
    if wants_json(request):
        return json_ok(toast=ISSUED_TOAST, reload=True)
    toast(request, ISSUED_TOAST)
    return redirect('certificates')


@require_GET
def verify_certificate(request):
    query = request.GET.get('codigo', '').strip()
    code = ''.join(ch for ch in query.upper() if ch.isalnum())
    certificate = Certificate.objects.filter(code=code).first() if code else None
    return render(request, 'courses/verify_certificate.html', {'query': query,
        'certificate': certificate, 'searched': bool(query)})
