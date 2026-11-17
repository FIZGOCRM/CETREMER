from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses import models, services
from courses.models import Course, Enrollment, Lesson, Module, Progress, Quiz
from users.models import User


class FinalAssessmentTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='final-owner', role='CREATOR')
        self.user = User.objects.create_user(username='final-student')
        self.student = self.user.student_profile
        self.student.full_name = 'Aluno Completo'; self.student.cpf = '52998224725'; self.student.save()
        self.course = Course.objects.create(title='Curso', slug='final-course', creator=self.owner.creator_profile)
        self.lesson = Lesson.objects.create(module=Module.objects.create(course=self.course, title='M'), title='A')
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.quiz = Quiz.objects.create(course=self.course, kind='final')
        self.question = services.save_quiz_question(self.quiz, order=1, text='Final', explanation='Só após todas as respostas', choices=['Certa', 'Errada'], correct_index=0, actor=self.owner)
        self.client.force_login(self.user)

    def finish_final(self, correct=True):
        attempt = services.start_quiz(self.student, self.quiz)
        choice = self.question.choices.get(is_active=True, is_correct=correct)
        answer = services.answer_quiz(self.student, attempt, question_id=self.question.pk, choice_id=choice.pk)
        self.assertNotIn('correct', answer)
        self.assertNotIn('correct_choice_id', answer)
        self.assertNotIn('explanation', answer)
        return services.finish_quiz(self.student, attempt)

    def test_final_locked_until_all_published_lessons_are_completed(self):
        with self.assertRaises(PermissionDenied):
            services.start_quiz(self.student, self.quiz)
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        self.assertEqual(self.finish_final()['score_pct'], 100)

    def test_failed_final_blocks_certificate_and_best_passing_score_releases_it(self):
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        self.assertEqual(self.finish_final(False)['score_pct'], 0)
        with self.assertRaises(ValidationError):
            services.issue_enrollment_certificate(self.enrollment)
        self.finish_final(True)
        self.finish_final(False)
        self.assertIsNotNone(services.issue_enrollment_certificate(self.enrollment))
        self.assertEqual(models.ActivityEvent.objects.filter(kind='final_passed').count(), 1)

    def test_course_without_final_does_not_show_assessment_and_can_issue(self):
        self.quiz.is_active = False; self.quiz.save()
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        self.assertIsNotNone(services.issue_enrollment_certificate(self.enrollment))
        response = self.client.get(reverse('member_course', args=[self.course.slug]))
        self.assertNotContains(response, 'Fazer avaliação final')

    def test_qualified_before_end_can_issue_after_end(self):
        today = timezone.localdate()
        services.create_plan(self.enrollment, starts_on=today-timedelta(days=5), ends_on=today+timedelta(days=2), actor=self.owner)
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        self.finish_final(True)
        services.end_plan_early(self.enrollment, end_date=today+timedelta(days=1), reason='student_request', actor=self.owner)
        future = timezone.now()+timedelta(days=2)
        with patch('django.utils.timezone.now', return_value=future):
            self.assertIsNotNone(services.issue_enrollment_certificate(self.enrollment))

    def test_no_retroactive_qualification_for_incomplete_student(self):
        today = timezone.localdate()
        services.create_plan(self.enrollment, starts_on=today-timedelta(days=5), actor=self.owner)
        services.end_plan_early(self.enrollment, end_date=today, reason='withdrawal', actor=self.owner)
        with self.assertRaises(ValidationError):
            services.issue_enrollment_certificate(self.enrollment)

    def test_final_page_and_editor_exist(self):
        response = self.client.get(f'/dashboard/cursos/{self.course.slug}/avaliacao/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Só após todas as respostas')
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(f'/painel/cursos/{self.course.pk}/avaliacao/').status_code, 200)

    def test_exact_seventy_percent_passes_and_grade_is_server_calculated(self):
        for order in range(2, 11):
            services.save_quiz_question(self.quiz, order=order, text=f'Pergunta {order}', explanation='', choices=['Certa','Errada'], correct_index=0, actor=self.owner)
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        attempt = services.start_quiz(self.student, self.quiz)
        answers = {str(q['id']): q['choices'][0 if index < 7 else 1]['id'] for index,q in enumerate(attempt.question_snapshot)}
        response = self.client.post(reverse('submit_final_quiz', args=[attempt.pk]), {'answers':answers, 'score_pct':100}, content_type='application/json')
        self.assertEqual(response.json()['score_pct'], 70)
        self.assertIsNotNone(services.issue_enrollment_certificate(self.enrollment))

    def test_invalid_full_submission_is_atomic(self):
        services.save_quiz_question(self.quiz, order=2, text='Outra', explanation='', choices=['A','B'], correct_index=0, actor=self.owner)
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        attempt = services.start_quiz(self.student, self.quiz)
        answers = {str(q['id']): q['choices'][0]['id'] for q in attempt.question_snapshot}
        answers[str(attempt.question_snapshot[-1]['id'])] = 99999
        with self.assertRaises(ValidationError):
            services.submit_final_quiz(self.student, attempt, answers)
        attempt.refresh_from_db()
        self.assertEqual(attempt.answers, {})
        self.assertIsNone(attempt.finished_at)

    def test_http_issue_after_end_uses_recorded_qualification(self):
        today = timezone.localdate()
        services.create_plan(self.enrollment, today-timedelta(days=5), actor=self.owner)
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        self.finish_final(True)
        services.end_plan_early(self.enrollment, today+timedelta(days=1), 'student_request', actor=self.owner)
        with patch('django.utils.timezone.now', return_value=timezone.now()+timedelta(days=2)):
            response = self.client.post(reverse('issue_certificate', args=[self.course.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(models.Certificate.objects.filter(enrollment=self.enrollment).exists())

    def test_status_distinguishes_waiting_exam_done_and_ended(self):
        from courses.selectors import progress_info
        today = timezone.localdate()
        services.create_plan(self.enrollment, today, actor=self.owner)
        self.assertEqual(progress_info(self.student, self.course)['status'], 'new')
        self.lesson.module.release_month = 2; self.lesson.module.save()
        self.assertEqual(progress_info(self.student, self.course)['status'], 'waiting_release')
        self.lesson.module.release_month = 1; self.lesson.module.save()
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        self.assertEqual(progress_info(self.student, self.course)['status'], 'exam')
        self.finish_final(True)
        self.assertEqual(progress_info(self.student, self.course)['status'], 'done')
        services.end_plan_early(self.enrollment, today, 'withdrawal', actor=self.owner)
        self.assertEqual(progress_info(self.student, self.course)['status'], 'ended')
