from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from community.models import CommunityPost
from community.selectors import visible_posts
from core.http import json_error

from .access import access_decision, accessible_courses, lesson_availability
from .models import Course, Enrollment, Lesson, Module, Progress
from .selectors import ordered_lessons, progress_info, course_modules, member_summary, lesson_quiz_state
from .services import set_lesson_progress, plan_status


@login_required
def dashboard(request):
    if request.user.role != "STUDENT":
        return redirect("painel:dashboard")
    student = request.user.student_profile
    summary = member_summary(student)
    items = summary['items']
    enrollments = [item['enrollment'] for item in items]
    continuing = [
        item
        for item in items
        if item["access"].allowed and item["status"] != "done" and item["next_lesson"]
    ]
    continuing.sort(
        key=lambda item: (
            item["enrollment"].last_accessed_at or item["enrollment"].enrolled_at
        ),
        reverse=True,
    )
    hero_courses = sorted(
        items,
        key=lambda item: item["enrollment"].last_accessed_at or item["enrollment"].enrolled_at,
        reverse=True,
    )
    live_item = next(
        (
            item
            for item in items
            if item["access"].allowed and item["course"].live_meet_url
        ),
        None,
    )
    other_courses = (
        Course.objects.filter(is_published=True)
        .exclude(id__in=[e.course_id for e in enrollments])
        .select_related("category")
    )
    return render(
        request,
        "courses/dashboard.html",
        {
            "continue_item": continuing[0] if continuing else None,
            "my_courses": items,
            'summary': summary,
            "hero_courses": hero_courses,
            "community_posts": visible_posts(request.user).filter(course__in=[e.course_id for e in enrollments]).order_by("-created_at")[:4],
            "completed_lesson_count": sum(item["completed"] for item in items),
            "live_item": live_item,
            "other_courses": other_courses,
            "featured": continuing[0] if continuing else next((item for item in items if item["access"].allowed), None),
        },
    )


@login_required
def member_course(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    if request.user.role != "STUDENT":
        return redirect("painel:dashboard")
    enrollment = Enrollment.objects.filter(student=request.user.student_profile, course=course).first()
    decision = access_decision(enrollment)
    if not decision.allowed:
        return render(request, "courses/access_pending.html", {"course": course, "access": decision, "plan": plan_status(enrollment) if enrollment else None}, status=403)
    lessons = ordered_lessons(course)
    info = progress_info(request.user.student_profile, course, lessons)
    info['certificate'] = getattr(enrollment, 'certificate', None)
    modules = course_modules(enrollment)
    done = set(Progress.objects.filter(student=request.user.student_profile, lesson__module__course=course, is_completed=True).values_list("lesson_id", flat=True))
    return render(request, "courses/course_detail.html", {
        "course": course, "modules": modules, "item": info,
        "community_posts": visible_posts(request.user).filter(course=course)[:8], "completed_ids": done,
        "total_seconds": sum(lesson.duration_seconds for lesson in lessons),
        "access": decision,
    })


@login_required
def member_section(request, section):
    if request.user.role != "STUDENT":
        return redirect("painel:dashboard")
    redirects={'notificacoes':'notifications','ajuda':'support'}
    if section in redirects:return redirect(redirects[section])
    if section != 'progresso':raise Http404
    if section == "progresso":
        summary = member_summary(request.user.student_profile)
        items = summary['items']
        return render(request, "courses/member_progress.html", {
            'summary': summary, "progress_items": items, "completed_count": summary['completed'],
        })
    raise Http404


@login_required
def lesson_detail(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    if request.user.role != "STUDENT":
        return redirect("course_preview", course_slug=course.slug)
    student = request.user.student_profile
    enrollment = Enrollment.objects.filter(student=student, course=course).first()
    if not enrollment:
        return render(request,"courses/access_pending.html",{"course":course,"access":access_decision(None)},status=403)
    decision = access_decision(enrollment)
    if not decision.allowed:
        return render(
            request,
            "courses/access_pending.html",
            {"course": course, "access": decision, "plan": plan_status(enrollment)},
            status=403,
        )
    availability = lesson_availability(enrollment, lesson)
    if availability.state == 'draft':
        raise Http404
    if availability.state != 'available':
        return render(request, 'courses/lesson_locked.html', {'course': course, 'availability': availability}, status=403)
    if not getattr(request,"member_preview",False):
        enrollment.last_accessed_at = timezone.now()
        enrollment.save(update_fields=["last_accessed_at"])
    lessons = ordered_lessons(course)
    info = progress_info(student, course, lessons)
    completed_ids = set(
        Progress.objects.filter(
            student=student, lesson__in=lessons, is_completed=True
        ).values_list("lesson_id", flat=True)
    )
    modules = course_modules(enrollment)
    for position, item in enumerate(lessons, 1):
        item.position = position
    by_id = {item.id: item for item in lessons}
    for module in modules:
        module.lessons_list = [
            by_id[item.id] for item in module.lessons.all() if item.id in by_id
        ]
        module.total_count = len(module.lessons_list)
        module.done_count = sum(
            item.id in completed_ids for item in module.lessons_list
        )
    index = next(i for i, item in enumerate(lessons) if item.id == lesson.id)
    posts = (
        CommunityPost.objects.filter(lesson=lesson, is_hidden=False)
        .select_related("author", "course")
        .prefetch_related("comments")
    )
    quiz_context = lesson_quiz_state(student, lesson)
    progress = Progress.objects.filter(student=student, lesson=lesson).first()
    return render(
        request,
        "courses/lesson_detail.html",
        {
            "course": course,
            "lesson": lesson,
            'progress': progress,
            **quiz_context,
            'watched_pct': min(100, round(100*progress.watched_seconds/lesson.duration_seconds)) if progress and lesson.duration_seconds else 0,
            'notes': lesson.notes.filter(student=student),
            "modules": modules,
            "completed_ids": completed_ids,
            "completed_count": info["completed"],
            "total": info["total"],
            "remaining": info["total"] - info["completed"],
            "pct": info["pct"],
            "total_seconds": sum(item.duration_seconds for item in lessons),
            "prev_lesson": next((l for l in reversed(lessons[:index]) if lesson_availability(enrollment, l, completed_ids=completed_ids).state == 'available'), None),
            "next_lesson_nav": next((l for l in lessons[index+1:] if lesson_availability(enrollment, l, completed_ids=completed_ids).state == 'available'), None),
            'next_release': info.get('next_release'),
            "lesson_index": index + 1,
            "is_completed": lesson.id in completed_ids,
            "materials": lesson.materials.all(),
            "posts": posts,
            "completed_lesson_ids": completed_ids,
            "total_lessons": info["total"],
            "completed_percent": info["pct"],
        },
    )


@login_required
@require_POST
def complete_lesson(request, lesson_id):
    return _progress_response(request, lesson_id, completed=True)


@login_required
@require_POST
def toggle_progress(request, lesson_id):
    return _progress_response(request, lesson_id)


def _progress_response(request, lesson_id, *, completed=None):
    lesson = get_object_or_404(
        Lesson.objects.select_related("module__course"), id=lesson_id
    )
    if request.user.role != "STUDENT":
        return json_error("Acesso negado.", status=403, code="student_required")
    try:
        result = set_lesson_progress(
            request.user.student_profile, lesson, completed=completed
        )
    except PermissionDenied as exc:
        return json_error(str(exc), status=403, code="enrollment_required")
    return JsonResponse(result)


@login_required
def live_classes(request):
    if request.user.role != "STUDENT":
        return redirect("painel:dashboard")
    courses = accessible_courses(request.user.student_profile).select_related(
        "category"
    )
    return render(
        request,
        "courses/live_classes.html",
        {
            "live_courses": [
                c for c in courses if c.live_meet_url or c.live_calendar_url
            ],
            "other_enrolled": [
                c for c in courses if not c.live_meet_url and not c.live_calendar_url
            ],
        },
    )


@login_required
def my_courses(request):
    if request.user.role!='STUDENT':return redirect('painel:courses')
    from .selectors import member_course_items
    return render(request,'courses/my_courses.html',{'my_courses':member_course_items(request.user.student_profile)})

@login_required
def search(request):
    if request.user.role!='STUDENT':return redirect('painel:courses')
    from .selectors import search_lessons
    term=request.GET.get('q','').strip()[:100]
    return render(request,'courses/search.html',{'results':search_lessons(request.user.student_profile,term) if term else [],'term':term})
