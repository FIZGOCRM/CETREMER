from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from users.models import User,StudentVisit
from courses.models import Course,Enrollment,Module,Lesson,Progress

class MemberPreviewTests(TestCase):
 def setUp(self):
  self.admin=User.objects.create_user(username='preview-admin',role='CREATOR')
  self.student=User.objects.create_user(username='preview-member',email='preview@example.org')
  self.student.student_profile.full_name='Aluno escolhido';self.student.student_profile.save()
  self.other=User.objects.create_user(username='preview-other')
  self.course=Course.objects.create(is_published=True, title='Curso do aluno',slug='preview-course',creator=self.admin.creator_profile)
  self.enrollment=Enrollment.objects.create(student=self.student.student_profile,course=self.course)
  self.lesson=Lesson.objects.create(module=Module.objects.create(course=self.course,title='Módulo'),title='Aula do aluno',video_url='https://vimeo.com/76979871')
  self.progress=Progress.objects.create(student=self.student.student_profile,lesson=self.lesson,last_position_seconds=12)
  self.client.force_login(self.admin)
 def start(self):return self.client.get(f'/painel/visualizar/{self.student.pk}/')
 def test_preview_keeps_admin_session_and_shows_student_banner(self):
  self.assertEqual(self.start().status_code,302)
  response=self.client.get('/dashboard/')
  self.assertEqual(response.context['user'].pk,self.student.pk)
  self.assertContains(response,'Vendo como membro');self.assertContains(response,'Aluno escolhido')
  self.assertEqual(self.client.session['_auth_user_id'],str(self.admin.pk))
 def test_preview_gets_do_not_change_access_dates_visits_or_position(self):
  self.assertEqual(self.start().status_code,302);self.client.get(f'/courses/{self.course.slug}/lessons/{self.lesson.pk}/')
  self.enrollment.refresh_from_db();self.progress.refresh_from_db();self.student.refresh_from_db()
  self.assertIsNone(self.enrollment.last_accessed_at);self.assertEqual(self.progress.last_position_seconds,12)
  self.assertFalse(StudentVisit.objects.exists());self.assertIsNone(self.student.last_login)
 def test_all_member_posts_including_player_and_logout_are_blocked(self):
  self.start()
  paths=[f'/courses/lesson/{self.lesson.pk}/heartbeat/',f'/courses/lesson/{self.lesson.pk}/toggle-progress/',f'/courses/lesson/{self.lesson.pk}/notes/','/settings/','/quizzes/999/start/','/logout/','/notificacoes/lidas/','/community/post/new/']
  for path in paths:
   response=self.client.post(path,{'position':60,'playing':True,'action':'profile_account','email':'changed@example.org'})
   self.assertEqual(response.status_code,403,path);self.assertIn('Modo visualização: ações desativadas',response.content.decode())
  self.student.refresh_from_db();self.assertEqual(self.student.email,'preview@example.org')
  self.assertEqual(self.client.session['_auth_user_id'],str(self.admin.pk))
 def test_exit_closes_audit_and_restores_panel(self):
  from users.models import MemberPreviewLog
  self.start();response=self.client.get('/painel/visualizar/encerrar/')
  self.assertEqual(response.status_code,302)
  log=MemberPreviewLog.objects.get();self.assertIsNotNone(log.ended_at)
  self.assertEqual(log.admin,self.admin);self.assertEqual(log.student,self.student.student_profile)
  self.assertEqual(self.client.get('/painel/').context['user'].pk,self.admin.pk)
 def test_student_cannot_start_or_forge_preview_session(self):
  self.client.force_login(self.other)
  self.assertEqual(self.start().status_code,403)
  session=self.client.session;session['member_preview']={'admin_id':self.admin.pk,'student_id':self.student.pk,'log_id':999};session.save()
  response=self.client.get('/dashboard/');self.assertEqual(response.context['user'].pk,self.other.pk)
  self.assertNotContains(response,'Aluno escolhido')
 def test_preview_respects_target_access_period_and_switch_closes_previous_log(self):
  from users.models import MemberPreviewLog
  self.enrollment.access_policy='periods';self.enrollment.save()
  self.start();response=self.client.get(f'/courses/{self.course.slug}/lessons/{self.lesson.pk}/')
  self.assertEqual(response.status_code,403);self.assertNotContains(response,'player.vimeo.com',status_code=403)
  self.client.get(f'/painel/visualizar/{self.other.pk}/')
  self.assertEqual(MemberPreviewLog.objects.count(),2)
  self.assertEqual(MemberPreviewLog.objects.filter(ended_at__isnull=True).get().student,self.other.student_profile)
 def test_preview_material_does_not_mark_open_or_issue_certificate(self):
  from tempfile import TemporaryDirectory
  from django.test import override_settings
  from django.core.files.uploadedfile import SimpleUploadedFile
  from courses.models import CourseMaterial,MaterialOpen,Certificate
  with TemporaryDirectory() as folder,override_settings(MEDIA_ROOT=folder):
   material=CourseMaterial.objects.create(course=self.course,title='PDF de prévia',file=SimpleUploadedFile('preview.pdf',b'%PDF-1.4\n%%EOF',content_type='application/pdf'))
   self.start();response=self.client.get(f'/materiais/course/{material.pk}/')
   self.assertEqual(response.status_code,200);response.close()
   self.assertFalse(MaterialOpen.objects.exists())
   self.client.get(f'/courses/{self.course.slug}/certificate/')
   self.assertFalse(Certificate.objects.exists())
 def test_malformed_preview_payload_never_causes_impersonation(self):
  session=self.client.session;session['member_preview']={'admin_id':self.admin.pk,'student_id':'bad','log_id':'bad'};session.save()
  response=self.client.get('/dashboard/')
  self.assertEqual(response.status_code,302)
  self.assertNotIn('member_preview',self.client.session)
