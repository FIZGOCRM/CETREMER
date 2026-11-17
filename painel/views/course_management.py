"""Management HTTP adapters: course_management."""

import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from core.decorators import painel_required
from courses.integrations.vimeo import video_duration
from courses.models import Category, Course, Enrollment, Lesson, Module
from courses.services import save_course, save_lesson, save_module, delete_content
from painel.forms import CourseForm, IdentifierForm, LessonForm, ModuleForm
from users.models import CreatorProfile

from .common import page


@painel_required
def courses(request):
    qs = Course.objects.select_related("category").annotate(
        lessons_count=Count("modules__lessons", distinct=True),
        students_count=Count("enrollments", distinct=True),
    )
    q = request.GET.get("q", "").strip()
    category = request.GET.get("categoria", "")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(short_name__icontains=q))
    if category:
        qs = qs.filter(category__slug=category)
    return page(
        request,
        "courses",
        courses=qs,
        categories=Category.objects.all(),
        q=q,
        category=category,
    )


def _creator(user):
    profile = CreatorProfile.objects.filter(user=user).first()
    return (
        profile
        or CreatorProfile.objects.first()
        or CreatorProfile.objects.create(user=user)
    )


@painel_required
def course_edit(request, course_id=None):
    course = get_object_or_404(Course, pk=course_id) if course_id else None
    data = request.POST.copy() if request.method == "POST" else None
    if data is not None:
        data["learning_objectives"] = "\n".join(
            x.strip() for x in request.POST.getlist("objectives") if x.strip()
        )
    form = CourseForm(data, request.FILES or None, instance=course)
    if request.method == "POST" and form.is_valid():
        course = save_course(form.save(commit=False), creator=_creator(request.user))
        messages.success(request, "Curso salvo com sucesso.")
        return redirect("painel:course_edit", course_id=course.id)
    return page(
        request,
        "course_edit" if course else "course_create",
        course=course,
        form=form,
        categories=Category.objects.all(),
        objectives=request.POST.getlist("objectives")
        if request.method == "POST"
        else course.objectives_list
        if course
        else [],
        modules_count=Module.objects.filter(course=course).count() if course else 0,
        lessons_count=Lesson.objects.filter(module__course=course).count()
        if course
        else 0,
        students_count=Enrollment.objects.filter(course=course).count()
        if course
        else 0,
    )


@painel_required
def course_lessons(request, course_id):
    identifiers = IdentifierForm(
        request.POST if request.method == "POST" else request.GET
    )
    if not identifiers.is_valid():
        if request.method == "POST":
            messages.error(request, "Identificador inválido.")
            return redirect("painel:course_lessons", course_id=course_id)
        return HttpResponseBadRequest("Identificador inválido.")
    ids = identifiers.cleaned_data
    course = get_object_or_404(Course, pk=course_id)
    if request.method == "POST":
        action = request.POST.get("action", "save_lesson")
        module = (
            Module.objects.filter(pk=ids["module_id"], course=course).first()
            if ids["module_id"]
            else None
        )
        if action in ('new_module', 'rename_module', 'save_module'):
            candidate = module or Module(course=course, order=course.modules.count()+1)
            form = ModuleForm(request.POST, instance=candidate)
            if form.is_valid():
                try:
                    save_module(form.save(commit=False), actor=request.user, confirm_impact=bool(request.POST.get('confirm_impact')))
                except ValidationError as exc:
                    return page(request, 'module_confirmation', course=course, module=candidate, form=form, errors=exc.messages)
            else:
                messages.error(request, ' '.join(error for errors in form.errors.values() for error in errors))
        elif action == 'delete_module' and module:
            try:
                delete_content(module, actor=request.user)
            except ValidationError as exc:
                messages.error(request, ' '.join(exc.messages))
        elif action in ("save_lesson", "delete_lesson"):
            lesson = (
                Lesson.objects.filter(
                    pk=ids["lesson_id"], module__course=course
                ).first()
                if ids["lesson_id"]
                else None
            )
            if action == "delete_lesson" and lesson:
                try:
                    delete_content(lesson, actor=request.user)
                except ValidationError as exc:
                    messages.error(request, ' '.join(exc.messages))
            elif module and request.POST.get("title", "").strip():
                if lesson is None:
                    lesson = Lesson(
                        module=module,
                        order=Lesson.objects.filter(module=module).count() + 1,
                    )
                old_url = lesson.video_url
                data = request.POST.copy()
                data["module"] = data.get("module_id", "")
                form = LessonForm(data, instance=lesson, course=course)
                if not form.is_valid():
                    messages.error(
                        request,
                        " ".join(
                            error for errors in form.errors.values() for error in errors
                        ),
                    )
                    return redirect("painel:course_lessons", course_id=course.id)
                lesson = form.save(commit=False)
                minutes = form.cleaned_data["duration_minutes"]
                if minutes is not None:
                    lesson.duration_seconds = minutes * 60
                if lesson.video_url != old_url:
                    lesson.duration_seconds = (
                        video_duration(lesson.video_url) or lesson.duration_seconds
                    )
                try:
                    save_lesson(lesson, materials=request.FILES.getlist("materials"))
                except ValidationError as exc:
                    messages.error(request, " ".join(exc.messages))
                    return redirect("painel:course_lessons", course_id=course.id)
        messages.success(request, "Alterações salvas.")
        return redirect("painel:course_lessons", course_id=course.id)
    modules = list(
        Module.objects.filter(course=course).prefetch_related("lessons__materials")
    )
    for module in modules:
        module.lessons_list = list(module.lessons.all())
        for lesson in module.lessons_list:
            lesson.material_count = len(lesson.materials.all())
    selected = (
        Lesson.objects.filter(pk=ids["aula"], module__course=course).first()
        if ids["aula"]
        else None
    )
    new_module = (
        Module.objects.filter(pk=ids["nova"], course=course).first()
        if ids["nova"]
        else None
    )
    return page(
        request,
        "course_lessons",
        course=course,
        modules=modules,
        selected_lesson=selected,
        new_lesson_module=new_module,
    )


@painel_required
@require_POST
def course_reorder(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    try:
        payload = json.loads(request.body)
        module_ids = [int(x) for x in payload["modules"]]
        lessons = {int(k): [int(x) for x in v] for k, v in payload["lessons"].items()}
        actual_modules = set(
            Module.objects.filter(course=course).values_list("id", flat=True)
        )
        actual_lessons = set(
            Lesson.objects.filter(module__course=course).values_list("id", flat=True)
        )
        if (
            set(module_ids) != actual_modules
            or len(module_ids) != len(actual_modules)
            or set(lessons) != actual_modules
        ):
            raise ValueError("Módulos inválidos")
        flat = [x for values in lessons.values() for x in values]
        if set(flat) != actual_lessons or len(flat) != len(actual_lessons):
            raise ValueError("Aulas inválidas")
        with transaction.atomic():
            for index, module_id in enumerate(module_ids, 1):
                Module.objects.filter(pk=module_id).update(order=index)
            for module_id, ids in lessons.items():
                for index, lesson_id in enumerate(ids, 1):
                    Lesson.objects.filter(pk=lesson_id).update(
                        module_id=module_id, order=index
                    )
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return JsonResponse({"ok": False}, status=400)
    return JsonResponse({"ok": True})
