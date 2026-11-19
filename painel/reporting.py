"""Aggregate producer reports from recorded data, independent of request/rendering."""
from collections import defaultdict
from datetime import datetime, time, timedelta
from django.db.models import Avg, Count, F, FilteredRelation, FloatField, Max, Q, Sum, Value
from django.db.models.functions import Greatest, Least, NullIf
from django.utils import timezone
from courses.models import Course,Enrollment,Lesson,Progress,Quiz,QuizAttempt,StudyDay
from courses.access import access_decision
from courses.services import plan_status
from users.models import StudentProfile,StudentVisit


LESSON_SORTS = (
    ('title', 'Título da aula'), ('started', 'Alunos que começaram'),
    ('finished', 'Chegaram ao final'), ('finish_pct', 'Percentual que chegou ao final'),
    ('avg_pct', 'Avanço médio'), ('manual', 'Conclusões manuais'),
)


def lesson_metrics(*, course=None, days=None, order='-started', on=None):
    lessons = Lesson.objects.select_related('module__course')
    if course:
        lessons = lessons.filter(module__course=course)
    window = Q()
    if days is not None:
        today = on or timezone.localdate()
        first_day = today - timedelta(days=days - 1)
        start = timezone.make_aware(datetime.combine(first_day, time.min))
        end = timezone.make_aware(datetime.combine(today + timedelta(days=1), time.min))
        window = Q(student_progress__started_at__gte=start, student_progress__started_at__lt=end)
    lessons = lessons.annotate(tracking=FilteredRelation('student_progress', condition=window))
    lessons = lessons.alias(
        furthest=Greatest('tracking__max_position_seconds', 'tracking__last_position_seconds'),
    )
    advanced = Q(furthest__gt=0) | Q(tracking__watched_seconds__gt=0)
    measured = advanced & Q(duration_seconds__gt=0)
    reached_end = Q(duration_seconds__gt=0, furthest__gte=F('duration_seconds') * 0.9)
    reached_end |= Q(tracking__auto_completed_at__isnull=False)
    percent = Least(Value(100.0), F('furthest') * 100.0 / NullIf('duration_seconds', 0))
    lessons = lessons.alias(percent=percent).annotate(
        started=Count('tracking', filter=advanced),
        finished=Count('tracking', filter=advanced & reached_end),
        manual=Count('tracking', filter=Q(tracking__manual_completed_at__isnull=False)),
        avg_pct=Avg('percent', filter=measured, output_field=FloatField()),
        first_band=Count('tracking', filter=measured & Q(percent__lt=25)),
        second_band=Count('tracking', filter=measured & Q(percent__gte=25, percent__lt=50)),
        third_band=Count('tracking', filter=measured & Q(percent__gte=50, percent__lt=75)),
        fourth_band=Count('tracking', filter=measured & Q(percent__gte=75)),
    ).annotate(finish_pct=F('finished') * 100.0 / NullIf('started', 0))
    key = order.lstrip('-')
    if key not in dict(LESSON_SORTS):
        key, order = 'started', '-started'
    ordering = F(key).desc(nulls_last=True) if order.startswith('-') else F(key).asc(nulls_last=True)
    return [{
        'lesson': lesson, 'started': lesson.started, 'finished': lesson.finished,
        'finish_pct': lesson.finish_pct, 'manual': lesson.manual, 'avg_pct': lesson.avg_pct,
        'bands': [lesson.first_band, lesson.second_band, lesson.third_band, lesson.fourth_band],
    } for lesson in lessons.order_by(ordering, 'title', 'pk')]


def report_data(*,days=7,on=None):
    today=on or timezone.localdate();since=today-timedelta(days=days-1)
    daily=dict(StudentVisit.objects.filter(date__range=(since,today)).values('date').annotate(total=Count('student_id',distinct=True)).values_list('date','total'))
    maximum=max(daily.values(),default=1) or 1
    visits=[{'date':today-timedelta(days=offset),'count':daily.get(today-timedelta(days=offset),0),'height':round(daily.get(today-timedelta(days=offset),0)*140/maximum)} for offset in reversed(range(days))]
    study_seconds=StudyDay.objects.filter(date__range=(since,today)).aggregate(value=Sum('seconds'))['value'] or 0
    enrollments=list(Enrollment.objects.select_related('course','student__user').prefetch_related('access_periods','access_changes'))
    by_course=defaultdict(list)
    for enrollment in enrollments:by_course[enrollment.course_id].append(enrollment)
    totals=dict(Lesson.objects.filter(status='published',module__status='published').values('module__course_id').annotate(total=Count('pk')).values_list('module__course_id','total'))
    done={(row['lesson__module__course_id'],row['student_id']):row['done'] for row in Progress.objects.filter(is_completed=True,lesson__status='published',lesson__module__status='published').values('lesson__module__course_id','student_id').annotate(done=Count('lesson_id',distinct=True))}
    exam_results=defaultdict(list)
    for row in QuizAttempt.objects.filter(quiz__kind='final',quiz__is_active=True,finished_at__isnull=False).values('quiz__course_id','student_id').annotate(best=Max('score_pct')):exam_results[row['quiz__course_id']].append(row)
    finals=set(Quiz.objects.filter(kind='final',is_active=True).values_list('course_id',flat=True))
    courses=[];progress={}
    for course in Course.objects.order_by('title','pk'):
        members=by_course[course.pk];total=totals.get(course.pk,0)
        for enrollment in members:progress[enrollment.pk]=100*done.get((course.pk,enrollment.student_id),0)/total if total else 0
        exams=[row for row in exam_results[course.pk] if row['student_id'] in {e.student_id for e in members}]
        approved=sum(row['best']>=70 for row in exams)
        courses.append({'course':course,'students':len(members),'lessons':total,'progress_pct':sum(progress[e.pk] for e in members)/len(members) if members else None,'has_final':course.pk in finals,'exam_students':len(exams),'approved':approved,'approval_pct':approved*100/len(exams) if exams else None})
    inactive=list(StudentProfile.objects.filter(user__role='STUDENT',enrollments__isnull=False).select_related('user').annotate(last_seen=Max('visits__date')).filter(Q(last_seen__lt=today-timedelta(days=6))|Q(last_seen__isnull=True)).distinct().order_by('last_seen','user__username'))
    expiring=[]
    for enrollment in enrollments:
        plan=plan_status(enrollment,on=today)
        if plan['state']=='ending_soon':expiring.append({'enrollment':enrollment,'plan':plan,'pct':progress[enrollment.pk]})
    expiring.sort(key=lambda row:row['plan']['ends_on'])
    top=list(Lesson.objects.select_related('module__course').annotate(completions=Count('student_progress',filter=Q(student_progress__is_completed=True),distinct=True)).filter(completions__gt=0).order_by('-completions','pk')[:5])
    visitors = set(StudentVisit.objects.filter(date__range=(since, today)).values_list('student_id', flat=True).distinct())
    current_students = {e.student_id for e in enrollments if access_decision(e, on=today).allowed}
    courses.sort(key=lambda row: -row['students'])
    return {'visiting_students': len(visitors), 'inactive_current': len(current_students - visitors),
            'first_visit': StudentVisit.objects.order_by('date').values_list('date', flat=True).first(),
            'days':days,'since':since,'today':today,'visits':visits,'active_7':StudentVisit.objects.filter(date__range=(today-timedelta(days=6),today)).values('student_id').distinct().count(),'study_seconds':study_seconds,'study_hours':study_seconds/3600,'courses':courses,'top_lessons':top,'inactive':inactive,'expiring':expiring}
