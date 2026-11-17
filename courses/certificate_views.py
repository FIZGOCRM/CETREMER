from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from .access import access_decision
from .models import Certificate, Course, Enrollment
from .selectors import progress_info
from .services import issue_enrollment_certificate, profile_data_ok


@login_required
@require_GET
def certificates(request):
    if request.user.role != "STUDENT":
        return redirect("painel:dashboard")
    student = request.user.student_profile
    items = []
    for enrollment in (
        Enrollment.objects.filter(student=student)
        .select_related("course")
        .order_by("-enrolled_at")
    ):
        info = progress_info(student, enrollment.course)
        info["remaining"] = info["total"] - info["completed"]
        info["certificate"] = Certificate.objects.filter(enrollment=enrollment).first()
        items.append(info)
    return render(
        request,
        "courses/certificates.html",
        {"items": items, "data_ok": profile_data_ok(student)},
    )


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
    if certificate is None:
        decision = access_decision(enrollment)
        if not decision.allowed:
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
            "progress_ok": info["status"] == "done",
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
    return render(
        request,
        "courses/certificate.html",
        {"certificate": certificate, "verify_url": verify_url},
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
