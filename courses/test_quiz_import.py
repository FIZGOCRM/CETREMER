from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command, CommandError
from django.test import TestCase

from courses.models import Course, Enrollment, Lesson, Module, Quiz, QuizQuestion
from courses.services import save_quiz_question, set_lesson_progress, start_quiz
from users.models import User


class QuizImportTests(TestCase):
    header = 'curso,tipo,aula,ordem,pergunta,alternativa_a,alternativa_b,alternativa_c,alternativa_d,correta,comentario\n'

    def setUp(self):
        self.owner = User.objects.create_user(username='csv-owner', role='CREATOR')
        self.course = Course.objects.create(is_published=True, title='Curso', slug='csv-course', creator=self.owner.creator_profile)
        self.module = Module.objects.create(course=self.course, title='M')
        self.lesson = Lesson.objects.create(module=self.module, title='Aula única')
        self.row = 'csv-course,aula,Aula única,1,Pergunta?,A,B,,,A,Explicação\n'

    def run_csv(self, rows, **options):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'perguntas.csv'
            path.write_text(self.header+rows, encoding='utf-8')
            output = StringIO()
            call_command('import_quizzes', str(path), stdout=output, **options)
            return output.getvalue()

    def test_dry_run_has_summary_without_writes(self):
        result = self.run_csv(self.row, dry_run=True)
        self.assertIn('Aula única', result)
        self.assertFalse(Quiz.objects.exists())
        self.assertFalse(QuizQuestion.objects.exists())

    def test_valid_file_imports_lesson_and_final_in_one_transaction(self):
        self.run_csv(self.row+'csv-course,final,,1,Final?,Certa,Errada,,,A,Comentário\n')
        self.assertEqual(Quiz.objects.count(), 2)
        self.assertEqual(QuizQuestion.objects.count(), 2)
        self.assertFalse(Quiz.objects.filter(is_demo=True).exists())

    def test_one_bad_row_refuses_entire_file(self):
        with self.assertRaisesRegex(CommandError, 'Linha'):
            self.run_csv(self.row+'inexistente,final,,1,Inválida,A,B,,,A,\n')
        self.assertFalse(Quiz.objects.exists())

    def test_duplicate_order_invalid_choice_and_ambiguous_lesson_are_refused(self):
        for rows in (self.row+self.row, self.row.replace(',A,Explicação', ',D,Explicação'), self.row.replace('A,B,,,', 'A,,,, ')):
            with self.assertRaisesRegex(CommandError, 'Linha'):
                self.run_csv(rows)
        Lesson.objects.create(module=self.module, title='Aula única')
        with self.assertRaisesRegex(CommandError, 'Linha'):
            self.run_csv(self.row)
        self.assertFalse(Quiz.objects.exists())

    def test_real_attempt_blocks_overwrite_even_in_dry_run(self):
        quiz = Quiz.objects.create(course=self.course, lesson=self.lesson, kind='lesson', is_demo=True)
        save_quiz_question(quiz, order=1, text='Original', explanation='', choices=['A','B'], correct_index=0, actor=self.owner)
        real = User.objects.create_user(username='real-student', email='real@example.com')
        Enrollment.objects.create(student=real.student_profile, course=self.course)
        set_lesson_progress(real.student_profile, self.lesson, completed=True)
        start_quiz(real.student_profile, quiz)
        with self.assertRaisesRegex(CommandError, 'tentativas reais'):
            self.run_csv(self.row, dry_run=True)
        self.assertEqual(quiz.questions.get().text, 'Original')

    def test_demo_questions_are_replaced_and_unlisted_lesson_is_deactivated(self):
        demo = Quiz.objects.create(course=self.course, lesson=self.lesson, kind='lesson', is_demo=True)
        save_quiz_question(demo, order=1, text='Ilustrativa', explanation='', choices=['A','B'], correct_index=0, actor=self.owner)
        other = Lesson.objects.create(module=self.module, title='Outra')
        unlisted = Quiz.objects.create(course=self.course, lesson=other, kind='lesson', is_demo=True)
        self.run_csv(self.row)
        demo.refresh_from_db(); unlisted.refresh_from_db()
        self.assertFalse(demo.is_demo)
        self.assertEqual(list(demo.questions.filter(is_active=True).values_list('text',flat=True)), ['Pergunta?'])
        self.assertFalse(unlisted.is_active)

    def test_versioned_example_fixture_is_valid_without_writes(self):
        fixture = Path(__file__).parent/'tests'/'fixtures'/'quizzes-exemplo.csv'
        output = StringIO()
        call_command('import_quizzes', str(fixture), dry_run=True, stdout=output)
        self.assertIn('Prévia válida', output.getvalue())
        self.assertFalse(Quiz.objects.exists())

    def test_dry_run_lists_unlisted_quiz_without_deactivating_it(self):
        other = Lesson.objects.create(module=self.module, title='Outra aula')
        quiz = Quiz.objects.create(course=self.course, lesson=other, kind='lesson')
        result = self.run_csv(self.row, dry_run=True)
        quiz.refresh_from_db()
        self.assertTrue(quiz.is_active)
        self.assertIn('será desativado', result)

    def test_write_failure_rolls_back_every_quiz_and_question(self):
        from unittest.mock import patch
        from django.core.exceptions import ValidationError
        from courses.services import save_quiz_question as real_save
        calls = []
        def fail_second(*args, **kwargs):
            calls.append(1)
            if len(calls) == 2:
                raise ValidationError('Falha de gravação controlada')
            return real_save(*args, **kwargs)
        with patch('courses.services.save_quiz_question', side_effect=fail_second):
            with self.assertRaisesRegex(CommandError, 'Falha de gravação'):
                self.run_csv(self.row+'csv-course,final,,1,Final,A,B,,,A,\n')
        self.assertFalse(Quiz.objects.exists())
        self.assertFalse(QuizQuestion.objects.exists())
