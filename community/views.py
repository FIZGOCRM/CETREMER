"""Comunidade do aluno (HANDOFF-v2 7.6): lista, conversa em painel lateral, nova pergunta, respostas e "Sim, resolveu"."""
import re

from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from core.ajax import json_errors, json_ok, wants_json
from core.toasts import toast
from courses.models import Course, Enrollment, Lesson
from users.display import first_name
from .models import Comment, CommunityPost, is_staff_user
from .notifications import notify_staff_answer
from .questions import lesson_questions

SITUATIONS = ('todas', 'sem-resposta', 'respondidas', 'minhas')
PUBLISHED = 'Pergunta publicada. Avisaremos por e-mail quando responderem'


def _my_courses(user):
    """Cursos cuja comunidade a pessoa enxerga: os matriculados (aluno) ou todos (equipe)."""
    if user.role == 'STUDENT':
        return list(Course.objects.filter(enrollments__student=user.student_profile, enrollments__is_active=True)
                    .exclude(status='archived').order_by('title').distinct())
    return list(Course.objects.exclude(status='archived').order_by('title'))


def _visible(user, courses):
    return CommunityPost.objects.filter(is_hidden=False).filter(Q(course__isnull=True) | Q(course__in=courses))


def _lesson_positions(course_ids):
    """{lesson_id: número da aula no curso} das aulas publicadas."""
    positions = {}
    lessons = (Lesson.objects.filter(module__course_id__in=course_ids, status='published')
               .select_related('module').order_by('module__course_id', 'module__order', 'module_id', 'order', 'id'))
    current, counter = None, 0
    for lesson in lessons:
        if lesson.module.course_id != current:
            current, counter = lesson.module.course_id, 0
        counter += 1
        positions[lesson.id] = counter
    return positions


def _decorate(posts, positions):
    for post in posts:
        post.author_name = first_name(post.author)
        post.lesson_position = positions.get(post.lesson_id)
    return posts


def _thread_context(request, post, positions=None):
    positions = positions if positions is not None else _lesson_positions([post.course_id] if post.course_id else [])
    comments = list(post.comments.select_related('author__student_profile').order_by('created_at'))
    for comment in comments:
        comment.is_official = is_staff_user(comment.author)
        comment.author_name = 'Instrutor CETREMER' if comment.is_official else first_name(comment.author)
    post.author_name = first_name(post.author)
    post.lesson_position = positions.get(post.lesson_id)
    return {'post': post, 'is_author': post.author_id == request.user.id,
            'official': [c for c in comments if c.is_official], 'others': [c for c in comments if not c.is_official]}


def _render_thread(request, post):
    return render_to_string('community/_thread_drawer.html', _thread_context(request, post), request)


def _open_post(request, posts_qs, post_id):
    post = posts_qs.select_related('author__student_profile', 'course', 'lesson').filter(pk=post_id).first()
    if post is not None and post.author_id == request.user.id and post.has_unread_answer:
        post.has_unread_answer = False
        post.save(update_fields=['has_unread_answer'])
    return post


@login_required
def community(request):
    user = request.user
    courses = _my_courses(user)
    visible = _visible(user, courses)

    if request.GET.get('duvida', '').isdigit() and request.GET.get('parcial'):
        post = _open_post(request, visible, int(request.GET['duvida']))
        if post is None:
            return HttpResponseForbidden()
        return render(request, 'community/_thread_drawer.html', _thread_context(request, post))

    situation = request.GET.get('situacao') if request.GET.get('situacao') in SITUATIONS else 'todas'
    slugs = {c.slug for c in courses}
    course_filter = request.GET.get('curso') if request.GET.get('curso') in slugs | {'geral'} else ''
    query = request.GET.get('q', '').strip()

    posts_qs = visible.select_related('author__student_profile', 'course', 'lesson').annotate(replies=Count('comments'))
    if situation == 'sem-resposta':
        posts_qs = posts_qs.filter(is_answered_cache=False)
    elif situation == 'respondidas':
        posts_qs = posts_qs.filter(is_answered_cache=True)
    elif situation == 'minhas':
        posts_qs = posts_qs.filter(author=user)
    if course_filter == 'geral':
        posts_qs = posts_qs.filter(course__isnull=True)
    elif course_filter:
        posts_qs = posts_qs.filter(course__slug=course_filter)
    if query:
        posts_qs = posts_qs.filter(Q(title__icontains=query) | Q(content__icontains=query))
    posts = list(posts_qs.order_by('-is_pinned', '-created_at'))
    positions = _lesson_positions([c.id for c in courses])
    _decorate(posts, positions)
    new_id = request.GET.get('nova_id', '')
    for post in posts:
        post.is_new = str(post.id) == new_id

    open_post = None
    thread = None
    if request.GET.get('duvida', '').isdigit():
        open_post = _open_post(request, visible, int(request.GET['duvida']))
        if open_post is not None:
            thread = _thread_context(request, open_post, positions)

    compose_open = request.GET.get('nova') == '1'
    compose_course = next((c for c in courses if c.slug == request.GET.get('curso')), None)
    lesson_param = request.GET.get('aula', '')
    compose_lesson = None
    if lesson_param.isdigit():
        compose_lesson = Lesson.objects.filter(pk=int(lesson_param), status='published', module__course__in=courses).first()
        if compose_lesson and compose_course is None:
            compose_course = compose_lesson.module.course
    lessons_by_course = []
    for course in courses:
        group = list(Lesson.objects.filter(module__course=course, status='published')
                     .order_by('module__order', 'module_id', 'order', 'id'))
        for lesson in group:
            lesson.position = positions.get(lesson.id)
        if group:
            lessons_by_course.append((course, group))
    return render(request, 'community/hub.html', {
        'posts': posts, 'situation': situation, 'course_filter': course_filter, 'q': query, 'my_courses': courses,
        'open_post': open_post, 'thread': thread, 'compose_open': compose_open, 'compose_course': compose_course,
        'compose_lesson': compose_lesson, 'lessons_by_course': lessons_by_course, 'has_filters': bool(
            query or course_filter or situation != 'todas'),
    })


class QuestionForm(forms.Form):
    course = forms.CharField(required=False)
    lesson = forms.CharField(required=False)
    title = forms.CharField(max_length=200, error_messages={'required': 'Informe um título para a pergunta.'})
    content = forms.CharField(error_messages={'required': 'Conte o contexto da sua pergunta.'})

    def __init__(self, *args, user, courses, **kwargs):
        super().__init__(*args, **kwargs)
        self.user, self.courses = user, courses

    def clean_title(self):
        return self.cleaned_data['title'].strip()

    def clean_content(self):
        return self.cleaned_data['content'].strip()

    def clean(self):
        data = super().clean()
        course_id, lesson_id = data.get('course', ''), data.get('lesson', '')
        self.course = None
        if course_id and course_id != 'general':
            self.course = next((c for c in self.courses if str(c.id) == course_id), None)
            if self.course is None:
                self.add_error('course', 'Escolha um curso em que você está matriculado.')
        self.lesson = None
        if lesson_id:
            lesson = Lesson.objects.filter(pk=lesson_id, status='published').first() if lesson_id.isdigit() else None
            if lesson is None or self.course is None or lesson.module.course_id != self.course.id:
                self.add_error('lesson', 'Escolha uma aula do curso selecionado.')
            else:
                self.lesson = lesson
        return data


@login_required
@require_POST
def community_create(request):
    courses = _my_courses(request.user)
    form = QuestionForm(request.POST, user=request.user, courses=courses)
    if not form.is_valid():
        if wants_json(request):
            return json_errors(form)
        toast(request, next(iter(form.errors.values()))[0], level='error')
        return redirect(reverse('community') + '?nova=1')
    post = CommunityPost.objects.create(author=request.user, course=form.course, lesson=form.lesson,
                                        title=form.cleaned_data['title'], content=form.cleaned_data['content'])
    target = reverse('community') + f'?nova_id={post.id}'
    undo = reverse('community_delete_own', args=[post.id])
    if wants_json(request):
        return json_ok(toast=PUBLISHED, undo_url=undo, redirect=target)
    toast(request, PUBLISHED, undo_url=undo)
    return redirect(target)


def _post_for_participant(request, post_id):
    """Dúvida que a pessoa enxerga (curso dela ou geral); senão 404."""
    post = get_object_or_404(CommunityPost.objects.select_related('author__student_profile', 'course', 'lesson'), pk=post_id, is_hidden=False)
    if post.course_id and post.course not in _my_courses(request.user):
        return None
    return post


@login_required
@require_POST
def community_reply(request, post_id):
    post = _post_for_participant(request, post_id)
    if post is None:
        return HttpResponseForbidden('Matrícula necessária para comentar neste curso.')
    content = request.POST.get('content', '').strip()
    if not content:
        if wants_json(request):
            return JsonResponse({'ok': False, 'errors': {'content': ['Escreva uma resposta.']},
                                 'error': 'Corrija 1 campo para salvar.'}, status=400)
        toast(request, 'Escreva uma resposta.', level='error')
        return redirect(reverse('community') + f'?duvida={post.id}')
    comment = Comment.objects.create(post=post, author=request.user, content=content)
    notify_staff_answer(comment, request)
    if wants_json(request):
        post.refresh_from_db()
        return json_ok(toast='Resposta publicada', replace={'#thread-content': _render_thread(request, post)})
    toast(request, 'Resposta publicada')
    return redirect(reverse('community') + f'?duvida={post.id}')


@login_required
@require_POST
def community_resolve(request, post_id):
    """Só o autor. Alterna "Sim, resolveu". `?desfazer=1` (o Desfazer do aviso) recarrega a página."""
    post = get_object_or_404(CommunityPost, pk=post_id, author=request.user)
    post.is_resolved = not post.is_resolved
    post.save(update_fields=['is_resolved'])
    if request.GET.get('desfazer'):
        return json_ok(reload=True) if wants_json(request) else redirect(reverse('community') + f'?duvida={post.id}')
    undo = reverse('community_resolve', args=[post.id]) + '?desfazer=1'
    message = 'Obrigado! A dúvida foi marcada como resolvida' if post.is_resolved else ''
    if wants_json(request):
        return json_ok(toast=message, undo_url=undo if post.is_resolved else None,
                       replace={'#thread-content': _render_thread(request, post)})
    if message:
        toast(request, message, undo_url=undo)
    return redirect(reverse('community') + f'?duvida={post.id}')


@login_required
@require_POST
def community_delete_own(request, post_id):
    """Só o autor e só enquanto ninguém respondeu (é o Desfazer de "Pergunta publicada")."""
    post = get_object_or_404(CommunityPost, pk=post_id, author=request.user)
    if post.comments.exists():
        return HttpResponseForbidden('Esta pergunta já tem respostas.')
    post.delete()
    if wants_json(request):
        return json_ok(toast='Pergunta apagada', reload=True)
    toast(request, 'Pergunta apagada')
    return redirect('community')


@login_required
@require_GET
def community_suggest(request):
    """Até 3 dúvidas parecidas com o título digitado (palavras de 4 letras ou mais)."""
    words = [w for w in re.findall(r'\w+', request.GET.get('q', '').lower()) if len(w) >= 4]
    if not words:
        return render(request, 'community/_suggestions.html', {'posts': []})
    match = Q()
    for word in words:
        match |= Q(title__icontains=word)
    posts = list(_visible(request.user, _my_courses(request.user)).filter(match).order_by('-created_at')[:3])
    return render(request, 'community/_suggestions.html', {'posts': posts})


@login_required
@require_POST
def create_post(request, course_slug):
    """Creates a new top-level community post inside a course context."""
    course = get_object_or_404(Course, slug=course_slug)
    if request.user.role == 'STUDENT' and not Enrollment.objects.filter(
        student=request.user.student_profile, course=course
    ).exists():
        return HttpResponseForbidden('Matrícula necessária para publicar neste curso.')
    title = request.POST.get('title')
    content = request.POST.get('content')
    lesson_id = request.POST.get('lesson_id')
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course) if lesson_id else None
    if lesson and not title and content:
        title = content[:100]

    if lesson and not (content or '').strip():
        if wants_json(request):
            return JsonResponse({'ok': False, 'errors': {'content': ['Escreva sua dúvida.']},
                                 'error': 'Corrija 1 campo para salvar.'}, status=400)
        toast(request, 'Escreva sua dúvida.', level='error')
        return redirect(reverse('lesson_detail', args=[course.slug, lesson.id]) + '?aba=duvidas')

    if title and content:
        CommunityPost.objects.create(
            course=course,
            lesson=lesson,
            author=request.user,
            title=title,
            content=content
        )
        if lesson:
            message = 'Dúvida publicada. Avisaremos por e-mail quando responderem'
            if wants_json(request):
                html = render_to_string('courses/_lesson_questions.html', {'posts': lesson_questions(lesson), 'course': course}, request)
                return json_ok(toast=message, replace={'#lesson-questions': html})
            toast(request, message)
            return redirect(reverse('lesson_detail', args=[course.slug, lesson.id]) + '?aba=duvidas')

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    first_lesson = Lesson.objects.filter(status='published', module__course=course).order_by('module__order', 'order', 'id').first()
    if first_lesson:
        return redirect('lesson_detail', course_slug=course.slug, lesson_id=first_lesson.id)
    return redirect('course_preview', course_slug=course.slug)
