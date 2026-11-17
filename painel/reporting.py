"""Aggregate producer reports from recorded data, independent of request/rendering."""
from collections import defaultdict
from datetime import timedelta
from django.db.models import Count,Max,Sum,Q
from django.utils import timezone
from courses.models import Course,Enrollment,Lesson,Progress,Quiz,QuizAttempt,StudyDay
from courses.services import plan_status
from users.models import StudentProfile,StudentVisit


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
    return {'days':days,'since':since,'today':today,'visits':visits,'active_7':StudentVisit.objects.filter(date__range=(today-timedelta(days=6),today)).values('student_id').distinct().count(),'study_seconds':study_seconds,'study_hours':study_seconds/3600,'courses':courses,'top_lessons':top,'inactive':inactive,'expiring':expiring}
