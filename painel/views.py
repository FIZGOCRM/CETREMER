import csv
import io
import json
import secrets
import urllib.parse
import urllib.request
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from email.utils import parseaddr

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from community.models import Comment, CommunityPost
from community.notifications import notify_staff_answer
from core.crypto import encrypt
from core.activity import log, log_enrolled
from core.toasts import toast
from core.decorators import painel_admin_required, painel_required
from courses.models import Category, Course, Enrollment, Lesson, LessonMaterial, Module, Progress
from courses.student_views import progress_info
from sales.models import Order
from users.models import CreatorProfile, SiteSettings
from users.models import FirstAccessCode
from users.first_access import issue_code
from users.validators import validate_cpf

User = get_user_model()


def page(request, template, **context):
    return render(request, 'painel/' + template + '.html', context)


@painel_required
@require_POST
def course_reorder(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    try:
        payload = json.loads(request.body)
        module_ids = [int(x) for x in payload['modules']]
        lessons = {int(k): [int(x) for x in v] for k, v in payload['lessons'].items()}
        actual_modules = set(Module.objects.filter(course=course).values_list('id', flat=True))
        actual_lessons = set(Lesson.objects.filter(module__course=course).values_list('id', flat=True))
        if set(module_ids) != actual_modules or len(module_ids) != len(actual_modules) or set(lessons) != actual_modules:
            raise ValueError('Módulos inválidos')
        flat = [x for values in lessons.values() for x in values]
        if set(flat) != actual_lessons or len(flat) != len(actual_lessons): raise ValueError('Aulas inválidas')
        with transaction.atomic():
            for index, module_id in enumerate(module_ids, 1): Module.objects.filter(pk=module_id).update(order=index)
            for module_id, ids in lessons.items():
                for index, lesson_id in enumerate(ids, 1): Lesson.objects.filter(pk=lesson_id).update(module_id=module_id, order=index)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return JsonResponse({'ok': False}, status=400)
    return JsonResponse({'ok': True})
