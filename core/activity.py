from .models import ActivityLog


def log(verb, text, actor=None, student=None, course=None):
    """Grava uma linha de atividade já pronta para exibição: log("enrolled", "Jane foi matriculada em BLS", ...)."""
    return ActivityLog.objects.create(verb=verb, text=text[:200], actor=actor, student=student, course=course)


def _label(course):
    return course.short_name or course.title


def _name(user):
    from users.display import full_name
    return full_name(user)


def log_enrolled(user, course, actor=None):
    return log('enrolled', f'{_name(user)} foi matriculado em {_label(course)}', actor=actor, student=user, course=course)


def log_completed_lesson(user, course, position):
    return log('completed_lesson', f'{_name(user)} concluiu a aula {position} de {_label(course)}', student=user, course=course)


def log_certificate(user, course):
    return log('certificate_issued', f'{_name(user)} recebeu o certificado de {_label(course)}', student=user, course=course)
