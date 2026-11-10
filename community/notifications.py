from users.notify import notify

from .models import is_staff_user


def notify_staff_answer(comment, request=None):
    """Resposta da equipe a uma dúvida avisa o autor (HANDOFF-v2 6.1). Não avisa quem responde a si mesmo."""
    post = comment.post
    if not is_staff_user(comment.author) or post.author_id == comment.author_id:
        return None
    meta = f'{post.course.title} · {post.title}' if post.course_id else post.title
    return notify(post.author, 'answer', 'O instrutor respondeu sua dúvida', meta,
                  f'/community/?duvida={post.id}', request=request)
