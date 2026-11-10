from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST


@login_required
@require_GET
def live_classes(request):
    return render(request, 'phase0/student.html', {'page_title': 'Aulas ao vivo'})


@login_required
@require_GET
def certificates(request):
    return render(request, 'phase0/student.html', {'page_title': 'Certificados'})


@require_GET
def verify_certificate(request):
    return render(request, 'phase0/public.html')


@require_GET
def password_reset(request):
    return render(request, 'phase0/auth.html')


@login_required
@require_POST
def complete_lesson(request, lesson_id):
    return HttpResponse('Em construção', status=501)
