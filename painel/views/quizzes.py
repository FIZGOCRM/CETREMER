from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect
from core.decorators import painel_required
from courses.models import Course, Lesson, Quiz, QuizQuestion
from courses.services import create_lesson_quiz, create_final_quiz, save_quiz_question, delete_quiz_content, set_quiz_active
from painel.forms import QuizQuestionForm
from .common import page


@painel_required
def lesson_quiz(request, lesson_id):
    if request.user.role not in ('ADMIN', 'CREATOR'):
        raise PermissionDenied
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), pk=lesson_id)
    return _edit_quiz(request, lesson=lesson, course=lesson.module.course)


@painel_required
def final_quiz(request, course_id):
    if request.user.role not in ('ADMIN', 'CREATOR'):
        raise PermissionDenied
    return _edit_quiz(request, course=get_object_or_404(Course, pk=course_id))


def _edit_quiz(request, *, course, lesson=None):
    quiz = getattr(lesson, 'quiz', None) if lesson else Quiz.objects.filter(course=course, kind='final').first()
    context = {'lesson':lesson, 'course':course, 'is_final':lesson is None}
    question = None
    raw_id = request.POST.get('question_id') if request.method == 'POST' else request.GET.get('pergunta')
    if raw_id:
        if not raw_id.isdigit() or len(raw_id) > 18:
            raise PermissionDenied('Identificador inválido.')
        question = get_object_or_404(QuizQuestion, pk=int(raw_id), quiz=quiz)
    initial = {'order': (quiz.questions.aggregate(value=Max('order'))['value'] or 0)+1} if quiz else {'order': 1}
    if question:
        initial.update(order=question.order, text=question.text, explanation=question.explanation)
        for key, choice in zip('abcd', question.choices.filter(is_active=True)):
            initial['choice_'+key] = choice.text
            if choice.is_correct:
                initial['correct'] = key
    form = QuizQuestionForm(request.POST if request.method == 'POST' and request.POST.get('action') == 'save' else None, initial=initial)
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'create':
                quiz = create_lesson_quiz(lesson, actor=request.user) if lesson else create_final_quiz(course, actor=request.user)
            elif not quiz:
                raise ValidationError('Crie o quiz antes de cadastrar perguntas.')
            elif action == 'toggle':
                set_quiz_active(question or quiz, request.POST.get('is_active') == '1', actor=request.user)
            elif action == 'delete':
                delete_quiz_content(question or quiz, actor=request.user)
            elif action == 'save' and form.is_valid():
                data = form.cleaned_data
                save_quiz_question(quiz, question=question, actor=request.user, **{key: data[key] for key in ('order','text','explanation','choices','correct_index')})
            elif action == 'save':
                return page(request, 'lesson_quiz', **context, quiz=quiz, question=question, form=form, questions=quiz.questions.all())
            else:
                raise ValidationError('Ação inválida.')
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        else:
            messages.success(request, 'Quiz atualizado. Tentativas anteriores preservadas.')
        return redirect('painel:lesson_quiz', lesson_id=lesson.pk) if lesson else redirect('painel:final_quiz', course_id=course.pk)
    return page(request, 'lesson_quiz', **context, quiz=quiz, question=question, form=form, questions=quiz.questions.all() if quiz else [])
