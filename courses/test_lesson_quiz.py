from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from courses import models, services
from courses.models import Course, Enrollment, Lesson, Module, Progress
from users.models import User


class LessonQuizTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='quiz-owner', role='CREATOR')
        self.user = User.objects.create_user(username='quiz-user')
        self.student = self.user.student_profile
        self.course = Course.objects.create(is_published=True, title='Curso', slug='quiz-course', creator=self.owner.creator_profile)
        self.lesson = Lesson.objects.create(module=Module.objects.create(course=self.course, title='M'), title='A')
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        quiz_model = getattr(models, 'Quiz', None)
        self.assertIsNotNone(quiz_model, 'Modelo Quiz ainda não implementado')
        self.quiz = quiz_model.objects.create(course=self.course, lesson=self.lesson, kind='lesson')
        self.question = services.save_quiz_question(self.quiz, order=1, text='Pergunta original', explanation='Comentário original', choices=['A original', 'B original'], correct_index=0, actor=self.owner)
        self.client.force_login(self.user)

    def start(self):
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        return services.start_quiz(self.student, self.quiz)

    def test_start_requires_completed_lesson(self):
        with self.assertRaises(PermissionDenied):
            services.start_quiz(self.student, self.quiz)
        self.assertFalse(models.QuizAttempt.objects.exists())

    def test_start_payload_never_contains_answer_key_or_explanation(self):
        self.start()
        response = self.client.post(reverse('quiz_start', args=[self.quiz.pk]))
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('correct_choice_id', response.content.decode())
        self.assertNotIn('is_correct', response.content.decode())
        self.assertNotIn('Comentário original', response.content.decode())
        self.assertEqual(response.json()['questions'][0]['text'], 'Pergunta original')

    def test_answer_is_corrected_once_then_finish_is_idempotent(self):
        attempt = self.start()
        choice = self.question.choices.get(is_correct=True, is_active=True)
        result = services.answer_quiz(self.student, attempt, question_id=self.question.pk, choice_id=choice.pk)
        self.assertTrue(result['correct']); self.assertEqual(result['explanation'], 'Comentário original')
        with self.assertRaises(ValidationError):
            services.answer_quiz(self.student, attempt, question_id=self.question.pk, choice_id=choice.pk)
        first = services.finish_quiz(self.student, attempt)
        self.assertEqual(first['score_pct'], 100)
        self.assertEqual(services.finish_quiz(self.student, attempt)['score_pct'], 100)
        self.assertEqual(models.ActivityEvent.objects.filter(kind='quiz_finished', student=self.student).count(), 1)

    def test_finished_attempt_keeps_grade_and_snapshot_when_question_is_edited(self):
        attempt = self.start()
        choice = self.question.choices.get(is_correct=True, is_active=True)
        services.save_quiz_question(self.quiz, question=self.question, order=1, text='Pergunta nova', explanation='Comentário novo', choices=['A nova', 'B nova'], correct_index=1, actor=self.owner)
        result = services.answer_quiz(self.student, attempt, question_id=self.question.pk, choice_id=choice.pk)
        self.assertTrue(result['correct']); self.assertEqual(result['explanation'], 'Comentário original')
        self.assertEqual(services.finish_quiz(self.student, attempt)['score_pct'], 100)

    def test_finish_requires_all_answers_and_rejects_foreign_choice(self):
        attempt = self.start()
        with self.assertRaises(ValidationError):
            services.finish_quiz(self.student, attempt)
        with self.assertRaises(ValidationError):
            services.answer_quiz(self.student, attempt, question_id=self.question.pk, choice_id=999999)
        attempt.refresh_from_db(); self.assertEqual(attempt.answers, {})

    def test_question_and_quiz_with_attempts_can_only_be_deactivated(self):
        self.start()
        with self.assertRaisesMessage(ValidationError, 'desativar'):
            services.delete_quiz_content(self.question, actor=self.owner)
        with self.assertRaisesMessage(ValidationError, 'desativar'):
            services.delete_quiz_content(self.quiz, actor=self.owner)
        self.assertTrue(models.QuizQuestion.objects.filter(pk=self.question.pk).exists())

    def test_choices_require_two_to_five_options_and_one_correct(self):
        for choices, correct in [(['Só uma'], 0), (['a','b'], 2), (list('abcdef'), 0)]:
            with self.assertRaises(ValidationError):
                services.save_quiz_question(self.quiz, order=2, text='Inválida', explanation='', choices=choices, correct_index=correct, actor=self.owner)

    def test_feedback_uses_chosen_and_correct_explanations_from_snapshot(self):
        services.save_quiz_question(self.quiz, question=self.question, order=1, text='ABCDE',
            explanation='Comentário geral', choices=list('ABCDE'), correct_index=4, actor=self.owner,
            choice_explanations=[f'Justificativa {letter}' for letter in 'ABCDE'])
        services.set_lesson_progress(self.student, self.lesson, completed=True)
        response = self.client.post(reverse('quiz_start', args=[self.quiz.pk]))
        self.assertNotContains(response, 'Justificativa', status_code=201)
        public = response.json()
        question = public['questions'][0]
        self.assertEqual(len(question['choices']), 5)
        services.save_quiz_question(self.quiz, question=self.question, order=1, text='Outra',
            explanation='', choices=['A2','B2'], correct_index=0, actor=self.owner,
            choice_explanations=['Outra A','Outra B'])
        result = self.client.post(reverse('quiz_answer', args=[public['id']]), {
            'question_id': question['id'], 'choice_id': question['choices'][1]['id'],
        }, content_type='application/json').json()
        self.assertFalse(result['correct'])
        self.assertEqual(result['correct_choice_id'], question['choices'][4]['id'])
        self.assertEqual(result['chosen_explanation'], 'Justificativa B')
        self.assertEqual(result['correct_explanation'], 'Justificativa E')
        review = self.client.post(reverse('quiz_finish', args=[public['id']])).json()['questions'][0]
        self.assertEqual(review['chosen_explanation'], result['chosen_explanation'])
        self.assertEqual(review['correct_explanation'], result['correct_explanation'])

    def test_legacy_snapshot_without_choice_explanations_uses_question_comment(self):
        attempt = self.start()
        question = attempt.question_snapshot[0]
        for choice in question['choices']:
            choice.pop('explanation')
        attempt.save(update_fields=['question_snapshot'])
        response = services.answer_quiz(self.student, attempt, question_id=question['id'],
                                        choice_id=question['choices'][1]['id'])
        self.assertEqual(response['chosen_explanation'], 'Comentário original')
        result = services.finish_quiz(self.student, attempt)
        self.assertEqual(result['questions'][0]['correct_explanation'], 'Comentário original')

    def test_another_student_cannot_answer_my_attempt(self):
        attempt = self.start()
        other = User.objects.create_user(username='quiz-outsider')
        Enrollment.objects.create(student=other.student_profile, course=self.course)
        self.client.force_login(other)
        response = self.client.post(reverse('quiz_answer', args=[attempt.pk]), {'question_id': self.question.pk, 'choice_id': self.question.choices.first().pk}, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_best_score_is_kept_and_quiz_does_not_block_certificate(self):
        attempt = self.start()
        correct = self.question.choices.get(is_active=True, is_correct=True)
        services.answer_quiz(self.student, attempt, question_id=self.question.pk, choice_id=correct.pk)
        services.finish_quiz(self.student, attempt)
        other = services.start_quiz(self.student, self.quiz)
        wrong = self.question.choices.get(is_active=True, is_correct=False)
        services.answer_quiz(self.student, other, question_id=self.question.pk, choice_id=wrong.pk)
        result = services.finish_quiz(self.student, other)
        self.assertEqual((result['score_pct'], result['best_score']), (0, 100))
        self.student.full_name = 'Aluno de Demonstração'; self.student.cpf = '52998224725'; self.student.save()
        self.assertIsNotNone(services.issue_enrollment_certificate(self.enrollment))

    def test_start_requires_csrf_and_expired_plan_cannot_answer(self):
        from datetime import timedelta
        from django.test import Client
        from django.utils import timezone
        attempt = self.start()
        strict = Client(enforce_csrf_checks=True); strict.force_login(self.user)
        self.assertEqual(strict.post(reverse('quiz_start', args=[self.quiz.pk])).status_code, 403)
        services.create_plan(self.enrollment, timezone.localdate()-timedelta(days=1), actor=self.owner)
        services.end_plan_early(self.enrollment, timezone.localdate(), 'withdrawal', actor=self.owner)
        with self.assertRaises(PermissionDenied):
            services.answer_quiz(self.student, attempt, question_id=self.question.pk, choice_id=self.question.choices.first().pk)

    def test_result_endpoint_is_closed_until_attempt_is_finished(self):
        attempt = self.start()
        response = self.client.get(reverse('quiz_result', args=[attempt.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, 'Comentário original', status_code=403)

    def test_panel_can_edit_questions_and_student_html_has_no_answer_key(self):
        self.client.force_login(self.owner)
        url = reverse('painel:lesson_quiz', args=[self.lesson.pk])
        data = {'action':'save', 'order':2, 'text':'Segunda', 'explanation':'Explicação privada',
            'choice_a':'Opção 1', 'choice_b':'Opção 2', 'correct':'b'}
        response = self.client.post(url, data)
        self.assertIn('explanation_a', response.context['form'].errors)
        self.assertEqual(self.quiz.questions.count(), 1)
        response = self.client.post(url, {**data, 'explanation_a':'Motivo A', 'explanation_b':'Motivo B'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.quiz.questions.count(), 2)
        self.client.force_login(self.user)
        response = self.client.get(reverse('lesson_detail', args=[self.course.slug, self.lesson.pk]))
        self.assertContains(response, 'Esta aula tem um quiz de 2 perguntas')
        self.assertNotContains(response, 'Explicação privada')
        self.assertEqual(self.client.get(url).status_code, 403)
