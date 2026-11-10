"""Context processors v2. Copiar para core/context_processors.py (ao lado de `site` do v1) e registrar:

    TEMPLATES[0]["OPTIONS"]["context_processors"] += [
        "core.context_processors.user_shell",
        "core.context_processors.student_shell",
        "core.context_processors.painel_shell",
    ]

Cada função só faz consultas quando a página é do layout correspondente (aluno ou painel), para não pesar
nas páginas públicas. As consultas são poucas e agregadas: não fazer query por item em template.
Ajuste os nomes de modelo e related_name para os do projeto (marcados com AJUSTAR).
"""
from django.db.models import Count, Q
from django.utils import timezone

PAINEL_ROLES = ("ADMIN", "CREATOR")
WEEKDAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def _is_painel(request):
    m = getattr(request, "resolver_match", None)
    return bool(m and m.namespace == "painel")


def user_shell(request):
    """Nome, iniciais e foto do usuário logado. Usado nos dois layouts."""
    u = getattr(request, "user", None)
    if not u or not u.is_authenticated:
        return {}
    profile = getattr(u, "student_profile", None)  # AJUSTAR related_name se for outro
    full = (getattr(profile, "full_name", "") or u.get_full_name() or u.email.split("@")[0]).strip()
    display = (getattr(profile, "display_name", "") or full.split(" ")[0]).strip()
    parts = [p for p in full.split() if p]
    initials = ((parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")) if parts else u.email[:2]).upper()
    photo = getattr(profile, "photo", None)
    return {
        "user_full_name": full,
        "user_first_name": display[:1].upper() + display[1:] if display else "",
        "user_initials": initials,
        "user_avatar_url": photo.url if photo else "",
    }


def student_shell(request):
    """Avisos, selos do menu e progresso geral. Só para usuário logado fora do painel."""
    u = getattr(request, "user", None)
    if not u or not u.is_authenticated or _is_painel(request):
        return {}
    from users.models import Notification                     # novo (HANDOFF-v2 6.1)
    from courses.models import Enrollment, Lesson, LiveSession, Certificate  # AJUSTAR
    from courses.services import completed_lesson_ids           # novo helper (HANDOFF-v2 6.4)
    from community.models import CommunityPost                  # AJUSTAR

    notifications = list(Notification.objects.filter(user=u).order_by("-created_at")[:8])
    unread_count = Notification.objects.filter(user=u, read_at__isnull=True).count()

    enrollments = list(Enrollment.objects.filter(user=u, is_active=True).select_related("course"))  # AJUSTAR filtro de ativo
    course_ids = [e.course_id for e in enrollments]

    # Selo de "Aulas ao vivo": próximo encontro em até 7 dias
    now = timezone.localtime()
    live_badge = None
    nxt = (LiveSession.objects.filter(course_id__in=course_ids, ends_at__gte=now)
           .order_by("starts_at").first())
    if nxt and nxt.starts_at <= now + timezone.timedelta(days=7):
        start = timezone.localtime(nxt.starts_at)
        if nxt.starts_at <= now <= nxt.ends_at:
            live_badge = {"label": "Ao vivo", "is_live": True}
        elif start.date() == now.date():
            live_badge = {"label": "Hoje", "is_live": False}
        else:
            live_badge = {"label": WEEKDAYS[start.weekday()], "is_live": False}

    # Comunidade: minhas dúvidas com resposta que eu ainda não li
    community_unread = CommunityPost.objects.filter(author=u, has_unread_answer=True, is_hidden=False).count()

    # Progresso geral e certificados prontos
    lessons_by_course = dict(
        Lesson.objects.filter(module__course_id__in=course_ids, is_published=True)  # AJUSTAR campo de publicada
        .values_list("module__course_id").annotate(n=Count("id"))
    )
    done_ids = completed_lesson_ids(u, course_ids)  # set de ids de aulas publicadas concluídas
    done_by_course = dict(
        Lesson.objects.filter(id__in=done_ids).values_list("module__course_id").annotate(n=Count("id"))
    )
    lessons_total = sum(lessons_by_course.values())
    lessons_done = sum(done_by_course.values())
    issued = set(Certificate.objects.filter(enrollment__user=u).values_list("enrollment__course_id", flat=True))
    certificates_ready = sum(
        1 for cid, total in lessons_by_course.items()
        if total and done_by_course.get(cid, 0) >= total and cid not in issued
    )

    return {
        "notifications": notifications,
        "unread_count": unread_count,
        "live_badge": live_badge,
        "community_unread": community_unread,
        "certificates_ready": certificates_ready,
        "lessons_done": lessons_done,
        "lessons_total": lessons_total,
        "lessons_pct": round(lessons_done * 100 / lessons_total) if lessons_total else 0,
    }


def painel_shell(request):
    """Selo de dúvidas sem resposta e permissões do menu do painel."""
    if not _is_painel(request) or not request.user.is_authenticated:
        return {}
    from community.models import CommunityPost  # AJUSTAR
    from courses.models import Category, Course  # AJUSTAR
    u = request.user
    role = getattr(u, "role", "")
    is_admin = u.is_superuser or u.is_staff or role == "ADMIN"
    return {
        "pending_questions": CommunityPost.objects.filter(is_hidden=False, is_answered_cache=False).count(),
        "painel_categories": Category.objects.all(),
        "painel_courses": Course.objects.exclude(status="archived").order_by("title"),
        "perms_painel": {"orders": is_admin, "settings": is_admin, "content": True, "community": True},
    }
