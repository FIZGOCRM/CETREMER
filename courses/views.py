from django.shortcuts import get_object_or_404, render

from .access import access_decision
from .models import Course, Enrollment, Lesson, Module


def landing(request):
    """Lists published courses on landing page, checking enrollment details if logged in."""
    courses = Course.objects.filter(is_published=True).select_related(
        "creator__user", "category"
    )
    # Query active Hero Banner
    from .models import Category, HeroBanner

    hero = HeroBanner.objects.filter(is_active=True).first()

    enrolled_courses = []
    if request.user.is_authenticated:
        if request.user.role == "STUDENT":
            student_profile = request.user.student_profile
            # Check enrolled courses using direct Enrollment model
            enrolled_courses = Course.objects.filter(
                enrollments__student=student_profile
            )

    return render(
        request,
        "landing.html",
        {
            "courses": courses,
            "enrolled_courses": enrolled_courses,
            "hero": hero,
            "categories": Category.objects.all(),
        },
    )


def course_preview(request, course_slug):
    """Renders the public Udemy-style course landing/preview page with syllabus and buy options."""
    course = get_object_or_404(Course, slug=course_slug)

    is_enrolled = False
    decision = access_decision(None)
    if request.user.is_authenticated:
        if request.user.role == "STUDENT":
            student_profile = request.user.student_profile
            enrollment = (
                Enrollment.objects.filter(student=student_profile, course=course)
                .prefetch_related("access_periods")
                .first()
            )
            is_enrolled = enrollment is not None
            decision = access_decision(enrollment)

    from django.db.models import Prefetch
    modules = Module.objects.filter(course=course, status='published').prefetch_related(Prefetch('lessons', queryset=Lesson.objects.filter(status='published')))
    total_lessons = Lesson.objects.filter(module__course=course, status='published', module__status='published').count()
    first_lesson = (
        Lesson.objects.filter(module__course=course, status='published', module__status='published')
        .order_by("module__order", "order", "id")
        .first()
    )
    from .selectors import ordered_lessons, progress_info

    lessons = ordered_lessons(course)
    next_lesson = first_lesson
    if is_enrolled:
        next_lesson = progress_info(request.user.student_profile, course, lessons)[
            "next_lesson"
        ]

    # Calculate total duration
    total_seconds = sum(l.duration_seconds for m in modules for l in m.lessons.all())
    total_hours = total_seconds // 3600
    total_minutes = (total_seconds % 3600) // 60

    duration_str = ""
    if total_hours > 0:
        duration_str += f"{total_hours}h "
    duration_str += f"{total_minutes}min"

    return render(
        request,
        "courses/course_preview.html",
        {
            "course": course,
            "modules": modules,
            "total_lessons": total_lessons,
            "duration_str": duration_str,
            "is_enrolled": is_enrolled,
            "course_access": decision,
            "first_lesson": first_lesson,
            "next_lesson": next_lesson,
            "total_seconds": total_seconds,
            "has_materials": Lesson.objects.filter(
                module__course=course, materials__isnull=False
            ).exists(),
        },
    )
