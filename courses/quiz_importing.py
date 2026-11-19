"""Leitura e prévia do CSV de perguntas; nenhuma gravação."""
import csv
import io
from dataclasses import dataclass

from .models import Course, Lesson, Quiz

LEGACY_HEADERS = ['curso', 'tipo', 'aula', 'ordem', 'pergunta', 'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'correta', 'comentario']
HEADERS = LEGACY_HEADERS + ['alternativa_e'] + ['justificativa_'+key for key in 'abcde']


@dataclass(frozen=True)
class QuizImportRow:
    line: int
    course: Course
    lesson: object
    kind: str
    order: int
    text: str
    choices: tuple
    correct_index: int
    explanation: str
    choice_explanations: tuple | None

    @property
    def key(self):
        return self.course.pk, self.kind, self.lesson.pk if self.lesson else None


def parse_quiz_csv(path):
    text = path.read_text(encoding='utf-8-sig')
    if not text.strip():
        raise ValueError('Arquivo vazio.')
    reader = csv.DictReader(io.StringIO(text), delimiter=';' if ';' in text.splitlines()[0] and ',' not in text.splitlines()[0] else ',')
    headers = sorted(reader.fieldnames or [])
    legacy = headers == sorted(LEGACY_HEADERS)
    if not legacy and headers != sorted(HEADERS):
        raise ValueError('Use o cabeçalho antigo ou o novo cabeçalho: '+','.join(HEADERS))
    rows, errors, seen = [], [], set()
    courses, lessons = {}, {}
    for line, source in enumerate(reader, 2):
        try:
            if None in source or any(value is None for value in source.values()):
                raise ValueError('Quantidade de colunas inválida.')
            data = {key:value.strip() for key,value in source.items()}
            slug = data['curso']
            if slug not in courses:
                courses[slug] = Course.objects.select_related('creator__user').filter(slug=slug).first()
            course = courses[slug]
            if not course:
                raise ValueError('Curso não encontrado pelo slug.')
            if data['tipo'] not in ('aula', 'final'):
                raise ValueError('Tipo deve ser aula ou final.')
            kind = 'lesson' if data['tipo'] == 'aula' else 'final'
            lesson = None
            if kind == 'lesson':
                key = course.pk, data['aula']
                if key not in lessons:
                    lessons[key] = list(Lesson.objects.filter(module__course=course, title=data['aula']))
                matches = lessons[key]
                if len(matches) != 1:
                    raise ValueError('Aula não encontrada de forma única: confira o título exato dentro do curso.')
                lesson = matches[0]
            elif data['aula']:
                raise ValueError('A coluna aula deve ficar vazia quando tipo = final.')
            if not data['ordem'].isascii() or not data['ordem'].isdigit() or not 1 <= int(data['ordem']) <= 2147483647:
                raise ValueError('Ordem deve ser um inteiro positivo válido.')
            order = int(data['ordem'])
            if not data['pergunta']:
                raise ValueError('Preencha o enunciado da pergunta.')
            keys = [key for key in 'abcde' if data.get('alternativa_'+key)]
            if len(keys) < 2:
                raise ValueError('Preencha pelo menos duas alternativas.')
            correct = data['correta'].lower()
            if correct not in keys:
                raise ValueError('A correta deve apontar para uma alternativa preenchida.')
            explanations = None
            if not legacy:
                for key in 'abcde':
                    if bool(data['justificativa_'+key]) != (key in keys):
                        raise ValueError(f'A alternativa {key.upper()} e sua justificativa devem ser preenchidas juntas.')
                explanations = tuple(data['justificativa_'+key] for key in keys)
            row = QuizImportRow(line, course, lesson, kind, order, data['pergunta'],
                                tuple(data['alternativa_'+key] for key in keys), keys.index(correct),
                                data['comentario'], explanations)
            if (row.key, order) in seen:
                raise ValueError('Ordem repetida no mesmo quiz.')
            seen.add((row.key, order)); rows.append(row)
        except ValueError as exc:
            errors.append(f'Linha {line}: {exc}')
    if not rows and not errors:
        errors.append('Arquivo sem perguntas.')
    return rows, errors


def quiz_import_targets(rows):
    keys = {row.key for row in rows}
    course_ids = {row.course.pk for row in rows}
    listed_lessons = {row.lesson.pk for row in rows if row.lesson}
    current = list(Quiz.objects.filter(course_id__in=course_ids).select_related('lesson', 'course'))
    touched = [quiz for quiz in current if (quiz.course_id, quiz.kind, quiz.lesson_id) in keys or quiz.kind == 'lesson' and quiz.is_active and quiz.lesson_id not in listed_lessons]
    errors = []
    for quiz in touched:
        real_attempts = quiz.attempts.exclude(student__user__username='gomut-demo-student', student__user__email='aluno@gomut.example')
        if real_attempts.exists():
            errors.append(f'{quiz.course.slug} / {quiz.lesson.title if quiz.lesson else "avaliação final"}: tem tentativas reais; não será sobrescrito nem desativado.')
    unlisted = [quiz for quiz in touched if quiz.kind == 'lesson' and quiz.lesson_id not in listed_lessons]
    return touched, unlisted, errors
