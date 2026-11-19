from django import template
from django.db.models import Count, Q

from courses.models import Lesson

register = template.Library()


@register.simple_tag
def course_counts(course):
    counts = Lesson.objects.filter(module__course=course).aggregate(
        lessons=Count("pk"),
        published=Count("pk", filter=Q(status="published", module__status="published")),
    )
    counts.update(modules=course.modules.count(), students=course.enrollments.count(),
                  materials=course.materials.filter(is_active=True).count())
    return counts
