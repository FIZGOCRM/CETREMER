"""Início (8.1) e Cursos (8.2) do painel, mais as ações da lista: criar, duplicar, mover para rascunho e arquivar."""
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from community.models import CommunityPost
from core.activity import log
from core.ajax import json_ok, wants_json
from core.decorators import is_painel_admin, painel_required
from core.models import ActivityLog
from core.toasts import toast
from courses.models import Category, Course, CourseFAQ, Lesson, LessonMaterial, Module
from users.display import first_name, full_name
from users.models import CreatorProfile, SiteSettings

from . import stats

STATUS_FILTERS = {'publicados': 'published', 'rascunhos': 'draft', 'arquivados': 'archived'}


def _creator(user):
    profile = CreatorProfile.objects.filter(user=user).first()
    return profile or CreatorProfile.objects.first() or CreatorProfile.objects.create(user=user)


def _course_label(course):
    return course.short_name or course.title


def _split_lead(text, name, url):
    """Separa o nome (link) do resto da frase quando o texto começa com ele."""
    if name and text.startswith(name):
        return {'lead': name, 'url': url, 'rest': text[len(name):]}
    return {'lead': '', 'url': '', 'rest': text}


def _activity_items(limit=8):
    items = []
    for entry in ActivityLog.objects.select_related('actor', 'student', 'course').order_by('-created_at', '-id')[:limit]:
        if entry.student_id:
            part = _split_lead(entry.text, full_name(entry.student), reverse('painel:student_detail', args=[entry.student_id]))
        elif entry.course_id:
            label = _course_label(entry.course)
            before, sep, after = entry.text.partition(label)
            part = ({'before': before, 'lead': label, 'url': reverse('painel:course_content', args=[entry.course_id]), 'rest': after}
                    if sep else {'lead': '', 'url': '', 'rest': entry.text})
        else:
            part = {'lead': '', 'url': '', 'rest': entry.text}
        part.setdefault('before', '')
        part['created_at'] = entry.created_at
        part['by'] = first_name(entry.actor) if entry.actor_id else ''
        items.append(part)
    return items


def _attention(admin):
    items = []
    pending = CommunityPost.objects.filter(is_hidden=False, is_answered_cache=False)
    count = pending.count()
    if count:
        oldest = pending.order_by('created_at').first()
        items.append({'kind': 'danger', 'icon': 'chat', 'count': count, 'key': 'questions', 'since': oldest.created_at,
                      'url': reverse('painel:community'), 'cta': 'Responder'})
    by_course = stats.non_vimeo_by_course()
    if by_course:
        worst = max(by_course, key=by_course.get)
        items.append({'kind': 'warn', 'icon': 'video', 'count': sum(by_course.values()), 'key': 'youtube',
                      'url': reverse('painel:course_content', args=[worst]), 'cta': 'Corrigir'})
    if admin and not SiteSettings.load().signer_name.strip():
        items.append({'kind': 'warn', 'icon': 'award', 'count': 1, 'key': 'signer',
                      'url': reverse('painel:settings') + '?secao=certificado', 'cta': 'Configurar'})
    never = stats.never_accessed().count()
    if never:
        items.append({'kind': '', 'icon': 'users', 'count': never, 'key': 'never',
                      'url': reverse('painel:students') + '?filtro=nunca', 'cta': 'Ver alunos'})
    return items


@painel_required
def dashboard(request):
    admin = is_painel_admin(request.user)
    period = stats.parse_period(request.GET.get('periodo'))
    numbers = stats.dashboard_numbers(period)
    courses = list(Course.objects.filter(status='published').order_by('title'))
    per_course = stats.course_stats([c.id for c in courses], since=numbers['since'])
    rows = [{'course': c, **per_course[c.id]} for c in courses]
    attention = _attention(admin)
    return render(request, 'painel/dashboard.html', {
        'greeting': stats.greeting(), 'period': period, 'periods': stats.PERIODS,
        'numbers': numbers, 'admin': admin, 'attention': attention, 'activity': _activity_items(),
        'courses_table': rows,
    })


def _filtered_courses(request):
    status = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()
    category = request.GET.get('categoria', '')
    base = Course.objects.all()
    if q:
        base = base.filter(Q(title__icontains=q) | Q(short_name__icontains=q))
    if category:
        base = base.filter(category__slug=category)
    counts = {
        'all': base.exclude(status='archived').count(), 'published': base.filter(status='published').count(),
        'draft': base.filter(status='draft').count(), 'archived': base.filter(status='archived').count(),
    }
    wanted = STATUS_FILTERS.get(status)
    qs = base.filter(status=wanted) if wanted else base.exclude(status='archived')
    return qs, counts, status if wanted else '', q, category


@painel_required
def courses(request):
    qs, counts, status, q, category = _filtered_courses(request)
    qs = (qs.select_related('category')
          .annotate(modules_count=Count('modules', distinct=True)).order_by('title'))
    items = list(qs)
    ids = [c.id for c in items]
    lessons = {row['module__course_id']: row for row in
               Lesson.objects.filter(module__course_id__in=ids).values('module__course_id')
               .annotate(n=Count('id'), seconds=Sum('duration_seconds'))}
    youtube = stats.non_vimeo_by_course()
    per_course = stats.course_stats(ids)
    cards = []
    for course in items:
        info = lessons.get(course.id, {})
        cards.append({
            'course': course, 'lessons': info.get('n', 0), 'minutes': round((info.get('seconds') or 0) / 60),
            'youtube': youtube.get(course.id, 0), 'no_workload': not course.workload_hours,
            **per_course[course.id],
            'sales_url': request.build_absolute_uri(reverse('course_preview', args=[course.slug])),
        })
    return render(request, 'painel/courses.html', {
        'cards': cards, 'counts': counts, 'status': status, 'q': q, 'category': category,
        'categories': Category.objects.all(), 'has_any': Course.objects.exists(),
        'filtered': bool(status or q or category),
    })


def _unique_slug(title):
    base = slugify(title) or 'curso'
    slug, index = base, 2
    while Course.objects.filter(slug=slug).exists():
        slug = f'{base}-{index}'
        index += 1
    return slug


def _failure(request, field, message, back):
    if wants_json(request):
        return JsonResponse({'ok': False, 'errors': {field: [message]}, 'error': message}, status=400)
    toast(request, message, level='error')
    return redirect(back)


def _done(request, url):
    return json_ok(redirect=url) if wants_json(request) else redirect(url)


@painel_required
def course_create(request):
    """Diálogo "Novo curso": cria como rascunho com o "Módulo 1" pronto e abre a aba Conteúdo."""
    if request.method != 'POST':
        return redirect(reverse('painel:courses') + '?abrir=dlg-new-course')
    back = reverse('painel:courses') + '?abrir=dlg-new-course'
    title = request.POST.get('title', '').strip()
    if not title:
        return _failure(request, 'title', 'Informe o título do curso.', back)
    if len(title) > 200:
        return _failure(request, 'title', 'Use até 200 caracteres no título.', back)
    category = Category.objects.filter(pk=request.POST.get('category') or None).first()
    with transaction.atomic():
        course = Course.objects.create(title=title, slug=_unique_slug(title), category=category,
                                       creator=_creator(request.user), status='draft')
        Module.objects.create(course=course, title='Módulo 1', order=1)
        log('course_updated', f'Curso {_course_label(course)} foi criado', actor=request.user, course=course)
    toast(request, 'Curso criado como rascunho')
    return _done(request, reverse('painel:course_content', args=[course.id]))


def _copy_row(obj, **changes):
    obj.pk = None
    obj.id = None
    obj._state.adding = True
    for key, value in changes.items():
        setattr(obj, key, value)
    obj.save()
    return obj


@painel_required
@require_POST
def course_duplicate(request, course_id):
    source = get_object_or_404(Course, pk=course_id)
    with transaction.atomic():
        modules = list(source.modules.all())
        faqs = list(source.faqs.all())
        lessons = {m.id: list(Lesson.objects.filter(module=m)) for m in modules}
        materials = {l.id: list(l.materials.all()) for ls in lessons.values() for l in ls}
        new_title = f'{source.title} (cópia)'[:200]
        copy = _copy_row(Course.objects.get(pk=source.pk), title=new_title, slug=_unique_slug(new_title),
                         status='draft', archived_at=None)
        for faq in faqs:
            _copy_row(faq, course=copy)
        for module in modules:
            old_id = module.id
            new_module = _copy_row(module, course=copy)
            for lesson in lessons[old_id]:
                old_lesson = lesson.id
                new_lesson = _copy_row(lesson, module=new_module)
                for material in materials.get(old_lesson, []):
                    _copy_row(material, lesson=new_lesson)
        log('course_updated', f'Curso {_course_label(copy)} foi criado a partir de uma cópia', actor=request.user, course=copy)
    toast(request, 'Cópia criada como rascunho')
    return _done(request, reverse('painel:course_content', args=[copy.id]))


STATUS_LABEL = {'draft': 'rascunho', 'published': 'publicado', 'archived': 'arquivado'}


@painel_required
@require_POST
def course_status(request, course_id):
    """Muda o status: para rascunho, para arquivado (com a sigla digitada) ou de volta (Desfazer, `?para=`)."""
    course = get_object_or_404(Course, pk=course_id)
    target = request.POST.get('para') or request.GET.get('para') or ''
    if target not in STATUS_LABEL:
        return _failure(request, 'para', 'Status inválido.', reverse('painel:courses'))
    previous = course.status
    undo = request.GET.get('desfazer') == '1'
    if target == 'archived':
        expected = _course_label(course).strip().lower()
        if request.POST.get('confirmar', '').strip().lower() != expected:
            return _failure(request, 'confirmar', f'Digite {_course_label(course)} para confirmar.', reverse('painel:courses'))
    course.status = target
    course.archived_at = timezone.now() if target == 'archived' else None
    course.save(update_fields=['status', 'archived_at'])
    label = _course_label(course)
    if undo:
        toast(request, 'Alteração desfeita')
        log('course_updated', f'Curso {label} voltou a ficar {STATUS_LABEL[target]}', actor=request.user, course=course)
        return _done(request, reverse('painel:courses') + ('?status=arquivados' if target == 'archived' else ''))
    undo_url = f"{reverse('painel:course_status', args=[course.id])}?para={previous}&desfazer=1"
    if target == 'archived':
        toast(request, 'Curso arquivado', undo_url=undo_url)
        log('course_updated', f'Curso {label} foi arquivado', actor=request.user, course=course)
        return _done(request, reverse('painel:courses') + '?status=arquivados')
    toast(request, 'Curso movido para rascunho' if target == 'draft' else 'Curso publicado', undo_url=undo_url)
    log('course_updated', f'Curso {label} foi movido para {STATUS_LABEL[target]}', actor=request.user, course=course)
    return _done(request, reverse('painel:courses'))
