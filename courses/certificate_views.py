from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods
from django.contrib import messages
from django.utils import timezone
from users.models import SiteSettings

from .access import access_decision
from .models import Certificate, Course, Enrollment
from .selectors import progress_info, certificate_requirements, member_course_items
from .services import issue_enrollment_certificate, profile_data_ok, update_certificate_data, issue_certificate_with_data
from .forms import CertificateDataForm


@login_required
@require_http_methods(['GET', 'POST'])
def certificates(request):
    if request.user.role != "STUDENT":
        return redirect("painel:dashboard")
    student = request.user.student_profile
    if request.method == 'POST':
        raw = request.POST.get('enrollment_id', '')
        if not raw.isdigit() or len(raw) > 18:
            from django.http import Http404
            raise Http404
        enrollment = get_object_or_404(Enrollment, pk=int(raw), student=student)
        form = CertificateDataForm(request.POST, profile=student, prefix=f'enrollment-{enrollment.pk}')
        if form.is_valid():
            try:
                update_certificate_data(student, **form.cleaned_data)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, 'Dados do certificado salvos.')
                return redirect('certificates')
        return _certificate_list(request, student, bound=(enrollment.pk, form), status=400)
    return _certificate_list(request, student)


def _certificate_list(request, student, *, bound=None, status=200):
    items = member_course_items(student)
    for item in items:
        item['form'] = bound[1] if bound and bound[0] == item['enrollment'].pk else CertificateDataForm(profile=student, prefix=f'enrollment-{item["enrollment"].pk}')
        item['academic_ready'] = item['all_lessons'] and (not item['has_final'] or item['final_best_score'] is not None and item['final_best_score'] >= 70)
    return render(request, 'courses/certificates.html', {'items':items, 'data_ok':profile_data_ok(student)}, status=status)


@login_required
@require_http_methods(["GET", "POST"])
def issue_certificate(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    if request.user.role != "STUDENT":
        return redirect("course_preview", course_slug=course_slug)
    student = request.user.student_profile
    enrollment = Enrollment.objects.filter(student=student, course=course).first()
    if not enrollment:
        return redirect("course_preview", course_slug=course_slug)
    certificate = Certificate.objects.filter(enrollment=enrollment).first()
    if certificate is None and request.method == 'POST' and request.POST.get('action') == 'save_and_issue':
        form = CertificateDataForm(request.POST, profile=student, prefix=f'enrollment-{enrollment.pk}')
        if form.is_valid():
            try:
                issue_certificate_with_data(enrollment, **form.cleaned_data)
            except ValidationError as exc:
                student.refresh_from_db()
                form.add_error(None, exc)
            else:
                return redirect('issue_certificate', course_slug=course.slug)
        return _certificate_list(request, student, bound=(enrollment.pk, form), status=400)
    if certificate is None:
        requirements = certificate_requirements(enrollment)
        decision = requirements['access']
        if not decision.allowed and not requirements['can_issue']:
            return render(
                request,
                "courses/access_pending.html",
                {"course": course, "access": decision},
                status=403,
            )
        info = progress_info(student, course)
        context = {
            "course": course,
            "completed_count": info["completed"],
            "total": info["total"],
            "remaining": info["total"] - info["completed"],
            "pct": info["pct"],
            "next_lesson": info["next_lesson"],
            "progress_ok": requirements['all_lessons'] and requirements['final_passed'],
            'requirements': requirements,
            "data_ok": profile_data_ok(student),
        }
        if not context["progress_ok"] or not context["data_ok"]:
            return render(request, "courses/certificate_error.html", context)
        if request.method == "GET":
            return render(request, "courses/certificate_ready.html", context)
        try:
            issue_enrollment_certificate(enrollment)
        except ValidationError:
            return render(
                request, "courses/certificate_error.html", context, status=400
            )
        return redirect("issue_certificate", course_slug=course.slug)
    if request.method == "POST":
        return redirect("issue_certificate", course_slug=course.slug)
    verify_url = (
        request.build_absolute_uri(reverse("verify_certificate"))
        + "?codigo="
        + certificate.code
    )
    issued = timezone.localtime(certificate.issued_at)
    school = SiteSettings.load().school_name
    linkedin_details = '\n'.join([
        'Nome: '+certificate.course_title, 'Instituição: '+school,
        f'Emissão: {issued.month:02d}/{issued.year}', 'Código: '+certificate.code,
        'URL de validação: '+verify_url,
    ])
    return render(
        request,
        "courses/certificate.html",
        {"certificate": certificate, "verify_url": verify_url,
         'linkedin_url':'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME',
         'linkedin_details':linkedin_details},
    )


@require_GET
def verify_certificate(request):
    query = request.GET.get("codigo", "").strip()
    code = "".join(ch for ch in query.upper() if ch.isalnum())
    certificate = Certificate.objects.filter(code=code).first() if code else None
    return render(
        request,
        "courses/verify_certificate.html",
        {"query": query, "certificate": certificate, "searched": bool(query)},
    )
