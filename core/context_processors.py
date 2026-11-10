from users.models import SiteSettings


def site(request):
    return {'site': SiteSettings.load()}


def _is_painel(request):
    match = getattr(request, 'resolver_match', None)
    return bool(match and match.namespace == 'painel')


def user_shell(request):
    """Nome, iniciais e foto do usuário logado (HANDOFF-v2 3.2). Usado nos dois layouts."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    profile = getattr(user, 'student_profile', None)
    full = (getattr(profile, 'full_name', '') or user.get_full_name() or user.email.split('@')[0]).strip()
    display = (getattr(profile, 'display_name', '') or full.split(' ')[0]).strip()
    parts = [p for p in full.split() if p]
    initials = ((parts[0][0] + (parts[-1][0] if len(parts) > 1 else '')) if parts else user.email[:2]).upper()
    return {
        'user_full_name': full,
        'user_first_name': display[:1].upper() + display[1:] if display else '',
        'user_initials': initials,
        'user_avatar_url': user.avatar.url if user.avatar else '',
    }


WEEKDAYS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']


def student_shell(request):
    """Avisos, selos do menu e progresso geral (HANDOFF-v2 3.2). Só para usuário logado fora do painel.

    No máximo 8 consultas por página: avisos (2), matrículas, próximo encontro, dúvidas com resposta
    nova, aulas e concluídas por curso (agregadas em uma só) e certificados emitidos.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or _is_painel(request):
        return {}
    from django.db.models import Count, Q
    from django.utils import timezone
    from community.models import CommunityPost
    from courses.models import Certificate, Enrollment, Lesson, LiveSession
    from users.models import Notification

    context = {
        'notifications': list(Notification.objects.filter(user=user)[:8]),
        'unread_count': Notification.objects.filter(user=user, read_at__isnull=True).count(),
        'live_badge': None, 'community_unread': 0, 'certificates_ready': 0,
        'lessons_done': 0, 'lessons_total': 0, 'lessons_pct': 0,
    }
    profile = getattr(user, 'student_profile', None)
    if profile is None:
        return context

    enrollments = list(Enrollment.objects.filter(student=profile, is_active=True).select_related('course'))
    course_ids = [e.course_id for e in enrollments]

    now = timezone.now()
    next_session = (LiveSession.objects.filter(course_id__in=course_ids, ends_at__gte=now)
                    .order_by('starts_at').only('starts_at', 'ends_at').first())
    if next_session and next_session.starts_at <= now + timezone.timedelta(days=7):
        start = timezone.localtime(next_session.starts_at)
        if next_session.starts_at <= now:
            context['live_badge'] = {'label': 'Ao vivo', 'is_live': True}
        elif start.date() == timezone.localdate():
            context['live_badge'] = {'label': 'Hoje', 'is_live': False}
        else:
            context['live_badge'] = {'label': WEEKDAYS[start.weekday()], 'is_live': False}

    context['community_unread'] = CommunityPost.objects.filter(author=user, has_unread_answer=True, is_hidden=False).count()

    per_course = {row['module__course_id']: row for row in
                  Lesson.objects.filter(module__course_id__in=course_ids, status='published')
                  .values('module__course_id')
                  .annotate(total=Count('id', distinct=True),
                            done=Count('student_progress', filter=Q(student_progress__student=profile,
                                                                    student_progress__is_completed=True)))}
    total = sum(row['total'] for row in per_course.values())
    done = sum(row['done'] for row in per_course.values())
    issued = set(Certificate.objects.filter(enrollment__in=enrollments).values_list('enrollment__course_id', flat=True))
    context.update({
        'lessons_done': done, 'lessons_total': total,
        'lessons_pct': round(100 * done / total) if total else 0,
        'certificates_ready': sum(
            1 for e in enrollments
            if e.course.certificate_enabled and per_course.get(e.course_id, {}).get('total')
            and per_course[e.course_id]['done'] >= per_course[e.course_id]['total'] and e.course_id not in issued),
    })
    return context


def painel_shell(request):
    """Selo de dúvidas sem resposta e permissões do menu do painel (HANDOFF-v2 3.2).

    Fase A0: `painel_courses` ainda não exclui arquivados (Course.status entra na A1) e a contagem
    de dúvidas usa a mesma regra de `CommunityPost.is_answered` (resposta de staff, ADMIN ou CREATOR).
    """
    if not _is_painel(request) or not request.user.is_authenticated:
        return {}
    from community.models import CommunityPost
    from courses.models import Category, Course
    user = request.user
    is_admin = user.is_superuser or user.is_staff or getattr(user, 'role', '') == 'ADMIN'
    pending = CommunityPost.objects.filter(is_hidden=False, is_answered_cache=False).count()
    return {
        'pending_questions': pending,
        'painel_categories': Category.objects.all(),
        'painel_courses': Course.objects.exclude(status='archived').order_by('title'),
        'perms_painel': {'orders': is_admin, 'settings': is_admin, 'content': True, 'community': True},
    }
