"""Management HTTP adapters: students."""

import csv
from datetime import timedelta
from uuid import uuid4
from smtplib import SMTPException

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from core.portal_routing import user_access_url

from core.decorators import painel_required
from core.csv_export import safe_csv_cell
from courses.access import access_decision
from courses.models import Course, Enrollment, Lesson, Progress
from courses.selectors import progress_info
from painel.forms import AccessPeriodForm, ManualEnrollmentForm, IdentifierForm
from courses.services import grant_manual_period
from courses.services import plan_status
from sales.migration_import import parse_subscription_csv
from sales.migration_services import import_subscription_periods
from users.first_access import issue_code
from users.importing import parse_student_csv
from users.models import FirstAccessCode
from users.services import enroll_student_with_plan, import_students

User = get_user_model()

from .common import access_email, page, report_access_delivery


def deliver_code(request, user):
    request.session["panel_access_code"] = {"user": user.pk, "code": issue_code(user)}


@painel_required
def students(request):
    identifiers = IdentifierForm(
        request.POST if request.method == "POST" else request.GET
    )
    if not identifiers.is_valid():
        if request.method == "POST":
            messages.error(request, "Identificador inválido.")
            return redirect("painel:students")
        return HttpResponseBadRequest("Identificador inválido.")
    ids = identifiers.cleaned_data
    if request.method == "POST":
        action = request.POST.get("action")
        email = request.POST.get("email", "").strip()
        selected_id = ids["student_id"]
        user = (
            User.objects.filter(pk=selected_id, role=User.Role.STUDENT).first()
            if selected_id
            else User.objects.filter(
                email__iexact=email, role=User.Role.STUDENT
            ).first()
        )
        if action == "enroll":
            form = ManualEnrollmentForm(request.POST)
            if not form.is_valid():
                return _students_page(request, ids, creation_form=form)
            course = form.cleaned_data["course_id"]
            email = form.cleaned_data["email"]
            try:
                user = enroll_student_with_plan(
                    actor=request.user, starts_on=form.cleaned_data["starts_on"],last_day=form.cleaned_data["last_day"],
                    course=course,
                    email=email,
                    full_name=form.cleaned_data["full_name"],
                    student_id=form.cleaned_data["student_id"],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
                return _students_page(request, ids, creation_form=form)
            if user:
                messages.success(request, "Cadastro e plano criados. Confira as datas antes de entregar o acesso.")
                if (
                    not user.has_usable_password()
                    and not FirstAccessCode.objects.filter(user=user).exists()
                ):
                    deliver_code(request, user)
                if request.POST.get("send_email"):
                    try:
                        sent = access_email(request, user)
                    except (OSError, SMTPException):
                        sent = 0
                    report_access_delivery(request, sent)
        elif action == "grant_period" and user:
            form = AccessPeriodForm(request.POST)
            enrollment = Enrollment.objects.filter(student=user.student_profile, course_id=ids["course_id"]).first()
            if not form.is_valid():
                messages.error(request, " ".join(error for errors in form.errors.values() for error in errors))
            elif not enrollment:
                messages.error(request, "Matricule o aluno neste curso antes de definir o período.")
            else:
                try:
                    grant_manual_period(enrollment=enrollment, starts_on=form.cleaned_data["starts_on"],
                                        paid_through=form.cleaned_data["paid_through"],
                                        reference=form.cleaned_data["reference"], actor=request.user)
                    messages.success(request, "Período quitado registrado. Nenhuma cobrança foi criada.")
                except ValidationError as exc:
                    messages.error(request, " ".join(exc.messages))
        elif action == "unenroll" and user:
            enrollment = Enrollment.objects.filter(
                student=user.student_profile, course_id=ids["course_id"]
            ).first()
            if enrollment and hasattr(enrollment, "certificate"):
                messages.error(
                    request,
                    "Este acesso tem certificado emitido e precisa ser preservado.",
                )
            elif enrollment and (
                enrollment.access_periods.exists()
                or hasattr(enrollment, "subscription")
            ):
                messages.error(
                    request,
                    "Esta matrícula tem períodos quitados ou contrato e precisa ser preservada. Revise a situação financeira sem apagar o histórico.",
                )
            elif enrollment:
                enrollment.delete()
                messages.success(request, "Acesso removido. O progresso foi mantido.")
        elif action == "resend_access" and user:
            try:
                sent = access_email(request, user)
            except (OSError, SMTPException):
                sent = 0
            report_access_delivery(request, sent)
            if not sent and not user.has_usable_password():
                deliver_code(request, user)
        elif action == "generate_first_access" and user:
            if user.has_usable_password():
                messages.error(
                    request,
                    "Este aluno já tem senha. Use a recuperação de senha se necessário.",
                )
            else:
                deliver_code(request, user)
        return redirect(
            reverse("painel:students") + (f"?aluno={user.id}" if user else "")
        )
    return _students_page(request, ids)


def _students_page(request, ids, *, creation_form=None):
    from django.db.models import Prefetch
    qs = (
        User.objects.filter(role=User.Role.STUDENT)
        .select_related("student_profile")
        .prefetch_related(Prefetch('student_profile__enrollments',queryset=Enrollment.objects.select_related('course').prefetch_related('access_periods','access_changes')))
        .annotate(courses_count=Count("student_profile__enrollments", distinct=True))
    )
    q = request.GET.get("q", "").strip()
    course_id = ids["curso"]
    if q:
        qs = qs.filter(
            Q(email__icontains=q)
            | Q(username__icontains=q)
            | Q(student_profile__full_name__icontains=q)
            | Q(student_profile__cpf__icontains=q)
        )
    if course_id:
        qs = qs.filter(student_profile__enrollments__course_id=course_id)
    students_list = list(qs.distinct().order_by("-date_joined", "-pk"))
    from users.models import StudentVisit
    today = timezone.localdate()
    visitors = set(StudentVisit.objects.filter(date__gte=today-timedelta(days=6)).values_list("student_id",flat=True))
    totals = dict(Lesson.objects.filter(status="published", module__status="published").values("module__course_id")
                  .annotate(n=Count("pk")).values_list("module__course_id","n"))
    done = {(student, course): n for student, course, n in Progress.objects.filter(
        is_completed=True, lesson__status="published", lesson__module__status="published",
        student__user__in=qs).values("student_id","lesson__module__course_id").annotate(n=Count("pk"))
            .values_list("student_id","lesson__module__course_id","n")}
    views = {"todos": "Todos", "terminam": "Terminam em 30 dias", "pendentes": "Primeiro acesso pendente",
             "inativos": "Sem acesso há 7 dias", "encerrados": "Encerrados"}
    counts = dict.fromkeys(views, 0)
    view = request.GET.get("visao", "terminam" if request.GET.get("expiring") else "todos")
    if view not in views:
        view = "todos"
    filtered = []
    active_count = 0
    new_since = timezone.now() - timedelta(days=1)
    for user in students_list:
        enrollments = list(user.student_profile.enrollments.all())
        user.plan_items = []
        user.newly_registered = user.date_joined >= new_since
        for enrollment in enrollments:
            total = totals.get(enrollment.course_id, 0)
            progress = done.get((enrollment.student_id, enrollment.course_id), 0)
            user.plan_items.append({"enrollment": enrollment, "plan": plan_status(enrollment),
                                    "pct": round(100 * progress / total) if total else 0})
            active_count += int(access_decision(enrollment).allowed)
        states = {item["plan"]["state"] for item in user.plan_items}
        pending = not user.has_usable_password()
        modes = {"todos": True, "pendentes": pending, "encerrados": "ended" in states,
                 "terminam": "ending_soon" in states, "inativos": user.student_profile.pk not in visitors}
        if request.GET.get("acesso") == "pendente" and not pending or request.GET.get("acesso") == "liberado" and pending:
            continue
        for key, matches in modes.items():
            counts[key] += int(matches)
        if modes[view]:
            filtered.append(user)
        first = min(enrollments, key=lambda e:e.enrolled_at) if enrollments else None
        user.first_enrollment_source = first.get_source_display() if first else ""
    from django.core.paginator import Paginator

    students_page = Paginator(filtered, 25).get_page(request.GET.get("page"))
    selected = (
        User.objects.filter(pk=ids["aluno"] or ids["student_id"], role=User.Role.STUDENT).first()
        if ids["aluno"] or ids["student_id"]
        else None
    )
    if selected:
        selected.certificate_count = selected.student_profile.enrollments.filter(certificate__isnull=False).count()
        selected.access_delivery=selected.email_logs.filter(kind__in=["first_access","reset_access"],status="sent").order_by("-created_at").first()
        selected.enrollment_items = []
        for enrollment in (
            Enrollment.objects.filter(student=selected.student_profile)
            .select_related("course", "subscription")
            .prefetch_related("access_periods")
        ):
            info = progress_info(selected.student_profile, enrollment.course)
            info["access"] = access_decision(enrollment)
            info["enrollment"] = enrollment
            info["plan"] = plan_status(enrollment)
            if not info["plan"].get("period"):
                info["actions"] = [("create", "Criar plano")]
            else:
                info["actions"] = [("correct", "Corrigir datas")]
                if info["plan"]["state"] == "ended":
                    info["actions"].append(("reactivate", "Reativar plano"))
                elif info["access"].allowed:
                    info["actions"].extend([("extend","Estender acesso"), ("end","Encerrar plano")])
            retry = request.session.get("panel_plan_retry")
            if retry and retry["enrollment"] == enrollment.pk:
                info["retry"] = request.session.pop("panel_plan_retry")
            info["subscription"] = getattr(enrollment, "subscription", None)
            info["manual_reference"] = uuid4()
            selected.enrollment_items.append(info)
        selected.available_courses = Course.objects.exclude(
            enrollments__student=selected.student_profile
        )
    delivery = request.session.get("panel_access_code")
    if selected and delivery and delivery["user"] == selected.pk:
        delivery = request.session.pop("panel_access_code")
        destination = user_access_url(request, selected, reverse("first_access"))
        delivery["message"] = f"Acesse {destination} com o e-mail {selected.email} e o código {delivery['code']}. Ele vale por 7 dias."
    else:
        delivery = None
    response = page(
        request,
        "students",
        students=students_page,
        selected=selected,
        courses=Course.objects.all(),
        q=q, view=view, views=[(key, label, counts[key]) for key,label in views.items()],
        student_count=counts["todos"], active_count=active_count, delivery=delivery, today=today,
        creation_form=creation_form,
        drawer_tab=request.GET.get("aba", "cursos"),
        student_tabs=(("cursos","Cursos e planos"), ("acesso","Acesso"), ("historico","Histórico"), ("observacoes","Observações")),
    )
    if delivery:
        response["Cache-Control"] = "private, no-store"
        response["Referrer-Policy"] = "no-referrer"
    return response


@painel_required
def students_export(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="alunos.csv"'
    writer = csv.writer(response)
    writer.writerow(["nome", "email", "cpf", "cursos"])
    for user in (
        User.objects.filter(role=User.Role.STUDENT)
        .select_related("student_profile")
        .prefetch_related("student_profile__enrollments__course")
    ):
        p = user.student_profile
        writer.writerow(
            [safe_csv_cell(value) for value in [
                p.full_name or "",
                user.email,
                p.cpf or "",
                ", ".join(e.course.title for e in p.enrollments.all()),
            ]]
        )
    return response


@painel_required
def students_import(request):
    preview = request.session.get("import_preview")
    if request.method == "POST" and request.POST.get("action") == "confirm":
        if not preview:
            messages.error(request, "Leia o arquivo antes de confirmar.")
        else:
            if preview.get("mode") == "subscriptions":
                if not request.POST.get("confirm_periods"):
                    messages.error(
                        request,
                        "Confirme a revisão dos períodos quitados antes de importar.",
                    )
                    return redirect("painel:students_import")
                try:
                    result = import_subscription_periods(
                        preview["rows"], actor=request.user
                    )
                except ValidationError as exc:
                    messages.error(request, " ".join(exc.messages))
                    return redirect("painel:students_import")
                del request.session["import_preview"]
                messages.success(
                    request,
                    f"{result.imported} períodos importados; {result.unchanged} já estavam registrados; {result.skipped} linhas ignoradas. Nenhuma cobrança foi criada.",
                )
                return redirect("painel:students")
            try:
                result = import_students(preview["rows"], preview["course_ids"])
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
                return redirect("painel:students_import")
            new_count, old_count = result.created, result.existing
            if request.POST.get("send_email"):
                for user in User.objects.filter(pk__in=result.user_ids):
                    try:
                        sent = access_email(request, user)
                    except (OSError, SMTPException):
                        sent = 0
                    report_access_delivery(request, sent)
            del request.session["import_preview"]
            messages.success(
                request,
                f"{new_count} alunos importados. {old_count} já existiam e receberam os cursos.",
            )
            return redirect("painel:students")
    elif request.method == "POST":
        request.session.pop("import_preview", None)
        preview = None
        mode = request.POST.get("mode", "students")
        upload = request.FILES.get("file")
        if mode not in {"students", "subscriptions"}:
            messages.error(request, "Modalidade de importação inválida.")
        elif not upload:
            messages.error(request, "Escolha um arquivo CSV.")
        elif mode == "subscriptions":
            try:
                rows = parse_subscription_csv(upload)
            except (ValueError, UnicodeDecodeError, csv.Error) as exc:
                messages.error(request, f"Arquivo inválido: {exc}")
            else:
                preview = {"mode": mode, "rows": rows}
                request.session["import_preview"] = preview
        else:
            course_ids = [
                int(x)
                for x in request.POST.getlist("courses")
                if x.isdigit() and len(x) < 19
            ]
            course_ids = list(
                Course.objects.filter(id__in=course_ids).values_list("id", flat=True)
            )
            if not course_ids:
                messages.error(
                    request,
                    "Escolha pelo menos um curso para a liberação administrativa.",
                )
            else:
                try:
                    rows = parse_student_csv(upload)
                except (ValueError, UnicodeDecodeError, csv.Error) as exc:
                    messages.error(request, f"Arquivo inválido: {exc}")
                else:
                    preview = {"mode": mode, "rows": rows, "course_ids": course_ids}
                    request.session["import_preview"] = preview
    summary = {"new": 0, "existing": 0, "error": 0}
    if preview:
        for row in preview["rows"]:
            if preview.get("mode") == "subscriptions":
                summary["new" if row["valid"] else "error"] += 1
            elif row["status"] == "Novo aluno":
                summary["new"] += 1
            elif row["status"] == "Já cadastrado":
                summary["existing"] += 1
            else:
                summary["error"] += 1
    return page(
        request,
        "students_import",
        courses=Course.objects.all(),
        preview=preview,
        summary=summary,
    )
