"""Read-only queries shared by student, certificate and management views."""

from .models import Lesson, Progress


def course_modules(enrollment):
    from django.db.models import Prefetch
    from .models import Module
    from .access import lesson_availability, module_release_date
    done = set(Progress.objects.filter(student=enrollment.student, lesson__module__course=enrollment.course, is_completed=True).values_list('lesson_id', flat=True))
    modules = list(Module.objects.filter(course=enrollment.course, status='published').prefetch_related(Prefetch('lessons', queryset=Lesson.objects.filter(status='published').select_related('module__course').prefetch_related('materials'))))
    from django.db.models import Count, Q
    from .models import Quiz, QuizAttempt
    quizzes = {q.lesson_id: q for q in Quiz.objects.filter(course=enrollment.course, kind='lesson', is_active=True).annotate(question_count=Count('questions', filter=Q(questions__is_active=True))).filter(question_count__gt=0)}
    latest = {}
    for attempt in QuizAttempt.objects.filter(student=enrollment.student, quiz_id__in=[q.pk for q in quizzes.values()], finished_at__isnull=False).order_by('-finished_at', '-id'):
        latest.setdefault(attempt.quiz_id, attempt)
    for module in modules:
        module.release_date = module_release_date(enrollment, module)
        for lesson in module.lessons.all():
            lesson.availability = lesson_availability(enrollment, lesson, completed_ids=done)
            quiz = quizzes.get(lesson.pk)
            lesson.quiz_count = quiz.question_count if quiz else 0
            lesson.quiz_result = latest.get(quiz.pk) if quiz else None
    return modules


def ordered_lessons(course):
    return list(
        Lesson.objects.filter(module__course=course, status='published', module__status='published').select_related('module__course').order_by(
            "module__order", "module_id", "order", "id"
        )
    )


def progress_info(student, course, lessons=None, *, enrollment=None, completed_ids=None, started=None, final_data=None):
    lessons = lessons if lessons is not None else ordered_lessons(course)
    done_ids = set(completed_ids) if completed_ids is not None else set(
        Progress.objects.filter(
            student=student,
            lesson__in=lessons,
            is_completed=True,
        ).values_list("lesson_id", flat=True)
    )
    total = len(lessons)
    completed = len(done_ids)
    from .access import lesson_availability, access_decision
    from .models import Enrollment
    if enrollment is None:
        enrollment = Enrollment.objects.filter(student=student, course=course).prefetch_related('access_periods').first()
    availability = {lesson.pk: lesson_availability(enrollment, lesson, completed_ids=done_ids) for lesson in lessons}
    available = [lesson for lesson in lessons if availability[lesson.pk].state == 'available']
    next_lesson = next((lesson for lesson in available if lesson.id not in done_ids), available[-1] if available and completed == total else None)
    scheduled = [a.release_date for a in availability.values() if a.state == 'scheduled' and a.release_date]
    if started is None:
        from django.db.models import Q
        started = bool(completed) or Progress.objects.filter(student=student, lesson__in=lessons).filter(Q(watched_seconds__gt=0)|Q(last_position_seconds__gt=0)).exists()
    final_data = student_final_data(student, course) if final_data is None else final_data
    best = final_data.get('best_score')
    all_lessons = bool(total) and completed == total
    status = 'new'
    if not access_decision(enrollment).allowed:
        status = 'ended'
    elif all_lessons:
        status = 'exam' if final_data.get('quiz') and (best is None or best < 70) else 'done'
    elif not any(lesson.pk not in done_ids for lesson in available) and scheduled:
        status = 'waiting_release'
    elif started:
        status = 'progress'
    return {
        "course": course,
        "pct": round(100 * completed / total) if total else 0,
        "completed": completed,
        "total": total,
        "next_lesson": next_lesson,
        "status": status,
        'next_release': min(scheduled) if scheduled else None,
        'has_final': bool(final_data.get('quiz')), 'final_quiz': final_data.get('quiz'), 'final_best_score': best,
        'all_lessons': all_lessons,
    }


def member_course_items(student):
    from collections import defaultdict
    from .access import access_decision
    from .models import Certificate, Enrollment, Quiz, QuizAttempt
    from django.db.models import Count, Max, Q
    from .services import plan_status, profile_data_ok
    enrollments = list(Enrollment.objects.filter(student=student, course__is_published=True).select_related('course__category').prefetch_related('access_periods', 'access_changes').order_by('-enrolled_at'))
    course_ids = [e.course_id for e in enrollments]
    lessons_by_course = defaultdict(list)
    for lesson in Lesson.objects.filter(module__course_id__in=course_ids, status='published', module__status='published').select_related('module__course').order_by('module__order', 'order', 'id'):
        lessons_by_course[lesson.module.course_id].append(lesson)
    records_by_course = defaultdict(list)
    for record in Progress.objects.filter(student=student, lesson__module__course_id__in=course_ids, lesson__status='published', lesson__module__status='published').select_related('lesson__module'):
        records_by_course[record.lesson.module.course_id].append(record)
    certificates = {cert.enrollment_id: cert for cert in Certificate.objects.filter(enrollment__student=student)}
    finals = {q.course_id: q for q in Quiz.objects.filter(course_id__in=course_ids, kind='final', is_active=True).annotate(question_count=Count('questions', filter=Q(questions__is_active=True))).filter(question_count__gt=0)}
    from django.db.models import Min
    final_results = {row['quiz_id']:row for row in QuizAttempt.objects.filter(student=student, quiz_id__in=[q.pk for q in finals.values()], finished_at__isnull=False).values('quiz_id').annotate(best=Max('score_pct'), passed_at=Min('finished_at', filter=Q(score_pct__gte=70)))}
    quizzes = list(Quiz.objects.filter(course_id__in=course_ids, kind='lesson', is_active=True, lesson__status='published', lesson__module__status='published').select_related('lesson').annotate(question_count=Count('questions', filter=Q(questions__is_active=True))).filter(question_count__gt=0).order_by('lesson__module__order', 'lesson__order', 'id'))
    quiz_results = {row['quiz_id']: row for row in QuizAttempt.objects.filter(student=student, quiz_id__in=[q.pk for q in quizzes], finished_at__isnull=False).values('quiz_id').annotate(best=Max('score_pct'))}
    data_ok = profile_data_ok(student)
    items = []
    for enrollment in enrollments:
        records = records_by_course[enrollment.course_id]
        done = {r.lesson_id for r in records if r.is_completed}
        started = any(r.is_completed or r.watched_seconds or r.last_position_seconds for r in records)
        final = finals.get(enrollment.course_id)
        final_result = final_results.get(final.pk, {}) if final else {}
        item = progress_info(student, enrollment.course, lessons_by_course[enrollment.course_id], enrollment=enrollment, completed_ids=done, started=started, final_data={'quiz':final, 'best_score':float(final_result['best']) if final_result.get('best') is not None else None})
        item.update(enrollment=enrollment, access=access_decision(enrollment), plan=plan_status(enrollment),
            certificate=certificates.get(enrollment.pk), watched_seconds=sum(r.watched_seconds for r in records),
            started=any(r.is_completed or r.watched_seconds or r.last_position_seconds for r in records))
        from .access import access_decision as historical_access
        from django.utils import timezone
        qualification = enrollment.certificate_qualified_at
        times = [r.completed_at for r in records if r.is_completed and r.completed_at]+[t for t in (qualification, final_result.get('passed_at')) if t]
        historical_ok = bool(qualification and times and historical_access(enrollment, on=timezone.localdate(max(times))).allowed)
        academic_ok = item['all_lessons'] and (not item['has_final'] or item['final_best_score'] is not None and item['final_best_score'] >= 70)
        item['certificate_ready'] = bool(academic_ok and (item['access'].allowed or historical_ok) and data_ok and not item['certificate'])
        item['ring_offset'] = round(194.78*(1-item['pct']/100), 2)
        course_quizzes = [q for q in quizzes if q.course_id == enrollment.course_id]
        item['quizzes_total'] = len(course_quizzes)
        item['quizzes_done'] = sum(q.pk in quiz_results for q in course_quizzes)
        item['pending_quiz'] = next((q for q in course_quizzes if q.lesson_id in done and q.pk not in quiz_results), None)
        items.append(item)
    return items


def member_summary(student, *, on=None):
    from django.conf import settings
    from datetime import timedelta
    from math import ceil
    from django.urls import reverse
    from django.utils import timezone
    from .models import ActivityEvent, StudyDay
    today = on or timezone.localdate()
    items = member_course_items(student)
    days = dict(StudyDay.objects.filter(student=student, date__lte=today).values_list('date', 'seconds'))
    week_seconds = sum(days.get(today-timedelta(days=i), 0) for i in range(7))
    previous = sum(days.get(today-timedelta(days=i), 0) for i in range(7, 14))
    streak = 0
    while days.get(today-timedelta(days=streak), 0) >= 60:
        streak += 1
    max_seconds = max((days.get(today-timedelta(days=i), 0) for i in range(84)), default=0)
    heatmap = []
    for i in reversed(range(84)):
        day = today-timedelta(days=i); seconds = days.get(day, 0)
        heatmap.append({'date': day, 'seconds': seconds, 'level': ceil(seconds*4/max_seconds) if max_seconds else 0, 'today': i == 0})
    week = []
    max_minutes = max(40, max((days.get(today-timedelta(days=i), 0)/60 for i in range(7)), default=0))
    for index, offset in enumerate(reversed(range(7))):
        day = today-timedelta(days=offset); seconds = days.get(day, 0)
        height = round(seconds/60/max_minutes*140)
        week.append({'date': day, 'label': 'Hoje' if offset == 0 else ('Seg','Ter','Qua','Qui','Sex','Sáb','Dom')[day.weekday()],
            'seconds': seconds, 'minutes': round(seconds/60, 1), 'height': height or 2, 'y': 160-height if height else 158, 'x': 35+index*74, 'today': offset == 0})
    activity = list(ActivityEvent.objects.filter(student=student).select_related('lesson', 'course')[:6])
    labels = {'lesson_completed': 'Aula concluída', 'quiz_finished': 'Quiz concluído', 'final_passed': 'Avaliação aprovada', 'certificate_issued': 'Certificado emitido'}
    for event in activity:
        event.label = labels.get(event.kind, 'Atividade')
    next_steps = []
    for item in items:
        if not item['access'].allowed:
            if item['certificate_ready']:
                next_steps.append({'priority':5, 'title':'Emitir certificado', 'detail':item['course'].title, 'url':reverse('certificates'), 'icon':'award'})
            continue
        quiz = item.get('pending_quiz')
        if quiz:
            next_steps.append({'priority': 1, 'title': 'Fazer o quiz: '+quiz.lesson.title, 'detail': item['course'].title+f' · {quiz.question_count} perguntas',
                'url': reverse('lesson_detail', args=[item['course'].slug, quiz.lesson_id])+'#quiz', 'icon': 'quiz'})
        lesson = item['next_lesson']
        if item['status'] == 'exam':
            next_steps.append({'priority':4, 'title':'Fazer a avaliação final', 'detail':item['course'].title+' · mínimo 70%', 'url':reverse('final_assessment', args=[item['course'].slug]), 'icon':'quiz'})
        elif lesson and item['status'] not in ('done', 'ended', 'waiting_release'):
            next_steps.append({'priority': 2 if item['started'] else 3, 'title': ('Continuar: '+lesson.title) if item['started'] else ('Começar '+item['course'].title),
                'detail': item['course'].title, 'url': reverse('lesson_detail', args=[item['course'].slug, lesson.pk]), 'icon': 'play'})
        elif item['status'] == 'done' and not item['certificate']:
            next_steps.append({'priority': 5, 'title': 'Emitir certificado', 'detail': item['course'].title+' · precisa de nome e CPF', 'url': reverse('certificates'), 'icon': 'award'})
        elif item['next_release']:
            next_steps.append({'priority': 6, 'title': 'Próximo módulo libera em '+item['next_release'].strftime('%d/%m'), 'detail': item['course'].title,
                'url': reverse('member_course', args=[item['course'].slug]), 'icon': 'lock'})
    from .live_selectors import student_events
    next_event=student_events(student).filter(starts_at__gte=timezone.now()).first()
    if next_event:
        next_steps.append({'priority':7,'title':next_event.title,'detail':timezone.localtime(next_event.starts_at).strftime('%d/%m às %H:%M'),'url':reverse('live_classes'),'icon':'live'})
    next_steps.sort(key=lambda step: step['priority'])
    total = sum(item['total'] for item in items); completed = sum(item['completed'] for item in items)
    return {'items': items, 'total': total, 'completed': completed, 'remaining': total-completed,
        'is_demo': settings.GOMUT_DEMO_MODE and student.user.username=='gomut-demo-student' and student.user.email=='aluno@gomut.example',
        'week_seconds': week_seconds, 'previous_seconds': previous, 'difference_seconds': week_seconds-previous, 'difference_abs_seconds': abs(week_seconds-previous), 'streak': streak,
        'week': week, 'heatmap': heatmap, 'activity': activity, 'next_steps': next_steps[:4],
        'certificates_issued': sum(bool(item['certificate']) for item in items), 'certificates_ready': sum(item['certificate_ready'] for item in items)}


def public_quiz_attempt(attempt):
    return {'id': attempt.pk, 'quiz_id': attempt.quiz_id, 'is_demo': attempt.quiz.is_demo, 'kind': attempt.quiz.kind,
        'questions': [{'id': question['id'], 'text': question['text'],
                       'choices': [{'id': c['id'], 'text': c['text']} for c in question['choices']]}
                      for question in attempt.question_snapshot]}


def quiz_question_feedback(question, chosen_id):
    correct_id = question['correct_choice_id']
    general = question.get('explanation', '')
    explanations = {choice['id']: choice.get('explanation') or general for choice in question['choices']}
    return {'correct': chosen_id == correct_id, 'chosen_choice_id': chosen_id, 'correct_choice_id': correct_id,
            'explanation': general, 'chosen_explanation': explanations.get(chosen_id, general),
            'correct_explanation': explanations[correct_id]}


def quiz_attempt_result(attempt):
    from django.core.exceptions import PermissionDenied
    from django.db.models import Max
    if not attempt.finished_at:
        raise PermissionDenied('Finalize a tentativa antes de ver a correção.')
    best = attempt.quiz.attempts.filter(student=attempt.student, finished_at__isnull=False).aggregate(value=Max('score_pct'))['value'] or 0
    return {'id': attempt.pk, 'correct': attempt.correct, 'total': attempt.total, 'score_pct': float(attempt.score_pct), 'best_score': float(best),
        'questions': [dict(question, **quiz_question_feedback(question, attempt.answers.get(str(question['id']))))
                      for question in attempt.question_snapshot]}


def lesson_quiz_state(student, lesson):
    quiz = getattr(lesson, 'quiz', None)
    if not quiz or not quiz.is_active:
        return {'has_quiz': False}
    count = quiz.questions.filter(is_active=True).count()
    if not count:
        return {'has_quiz': False}
    latest = quiz.attempts.filter(student=student, finished_at__isnull=False).order_by('-finished_at', '-id').first()
    completed = Progress.objects.filter(student=student, lesson=lesson, is_completed=True).exists()
    result = quiz_attempt_result(latest) if latest else None
    return {'has_quiz': True, 'quiz': quiz, 'quiz_question_count': count, 'quiz_pending': latest is None,
        'quiz_state': 'done' if latest else 'available' if completed else 'blocked', 'quiz_result': result}


def has_active_lesson_quiz(lesson):
    quiz = getattr(lesson, 'quiz', None)
    return bool(quiz and quiz.is_active and quiz.questions.filter(is_active=True).exists())


def active_final_quiz(course):
    from django.db.models import Count, Q
    from .models import Quiz
    return Quiz.objects.filter(course=course, kind='final', is_active=True).annotate(question_count=Count('questions', filter=Q(questions__is_active=True))).filter(question_count__gt=0).first()


def certificate_requirements(enrollment):
    from django.db.models import Max, Min
    from .access import access_decision
    from .models import Enrollment
    from .services import profile_data_ok
    from django.utils import timezone
    enrollment = Enrollment.objects.select_related('student', 'course').prefetch_related('access_periods').get(pk=enrollment.pk)
    lessons = ordered_lessons(enrollment.course)
    completed = list(Progress.objects.filter(student=enrollment.student, lesson__in=lessons, is_completed=True))
    all_lessons = bool(lessons) and len(completed) == len(lessons)
    final = active_final_quiz(enrollment.course)
    best, passed_at = None, None
    if final:
        best = final.attempts.filter(student=enrollment.student, finished_at__isnull=False).aggregate(score=Max('score_pct'))['score']
        passed_at = final.attempts.filter(student=enrollment.student, finished_at__isnull=False, score_pct__gte=70).aggregate(at=Min('finished_at'))['at']
    data_ok = profile_data_ok(enrollment.student)
    requirements_met = all_lessons and data_ok and (not final or best is not None and best >= 70)
    access = access_decision(enrollment)
    qualified_at = enrollment.certificate_qualified_at
    times = [record.completed_at for record in completed if record.completed_at] + [t for t in (qualified_at, passed_at) if t]
    historical_ok = bool(qualified_at and times and access_decision(enrollment, on=timezone.localdate(max(times))).allowed)
    return {'total': len(lessons), 'completed': len(completed), 'all_lessons': all_lessons,
        'has_final': bool(final), 'final_quiz': final, 'best_score': float(best) if best is not None else None,
        'final_passed': not final or best is not None and best >= 70, 'data_ok': data_ok,
        'requirements_met': requirements_met, 'access': access, 'qualified_at': qualified_at,
        'can_issue': bool(requirements_met and (access.allowed or historical_ok))}


def student_final_data(student, course):
    from django.db.models import Max
    final = active_final_quiz(course)
    best = final.attempts.filter(student=student, finished_at__isnull=False).aggregate(value=Max('score_pct'))['value'] if final else None
    return {'quiz':final, 'best_score':float(best) if best is not None else None}


def library_items(student, *, kind='', course=None, q=''):
    from .models import CourseMaterial, Enrollment, LessonMaterial, MaterialOpen
    from .access import access_decision, lesson_availability
    from django.db.models import Q
    from django.urls import reverse
    enrollments = {e.course_id:e for e in Enrollment.objects.filter(student=student).select_related('course').prefetch_related('access_periods')}
    allowed = [pk for pk,e in enrollments.items() if e.course.is_published and access_decision(e).allowed and (not course or pk == course)]
    opened = set(MaterialOpen.objects.filter(student=student).values_list('material_kind','material_id'))
    done = set(Progress.objects.filter(student=student,is_completed=True).values_list('lesson_id',flat=True))
    items = []
    if kind != 'course':
        materials = LessonMaterial.objects.filter(lesson__module__course_id__in=allowed, lesson__status='published',lesson__module__status='published').select_related('lesson__module__course')
        if q:
            materials = materials.filter(Q(title__icontains=q)|Q(lesson__title__icontains=q)|Q(lesson__module__course__title__icontains=q))
        for material in materials:
            lesson = material.lesson
            if lesson_availability(enrollments[lesson.module.course_id], lesson, completed_ids=done).state == 'available' and (material.file or material.url):
                items.append({'kind':'lesson','material':material,'course':lesson.module.course,'lesson':lesson,'opened':('lesson',material.pk) in opened,'url':reverse('material_open',args=['lesson',material.pk])})
    if kind != 'lesson':
        materials = CourseMaterial.objects.filter(course_id__in=allowed,is_active=True).select_related('course')
        if q:
            materials = materials.filter(Q(title__icontains=q)|Q(course__title__icontains=q))
        for material in materials:
            items.append({'kind':'course','material':material,'course':material.course,'opened':('course',material.pk) in opened,'url':reverse('material_open',args=['course',material.pk])})
    if kind == 'opened':
        items = [item for item in items if item['opened']]
    return sorted(items,key=lambda item:(item['course'].title,item['material'].order,item['material'].pk))


def search_lessons(student,term):
    from django.db.models import Q
    from .models import Enrollment,Lesson,Progress
    from .access import lesson_availability
    enrollments={e.course_id:e for e in Enrollment.objects.filter(student=student).prefetch_related('access_periods')}
    completed=set(Progress.objects.filter(student=student,is_completed=True).values_list('lesson_id',flat=True))
    lessons=Lesson.objects.filter(module__course_id__in=enrollments,module__course__is_published=True,status='published',module__status='published').filter(Q(title__icontains=term)|Q(module__title__icontains=term)).select_related('module__course').order_by('module__course__title','module__order','order','pk')[:100]
    return [{'lesson':lesson,'availability':lesson_availability(enrollments[lesson.module.course_id],lesson,completed_ids=completed)} for lesson in lessons]


def course_publication_time(enrollment, module, published_at, *, attachment_created_at=None):
    """Earliest instant this published item could appear for this enrollment."""
    from datetime import datetime, time
    from django.utils import timezone
    from .access import module_release_date

    known = [stamp for stamp in (published_at, attachment_created_at) if stamp is not None]
    if not known:
        return None
    if module.release_month > 1:
        release = module_release_date(enrollment, module)
        if release:
            known.append(timezone.make_aware(datetime.combine(release, time.min)))
    return max(known)
