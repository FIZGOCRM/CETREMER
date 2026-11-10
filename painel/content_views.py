"""Curso · Conteúdo (HANDOFF-v2 8.3): módulos, aulas, painel da aula, criação rápida e exclusão com Desfazer."""
import json
import urllib.parse
import urllib.request

from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.ajax import json_error, json_ok, wants_json
from core.decorators import is_painel_admin, painel_required
from core.toasts import toast
from courses.models import Course, Enrollment, Lesson, LessonMaterial, Module
from users.models import SiteSettings

from . import stats

MAX_PDF = 20 * 1024 * 1024


def vimeo_duration(url):
    """Duração em segundos pelo oEmbed do Vimeo; 0 quando não dá para saber."""
    try:
        endpoint = 'https://vimeo.com/api/oembed.json?' + urllib.parse.urlencode({'url': url})
        with urllib.request.urlopen(endpoint, timeout=5) as response:
            return int(json.load(response).get('duration') or 0)
    except Exception:
        return 0


def video_kind(lesson):
    """'vimeo', 'other' (YouTube ou outro endereço) ou 'none'."""
    if lesson.vimeo_id:
        return 'vimeo'
    return 'other' if lesson.video_url else 'none'


def is_youtube(lesson):
    host = (urllib.parse.urlparse(lesson.video_url).hostname or '').lower()
    return 'youtube' in host or host == 'youtu.be'


def _decorate(lesson, number):
    lesson.number = number
    lesson.kind = video_kind(lesson)
    lesson.is_youtube = lesson.kind == 'other' and is_youtube(lesson)
    lesson.material_count = len(lesson.materials.all())
    return lesson


def course_modules(course):
    """Módulos com `lessons_list` (aulas não excluídas, já numeradas dentro do módulo)."""
    modules = list(Module.objects.filter(course=course).prefetch_related('lessons__materials'))
    for module in modules:
        module.lessons_list = [_decorate(lesson, index) for index, lesson in enumerate(module.lessons.all(), 1)]
        module.published_count = sum(1 for lesson in module.lessons_list if lesson.status == 'published')
    return modules


def course_head_context(course, user):
    lessons = Lesson.objects.filter(module__course=course)
    seconds = sum(lessons.values_list('duration_seconds', flat=True))
    return {
        'course': course, 'modules_total': course.modules.count(), 'lessons_total': lessons.count(),
        'minutes_total': round(seconds / 60), 'students_total': Enrollment.objects.filter(course=course).count(),
    }


def readiness(course, user):
    """Lista "Pronto para vender?": cada item tem state ok|warn|todo, título, subtítulo e link."""
    published = Lesson.objects.filter(module__course=course, status='published')
    published_count = published.count()
    non_vimeo = stats.non_vimeo_by_course().get(course.id, 0)
    admin = is_painel_admin(user)
    signer = bool(SiteSettings.load().signer_name.strip())
    items = [
        {'title': 'Capa e descrição', 'ok': bool(course.cover_image and course.description.strip()),
         'url': reverse('painel:course_sales', args=[course.id])},
        {'title': 'Preço e carga horária', 'ok': bool(course.price and course.workload_hours),
         'url': reverse('painel:course_settings', args=[course.id])},
        {'title': 'Pelo menos uma aula publicada', 'ok': published_count > 0, 'url': reverse('painel:course_content', args=[course.id])},
        {'title': 'Vídeos no Vimeo', 'ok': published_count > 0 and non_vimeo == 0 and not published.filter(vimeo_id='').exists(),
         'warn': non_vimeo > 0,
         'sub': (('1 aula ainda usa YouTube' if non_vimeo == 1 else f'{non_vimeo} aulas ainda usam YouTube') if non_vimeo else ''),
         'url': reverse('painel:course_content', args=[course.id])},
        {'title': 'O que o aluno vai aprender', 'ok': bool(course.objectives_list), 'sub': 'Aparece na página de venda',
         'url': reverse('painel:course_sales', args=[course.id])},
        {'title': 'Assinatura do certificado', 'ok': signer, 'sub': 'Configuração geral da escola',
         'url': (reverse('painel:settings') + '?secao=certificado') if admin else ''},
    ]
    always = ('O que o aluno vai aprender', 'Assinatura do certificado')
    for item in items:
        item['state'] = 'ok' if item['ok'] else 'warn' if item.get('warn') else 'todo'
        item['show_sub'] = bool(item.get('sub')) and (item['title'] in always or item['state'] != 'ok')
    return items


@painel_required
def course_content(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    modules = course_modules(course)
    lessons = [lesson for module in modules for lesson in module.lessons_list]
    selected = next((lesson for lesson in lessons if str(lesson.id) == request.GET.get('aula', '')), None)
    if selected is not None:
        selected.editing = True
    items = readiness(course, request.user)
    context = {
        **course_head_context(course, request.user), 'tab': 'content', 'modules': modules, 'selected': selected,
        'ready_items': items, 'ready_count': sum(1 for item in items if item['ok']),
        'show_live_link': course.status == 'published',
    }
    if selected is not None:
        context.update(drawer_context(course, selected, lessons))
    return render(request, 'painel/course_content.html', context)


def drawer_context(course, lesson, lessons=None):
    if lessons is None:
        lessons = [lesson for module in course_modules(course) for lesson in module.lessons_list]
    index = next(i for i, item in enumerate(lessons) if item.id == lesson.id)
    module_lessons = lesson.module.lessons.all()
    position = [item.id for item in module_lessons].index(lesson.id) + 1
    return {
        'lesson': lesson, 'lesson_course': course, 'position': position, 'module_total': len(module_lessons),
        'prev_lesson': lessons[index - 1] if index > 0 else None,
        'next_lesson': lessons[index + 1] if index + 1 < len(lessons) else None,
        'materials': list(lesson.materials.all()), 'is_youtube': lesson.vimeo_id == '' and bool(lesson.video_url),
        'needs_duration': bool(lesson.vimeo_id) and not lesson.duration_seconds,
        'duration_minutes': round(lesson.duration_seconds / 60) if lesson.duration_seconds else '',
    }


def _lesson_in_course(course_id, lesson_id):
    return get_object_or_404(Lesson.objects.select_related('module__course'), pk=lesson_id, module__course_id=course_id)


def _row_html(request, lesson, number):
    lesson = _decorate(Lesson.objects.prefetch_related('materials').get(pk=lesson.pk), number)
    return render_to_string('painel/_lesson_row.html', {'lesson': lesson, 'course': lesson.module.course, 'is_new': False}, request=request)


def _module_count_text(module):
    lessons = list(module.lessons.all())
    published = sum(1 for lesson in lessons if lesson.status == 'published')
    return f"{len(lessons)} {'aula' if len(lessons) == 1 else 'aulas'} · {published} {'publicada' if published == 1 else 'publicadas'}"


@painel_required
def lesson_drawer(request, course_id, lesson_id):
    course = get_object_or_404(Course, pk=course_id)
    lesson = _lesson_in_course(course_id, lesson_id)
    if request.method == 'POST':
        return _save_lesson(request, course, lesson)
    context = drawer_context(course, lesson)
    if wants_json(request) or request.GET.get('parcial'):
        return render(request, 'painel/_lesson_drawer.html', context)
    return redirect(reverse('painel:course_content', args=[course.id]) + f'?aula={lesson.id}')


def _save_lesson(request, course, lesson):
    errors = {}
    title = request.POST.get('title', '').strip()
    if not title:
        errors['title'] = 'Informe o título da aula.'
    elif len(title) > 200:
        errors['title'] = 'Use até 200 caracteres no título.'
    video_url = request.POST.get('video_url', '').strip()
    if video_url:
        parsed = urllib.parse.urlparse(video_url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            errors['video_url'] = 'Cole o endereço completo do vídeo, começando com https://.'
    minutes_raw = request.POST.get('duration_minutes', '').strip()
    minutes = None
    if minutes_raw:
        if minutes_raw.isdigit() and int(minutes_raw) <= 1440:
            minutes = int(minutes_raw)
        else:
            errors['duration_minutes'] = 'Informe a duração em minutos, só números.'
    status = request.POST.get('status', lesson.status)
    if status not in ('draft', 'published'):
        status = lesson.status
    uploads = request.FILES.getlist('materials')
    for upload in uploads:
        if not upload.name.lower().endswith('.pdf'):
            errors['materials'] = 'Envie apenas arquivos PDF.'
        elif upload.size > MAX_PDF:
            errors['materials'] = 'Cada PDF pode ter até 20 MB.'
    if errors:
        if wants_json(request):
            return JsonResponse({'ok': False, 'errors': {k: [v] for k, v in errors.items()},
                                 'error': 'Corrija 1 campo para salvar.' if len(errors) == 1 else f'Corrija {len(errors)} campos para salvar.'}, status=400)
        toast(request, next(iter(errors.values())), level='error')
        return redirect(reverse('painel:course_content', args=[course.id]) + f'?aula={lesson.id}')

    with transaction.atomic():
        old_url = lesson.video_url
        lesson.title = title
        lesson.description = request.POST.get('description', '')
        lesson.status = status
        lesson.is_free_preview = bool(request.POST.get('is_free_preview'))
        lesson.video_url = video_url
        if minutes is not None:
            lesson.duration_seconds = minutes * 60
        lesson.save()
        if lesson.video_url != old_url and lesson.vimeo_id and minutes is None:
            found = vimeo_duration(lesson.video_url)
            if found:
                lesson.duration_seconds = found
                lesson.save(update_fields=['duration_seconds'])
        for material in lesson.materials.all():
            new_title = request.POST.get(f'material_{material.id}', '').strip()
            if new_title and new_title != material.title:
                material.title = new_title[:120]
                material.save(update_fields=['title'])
        for upload in uploads:
            material = LessonMaterial(lesson=lesson, title=upload.name[:120], file=upload,
                                      order=lesson.materials.count() + 1)
            material.full_clean()
            material.save()
    siblings = list(lesson.module.lessons.all())
    number = [item.id for item in siblings].index(lesson.id) + 1
    row = _row_html(request, lesson, number)
    if wants_json(request):
        return json_ok(toast='Aula salva', replace={f'#lesson-row-{lesson.id}': row},
                       counts={f'#module-count-{lesson.module_id}': _module_count_text(lesson.module)})
    toast(request, 'Aula salva')
    return redirect(reverse('painel:course_content', args=[course.id]))


@painel_required
@require_POST
def lesson_quick_create(request, module_id):
    module = get_object_or_404(Module.objects.select_related('course'), pk=module_id)
    title = request.POST.get('title', '').strip()
    back = reverse('painel:course_content', args=[module.course_id])
    if not title:
        if wants_json(request):
            return json_error('Informe o título da aula.')
        toast(request, 'Informe o título da aula.', level='error')
        return redirect(back)
    if len(title) > 200:
        if wants_json(request):
            return json_error('Use até 200 caracteres no título.')
        toast(request, 'Use até 200 caracteres no título.', level='error')
        return redirect(back)
    last = Lesson.all_objects.filter(module=module).aggregate(top=Max('order'))['top'] or 0
    lesson = Lesson.objects.create(module=module, title=title, order=last + 1, status='draft')
    if wants_json(request):
        number = module.lessons.count()
        lesson = _decorate(Lesson.objects.prefetch_related('materials').get(pk=lesson.pk), number)
        html = render_to_string('painel/_lesson_row.html', {'lesson': lesson, 'course': module.course, 'is_new': True}, request=request)
        return json_ok(html=html, open_selector=f'#lesson-row-{lesson.id} [data-drawer-url]',
                       counts={f'#module-count-{module.id}': _module_count_text(module)})
    return redirect(back + f'?aula={lesson.id}')


@painel_required
@require_POST
def lesson_delete(request, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), pk=lesson_id)
    course_id = lesson.module.course_id
    Lesson.all_objects.filter(pk=lesson.pk).update(deleted_at=timezone.now())
    undo = reverse('painel:lesson_restore', args=[lesson.id])
    if wants_json(request):
        return json_ok(toast='Aula excluída', undo_url=undo, remove=f'#lesson-row-{lesson.id}',
                       counts={f'#module-count-{lesson.module_id}': _module_count_text(lesson.module)})
    toast(request, 'Aula excluída', undo_url=undo)
    return redirect('painel:course_content', course_id=course_id)


@painel_required
@require_POST
def lesson_restore(request, lesson_id):
    lesson = get_object_or_404(Lesson.all_objects.select_related('module__course'), pk=lesson_id, deleted_at__isnull=False)
    Lesson.all_objects.filter(pk=lesson.pk).update(deleted_at=None)
    toast(request, 'Aula restaurada')
    url = reverse('painel:course_content', args=[lesson.module.course_id])
    return json_ok(redirect=url) if wants_json(request) else redirect(url)


@painel_required
@require_POST
def material_delete(request, material_id):
    material = get_object_or_404(LessonMaterial.objects.select_related('lesson__module'), pk=material_id)
    lesson = material.lesson
    material.delete()
    if wants_json(request):
        return json_ok(toast='Material excluído', remove=f'#material-{material_id}')
    toast(request, 'Material excluído')
    return redirect(reverse('painel:course_content', args=[lesson.module.course_id]) + f'?aula={lesson.id}')


@painel_required
@require_POST
def module_create(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    title = request.POST.get('title', '').strip()
    back = reverse('painel:course_content', args=[course.id])
    if not title or len(title) > 200:
        message = 'Informe o título do módulo.' if not title else 'Use até 200 caracteres no título.'
        if wants_json(request):
            return JsonResponse({'ok': False, 'errors': {'title': [message]}, 'error': message}, status=400)
        toast(request, message, level='error')
        return redirect(back)
    last = course.modules.aggregate(top=Max('order'))['top'] or 0
    Module.objects.create(course=course, title=title, order=last + 1)
    toast(request, 'Módulo criado')
    return json_ok(redirect=back) if wants_json(request) else redirect(back)


@painel_required
@require_POST
def module_rename(request, module_id):
    module = get_object_or_404(Module, pk=module_id)
    title = request.POST.get('title', '').strip()
    back = reverse('painel:course_content', args=[module.course_id])
    if not title or len(title) > 200:
        message = 'Informe o título do módulo.' if not title else 'Use até 200 caracteres no título.'
        if wants_json(request):
            return JsonResponse({'ok': False, 'errors': {'title': [message]}, 'error': message}, status=400)
        toast(request, message, level='error')
        return redirect(back)
    module.title = title
    module.save(update_fields=['title'])
    toast(request, 'Módulo renomeado')
    return json_ok(redirect=back) if wants_json(request) else redirect(back)


@painel_required
@require_POST
def module_delete(request, module_id):
    """Apaga o módulo, as aulas dele e o progresso dos alunos nelas (diálogo "Afeta alunos")."""
    module = get_object_or_404(Module, pk=module_id)
    back = reverse('painel:course_content', args=[module.course_id])
    if module.course.modules.count() <= 1:
        message = 'O curso precisa ter pelo menos um módulo.'
        if wants_json(request):
            return json_error(message)
        toast(request, message, level='error')
        return redirect(back)
    module.delete()
    toast(request, 'Módulo excluído')
    return json_ok(redirect=back) if wants_json(request) else redirect(back)


@painel_required
def course_edit_redirect(request, course_id):
    return redirect('painel:course_settings', course_id=course_id, permanent=True)


@painel_required
def course_lessons_redirect(request, course_id):
    return redirect('painel:course_content', course_id=course_id, permanent=True)
