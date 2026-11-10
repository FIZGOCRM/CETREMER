"""Comunidade do painel (HANDOFF-v2 8.10): mestre e detalhe, responder como CETREMER, fixar, ocultar e aviso de nova dúvida."""
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from community.models import Comment, CommunityPost, is_staff_user
from community.notifications import notify_staff_answer
from community.views import _lesson_positions
from core.ajax import json_error, json_ok, wants_json
from core.decorators import painel_required
from core.toasts import toast
from users.display import full_name
from users.models import CreatorProfile

TABS = ('sem-resposta', 'respondidas', 'ocultas')
MAX_REPLY = 5000


def pending_count():
    return CommunityPost.objects.filter(is_hidden=False, is_answered_cache=False).count()


def _staff_profile(user):
    profile, _ = CreatorProfile.objects.get_or_create(user=user)
    return profile


def _base():
    return CommunityPost.objects.select_related('author__student_profile', 'course', 'lesson').prefetch_related('comments__author')


def _list_qs(tab, q):
    qs = _base()
    if tab == 'ocultas':
        qs = qs.filter(is_hidden=True)
    elif tab == 'respondidas':
        qs = qs.filter(is_hidden=False, is_answered_cache=True)
    else:
        qs = qs.filter(is_hidden=False, is_answered_cache=False)
    if q:
        qs = qs.filter(Q(author__email__icontains=q) | Q(author__student_profile__full_name__icontains=q) | Q(course__title__icontains=q)
                       | Q(course__short_name__icontains=q) | Q(title__icontains=q) | Q(content__icontains=q))
    return qs.order_by('-is_pinned', 'created_at' if tab == 'sem-resposta' else '-created_at')


def _decorate(post, positions):
    post.author_name = full_name(post.author)
    post.lesson_position = positions.get(post.lesson_id)
    waited = timezone.now() - post.created_at
    post.waiting_long = waited.total_seconds() > 86400
    return post


def next_unanswered(exclude_id=None):
    qs = CommunityPost.objects.filter(is_hidden=False, is_answered_cache=False).order_by('-is_pinned', 'created_at')
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.first()


def community_url(tab='sem-resposta', post_id=None):
    url = reverse('painel:community') + f'?aba={tab}'
    return url + (f'&duvida={post_id}' if post_id else '')


@painel_required
def community(request):
    tab = request.GET.get('aba', 'sem-resposta')
    tab = tab if tab in TABS else 'sem-resposta'
    q = request.GET.get('q', '').strip()
    posts = list(_list_qs(tab, q)[:100])
    course_ids = {p.course_id for p in posts if p.course_id}
    selected = None
    if request.GET.get('duvida', '').isdigit():
        selected = _base().filter(pk=request.GET['duvida']).first()
        if selected is not None:
            course_ids.add(selected.course_id) if selected.course_id else None
    elif posts:
        selected = posts[0]
    positions = _lesson_positions(list(course_ids))
    posts = [_decorate(p, positions) for p in posts]
    official, others = [], []
    if selected is not None:
        _decorate(selected, positions)
        for comment in selected.comments.all():
            comment.author_name = full_name(comment.author)
            comment.is_team = is_staff_user(comment.author)
            (official if comment.is_team else others).append(comment)
    profile = _staff_profile(request.user)
    return render(request, 'painel/community.html', {
        'tab': tab, 'q': q, 'posts': posts, 'selected': selected, 'official': official, 'others': others,
        'pending': pending_count(), 'notify_new_questions': profile.notify_new_questions,
    })


def _fail(request, message, back):
    if wants_json(request):
        return json_error(message)
    toast(request, message, level='error')
    return redirect(back)


def _done(request, url, **extra):
    return json_ok(redirect=url, **extra) if wants_json(request) else redirect(url)


@painel_required
@require_POST
def community_action(request, post_id):
    post = get_object_or_404(CommunityPost, pk=post_id)
    action = request.POST.get('action') or request.GET.get('action')
    tab = request.POST.get('aba') or request.GET.get('aba') or 'sem-resposta'
    tab = tab if tab in TABS else 'sem-resposta'
    here = community_url(tab, post.id)

    if action == 'reply':
        content = request.POST.get('content', '').strip()
        if not content:
            return _fail(request, 'Escreva a resposta antes de publicar.', here)
        if len(content) > MAX_REPLY:
            return _fail(request, 'A resposta passou de 5.000 caracteres.', here)
        comment = Comment.objects.create(post=post, author=request.user, content=content)
        notify_staff_answer(comment, request)
        toast(request, 'Resposta publicada')
        if request.POST.get('next_unanswered'):
            following = next_unanswered(post.id)
            url = community_url('sem-resposta', following.id) if following else community_url('sem-resposta')
        else:
            url = community_url('respondidas' if tab == 'sem-resposta' else tab, post.id)
        return _done(request, url, counts={'[data-pending-count]': str(pending_count())})

    if action == 'pin':
        post.is_pinned = not post.is_pinned
        post.save(update_fields=['is_pinned'])
        toast(request, 'Dúvida fixada no topo' if post.is_pinned else 'Dúvida desafixada')
        return _done(request, here)

    if action == 'hide':
        post.is_hidden = True
        post.save(update_fields=['is_hidden'])
        undo = f"{reverse('painel:community_action', args=[post.id])}?action=unhide&aba={tab}"
        toast(request, 'Dúvida ocultada', undo_url=undo)
        return _done(request, community_url(tab))

    if action == 'unhide':
        post.is_hidden = False
        post.save(update_fields=['is_hidden'])
        toast(request, 'Dúvida visível de novo')
        return _done(request, community_url('respondidas' if post.is_answered_cache else 'sem-resposta', post.id))

    return _fail(request, 'Ação inválida.', here)


@painel_required
@require_POST
def community_pref(request):
    """Interruptor "Me avisar por e-mail a cada nova dúvida": salva na hora."""
    profile = _staff_profile(request.user)
    profile.notify_new_questions = request.POST.get('notify_new_questions') == '1'
    profile.save(update_fields=['notify_new_questions'])
    if wants_json(request):
        return json_ok(toast='Preferência salva')
    toast(request, 'Preferência salva')
    return redirect(reverse('painel:community'))
