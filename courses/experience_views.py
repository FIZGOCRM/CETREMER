from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from . import experience_selectors as shelves
from .access import access_decision, accessible_courses
from .models import Course, Enrollment
from .services import plan_status


def enrolled_page(view):
    @login_required
    @require_GET
    @wraps(view)
    def wrapped(request, course_slug):
        if request.user.role != "STUDENT":
            return redirect("painel:dashboard")
        course = get_object_or_404(Course, slug=course_slug, is_published=True)
        enrollment = Enrollment.objects.filter(student=request.user.student_profile, course=course
                                                ).select_related("course", "student").prefetch_related("access_periods").first()
        decision = access_decision(enrollment)
        if not decision.allowed:
            return render(request, "courses/access_pending.html", {
                "course": course, "access": decision, "plan": plan_status(enrollment) if enrollment else None
            }, status=403)
        request.session["active_course_slug"] = course.slug
        return view(request, enrollment)
    return wrapped


@login_required
@require_GET
def choose_course(request, section):
    if request.user.role != "STUDENT":
        return redirect("painel:dashboard")
    target = {"inicio": "course_home", "trilha": "course_trail", "minha-lista": "course_saved",
              "ebooks": "course_ebooks", "ao-vivo": "course_live"}.get(section)
    if not target:
        raise Http404
    courses = list(accessible_courses(request.user.student_profile).order_by("title"))
    selected = next((course for course in courses if course.slug == request.session.get("active_course_slug")), None)
    if selected or len(courses) == 1:
        return redirect(target, (selected or courses[0]).slug)
    return render(request, "courses/choose_course.html", {"choices": courses, "target": target})


def render_home(request, enrollment, **extra):
    cards = shelves.course_lessons(enrollment)
    interrupted = shelves.interrupted_lessons(cards)
    next_lesson = next((card for card in cards.values() if not card["completed"]), None)
    upcoming, past = shelves.course_events(enrollment)
    return render(request, "courses/course_home.html", {
        "course": enrollment.course, "interrupted": interrupted, "resume": interrupted[0] if interrupted else next_lesson,
        "started_course": bool(interrupted or any(card["completed"] for card in cards.values())),
        "weekly": shelves.weekly_lessons(enrollment.course, cards), "news": shelves.course_news(enrollment, cards, past)[:6],
        "saved": shelves.saved_lessons(enrollment, cards)[:6], "upcoming": upcoming,
        "offers": shelves.other_courses(enrollment.student), **extra,
    })


@enrolled_page
def home(request, enrollment):
    return render_home(request, enrollment)


@enrolled_page
def news(request, enrollment):
    cards = shelves.course_lessons(enrollment)
    _, past = shelves.course_events(enrollment)
    return render(request, "courses/course_news.html", {
        "course": enrollment.course, "news": shelves.course_news(enrollment, cards, past)
    })


@enrolled_page
def saved(request, enrollment):
    cards = shelves.course_lessons(enrollment)
    return render(request, "courses/course_saved.html", {
        "course": enrollment.course, "saved": shelves.saved_lessons(enrollment, cards)
    })


@enrolled_page
def live(request, enrollment):
    upcoming, past = shelves.course_events(enrollment)
    return render(request, "courses/live_classes.html", {"course": enrollment.course, "upcoming": upcoming, "past": past})


@enrolled_page
def trail(request, enrollment):
    library = shelves.module_library(enrollment)
    modules = library["modules"]
    selected = request.GET.get("tema", "")
    groups = [g for g in modules if str(g["module"].pk) == selected] if selected else modules
    if selected and not groups:
        raise Http404
    return render(request, "courses/course_trail.html", {
        "course": enrollment.course, "themes": modules, "groups": groups, "selected": selected,
    })


@enrolled_page
def ebooks(request, enrollment):
    return render(request, "courses/ebooks.html", {"course": enrollment.course, **shelves.module_library(enrollment)})
