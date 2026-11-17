"""HTTP adapters for checkout. Payment processing requires a real gateway."""

from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.http import json_error
from courses.access import has_course_access
from courses.models import Course, Lesson
from users.models import User


@require_GET
def checkout(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    if request.user.is_authenticated and request.user.role == User.Role.STUDENT:
        if has_course_access(request.user.student_profile, course):
            first_lesson = (
                Lesson.objects.filter(module__course=course)
                .order_by(
                    "module__order",
                    "order",
                    "id",
                )
                .first()
            )
            if first_lesson:
                return redirect(
                    "lesson_detail", course_slug=course.slug, lesson_id=first_lesson.id
                )
            return redirect("course_preview", course_slug=course.slug)
    return render(request, "sales/checkout.html", {"course": course})


@require_POST
def process_checkout(request, course_slug):
    get_object_or_404(Course, slug=course_slug, is_published=True)
    if request.user.is_authenticated and request.user.role != User.Role.STUDENT:
        return json_error(
            "Acesso exclusivo para alunos.", status=403, code="student_required"
        )
    # No account, session, order or enrollment changes before gateway integration.
    return json_error(
        "Compras online temporariamente indisponíveis. Entre em contato com a equipe.",
        status=503,
        code="checkout_unavailable",
    )
