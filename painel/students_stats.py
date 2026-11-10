"""Números da lista e da ficha de alunos (HANDOFF-v2 8.6 e 8.7), calculados em poucas consultas por página."""
from collections import defaultdict
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Max, Q
from django.utils import timezone

from courses.models import Enrollment, Lesson, Progress

from . import stats

User = get_user_model()
FILTERS = ('todos', 'ativos', 'nunca', 'concluiram', 'sem-dados', 'importados-hoje')
ACTIVE_DAYS = 30


def students():
    return User.objects.filter(role=User.Role.STUDENT).select_related('student_profile')


def _published_totals(course_ids):
    return {row['module__course_id']: row['n'] for row in
            Lesson.objects.filter(module__course_id__in=list(course_ids), status='published')
            .values('module__course_id').annotate(n=Count('id'))}


def _done_counts(profile_ids, course_ids):
    done = defaultdict(int)
    rows = (Progress.objects.filter(student_id__in=list(profile_ids), is_completed=True, lesson__status='published',
                                    lesson__deleted_at__isnull=True, lesson__module__course_id__in=list(course_ids))
            .values('student_id', 'lesson__module__course_id').annotate(n=Count('id')))
    for row in rows:
        done[(row['student_id'], row['lesson__module__course_id'])] = row['n']
    return done


def completed_profile_ids():
    """Perfis com alguma matrícula ativa em que todas as aulas publicadas estão concluídas."""
    enrollments = list(Enrollment.objects.filter(is_active=True).values_list('student_id', 'course_id'))
    if not enrollments:
        return set()
    course_ids = {course_id for _, course_id in enrollments}
    totals = _published_totals(course_ids)
    done = _done_counts({student_id for student_id, _ in enrollments}, course_ids)
    return {student_id for student_id, course_id in enrollments
            if totals.get(course_id) and done.get((student_id, course_id), 0) >= totals[course_id]}


def filtered(name):
    qs = students()
    if name == 'ativos':
        since = timezone.now() - timedelta(days=ACTIVE_DAYS)
        return qs.filter(student_profile__progress_records__updated_at__gte=since).distinct()
    if name == 'nunca':
        return stats.never_accessed().select_related('student_profile')
    if name == 'concluiram':
        return qs.filter(student_profile__id__in=completed_profile_ids())
    if name == 'sem-dados':
        return qs.filter(Q(student_profile__full_name__isnull=True) | Q(student_profile__full_name='')
                         | Q(student_profile__cpf__isnull=True) | Q(student_profile__cpf=''))
    if name == 'importados-hoje':
        today = timezone.localdate()
        return qs.filter(student_profile__enrollments__source='import', student_profile__enrollments__enrolled_at__date=today).distinct()
    return qs


def filter_counts():
    return {name: filtered(name).count() for name in FILTERS}


def summaries(profiles):
    """{profile_id: {courses, avg_pct, last_seen, status}} para os perfis informados (uma página da lista)."""
    ids = [profile.id for profile in profiles]
    enrollments = list(Enrollment.objects.filter(student_id__in=ids, is_active=True).select_related('course').order_by('enrolled_at'))
    course_ids = {e.course_id for e in enrollments}
    totals = _published_totals(course_ids)
    done = _done_counts(ids, course_ids)
    seen = {row['student_id']: row['last'] for row in
            Progress.objects.filter(student_id__in=ids).values('student_id').annotate(last=Max('updated_at'))}
    access = {row['student_id']: row['last'] for row in
              Enrollment.objects.filter(student_id__in=ids).values('student_id').annotate(last=Max('last_accessed_at'))}
    per_profile = defaultdict(list)
    for enrollment in enrollments:
        total = totals.get(enrollment.course_id, 0)
        finished = done.get((enrollment.student_id, enrollment.course_id), 0)
        per_profile[enrollment.student_id].append({
            'course': enrollment.course, 'done': finished, 'total': total,
            'pct': min(round(finished / total * 100), 100) if total else 0,
        })
    result = {}
    for profile in profiles:
        courses = per_profile.get(profile.id, [])
        moments = [m for m in (profile.user.last_login, seen.get(profile.id), access.get(profile.id)) if m]
        last_seen = max(moments) if moments else None
        if not courses:
            status = 'none'
        elif last_seen is None:
            status = 'waiting'
        else:
            status = 'active'
        result[profile.id] = {
            'courses': courses, 'last_seen': last_seen, 'status': status,
            'avg_pct': round(sum(c['pct'] for c in courses) / len(courses)) if courses else None,
        }
    return result


def totals_line():
    active = Enrollment.objects.filter(is_active=True, student__user__role=User.Role.STUDENT)
    return {
        'students': students().count(), 'enrollments': active.count(),
        'courses': active.values('course').distinct().count(),
    }
