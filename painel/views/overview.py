from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from community.models import CommunityPost
from core.decorators import painel_required
from courses.access import access_decision
from courses.models import Certificate, Enrollment, LiveEvent, StudyDay
from django.db.models import Sum
from painel.reporting import report_data
from support.models import Ticket
from users.models import StudentVisit
from users.notifications import pending_email_count
from .common import page


@painel_required
def dashboard(request):
    now = timezone.localtime()
    period = request.GET.get("periodo", "7")
    report = report_data(days=int(period) if period in ("7", "30", "90") else 7)
    today = report["today"]
    seconds = (report["study_seconds"] if report["days"] == 7 else
               StudyDay.objects.filter(date__range=(today - timedelta(days=6), today)).aggregate(total=Sum("seconds"))["total"] or 0)
    active = [e.course_id for e in Enrollment.objects.prefetch_related("access_periods") if access_decision(e).allowed]
    issues = []

    def issue(count, singular, plural, detail, icon, tone, action, route, query=""):
        if count:
            issues.append({"title": f"{count} {singular if count == 1 else plural}", "detail": detail,
                           "icon": icon, "tone": tone, "action": action, "url": reverse("painel:" + route) + query})

    posts = CommunityPost.objects.filter(is_hidden=False, team_status="new", created_at__lt=now-timedelta(days=1))
    issue(posts.count(), "tópico aguarda resposta há mais de 24 h", "tópicos aguardam resposta há mais de 24 h",
          ", ".join(posts.exclude(course=None).order_by("course__title").values_list("course__title",flat=True).distinct()[:3]),
          "message", "warn", "Responder", "community", "?status=new")
    tickets = Ticket.objects.exclude(status="resolved").order_by("created_at")
    oldest = tickets.first()
    issue(tickets.count(), "chamado em andamento", "chamados em andamento", oldest.title if oldest else "",
          "help", "warn", "Abrir chamado", "tickets", "?status=active")
    issue(len(report["expiring"]), "plano termina nos próximos 30 dias", "planos terminam nos próximos 30 dias",
          ", ".join(row["enrollment"].student.full_name or row["enrollment"].student.user.username for row in report["expiring"][:3]), "calendar", "neutral", "Ver vencimentos", "expirations")
    issue(sum(row["course"].is_published and not row["lessons"] for row in report["courses"]),
          "curso publicado ainda não tem aulas", "cursos publicados ainda não têm aulas",
          "O aluno vê um curso vazio na vitrine.", "book", "danger", "Revisar cursos", "courses", "?visao=atencao")
    issue(pending_email_count(), "aviso por e-mail aguarda envio",
          "avisos por e-mail aguardam envio", "Consulte a configuração de envio da escola.", "mail", "danger", "Conferir envio", "settings", "?aba=email")
    events = LiveEvent.objects.filter(is_active=True,starts_at__gte=now).select_related("course").order_by("starts_at")
    courses = sorted((row for row in report["courses"] if row["students"]), key=lambda row: -row["students"])
    return page(request, "dashboard", report=report, issues=issues, popular=courses[:3], next_live=events.first(),
                tracking_since=StudentVisit.objects.order_by("date").values_list("date", flat=True).first(),
                greeting="Bom dia" if now.hour < 12 else "Boa tarde" if now.hour < 18 else "Boa noite",
                today=today, periods=(7, 30, 90), active_enrollments=len(active), active_course_count=len(set(active)),
                certificates_count=Certificate.objects.count(), watched=f"{seconds//3600}h {seconds//60%60:02d}min")
