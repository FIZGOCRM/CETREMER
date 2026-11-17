"""Access policy shared by all course-content boundaries, independent of billing."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from django.utils import timezone

from .models import Enrollment


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    state: str
    paid_through: Optional[date] = None
    grace_through: Optional[date] = None


def access_decision(enrollment, *, on=None):
    if enrollment is None:
        return AccessDecision(False, "missing")
    if enrollment.access_policy == Enrollment.AccessPolicy.UNRESTRICTED:
        return AccessDecision(True, "unrestricted")
    on = on or timezone.localdate()
    periods = list(enrollment.access_periods.all())
    active = [p for p in periods if p.starts_on <= on < p.ends_on]
    if active:
        period = max(active, key=lambda p: p.ends_on)
        return AccessDecision(True, "active", period.ends_on - timedelta(days=1))
    grace = [
        p
        for p in periods
        if p.ends_on.toordinal()
        <= on.toordinal()
        < p.ends_on.toordinal() + p.grace_days
    ]
    if grace:
        period = max(grace, key=lambda p: p.ends_on.toordinal() + p.grace_days)
        return AccessDecision(
            True,
            "grace",
            period.ends_on - timedelta(days=1),
            date.fromordinal(
                min(
                    date.max.toordinal(),
                    period.ends_on.toordinal() + period.grace_days - 1,
                )
            ),
        )
    past = [p for p in periods if p.ends_on <= on]
    if past:
        return AccessDecision(
            False, "expired", max(p.ends_on for p in past) - timedelta(days=1)
        )
    return AccessDecision(False, "pending")


def has_course_access(student, course, *, on=None):
    enrollment = (
        Enrollment.objects.filter(student=student, course=course)
        .prefetch_related("access_periods")
        .first()
    )
    return access_decision(enrollment, on=on).allowed


def accessible_courses(student, *, on=None):
    from .models import Course

    enrollments = Enrollment.objects.filter(student=student).prefetch_related(
        "access_periods"
    )
    ids = [e.course_id for e in enrollments if access_decision(e, on=on).allowed]
    return Course.objects.filter(pk__in=ids)

@dataclass(frozen=True)
class LessonAvailability:
    state: str
    release_date: Optional[date] = None


def module_release_date(enrollment, module):
    from .services import add_calendar_months
    if not enrollment or not enrollment.plan_started_on:
        return None
    return add_calendar_months(enrollment.plan_started_on, module.release_month - 1)


def lesson_availability(enrollment, lesson, *, on=None, completed_ids=None):
    from .models import Progress
    if lesson.status != 'published' or lesson.module.status != 'published':
        return LessonAvailability('draft')
    if not access_decision(enrollment, on=on).allowed:
        return LessonAvailability('plan_ended')
    release = module_release_date(enrollment, lesson.module)
    if (release and release > (on or timezone.localdate())) or (not release and lesson.module.release_month > 1):
        completed = lesson.pk in completed_ids if completed_ids is not None else Progress.objects.filter(student=enrollment.student, lesson=lesson, is_completed=True).exists()
        if not completed:
            return LessonAvailability('scheduled', release)
    return LessonAvailability('available', release)
