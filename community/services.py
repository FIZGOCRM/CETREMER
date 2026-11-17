from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from courses.models import Enrollment
from .access import is_team, require_topic_access, require_write
from .models import Comment, CommunityPost, Helpful


@transaction.atomic
def create_topic(user, *, title, content, course=None, lesson=None):
    if not is_team(user) and course and not Enrollment.objects.filter(student=user.student_profile,course=course).exists():
        raise PermissionDenied('Matrícula necessária para publicar neste curso.')
    require_write(user)
    if len(title.strip()) < 8 or len(content.strip()) < 15:
        raise ValidationError('Título: pelo menos 8 caracteres. Texto: pelo menos 15 caracteres.')
    if lesson and (not course or lesson.module.course_id != course.pk):
        raise ValidationError('A aula deve pertencer ao curso selecionado.')
    return CommunityPost.objects.create(author=user,course=course,lesson=lesson,title=title.strip(),content=content.strip())


@transaction.atomic
def add_reply(user, post, content, *, display_as='self'):
    require_topic_access(user,post);require_write(user)
    if display_as not in ('self','mentor','team') or (display_as != 'self' and not is_team(user)):
        raise PermissionDenied('Assinatura reservada à equipe.')
    if not content.strip():raise ValidationError('Escreva sua resposta.')
    reply=Comment.objects.create(post=post,author=user,content=content.strip(),display_as=display_as)
    if display_as in ('mentor','team'):
        post.team_status='answered';post.save(update_fields=['team_status'])
    return reply


@transaction.atomic
def mark_solution(user, post, comment=None):
    require_topic_access(user,post)
    if not is_team(user):
        require_write(user)
        if post.author_id != user.pk:raise PermissionDenied
        if not comment or comment.author_id == user.pk:raise ValidationError('Escolha a resposta de outra pessoa.')
    if comment and (comment.post_id != post.pk or comment.is_hidden):raise ValidationError('Resposta indisponível neste tópico.')
    post.solution=comment;post.solution_marked_by=('team' if is_team(user) else 'author') if comment else ''
    post.solved_at=timezone.now() if comment else None
    post.save(update_fields=['solution','solution_marked_by','solved_at'])


@transaction.atomic
def moderate(user, post, action, *, comment=None, note=''):
    if not is_team(user):raise PermissionDenied
    if action in ('hide_comment','show_comment'):
        if not comment or comment.post_id != post.pk:raise ValidationError('Resposta inválida.')
        comment.is_hidden=action=='hide_comment';comment.save(update_fields=['is_hidden'])
        if comment.is_hidden and post.solution_id==comment.pk:mark_solution(user,post,None)
        return
    if action in ('hide','show'):post.is_hidden=action=='hide'
    elif action=='pin':post.is_pinned=not post.is_pinned
    elif action=='forward':
        post.team_status='forwarded';post.team_note=note.strip();post.forwarded_at=timezone.now()
    elif action=='reopen':
        post.team_status='new';post.solution=None;post.solution_marked_by='';post.solved_at=None
    else:raise ValidationError('Ação inválida.')
    post.save()


@transaction.atomic
def toggle_helpful(user, post, comment=None):
    require_topic_access(user,post);require_write(user)
    if comment and (comment.post_id!=post.pk or comment.is_hidden):raise PermissionDenied
    target={'comment':comment} if comment else {'post':post}
    vote,created=Helpful.objects.get_or_create(user=user,**target)
    if not created:vote.delete()
    return created
