"""Management HTTP adapters: course_management."""

import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.decorators import painel_required
from courses.integrations.vimeo import video_duration
from courses.access import access_decision
from courses.models import Category, Course, Enrollment, Lesson, LiveEvent, Module, Progress, Quiz
from courses.services import create_quick_lesson, reorder_course_content, save_course, save_lesson, save_module, delete_content
from painel.forms import CourseBasicsForm, CourseForm, IdentifierForm, LessonForm, ModuleForm
from users.models import CreatorProfile

from .common import page


@painel_required
def courses(request):
    qs = Course.objects.select_related("category").annotate(
        lessons_count=Count("modules__lessons", distinct=True),
        published_count=Count("modules__lessons", filter=Q(modules__status="published", modules__lessons__status="published"), distinct=True),
        students_count=Count("enrollments", distinct=True),
    )
    totals = qs.aggregate(total=Count("pk"), published=Count("pk", filter=Q(is_published=True)),
                          attention=Count("pk", filter=Q(is_published=True, published_count=0)))
    totals["draft"] = totals["total"] - totals["published"]
    views = [("todos", "Todos", totals["total"]), ("publicados", "Publicados", totals["published"]),
             ("rascunhos", "Rascunhos", totals["draft"]), ("atencao", "Precisam de atenção", totals["attention"])]
    view = request.GET.get("visao", "todos")
    if view == "atencao":
        qs = qs.filter(is_published=True, published_count=0)
    elif view in ("publicados", "rascunhos"):
        qs = qs.filter(is_published=view == "publicados")
    else:
        view = "todos"
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
        views=views, view=view, totals=totals, lesson_total=Lesson.objects.count(),
        active_enrollments=sum(access_decision(e).allowed for e in Enrollment.objects.prefetch_related("access_periods")),
    )


def _creator(user):
    profile = CreatorProfile.objects.filter(user=user).first()
    return (
        profile
        or CreatorProfile.objects.first()
        or CreatorProfile.objects.create(user=user)
    )


@painel_required
@transaction.atomic
def course_edit(request, course_id=None):
    queryset = Course.objects.select_for_update() if request.method == "POST" else Course.objects.all()
    course = get_object_or_404(queryset, pk=course_id) if course_id else None
    data = request.POST.copy() if request.method == "POST" else None
    if course and data is not None and data.get("action") == "publication":
        status = data.get("status")
        if status not in ("published", "draft"):
            return HttpResponseBadRequest("Situação inválida.")
        if status == "published" and not Lesson.objects.filter(module__course=course, module__status="published", status="published").exists():
            messages.error(request, "Publique ao menos uma aula antes de publicar o curso.")
        else:
            course.is_published = status == "published"
            course.save(update_fields=["is_published"])
            messages.success(request, "Situação do curso atualizada.")
        from django.utils.http import url_has_allowed_host_and_scheme
        target = data.get("next", "")
        if target.startswith("/") and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(target)
        return redirect("painel:course_overview", course.pk)
    if course and data is not None and data.get("action") == "details":
        data["is_published"] = course.is_published
    if data is not None and "objectives" in data:
        data["learning_objectives"] = "\n".join(
            x.strip() for x in request.POST.getlist("objectives") if x.strip()
        )
    form_class=CourseBasicsForm if course else CourseForm
    form = form_class(data, request.FILES or None, instance=course)
    form.fields["category"].empty_label = "Escolha a categoria"
    if request.method == "POST" and form.is_valid():
        course = save_course(form.save(commit=False), creator=_creator(request.user))
        if course_id is None:
            messages.success(request, "Curso criado.")
            return redirect("painel:course_lessons", course_id=course.pk)
        messages.success(request, "Detalhes salvos.")
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
    invalid_module = None
    if request.method == "GET" and ids["aula"]:
        lesson=get_object_or_404(Lesson,pk=ids["aula"],module__course=course)
        return redirect("painel:lesson_edit",lesson_id=lesson.pk)
    if request.method == "POST":
        action = request.POST.get("action", "save_lesson")
        module = (
            Module.objects.filter(pk=ids["module_id"], course=course).first()
            if ids["module_id"]
            else None
        )
        if action == 'quick_lesson':
            try:
                if not module:raise ValidationError('Módulo inválido para este curso.')
                create_quick_lesson(module,request.POST.get('title',''),actor=request.user)
                messages.success(request,'Aula criada em rascunho. Complete o conteúdo antes de publicar.')
            except ValidationError as exc:messages.error(request,' '.join(exc.messages))
            return redirect('painel:course_lessons',course_id=course.pk)
        if action in ('new_module', 'rename_module', 'save_module'):
            candidate = module or Module(course=course, order=course.modules.count()+1)
            if ids["module_id"] and not module:
                return HttpResponseBadRequest("Módulo inválido para este curso.")
            form = ModuleForm(request.POST, request.FILES, instance=candidate)
            if form.is_valid():
                try:
                    save_module(form.save(commit=False), actor=request.user, confirm_impact=bool(request.POST.get('confirm_impact')))
                except ValidationError as exc:
                    return page(request, 'module_confirmation', course=course, module=candidate, form=form, errors=exc.messages)
            else:
                invalid_module = form
        elif action == 'delete_module' and module:
            try:
                delete_content(module, actor=request.user)
            except ValidationError as exc:
                messages.error(request, ' '.join(exc.messages))
                return redirect("painel:course_lessons", course_id=course.id)
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
                    return redirect("painel:course_lessons", course_id=course.id)
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
        if invalid_module is None:
            messages.success(request, "Alterações salvas.")
            return redirect("painel:course_lessons", course_id=course.id)
    modules = list(
        Module.objects.filter(course=course).prefetch_related("lessons__materials", "lessons__quiz")
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
    published = sum(lesson.status == "published" and module.status == "published"
                    for module in modules for lesson in module.lessons_list)
    details = reverse("painel:course_edit", args=[course.pk])
    readiness = [
        (bool(course.cover_image and course.description), "Capa e descrição", details + "#aparencia"),
        (bool(published), f"{published} aula publicada" if published == 1 else f"{published} aulas publicadas",
         reverse("painel:lesson_new", args=[course.pk])),
        (bool(course.plan_months), "Duração do acesso", details + "#acesso"),
        (bool(course.workload_hours), "Carga horária do certificado", details + "#acesso"),
        (bool(course.learning_objectives and course.target_audience), "Página do curso preenchida", details + "#pagina"),
    ]
    return page(
        request,
        "course_lessons",
        course=course,
        modules=modules,
        readiness=readiness,
        invalid_module=invalid_module,
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
        reorder_course_content(course,module_ids,lessons,actor=request.user)
    except (ValidationError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return JsonResponse({"ok": False}, status=400)
    return JsonResponse({"ok": True})

@painel_required
def course_overview_view(request,course_id):
    from painel.selectors import course_overview
    from painel.reporting import lesson_metrics
    course=get_object_or_404(Course,pk=course_id)
    overview = course_overview(course)
    members = course.enrollments.values("student_id")
    total = overview["published"]
    completed = list(Progress.objects.filter(student_id__in=members, is_completed=True, lesson__module__course=course,
                     lesson__module__status="published", lesson__status="published").values("student_id")
                     .annotate(done=Count("lesson_id", distinct=True)).values_list("done", flat=True))
    denominator = total * members.count()
    overview["progress"] = round(100 * sum(completed) / denominator) if denominator else 0
    overview["finished"] = sum(count == total for count in completed)
    upcoming = LiveEvent.objects.filter(Q(course=course) | Q(course__isnull=True),
        is_active=True, starts_at__gte=timezone.now()).order_by("starts_at", "pk")[:4]
    quiz = Quiz.objects.filter(course=course, kind="final").first()
    attempts = quiz.attempts.filter(finished_at__isnull=False) if quiz else None
    return page(request, "course_overview", course=course, overview=overview, rows=lesson_metrics(course=course)[:5],
                upcoming=upcoming, quiz=quiz, active_questions=quiz.questions.filter(is_active=True).count() if quiz else 0,
                assessed=attempts.values("student_id").distinct().count() if quiz else 0,
                passed=attempts.filter(score_pct__gte=70).values("student_id").distinct().count() if quiz else 0)
