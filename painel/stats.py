"""Números do painel (HANDOFF-v2 8.1 e 8.2). Agregados em poucas consultas; usados pelo Início e por Cursos."""
from collections import defaultdict
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone

from courses.models import Certificate, Enrollment, Lesson, Progress
from sales.models import Order

User = get_user_model()
PERIODS = (7, 30, 90)
DEFAULT_PERIOD = 30


def parse_period(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return DEFAULT_PERIOD
    return number if number in PERIODS else DEFAULT_PERIOD


def greeting(now=None):
    hour = timezone.localtime(now or timezone.now()).hour
    return 'Bom dia' if hour < 12 else 'Boa tarde' if hour < 18 else 'Boa noite'


def non_vimeo_lessons():
    """Aulas publicadas, de cursos que não estão arquivados, com vídeo que não é do Vimeo."""
    return (Lesson.objects.filter(status='published', vimeo_id='').exclude(video_url='')
            .exclude(module__course__status='archived'))


def non_vimeo_by_course():
    """{course_id: quantidade} de aulas publicadas que ainda usam outro vídeo que não o Vimeo."""
    rows = non_vimeo_lessons().values('module__course_id').annotate(n=Count('id'))
    return {row['module__course_id']: row['n'] for row in rows}


def never_accessed():
    """Alunos que nunca entraram e não têm nenhum registro de aula."""
    return (User.objects.filter(role=User.Role.STUDENT, last_login__isnull=True)
            .exclude(student_profile__progress_records__isnull=False))


def active_enrollments():
    return Enrollment.objects.filter(is_active=True)


def course_stats(course_ids, since=None):
    """{course_id: {students, avg_pct, completed, revenue}} para os cursos informados.

    Progresso médio = média, entre as matrículas ativas, de aulas publicadas concluídas / aulas publicadas do curso.
    `revenue` soma os pedidos pagos desde `since` (ou todos, sem `since`).
    """
    ids = list(course_ids)
    totals = {row['module__course_id']: row['n'] for row in
              Lesson.objects.filter(module__course_id__in=ids, status='published')
              .values('module__course_id').annotate(n=Count('id'))}
    done = defaultdict(int)
    for row in (Progress.objects.filter(is_completed=True, lesson__status='published', lesson__deleted_at__isnull=True,
                                        lesson__module__course_id__in=ids)
                .values('student_id', 'lesson__module__course_id').annotate(n=Count('id'))):
        done[(row['student_id'], row['lesson__module__course_id'])] = row['n']
    per_course = defaultdict(list)
    for enrollment in active_enrollments().filter(course_id__in=ids).values('student_id', 'course_id'):
        per_course[enrollment['course_id']].append(enrollment['student_id'])
    orders = Order.objects.filter(status=Order.Status.COMPLETED, course_id__in=ids)
    if since is not None:
        orders = orders.filter(created_at__gte=since)
    revenue = {row['course_id']: row['total'] for row in orders.values('course_id').annotate(total=Sum('amount'))}

    stats = {}
    for course_id in ids:
        students = per_course.get(course_id, [])
        total = totals.get(course_id, 0)
        ratios = [min(done.get((s, course_id), 0) / total, 1) for s in students] if total else [0 for _ in students]
        stats[course_id] = {
            'students': len(students),
            'avg_pct': round(sum(ratios) / len(ratios) * 100) if ratios else None,
            'completed': sum(1 for s in students if total and done.get((s, course_id), 0) >= total),
            'revenue': revenue.get(course_id) or 0,
        }
    return stats


def dashboard_numbers(period):
    now = timezone.now()
    since = now - timedelta(days=period)
    paid = Order.objects.filter(status=Order.Status.COMPLETED, created_at__gte=since)
    students = User.objects.filter(role=User.Role.STUDENT)
    return {
        'revenue': paid.aggregate(total=Sum('amount'))['total'] or 0,
        'paid_count': paid.count(),
        'new_students': students.filter(date_joined__gte=since).count(),
        'students_total': students.count(),
        'active_students': Progress.objects.filter(updated_at__gte=since).values('student').distinct().count(),
        'certificates': Certificate.objects.filter(issued_at__gte=since).count(),
        'since': since,
    }
