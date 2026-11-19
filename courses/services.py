"""Course use cases, independent of HTTP requests and templates."""

import secrets

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from users.models import StudentProfile
from users.validators import validate_cpf

from .access import access_decision, has_course_access
from .models import Certificate, Progress
from .selectors import progress_info


def profile_data_ok(profile):
    if not (profile.full_name or "").strip():
        return False
    try:
        validate_cpf(profile.cpf)
    except ValidationError:
        return False
    return True


@transaction.atomic
def set_lesson_progress(student, lesson, *, completed=None, automatic=False):
    """Set completion, or toggle when omitted, updating points atomically.

    SQLite serializes writes; select_for_update is not a lock on SQLite.
    """
    if not has_course_access(student, lesson.module.course):
        raise PermissionDenied("Matrícula necessária.")
    from .access import lesson_availability
    from .models import Enrollment
    enrollment = Enrollment.objects.filter(student=student, course=lesson.module.course).first()
    if lesson_availability(enrollment, lesson).state != 'available':
        raise PermissionDenied('Esta aula ainda não está liberada.')
    progress, _ = Progress.objects.get_or_create(student=student, lesson=lesson)
    desired = not progress.is_completed if completed is None else completed
    if desired and automatic is not None:
        origin = "auto_completed_at" if automatic else "manual_completed_at"
        Progress.objects.filter(pk=progress.pk, **{origin + "__isnull": True}).update(**{origin: timezone.now()})
    if desired != progress.is_completed:
        Progress.objects.filter(pk=progress.pk).update(
            is_completed=desired, completed_at=timezone.now() if desired else None
        )
        if desired:
            from .models import ActivityEvent
            ActivityEvent.objects.create(student=student, kind='lesson_completed', lesson=lesson, course=lesson.module.course)
            StudentProfile.objects.filter(pk=student.pk).update(points=F("points") + 10)
        else:
            # Historical automatic completions did not award points.
            StudentProfile.objects.filter(pk=student.pk, points__gte=10).update(
                points=F("points") - 10
            )
        student.refresh_from_db()
        student.level = student.points // 50 + 1
        student.title = (
            "Grandmaster"
            if student.level >= 5
            else "Scholar"
            if student.level >= 3
            else "Novice"
        )
        student.save(update_fields=["level", "title"])
        refresh_certificate_qualification(enrollment)
    info = progress_info(student, lesson.module.course)
    return {
        "status": "success",
        "is_completed": desired,
        "completed_count": info["completed"],
        "total_count": info["total"],
        "percentage": info["pct"],
    }


@transaction.atomic
def issue_enrollment_certificate(enrollment):
    existing = Certificate.objects.filter(enrollment=enrollment).first()
    if existing:
        return existing
    from .models import Enrollment
    enrollment = Enrollment.objects.select_related('student', 'course').get(pk=enrollment.pk)
    refresh_certificate_qualification(enrollment)
    from .selectors import certificate_requirements
    requirements = certificate_requirements(enrollment)
    student = enrollment.student
    course = enrollment.course
    if not requirements['can_issue']:
        raise ValidationError('Conclua as aulas, obtenha 70% na avaliação final (se houver) e informe nome completo e CPF válidos durante o acesso.')
    code = secrets.token_hex(6).upper()
    while Certificate.objects.filter(code=code).exists():
        code = secrets.token_hex(6).upper()
    certificate, created = Certificate.objects.get_or_create(
        enrollment=enrollment,
        defaults={
            "code": code,
            "student_name": student.full_name,
            "student_cpf": validate_cpf(student.cpf),
            "course_title": course.title,
            "workload_hours": course.workload_hours,
            "completed_at": requirements['qualified_at'] or timezone.now(),
        },
    )
    if created:
        from .models import ActivityEvent
        ActivityEvent.objects.create(student=student, course=course, kind='certificate_issued', payload={'code':certificate.code})
    return certificate


@transaction.atomic
def save_course(course, *, creator):
    from django.utils.text import slugify

    from .models import Course

    if course.pk is None:
        max_length = Course._meta.get_field("slug").max_length
        base = (slugify(course.title) or "curso")[:max_length].rstrip("-")
        slug = base
        suffix = 2
        while Course.objects.filter(slug=slug).exists():
            ending = f"-{suffix}"
            slug = base[: max_length - len(ending)].rstrip("-") + ending
            suffix += 1
        course.slug = slug
        course.creator = creator
    course.full_clean()
    course.save()
    return course


@transaction.atomic
def save_lesson(lesson, *, materials=()):
    from .models import LessonMaterial

    from .models import Lesson
    previous = Lesson.objects.filter(pk=lesson.pk).values('video_url', 'duration_seconds', 'status').first() if lesson.pk else None
    lesson.full_clean()
    pending = [
        LessonMaterial(lesson=lesson, title=file.name, file=file) for file in materials
    ]
    # Validate every upload before writing the lesson or touching file storage.
    for material in pending:
        material.full_clean(exclude=["lesson"])
    if lesson.status == 'published' and (not previous or previous['status'] != 'published'):
        lesson.published_at = timezone.now()
    lesson.save()
    if previous and (previous['video_url'] != lesson.video_url or previous['duration_seconds'] != lesson.duration_seconds):
        Progress.objects.filter(lesson=lesson).update(last_position_seconds=0, last_heartbeat_at=None)
    for material in pending:
        material.lesson = lesson
        material.save()
    refresh_course_qualifications(lesson.module.course_id)
    return lesson


@transaction.atomic
def grant_manual_period(*, enrollment, starts_on, paid_through, reference, actor):
    """Append an audited interval; never replace history or invoke billing."""
    from datetime import date, timedelta
    from django.core.exceptions import ValidationError
    from .models import AccessPeriod, Enrollment

    if not (actor.is_staff or actor.role in ("ADMIN", "CREATOR")):
        raise PermissionDenied("Acesso exclusivo da administração.")
    if paid_through < starts_on or paid_through == date.max:
        raise ValidationError("Período inválido.")
    locked = Enrollment.objects.select_for_update().get(pk=enrollment.pk)
    ends_on = paid_through + timedelta(days=1)
    reference = "manual:" + str(reference)
    existing = locked.access_periods.filter(source=AccessPeriod.Source.MANUAL, reference=reference).first()
    if existing:
        if existing.starts_on != starts_on or existing.ends_on != ends_on:
            raise ValidationError("Esta confirmação já foi usada para outro período. Recarregue e revise.")
        return existing
    if locked.access_periods.filter(starts_on__lt=ends_on, ends_on__gt=starts_on).exists():
        raise ValidationError("O período coincide com um acesso já registrado. O histórico foi preservado.")
    period = AccessPeriod(enrollment=locked, starts_on=starts_on, ends_on=ends_on,
                          grace_days=3, source=AccessPeriod.Source.MANUAL,
                          reference=reference, created_by=actor)
    period.full_clean()
    period.save()
    locked.access_policy = Enrollment.AccessPolicy.PERIODS
    locked.save(update_fields=["access_policy"])
    return period

# Planos V1: um período corrente, com alterações auditadas.
def add_calendar_months(value, months):
    from calendar import monthrange
    from datetime import date
    index = value.year * 12 + value.month - 1 + months
    year, month = divmod(index, 12)
    return date(year, month + 1, min(value.day, monthrange(year, month + 1)[1]))


def _plan_actor(actor):
    if not actor or not actor.is_active or actor.role not in ('ADMIN', 'CREATOR'):
        raise PermissionDenied('Acesso exclusivo da administração.')


def _current_period(enrollment):
    periods = list(enrollment.access_periods.select_for_update())
    if len(periods) != 1:
        raise ValidationError('A matrícula precisa ter exatamente um período. Revise o histórico antes de continuar.')
    return periods[0]


def _record_plan(enrollment, period, action, actor, old=None, reason_code='', reason_text=''):
    from .models import AccessChange
    AccessChange.objects.create(enrollment=enrollment, action=action,
        old_starts_on=old[0] if old else None, old_ends_on=old[1] if old else None,
        new_starts_on=period.starts_on, new_ends_on=period.ends_on,
        actor=actor, reason_code=reason_code, reason_text=reason_text)


def _contract_end(enrollment, period):
    change = enrollment.access_changes.filter(action__in=['created', 'corrected']).last()
    return change.new_ends_on if change else period.ends_on


@transaction.atomic
def create_plan(enrollment, starts_on, ends_on=None, *, actor):
    from .models import AccessPeriod, Enrollment
    _plan_actor(actor)
    enrollment = Enrollment.objects.select_for_update().select_related('course').get(pk=enrollment.pk)
    if enrollment.access_periods.exists():
        raise ValidationError('Já existe um plano. Use Corrigir datas; o histórico deve ser preservado.')
    ends_on = ends_on or add_calendar_months(starts_on, enrollment.course.plan_months)
    period = AccessPeriod(enrollment=enrollment, starts_on=starts_on, ends_on=ends_on,
        grace_days=3, source='manual', reference='v1-plan', created_by=actor)
    period.full_clean(); period.save()
    enrollment.plan_started_on = starts_on
    enrollment.access_policy = 'periods'
    enrollment.save(update_fields=['plan_started_on', 'access_policy'])
    _record_plan(enrollment, period, 'created', actor)
    return period


def _prepare_plan_change(enrollment, actor):
    from .models import Enrollment
    _plan_actor(actor)
    enrollment = Enrollment.objects.select_for_update().get(pk=enrollment.pk)
    period = _current_period(enrollment)
    if not enrollment.access_changes.exists():
        _record_plan(enrollment, period, 'created', actor, reason_text='Registro do período histórico existente, sem alterar datas.')
    return enrollment, period


@transaction.atomic
def end_plan_early(enrollment, end_date, reason, *, actor, reason_text=''):
    enrollment, period = _prepare_plan_change(enrollment, actor)
    if reason not in ('withdrawal', 'nonpayment', 'student_request', 'other'):
        raise ValidationError('Escolha um motivo de encerramento.')
    if reason == 'other' and not reason_text.strip():
        raise ValidationError('Explique o motivo do encerramento.')
    if end_date > _contract_end(enrollment, period):
        raise ValidationError('O encerramento não pode ultrapassar o fim contratual.')
    old = (period.starts_on, period.ends_on)
    period.ends_on = end_date
    period.grace_days = 0
    period.ended_early = True
    period.full_clean(); period.save(update_fields=['ends_on', 'grace_days', 'ended_early'])
    _record_plan(enrollment, period, 'ended_early', actor, old, reason, reason_text.strip())
    return period


@transaction.atomic
def reactivate_plan(enrollment, until_date, *, actor):
    enrollment, period = _prepare_plan_change(enrollment, actor)
    last = enrollment.access_changes.last()
    if not period.ended_early:
        raise ValidationError('Só é possível reativar um plano encerrado antecipadamente.')
    contract_end = _contract_end(enrollment, period)
    if until_date > contract_end or until_date <= timezone.localdate():
        raise ValidationError('A reativação deve terminar no futuro, até o fim contratual corrigido.')
    old = (period.starts_on, period.ends_on)
    period.ends_on = until_date
    period.grace_days = 3 if until_date == contract_end else 0
    period.ended_early = False
    period.full_clean(); period.save(update_fields=['ends_on', 'grace_days', 'ended_early'])
    _record_plan(enrollment, period, 'reactivated', actor, old)
    return period


@transaction.atomic
def correct_plan_dates(enrollment, new_start, new_end, reason, *, actor):
    if not reason.strip():
        raise ValidationError('Informe o motivo da correção.')
    enrollment, period = _prepare_plan_change(enrollment, actor)
    old = (period.starts_on, period.ends_on)
    was_early = period.ended_early
    period.starts_on, period.ends_on = new_start, new_end
    period.grace_days = 0 if was_early else 3
    period.full_clean(); period.save(update_fields=['starts_on', 'ends_on', 'grace_days'])
    enrollment.plan_started_on = new_start
    enrollment.access_policy = 'periods'
    enrollment.save(update_fields=['plan_started_on', 'access_policy'])
    _record_plan(enrollment, period, 'corrected', actor, old, reason_text=reason.strip())
    return period


def plan_status(enrollment, *, on=None):
    from datetime import date, timedelta
    on = on or timezone.localdate()
    periods = list(enrollment.access_periods.all())
    if not periods:
        return {'state': 'active' if enrollment.access_policy == 'unrestricted' else 'pending', 'label': 'Sem plano definido'}
    period = max(periods, key=lambda p: p.ends_on)
    decision = access_decision(enrollment, on=on)
    changes = list(enrollment.access_changes.all())
    last = changes[-1] if changes else None
    early = period.ended_early
    days = (period.ends_on-on).days
    state = 'ended'
    if decision.state == 'grace':
        state = 'grace'; days = (period.ends_on+timedelta(days=period.grace_days)-on).days
    elif decision.allowed:
        state = 'ending_soon' if not early and 0 < days <= 30 else 'active'
    elif decision.state == 'pending':
        state = 'pending'
    day_unit = 'dia' if days == 1 else 'dias'
    labels = {'active': 'Ativo', 'ending_soon': f'Termina em {days} {day_unit}', 'grace': f'Seu acesso termina em {days} {day_unit}', 'ended': 'Encerrado', 'pending': 'Aguardando início'}
    month = 1
    if enrollment.plan_started_on:
        month = max(1, (on.year-enrollment.plan_started_on.year)*12+on.month-enrollment.plan_started_on.month+1)
        if on < add_calendar_months(enrollment.plan_started_on, month-1):
            month = max(1, month-1)
    reason_labels = {'withdrawal': 'Desistência', 'nonpayment': 'Inadimplência', 'student_request': 'Pedido do aluno', 'other': 'Outro'}
    reason = (last.reason_text or reason_labels.get(last.reason_code, 'Encerramento antecipado')) if early else 'Fim do período'
    access_end = period.ends_on.toordinal() + (0 if early else period.grace_days)
    access_last_day = date.fromordinal(min(date.max.toordinal(), access_end-1))
    return {'state': state, 'label': labels[state], 'days': days, 'starts_on': period.starts_on,
        'ends_on': period.ends_on, 'last_day': period.ends_on-timedelta(days=1), 'month': month,
        'access_last_day': access_last_day,
        'reason': reason,
        'period': period}


def plan_expiry_notice(enrollment, *, on=None):
    """Warn once daily during the last three actual access days, including grace."""
    from .models import Enrollment
    if enrollment.access_policy == Enrollment.AccessPolicy.UNRESTRICTED or not enrollment.course.is_published:
        return None
    today = on or timezone.localdate()
    plan = plan_status(enrollment, on=today)
    if plan['state'] not in ('active', 'ending_soon', 'grace') or not plan.get('access_last_day'):
        return None
    days = (plan['access_last_day']-today).days+1
    if not 1 <= days <= 3:
        return None
    return {'days': days, 'last_day': plan['access_last_day']}

@transaction.atomic
def save_module(module, *, actor, confirm_impact=False):
    from .models import Enrollment, Module, Progress
    from .access import module_release_date
    _plan_actor(actor)
    module.full_clean()
    old = Module.objects.select_for_update().filter(pk=module.pk).first() if module.pk else None
    affected = 0
    if old and module.release_month > old.release_month:
        lesson_ids = set(old.lessons.filter(status='published').values_list('id', flat=True))
        for enrollment in Enrollment.objects.filter(course=module.course).prefetch_related('access_periods'):
            previous = module_release_date(enrollment, old)
            future = module_release_date(enrollment, module)
            if access_decision(enrollment).allowed and previous and future and previous <= timezone.localdate() < future:
                done = set(Progress.objects.filter(student=enrollment.student, lesson_id__in=lesson_ids, is_completed=True).values_list('lesson_id', flat=True))
                affected += bool(lesson_ids - done)
    if affected and not confirm_impact:
        raise ValidationError(f'{affected} aluno(s) perderão acesso às aulas não concluídas até a nova data. Confirme para salvar.')
    module.save()
    if old and old.status != 'published' and module.status == 'published':
        module.lessons.filter(status='published').update(published_at=timezone.now())
    refresh_course_qualifications(module.course_id)
    return module


@transaction.atomic
def delete_content(content, *, actor):
    from .models import Module, Progress, ActivityEvent, LessonNote, QuizAttempt, LessonMaterial, MaterialOpen
    from community.models import CommunityPost
    _plan_actor(actor)
    filters = {'lesson__module': content} if isinstance(content, Module) else {'lesson': content}
    attempt_filters = {'quiz__lesson__module': content} if isinstance(content, Module) else {'quiz__lesson': content}
    has_history = Progress.objects.filter(**filters).exists() or ActivityEvent.objects.filter(**filters).exists() or LessonNote.objects.filter(**filters).exists() or QuizAttempt.objects.filter(**attempt_filters).exists()
    material_ids = LessonMaterial.objects.filter(**filters).values('pk')
    has_history = has_history or CommunityPost.objects.filter(**filters).exists() or MaterialOpen.objects.filter(material_kind='lesson', material_id__in=material_ids).exists()
    from .models import LessonLike, SavedLesson, WeeklySelectionItem
    has_history = has_history or any(model.objects.filter(**filters).exists() for model in (LessonLike, SavedLesson, WeeklySelectionItem))
    if has_history:
        raise ValidationError('Este conteúdo tem histórico de alunos. Use despublicar para preservar o histórico.')
    lessons = list(content.lessons.all()) if isinstance(content, Module) else [content]
    for lesson in lessons:
        quiz = getattr(lesson, 'quiz', None)
        if quiz:
            delete_quiz_content(quiz, actor=actor)
    course_id = content.course_id if isinstance(content, Module) else content.module.course_id
    content.delete()
    refresh_course_qualifications(course_id)

@transaction.atomic
def record_heartbeat(student, lesson, *, position, playing):
    import math
    from .access import lesson_availability
    from .models import Enrollment, StudyDay
    if isinstance(position, bool) or not isinstance(position, (int, float)) or not math.isfinite(position) or position < 0 or not isinstance(playing, bool):
        raise ValidationError('Posição ou estado do vídeo inválido.')
    # Obter a reserva de escrita do SQLite antes de ler o relógio compartilhado.
    StudentProfile.objects.filter(pk=student.pk).update(last_heartbeat_at=F('last_heartbeat_at'))
    current_student = StudentProfile.objects.get(pk=student.pk)
    enrollment = Enrollment.objects.filter(student=student, course=lesson.module.course).prefetch_related('access_periods').first()
    availability = lesson_availability(enrollment, lesson)
    if availability.state != 'available':
        raise PermissionDenied('Acesso encerrado.' if availability.state == 'plan_ended' else 'Esta aula ainda não está liberada.')
    now = timezone.now()
    elapsed = max(0, (now-current_student.last_heartbeat_at).total_seconds()) if current_student.last_heartbeat_at else 0
    # The previous pulse opens the playing interval; pause/hidden/end closes it.
    # Requiring the new state to be playing discarded the watched tail on pause.
    credit = min(20, int(elapsed)) if current_student.heartbeat_playing else 0
    progress, _ = Progress.objects.get_or_create(student=student, lesson=lesson)
    previous_watched = progress.watched_seconds
    position = min(position, lesson.duration_seconds) if lesson.duration_seconds else position
    if not progress.started_at and (position > 0 or credit > 0) and not (progress.max_position_seconds or progress.watched_seconds):
        progress.started_at = now
    progress.max_position_seconds = max(progress.max_position_seconds, position)
    progress.last_position_seconds = position
    progress.last_heartbeat_at = now
    progress.watched_seconds += credit
    progress.save(update_fields=['last_position_seconds', 'max_position_seconds', 'started_at', 'last_heartbeat_at', 'watched_seconds'])
    StudentProfile.objects.filter(pk=student.pk).update(last_heartbeat_at=now, heartbeat_playing=playing)
    if credit:
        # Dividir pulsos que atravessam meia-noite no fuso do projeto.
        from datetime import timedelta
        from collections import Counter
        by_day = Counter(timezone.localdate(now-timedelta(seconds=offset+1)) for offset in range(credit))
        for day, seconds in by_day.items():
            study_day, _ = StudyDay.objects.get_or_create(student=student, date=day)
            StudyDay.objects.filter(pk=study_day.pk).update(seconds=F('seconds')+seconds)
    if lesson.duration_seconds and previous_watched < lesson.duration_seconds*.9 <= progress.watched_seconds:
        set_lesson_progress(student, lesson, completed=True, automatic=True)
        progress.refresh_from_db()
    from .models import Lesson
    lesson_filters = {'module__course': lesson.module.course, 'module__status': 'published', 'status': 'published'}
    total = Lesson.objects.filter(**lesson_filters).count()
    completed = Progress.objects.filter(student=student, lesson__module__course=lesson.module.course,
        lesson__module__status='published', lesson__status='published', is_completed=True).count()
    from .selectors import has_active_lesson_quiz
    return {'access': 'active', 'completed': progress.is_completed, 'has_quiz': has_active_lesson_quiz(lesson),
        'completed_count': completed, 'total_count': total, 'percentage': round(100*completed/total) if total else 0,
        'position': progress.last_position_seconds, 'watched_seconds': progress.watched_seconds,
        'watched_pct': min(100, round(100*progress.watched_seconds/lesson.duration_seconds)) if lesson.duration_seconds else None,
        'is_completed': progress.is_completed}


def finish_video(student, lesson):
    from .access import lesson_availability
    from .models import Enrollment
    enrollment = Enrollment.objects.filter(student=student, course=lesson.module.course).first()
    if lesson_availability(enrollment, lesson).state != 'available':
        raise PermissionDenied('Esta aula ainda não está liberada.')
    progress = Progress.objects.filter(student=student, lesson=lesson).first()
    if progress and progress.is_completed:
        # An ended callback alone cannot turn a manual mark into observed playback.
        if not progress.auto_completed_at and (not lesson.duration_seconds or progress.watched_seconds < lesson.duration_seconds * .5):
            return set_lesson_progress(student, lesson, completed=True, automatic=None)
        return set_lesson_progress(student, lesson, completed=True, automatic=True)
    duration = lesson.duration_seconds
    if not duration:
        # Referência de duração obtida no servidor; nunca aceitar o valor do cliente.
        from .integrations.vimeo import video_duration
        duration = video_duration(lesson.video_url)
    if not duration:
        raise ValidationError('Não foi possível confirmar a duração. Use Marcar como concluída.')
    if not progress or progress.watched_seconds < duration*.5:
        raise ValidationError('Assista ao menos metade da aula antes da conclusão automática, ou use Marcar como concluída.')
    return set_lesson_progress(student, lesson, completed=True, automatic=True)


def create_lesson_note(student, lesson, *, position_seconds, text):
    from .access import require_lesson_access
    from .models import LessonNote
    require_lesson_access(student, lesson)
    if position_seconds < 0 or (lesson.duration_seconds and position_seconds > lesson.duration_seconds):
        raise ValidationError('O minuto deve pertencer à aula.')
    note = LessonNote(student=student, lesson=lesson, position_seconds=position_seconds, text=text.strip())
    note.full_clean(); note.save()
    return note


def delete_lesson_note(student, note):
    from .access import require_lesson_access
    if note.student_id != student.pk:
        raise PermissionDenied('Esta anotação é privada.')
    require_lesson_access(student, note.lesson)
    note.delete()


def require_quiz_access(student, quiz):
    if not quiz.course.is_published or not quiz.is_active:
        raise PermissionDenied('Este quiz não está disponível.')
    if quiz.kind == 'final':
        from .models import Enrollment, Lesson
        enrollment = Enrollment.objects.filter(student=student, course=quiz.course).prefetch_related('access_periods').first()
        lesson_ids = list(Lesson.objects.filter(module__course=quiz.course, module__status='published', status='published').values_list('id', flat=True))
        completed = Progress.objects.filter(student=student, lesson_id__in=lesson_ids, is_completed=True).count()
        if not access_decision(enrollment).allowed or not lesson_ids or completed != len(lesson_ids):
            raise PermissionDenied('Conclua todas as aulas publicadas com o plano ativo para liberar a avaliação final.')
        return
    if quiz.kind != 'lesson' or not quiz.lesson_id or quiz.lesson.module.course_id != quiz.course_id:
        raise PermissionDenied('Este quiz não está disponível.')
    from .access import require_lesson_access
    require_lesson_access(student, quiz.lesson)
    if not Progress.objects.filter(student=student, lesson=quiz.lesson, is_completed=True).exists():
        raise PermissionDenied('Conclua a aula para liberar o quiz.')


@transaction.atomic
def save_quiz_question(quiz, *, order, text, explanation, choices, correct_index, actor, question=None):
    from .models import QuizChoice, QuizQuestion
    _plan_actor(actor)
    choices = [str(value).strip() for value in choices]
    if not 2 <= len(choices) <= 4 or not all(choices) or isinstance(correct_index, bool) or correct_index not in range(len(choices)):
        raise ValidationError('Cadastre de duas a quatro alternativas preenchidas e exatamente uma correta.')
    if question and question.quiz_id != quiz.pk:
        raise ValidationError('A pergunta não pertence a este quiz.')
    question = question or QuizQuestion(quiz=quiz)
    question.order, question.text, question.explanation = order, text.strip(), explanation.strip()
    question.full_clean(); question.save()
    # Alternativas antigas permanecem guardadas; cada tentativa possui sua cópia.
    question.choices.filter(is_active=True).update(is_active=False)
    for index, value in enumerate(choices):
        choice = QuizChoice(question=question, order=index+1, text=value, is_correct=index == correct_index)
        choice.full_clean(); choice.save()
    if quiz.kind == 'final':refresh_course_qualifications(quiz.course_id)
    return question


@transaction.atomic
def delete_quiz_content(content, *, actor):
    from .models import Quiz, QuizQuestion
    _plan_actor(actor)
    quiz = content if isinstance(content, Quiz) else content.quiz
    course_id, kind = quiz.course_id, quiz.kind
    if quiz.attempts.exists():
        raise ValidationError('Há tentativas de alunos. Use desativar para preservar o histórico.')
    questions = list(quiz.questions.all()) if isinstance(content, Quiz) else [content]
    for question in questions:
        question.choices.all().delete()
        question.delete()
    if isinstance(content, Quiz):
        content.delete()
    if kind == 'final':refresh_course_qualifications(course_id)


@transaction.atomic
def start_quiz(student, quiz):
    from .models import QuizAttempt
    from django.db.models import Prefetch
    from .models import QuizChoice
    require_quiz_access(student, quiz)
    snapshot = []
    for question in quiz.questions.filter(is_active=True).prefetch_related(Prefetch('choices', queryset=QuizChoice.objects.filter(is_active=True), to_attr='active_choices')):
        choices = question.active_choices
        correct = [choice for choice in choices if choice.is_correct]
        if not 2 <= len(choices) <= 4 or len(correct) != 1:
            raise ValidationError('O quiz precisa ser revisado pela equipe antes de começar.')
        snapshot.append({'id': question.pk, 'text': question.text, 'explanation': question.explanation,
            'choices': [{'id': choice.pk, 'text': choice.text} for choice in choices], 'correct_choice_id': correct[0].pk})
    if not snapshot:
        raise ValidationError('Este quiz ainda não tem perguntas publicadas.')
    return QuizAttempt.objects.create(student=student, quiz=quiz, total=len(snapshot), question_snapshot=snapshot)


def _locked_attempt(student, attempt):
    from .models import QuizAttempt
    QuizAttempt.objects.filter(pk=attempt.pk, student=student).update(total=F('total'))
    current = QuizAttempt.objects.select_related('quiz__lesson__module__course').filter(pk=attempt.pk, student=student).first()
    if current is None:
        raise PermissionDenied('Tentativa privada do aluno.')
    require_quiz_access(student, current.quiz)
    return current


@transaction.atomic
def answer_quiz(student, attempt, *, question_id, choice_id):
    attempt = _locked_attempt(student, attempt)
    if attempt.finished_at or str(question_id) in attempt.answers:
        raise ValidationError('Esta pergunta já foi respondida nesta tentativa.')
    question = next((q for q in attempt.question_snapshot if q['id'] == question_id), None)
    if not question or choice_id not in [choice['id'] for choice in question['choices']]:
        raise ValidationError('Pergunta ou alternativa inválida para esta tentativa.')
    attempt.answers[str(question_id)] = choice_id
    attempt.save(update_fields=['answers'])
    if attempt.quiz.kind == 'final':
        return {'saved': True, 'answered': len(attempt.answers), 'total': attempt.total}
    return {'correct': choice_id == question['correct_choice_id'], 'correct_choice_id': question['correct_choice_id'], 'explanation': question['explanation']}


@transaction.atomic
def finish_quiz(student, attempt):
    from decimal import Decimal, ROUND_DOWN
    from .models import ActivityEvent
    attempt = _locked_attempt(student, attempt)
    if not attempt.finished_at:
        if len(attempt.answers) != len(attempt.question_snapshot):
            raise ValidationError('Responda todas as perguntas antes de finalizar.')
        attempt.correct = sum(attempt.answers.get(str(q['id'])) == q['correct_choice_id'] for q in attempt.question_snapshot)
        attempt.total = len(attempt.question_snapshot)
        attempt.score_pct = (Decimal(attempt.correct)*100/attempt.total).quantize(Decimal('.01'), rounding=ROUND_DOWN)
        attempt.finished_at = timezone.now()
        attempt.save(update_fields=['correct', 'total', 'score_pct', 'finished_at'])
        if attempt.quiz.kind == 'lesson' or attempt.score_pct >= 70:
            ActivityEvent.objects.create(student=student, kind='quiz_finished' if attempt.quiz.kind == 'lesson' else 'final_passed', lesson=attempt.quiz.lesson, course=attempt.quiz.course,
                payload={'quiz_id': attempt.quiz_id, 'score_pct': float(attempt.score_pct)})
        if attempt.quiz.kind == 'final':
            from .models import Enrollment
            refresh_certificate_qualification(Enrollment.objects.get(student=student, course=attempt.quiz.course))
    from .selectors import quiz_attempt_result
    return quiz_attempt_result(attempt)


@transaction.atomic
def create_lesson_quiz(lesson, *, actor):
    from .models import Quiz
    _plan_actor(actor)
    quiz, _ = Quiz.objects.get_or_create(lesson=lesson, defaults={'course': lesson.module.course, 'kind': 'lesson'})
    quiz.full_clean()
    return quiz


@transaction.atomic
def set_quiz_active(content, is_active, *, actor):
    from .models import Quiz
    _plan_actor(actor)
    content.is_active = bool(is_active)
    content.full_clean(); content.save(update_fields=['is_active'])
    quiz = content if isinstance(content, Quiz) else content.quiz
    if quiz.kind == 'final':refresh_course_qualifications(quiz.course_id)
    return content


def create_final_quiz(course, *, actor):
    from .models import Quiz
    _plan_actor(actor)
    quiz, _ = Quiz.objects.get_or_create(course=course, kind='final')
    quiz.full_clean()
    return quiz


def refresh_certificate_qualification(enrollment):
    from .models import Enrollment
    from .selectors import certificate_requirements
    current = Enrollment.objects.select_related('student', 'course').get(pk=enrollment.pk)
    requirements = certificate_requirements(current)
    if requirements['requirements_met'] and requirements['access'].allowed and not current.certificate_qualified_at:
        Enrollment.objects.filter(pk=current.pk).update(certificate_qualified_at=timezone.now())
    elif not requirements['requirements_met'] and current.certificate_qualified_at and not Certificate.objects.filter(enrollment=current).exists():
        Enrollment.objects.filter(pk=current.pk).update(certificate_qualified_at=None)


def refresh_course_qualifications(course_id):
    """Record eligibility at the actual editorial change, never backdate it."""
    from .models import Enrollment
    for enrollment in Enrollment.objects.filter(course_id=course_id).iterator():
        refresh_certificate_qualification(enrollment)


@transaction.atomic
def submit_final_quiz(student, attempt, answers):
    attempt = _locked_attempt(student, attempt)
    if attempt.quiz.kind != 'final':
        raise ValidationError('Esta tentativa não é uma avaliação final.')
    if attempt.finished_at:
        return finish_quiz(student, attempt)
    expected = {str(q['id']): q for q in attempt.question_snapshot}
    if not isinstance(answers, dict) or set(answers) != set(expected):
        raise ValidationError('Responda todas as perguntas antes de enviar.')
    for question_id, choice_id in answers.items():
        if isinstance(choice_id, bool) or choice_id not in [choice['id'] for choice in expected[question_id]['choices']]:
            raise ValidationError('Uma alternativa enviada não pertence à pergunta.')
        if question_id in attempt.answers and attempt.answers[question_id] != choice_id:
            raise ValidationError('Esta pergunta já foi respondida nesta tentativa.')
    attempt.answers = answers
    attempt.save(update_fields=['answers'])
    return finish_quiz(student, attempt)


@transaction.atomic
def import_quiz_rows(rows):
    from collections import defaultdict
    from .models import Quiz
    from .quiz_importing import quiz_import_targets
    from users.models import User
    if not rows:
        raise ValidationError('Arquivo sem perguntas.')
    course_ids = {row.course.pk for row in rows}
    Quiz.objects.filter(course_id__in=course_ids).update(is_active=F('is_active'))
    _, unlisted, conflicts = quiz_import_targets(rows)
    if conflicts:
        raise ValidationError(conflicts)
    actor = User.objects.filter(role__in=['ADMIN','CREATOR'], is_active=True).order_by('pk').first()
    if not actor:
        raise ValidationError('É necessário um administrador ativo para importar perguntas.')
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.key].append(row)
    for key, group in grouped.items():
        first = group[0]
        quiz, _ = Quiz.objects.get_or_create(course=first.course, kind=first.kind, lesson=first.lesson)
        quiz.questions.filter(is_active=True).update(is_active=False)
        quiz.is_demo = False; quiz.is_active = True
        quiz.save(update_fields=['is_demo','is_active'])
        for row in group:
            save_quiz_question(quiz, order=row.order, text=row.text, explanation=row.explanation, choices=row.choices, correct_index=row.correct_index, actor=actor)
    for quiz in unlisted:
        set_quiz_active(quiz, False, actor=actor)


@transaction.atomic
def update_certificate_data(student, *, full_name, cpf):
    student.full_name = full_name.strip()
    student.cpf = validate_cpf(cpf)
    student.full_clean()
    student.save(update_fields=['full_name', 'cpf'])
    for enrollment in student.enrollments.all():
        refresh_certificate_qualification(enrollment)


@transaction.atomic
def issue_certificate_with_data(enrollment, *, full_name, cpf):
    update_certificate_data(enrollment.student, full_name=full_name, cpf=cpf)
    return issue_enrollment_certificate(enrollment)


def mark_material_open(student, kind, material_id):
    from .models import MaterialOpen
    return MaterialOpen.objects.get_or_create(student=student,material_kind=kind,material_id=material_id)[0]


def save_course_material(material, *, actor):
    _plan_actor(actor)
    material.full_clean();material.save()
    return material


def remove_course_material(material, *, actor):
    _plan_actor(actor)
    material.is_active=False
    material.save(update_fields=['is_active'])

@transaction.atomic
def create_quick_lesson(module, title, *, actor):
    from .models import Lesson
    from django.db.models import Max
    _plan_actor(actor)
    title=title.strip()
    if not title:raise ValidationError('Informe o título da aula.')
    order=(module.lessons.aggregate(value=Max('order'))['value'] or 0)+1
    return save_lesson(Lesson(module=module,title=title,order=order,status='draft'))

@transaction.atomic
def reorder_course_content(course, module_ids, lessons, *, actor):
    from .models import Module,Lesson
    _plan_actor(actor)
    actual_modules=set(Module.objects.filter(course=course).values_list('pk',flat=True))
    actual_lessons=set(Lesson.objects.filter(module__course=course).values_list('pk',flat=True))
    if set(module_ids)!=actual_modules or len(module_ids)!=len(actual_modules) or set(lessons)!=actual_modules:
        raise ValidationError('Módulos inválidos. Recarregue a página.')
    flat=[lesson for values in lessons.values() for lesson in values]
    if set(flat)!=actual_lessons or len(flat)!=len(actual_lessons):raise ValidationError('Aulas inválidas. Recarregue a página.')
    for index,module_id in enumerate(module_ids,1):Module.objects.filter(pk=module_id,course=course).update(order=index)
    for module_id,ids in lessons.items():
        for index,lesson_id in enumerate(ids,1):Lesson.objects.filter(pk=lesson_id,module__course=course).update(module_id=module_id,order=index)
    refresh_course_qualifications(course.pk)

@transaction.atomic
def save_lesson_editor(lesson, *, actor, ebook=None):
    from .models import LessonMaterial
    _plan_actor(actor)
    material=None
    if ebook:
        from .validators import validate_pdf_file
        validate_pdf_file(ebook)
        material = lesson.materials.order_by('order', 'pk').first() if lesson.pk else None
        material = material or LessonMaterial(lesson=lesson, order=1)
        material.file=ebook;material.title=ebook.name[:120];material.url=''
        material.full_clean(exclude=['lesson'] if not lesson.pk else None)
    save_lesson(lesson)
    if material:material.save()
    return lesson
