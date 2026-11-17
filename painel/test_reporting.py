from datetime import timedelta
from decimal import Decimal
from django.test import TestCase,RequestFactory
from django.utils import timezone
from users.models import User
from courses.models import Course,Module,Lesson,Enrollment,Progress,StudyDay,Quiz,QuizAttempt

class ReportingTests(TestCase):
 def setUp(self):
  self.admin=User.objects.create_user(username='report-owner',role='CREATOR')
  self.student=User.objects.create_user(username='report-member',email='report@example.org')
  self.course=Course.objects.create(title='Curso relatório',slug='report-course',creator=self.admin.creator_profile)
  self.lesson=Lesson.objects.create(module=Module.objects.create(course=self.course,title='Módulo'),title='Aula',duration_seconds=99999)
  Enrollment.objects.create(student=self.student.student_profile,course=self.course)
 def test_student_visits_are_daily_unique_and_preview_does_not_write(self):
  from users.models import StudentVisit
  self.client.force_login(self.student);self.client.get('/dashboard/');self.client.get('/settings/')
  self.assertEqual(StudentVisit.objects.filter(student=self.student.student_profile).count(),1)
  from users.visit_middleware import StudentVisitMiddleware
  from django.http import HttpResponse
  request=RequestFactory().get('/dashboard/');request.user=self.student;request.member_preview=True
  StudentVisit.objects.all().delete();StudentVisitMiddleware(lambda request:HttpResponse('OK'))(request)
  self.assertFalse(StudentVisit.objects.exists())
 def test_study_hours_use_credited_seconds_and_course_progress_uses_publication(self):
  from painel.reporting import report_data
  StudyDay.objects.create(student=self.student.student_profile,date=timezone.localdate(),seconds=300)
  Progress.objects.create(student=self.student.student_profile,lesson=self.lesson,is_completed=True)
  Lesson.objects.create(module=self.lesson.module,title='Rascunho',status='draft')
  report=report_data()
  self.assertEqual(report['study_seconds'],300);self.assertAlmostEqual(report['study_hours'],1/12)
  self.assertEqual(report['courses'][0]['progress_pct'],100)
 def test_final_approval_counts_best_per_student_not_attempts(self):
  from painel.reporting import report_data
  quiz=Quiz.objects.create(course=self.course,kind='final')
  for score in (60,80):QuizAttempt.objects.create(student=self.student.student_profile,quiz=quiz,score_pct=score,total=5,correct=3 if score==60 else 4,finished_at=timezone.now())
  row=report_data()['courses'][0]
  self.assertEqual(row['exam_students'],1);self.assertEqual(row['approved'],1);self.assertEqual(row['approval_pct'],100)
 def test_report_and_csv_are_restricted_and_csv_neutralizes_formula_cells(self):
  self.client.force_login(self.student)
  self.assertEqual(self.client.get('/painel/relatorios/').status_code,403)
  self.assertEqual(self.client.get('/painel/relatorios/exportar/').status_code,403)
  self.client.force_login(self.admin)
  profile=self.student.student_profile;profile.full_name='=HYPERLINK("https://example.org")';profile.save()
  response=self.client.get('/painel/relatorios/exportar/')
  self.assertEqual(response.status_code,200);self.assertIn("'=HYPERLINK",response.content.decode('utf-8-sig'))
  self.assertTemplateUsed(self.client.get('/painel/relatorios/'),'base_painel_gomut.html')
 def test_visit_counts_and_inactive_members_have_no_fabricated_history(self):
  from users.models import StudentVisit
  from painel.reporting import report_data
  StudentVisit.objects.create(student=self.student.student_profile,date=timezone.localdate())
  report=report_data();self.assertEqual(report['active_7'],1);self.assertEqual(report['visits'][-1]['count'],1)
  self.assertFalse(report['inactive'])
