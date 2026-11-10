from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from courses.models import Course

class CommunityPost(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='community_posts', null=True, blank=True)
    lesson = models.ForeignKey('courses.Lesson', null=True, blank=True, on_delete=models.SET_NULL)
    is_hidden = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    has_unread_answer = models.BooleanField(default=False)
    is_answered_cache = models.BooleanField(default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.author.username}"

    @property
    def is_answered(self):
        return self.comments.filter(
            models.Q(author__is_staff=True) |
            models.Q(author__role__in=('ADMIN', 'CREATOR'))
        ).exists()

class Comment(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"


def is_staff_user(user):
    return bool(user.is_staff or getattr(user, 'role', '') in ('ADMIN', 'CREATOR'))


@receiver(post_save, sender=Comment)
def mark_answered_by_staff(sender, instance, created, **kwargs):
    """Comentário de equipe marca a dúvida como respondida e avisa o autor (HANDOFF-v2 6.1)."""
    if kwargs.get('raw') or not created or not is_staff_user(instance.author):
        return
    post = instance.post
    fields = ['is_answered_cache']
    post.is_answered_cache = True
    if post.author_id != instance.author_id:
        post.has_unread_answer = True
        fields.append('has_unread_answer')
    post.save(update_fields=fields)


@receiver(post_save, sender=CommunityPost)
def email_staff_about_new_question(sender, instance, created, **kwargs):
    """Equipe que ligou "Me avisar por e-mail a cada nova dúvida" recebe um e-mail por pergunta nova (HANDOFF-v2 8.10)."""
    if kwargs.get('raw') or not created:
        return
    from django.conf import settings as django_settings
    from django.core.mail import send_mail
    from django.urls import reverse
    from users.models import CreatorProfile
    profiles = (CreatorProfile.objects.filter(notify_new_questions=True, user__is_active=True)
                .exclude(user_id=instance.author_id).exclude(user__email='').select_related('user'))
    recipients = [p.user.email for p in profiles if is_staff_user(p.user)]
    if not recipients:
        return
    where = f'{instance.course.title}: ' if instance.course_id else ''
    link = f"{django_settings.SITE_URL}{reverse('painel:community')}?aba=sem-resposta&duvida={instance.id}"
    try:
        send_mail(f'Nova dúvida: {instance.title}', f'{where}{instance.title}\n\n{instance.content[:500]}\n\nResponder: {link}',
                  None, recipients, fail_silently=True)
    except Exception:
        pass
