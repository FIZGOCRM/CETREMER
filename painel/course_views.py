"""Curso · Página de venda (8.4) e Configurações (8.5), encontros ao vivo, excluir curso e certificado de exemplo."""
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from core.activity import log
from core.ajax import json_error, json_ok, wants_json
from core.decorators import is_painel_admin, painel_required
from core.toasts import toast
from courses.models import Category, Course, CourseFAQ, CourseSlugRedirect, Enrollment, Lesson, LiveSession, Module
from sales.models import Order
from users.models import SiteSettings

from .content_views import course_head_context

BRASILIA = ZoneInfo('America/Sao_Paulo')
MAX_PRICE = Decimal('99999999.99')
SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
TAGLINE_MAX = 160
COVER_MAX = 5 * 1024 * 1024


def parse_price(text):
    """"150", "150,00", "1.234,56", "R$ 150,00" e "150.50" viram Decimal. Levanta ValueError se não for um preço."""
    raw = (text or '').strip().replace('R$', '').replace(' ', '')
    if not raw:
        raise ValueError('vazio')
    if ',' in raw:
        raw = raw.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'\d{1,3}(\.\d{3})+', raw):
        raw = raw.replace('.', '')
    if not re.fullmatch(r'\d+(\.\d{1,2})?', raw):
        raise ValueError('formato')
    value = Decimal(raw)
    if value > MAX_PRICE:
        raise ValueError('grande')
    return value


def format_price(value):
    """Decimal -> "1.234,56" (campo de texto do painel)."""
    try:
        number = Decimal(str(value or 0))
    except InvalidOperation:
        number = Decimal(0)
    text = f'{number:,.2f}'
    return text.replace(',', '§').replace('.', ',').replace('§', '.')


def _errors_response(request, errors, back):
    total = len(errors)
    summary = 'Corrija 1 campo para salvar.' if total == 1 else f'Corrija {total} campos para salvar.'
    if wants_json(request):
        from django.http import JsonResponse
        return JsonResponse({'ok': False, 'errors': {k: [v] for k, v in errors.items()}, 'error': summary}, status=400)
    toast(request, next(iter(errors.values())), level='error')
    return redirect(back)


def _valid_url(value):
    try:
        URLValidator(schemes=['http', 'https'])(value)
        return True
    except ValidationError:
        return False


# ---------------------------------------------------------------- Página de venda


def _sales_context(course, user, preview):
    free = list(Lesson.objects.filter(module__course=course, is_free_preview=True).select_related('module')
                .order_by('module__order', 'order'))
    return {
        **course_head_context(course, user), 'tab': 'sales', 'show_live_link': course.status == 'published',
        'objectives': course.objectives_list, 'faqs': list(course.faqs.all()), 'free_lessons': free,
        'tagline_size': len(course.tagline), 'tagline_max': TAGLINE_MAX, 'preview': preview,
        'preview_url': reverse('course_preview', args=[course.slug]) + '?preview=1',
        'lessons_published': Lesson.objects.filter(module__course=course, status='published').count(),
    }


@painel_required
def course_sales(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    preview = 'celular' if request.GET.get('previa') == 'celular' else 'computador'
    back = reverse('painel:course_sales', args=[course.id])
    if request.method == 'POST':
        return _save_sales(request, course, back)
    return render(request, 'painel/course_sales.html', _sales_context(course, request.user, preview))


def _save_sales(request, course, back):
    errors = {}
    tagline = request.POST.get('tagline', '').strip()
    if len(tagline) > TAGLINE_MAX:
        errors['tagline'] = f'Use até {TAGLINE_MAX} caracteres na chamada curta.'
    objectives = [item.strip() for item in request.POST.getlist('objectives') if item.strip()]
    questions = request.POST.getlist('faq_question')
    answers = request.POST.getlist('faq_answer')
    faqs = []
    for question, answer in zip(questions, answers):
        question, answer = question.strip(), answer.strip()
        if not question and not answer:
            continue
        if not question or not answer:
            errors['faq_question'] = 'Preencha a pergunta e a resposta de cada item, ou apague o item.'
            break
        if len(question) > 160:
            errors['faq_question'] = 'Use até 160 caracteres em cada pergunta.'
            break
        faqs.append((question, answer))
    cover = request.FILES.get('cover_image')
    if cover:
        if not (cover.content_type or '').startswith('image/'):
            errors['cover_image'] = 'Envie uma imagem JPG, PNG ou WebP.'
        elif cover.size > COVER_MAX:
            errors['cover_image'] = 'A capa deve ter no máximo 5 MB.'
    if errors:
        return _errors_response(request, errors, back)

    with transaction.atomic():
        course.tagline = tagline
        course.description = request.POST.get('description', '').strip()
        course.learning_objectives = '\n'.join(objectives)
        course.target_audience = request.POST.get('target_audience', '').strip()
        if cover:
            course.cover_image = cover
        elif request.POST.get('remove_cover'):
            course.cover_image = None
        course.save()
        course.faqs.all().delete()
        CourseFAQ.objects.bulk_create([CourseFAQ(course=course, question=q, answer=a, order=i) for i, (q, a) in enumerate(faqs, 1)])
        log('course_updated', f'Curso {course.short_name or course.title} foi atualizado', actor=request.user, course=course)
    toast_text = 'Alterações salvas'
    if wants_json(request):
        context = _sales_context(course, request.user, 'computador')
        html = render_to_string('painel/_sales_preview.html', {**context, 'course': course}, request=request)
        return json_ok(toast=toast_text, replace={'#sales-preview': html},
                       counts={'#tagline-count': f'{len(course.tagline)} de {TAGLINE_MAX} caracteres'})
    toast(request, toast_text)
    return redirect(back)


# ---------------------------------------------------------------- Configurações


def _settings_context(course, user):
    modules = list(Module.objects.filter(course=course))
    for module in modules:
        if module.release_date:
            module.release_type, module.release_value = 'date', module.release_date.isoformat()
        elif module.release_after_days is not None:
            module.release_type, module.release_value = 'days', str(module.release_after_days)
        else:
            module.release_type, module.release_value = 'now', ''
    sessions = list(course.live_sessions.all())
    for session in sessions:
        start = session.starts_at.astimezone(BRASILIA)
        end = session.ends_at.astimezone(BRASILIA)
        session.date_value, session.start_value, session.end_value = start.date().isoformat(), start.strftime('%H:%M'), end.strftime('%H:%M')
    students = Enrollment.objects.filter(course=course).count()
    orders = Order.objects.filter(course=course).count()
    return {
        **course_head_context(course, user), 'tab': 'settings', 'show_live_link': course.status == 'published',
        'categories': Category.objects.all(), 'modules': modules, 'sessions': sessions, 'price_text': format_price(course.price),
        'access_choices': [('', 'Vitalício'), ('6', '6 meses'), ('12', '12 meses'), ('24', '24 meses')],
        'signer_missing': not SiteSettings.load().signer_name.strip(), 'admin': is_painel_admin(user),
        'orders_total': orders, 'can_delete': students == 0 and orders == 0,
    }


@painel_required
def course_settings(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    back = reverse('painel:course_settings', args=[course.id])
    if request.method == 'POST':
        return _save_settings(request, course, back)
    return render(request, 'painel/course_settings.html', _settings_context(course, request.user) | {'course': course})


def _save_settings(request, course, back):
    post = request.POST
    errors = {}
    title = post.get('title', '').strip()
    if not title:
        errors['title'] = 'Informe o título do curso.'
    elif len(title) > 200:
        errors['title'] = 'Use até 200 caracteres no título.'
    short_name = post.get('short_name', '').strip()
    if len(short_name) > 12:
        errors['short_name'] = 'Use até 12 caracteres na sigla.'
    slug = post.get('slug', '').strip().lower() or course.slug
    if not SLUG_RE.match(slug) or len(slug) > 50:
        errors['slug'] = 'Use só letras minúsculas, números e hífen, até 50 caracteres.'
    elif Course.objects.filter(slug=slug).exclude(pk=course.pk).exists():
        errors['slug'] = 'Já existe um curso com este endereço.'
    elif CourseSlugRedirect.objects.filter(old_slug=slug).exclude(course=course).exists():
        errors['slug'] = 'Este endereço foi usado por outro curso há pouco tempo.'
    category = None
    if post.get('category'):
        category = Category.objects.filter(pk=post['category']).first()
        if category is None:
            errors['category'] = 'Escolha uma categoria da lista.'
    try:
        price = parse_price(post.get('price', ''))
    except ValueError:
        errors['price'] = 'Informe o preço em reais, por exemplo 150,00.'
        price = None
    workload = None
    if post.get('workload_hours', '').strip():
        text = post['workload_hours'].strip()
        if text.isdigit() and 0 < int(text) <= 2000:
            workload = int(text)
        else:
            errors['workload_hours'] = 'Informe a carga horária em horas, só números.'
    access = post.get('access_months', '')
    if access not in ('', '6', '12', '24'):
        errors['access_months'] = 'Escolha um prazo da lista.'
    mode = post.get('release_mode', course.release_mode)
    if mode not in ('all', 'scheduled'):
        mode = course.release_mode
    releases = {}
    if mode == 'scheduled':
        for module in Module.objects.filter(course=course):
            kind = post.get(f'release_type_{module.id}', 'now')
            if kind == 'days':
                days = post.get(f'release_days_{module.id}', '').strip()
                if days.isdigit() and int(days) <= 3650:
                    releases[module.id] = (int(days), None)
                else:
                    errors[f'release_days_{module.id}'] = 'Informe os dias após a matrícula, só números.'
            elif kind == 'date':
                try:
                    releases[module.id] = (None, date.fromisoformat(post.get(f'release_date_{module.id}', '').strip()))
                except ValueError:
                    errors[f'release_date_{module.id}'] = 'Informe a data de liberação.'
            else:
                releases[module.id] = (None, None)
    meet = post.get('live_meet_url', '').strip()
    if meet and not _valid_url(meet):
        errors['live_meet_url'] = 'Cole o link completo, começando com https://.'
    if errors:
        return _errors_response(request, errors, back)

    with transaction.atomic():
        old_slug = course.slug
        course.title, course.short_name, course.category = title, short_name, category
        course.price, course.workload_hours = price, workload
        course.access_months = int(access) if access else None
        course.release_mode = mode
        course.notify_module_release = post.get('notify_module_release') == '1'
        course.certificate_enabled = post.get('certificate_enabled') == '1'
        course.live_meet_url = meet
        if slug != old_slug:
            CourseSlugRedirect.objects.filter(old_slug=slug, course=course).delete()
            CourseSlugRedirect.objects.update_or_create(old_slug=old_slug, defaults={'course': course})
            course.slug = slug
        course.save()
        for module_id, (days, release_date) in releases.items():
            Module.objects.filter(pk=module_id).update(release_after_days=days, release_date=release_date)
        log('course_updated', f'Curso {course.short_name or course.title} foi atualizado', actor=request.user, course=course)
    if wants_json(request):
        return json_ok(toast='Alterações salvas')
    toast(request, 'Alterações salvas')
    return redirect(back)


# ---------------------------------------------------------------- Encontros ao vivo


def _parse_session(post):
    errors = {}
    title = post.get('title', '').strip()
    if not title:
        errors['title'] = 'Informe o título do encontro.'
    try:
        day = date.fromisoformat(post.get('date', ''))
        start = datetime.strptime(post.get('start', ''), '%H:%M').time()
        end = datetime.strptime(post.get('end', ''), '%H:%M').time()
    except ValueError:
        errors['date'] = 'Informe a data e os horários de início e fim.'
        return None, errors
    starts_at = datetime.combine(day, start, tzinfo=BRASILIA)
    ends_at = datetime.combine(day, end, tzinfo=BRASILIA)
    if ends_at <= starts_at:
        errors['end'] = 'O fim precisa ser depois do início.'
    meet = post.get('meet_url', '').strip()
    recording = post.get('recording_url', '').strip()
    for name, value in (('meet_url', meet), ('recording_url', recording)):
        if value and not _valid_url(value):
            errors[name] = 'Cole o link completo, começando com https://.'
    if errors:
        return None, errors
    return {'title': title[:160], 'starts_at': starts_at, 'ends_at': ends_at, 'host_name': post.get('host_name', '').strip()[:80],
            'meet_url': meet, 'recording_url': recording}, {}


@painel_required
@require_POST
def live_session_save(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    back = reverse('painel:course_settings', args=[course.id]) + '#ao-vivo'
    session = None
    if request.POST.get('session_id'):
        session = get_object_or_404(LiveSession, pk=request.POST['session_id'], course=course)
    data, errors = _parse_session(request.POST)
    if errors:
        return _errors_response(request, errors, back)
    if session is None:
        LiveSession.objects.create(course=course, **data)
        message = 'Encontro adicionado'
    else:
        for key, value in data.items():
            setattr(session, key, value)
        session.reminder_sent_at = None if 'starts_at' in data else session.reminder_sent_at
        session.save()
        message = 'Encontro salvo'
    toast(request, message)
    return json_ok(redirect=back) if wants_json(request) else redirect(back)


@painel_required
@require_POST
def live_session_delete(request, session_id):
    session = get_object_or_404(LiveSession, pk=session_id)
    back = reverse('painel:course_settings', args=[session.course_id]) + '#ao-vivo'
    session.delete()
    toast(request, 'Encontro excluído')
    return json_ok(redirect=back) if wants_json(request) else redirect(back)


# ---------------------------------------------------------------- Excluir e certificado de exemplo


@painel_required
@require_POST
def course_delete(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    back = reverse('painel:course_settings', args=[course.id])
    label = course.short_name or course.title
    if Enrollment.objects.filter(course=course).exists() or Order.objects.filter(course=course).exists():
        message = 'Este curso tem alunos ou pedidos e não pode ser excluído. Arquive o curso.'
        return json_error(message) if wants_json(request) else (toast(request, message, level='error') or redirect(back))
    if request.POST.get('confirmar', '').strip().lower() != label.strip().lower():
        message = f'Digite {label} para confirmar.'
        if wants_json(request):
            from django.http import JsonResponse
            return JsonResponse({'ok': False, 'errors': {'confirmar': [message]}, 'error': message}, status=400)
        toast(request, message, level='error')
        return redirect(back)
    with transaction.atomic():
        log('course_updated', f'Curso {label} foi excluído', actor=request.user)
        course.delete()
    toast(request, 'Curso excluído')
    url = reverse('painel:courses')
    return json_ok(redirect=url) if wants_json(request) else redirect(url)


@painel_required
def course_certificate_sample(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    sample = SimpleNamespace(code='EXEMPLO', student_name='EXEMPLO · Nome completo do aluno', student_cpf='00000000000',
                             course_title=course.title, workload_hours=course.workload_hours, completed_at=timezone.now())
    return render(request, 'courses/certificate.html', {'certificate': sample, 'verify_url': ''})
