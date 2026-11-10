from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    """Registro para "Atividade recente" do painel e aba Atividade do aluno (HANDOFF-v2 6.1)."""
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='activity')
    course = models.ForeignKey('courses.Course', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    verb = models.CharField(max_length=60)  # enrolled, completed_lesson, course_updated, imported, certificate_issued
    text = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.text
