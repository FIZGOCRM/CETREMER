"""Início do aluno (HANDOFF-v2 7.1) e página do curso para o aluno (7.2)."""
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.utils import timezone
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST

from community.models import CommunityPost
from users import steps as step_store
from users.display import first_name
from .models import Certificate, Course, Enrollment, Lesson, LessonMaterial, LiveSession, Module, Progress
from .services import build_progress

BRASILIA = ZoneInfo('America/Sao_Paulo')
WEEKDAYS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
FILTERS = ('todos', 'andamento', 'nao_iniciados', 'concluidos')
ORIGIN_PHRASE = {'purchase': 'pela compra no site', 'import': 'por importação', 'manual': 'pela equipe', 'signup': 'pelo cadastro no site'}


def greeting():
    hour = timezone.localtime().hour
    return 'Bom dia' if 5 <= hour < 12 else 'Boa tarde' if 12 <= hour < 18 else 'Boa noite'


def _clock(moment):
    moment = timezone.localtime(moment, BRASILIA)
    return f'{moment.hour}h' if moment.minute == 0 else f'{moment.hour}h{moment.minute:02d}'


def _mmss(seconds):
    minutes, rest = divmod(int(seconds), 60)
    return f'{minutes:02d}:{rest:02d}'


def _since(moment):
    return timesince(moment).split(',')[0].replace('\xa0', ' ')


def _bulk_progress(user, profile, course_ids):
    """Progresso de vários cursos com 2 consultas: aulas publicadas e registros do aluno."""
    lessons = list(Lesson.objects.filter(module__course_id__in=course_ids, status='published')
                   .select_related('module').order_by('module__course_id', 'module__order', 'module_id', 'order', 'id'))
    by_course = {cid: [] for cid in course_ids}
    for lesson in lessons:
        by_course[lesson.module.course_id].append(lesson)
    records = {}
    for record in Progress.objects.filter(student=profile, lesson__in=lessons):
        records[record.lesson_id] = record
    result = {}
    for cid, course_lessons in by_course.items():
        course_records = {l.id: records[l.id] for l in course_lessons if l.id in records}
        info = build_progress(course_lessons, course_records)
        info['lessons'] = course_lessons
        info['started'] = bool(course_records)
        result[cid] = info
    return result


def _live_step(session, now):
    start = timezone.localtime(session.starts_at, BRASILIA)
    end = timezone.localtime(session.ends_at, BRASILIA)
    if session.starts_at <= now:
        badge_class, badge = 'badge--live', '● Ao vivo agora'
    else:
        days = (start.date() - timezone.localtime(now, BRASILIA).date()).days
        badge_class = 'badge--blue'
        badge = 'Hoje' if days == 0 else f'Em {days} dia' + ('' if days == 1 else 's')
    meta = (f'{WEEKDAYS[start.weekday()]}, {start:%d/%m}, das {_clock(session.starts_at)} às {_clock(session.ends_at)} '
            f'(horário de Brasília). O botão de entrar libera 15 min antes.')
    return {'key': f'live:{session.id}', 'icon': 'video', 'tone': '', 'title': f'Aula ao vivo · {session.course.short_name or session.course.title}',
            'meta': meta, 'badge_class': badge_class, 'badge': badge, 'action': 'Ver detalhes', 'url': reverse('live_classes')}


def _build_steps(user, profile, items, now):
    """Até 4 itens, na ordem: dados do certificado, certificado pronto, aula ao vivo, resposta nova."""
    candidates = []
    if items and not (profile.full_name and profile.cpf):
        candidates.append({'key': 'cpf', 'icon': 'alert', 'tone': 'task__icon--warn', 'title': 'Informe nome completo e CPF',
                           'meta': 'Sem isso o certificado não pode ser emitido. Leva 1 minuto.', 'badge_class': 'badge--warning',
                           'badge': 'Pendente', 'action': 'Completar dados', 'url': reverse('settings') + '?secao=certificado'})
    done_items = [i for i in items if i['status'] == 'concluido' and i['course'].certificate_enabled]
    if done_items:
        issued = set(Certificate.objects.filter(enrollment__student=profile, enrollment__is_active=True)
                     .values_list('enrollment__course_id', flat=True))
        for item in done_items:
            course = item['course']
            if course.id not in issued:
                candidates.append({'key': f'cert:{course.slug}', 'icon': 'award', 'tone': 'task__icon--ok',
                                   'title': f'Seu certificado do {course.short_name or course.title} está pronto',
                                   'meta': 'Confira nome e CPF e emita', 'badge_class': 'badge--success', 'badge': 'Pronto',
                                   'action': 'Emitir', 'url': reverse('certificates') + '?emitir=' + course.slug})
    course_ids = [i['course'].id for i in items]
    session = (LiveSession.objects.filter(course_id__in=course_ids, ends_at__gte=now, starts_at__lte=now + timedelta(days=7))
               .select_related('course').order_by('starts_at').first())
    if session:
        candidates.append(_live_step(session, now))
    for post in (CommunityPost.objects.filter(author=user, has_unread_answer=True, is_hidden=False)
                 .select_related('course').order_by('-created_at')[:4]):
        candidates.append({'key': f'resp:{post.id}', 'icon': 'check', 'tone': 'task__icon--ok', 'title': 'O instrutor respondeu sua dúvida',
                           'meta': f'{post.course.title} · {post.title}' if post.course_id else post.title,
                           'badge_class': 'badge--success', 'badge': 'Nova resposta', 'action': 'Ler resposta',
                           'url': reverse('community') + f'?duvida={post.id}'})
    hidden = step_store.dismissed(profile)
    steps = [c for c in candidates if c['key'] not in hidden][:4]
    for step in steps:
        step['dom_id'] = 'step-' + step['key'].replace(':', '-')
    return steps


@login_required
def dashboard(request):
    if request.user.role != 'STUDENT':
        return redirect('painel:dashboard')
    user = request.user
    profile = user.student_profile
    now = timezone.now()
    enrollments = list(Enrollment.objects.filter(student=profile, is_active=True).exclude(course__status='archived')
                       .select_related('course__category').order_by('-enrolled_at'))
    course_ids = [e.course_id for e in enrollments]
    progress = _bulk_progress(user, profile, course_ids)
    week = dict(LiveSession.objects.filter(course_id__in=course_ids, ends_at__gte=now, starts_at__lte=now + timedelta(days=7))
                .values_list('course_id').annotate(n=Count('id')))

    items = []
    for enrollment in enrollments:
        info = progress[enrollment.course_id]
        total, done = info['total'], info['done']
        if total and done == total:
            status = 'concluido'
        elif done or info['started']:
            status = 'andamento'
        else:
            status = 'nao_iniciado'
        first = info['lessons'][0] if info['lessons'] else None
        if status == 'andamento' and info['resume_lesson']:
            target, action = info['resume_lesson'], 'Continuar'
        elif status == 'concluido':
            target, action = first, 'Rever aulas'
        else:
            target, action = first, 'Começar curso'
        url = reverse('lesson_detail', args=[enrollment.course.slug, target.id]) if target else reverse('course_home', args=[enrollment.course.slug])
        if status == 'concluido':
            label = f'Concluído · {total} aula' + ('' if total == 1 else 's')
        elif status == 'nao_iniciado':
            label = f'Não iniciado · {total} aula' + ('' if total == 1 else 's')
        else:
            label = f'{done} de {total} aula' + ('' if total == 1 else 's')
            if info['last_seen_at']:
                label += f' · visto há {_since(info["last_seen_at"])}'
        items.append({'course': enrollment.course, 'enrollment': enrollment, 'pct': info['pct'], 'done': done, 'total': total,
                      'status': status, 'last_seen_at': info['last_seen_at'], 'live_count': week.get(enrollment.course_id, 0),
                      'url': url, 'action': action, 'label': label, 'info': info})

    counts = {'todos': len(items), 'andamento': sum(i['status'] == 'andamento' for i in items),
              'nao_iniciados': sum(i['status'] == 'nao_iniciado' for i in items),
              'concluidos': sum(i['status'] == 'concluido' for i in items)}
    current_filter = request.GET.get('filtro') if request.GET.get('filtro') in FILTERS else 'todos'
    wanted = {'todos': None, 'andamento': 'andamento', 'nao_iniciados': 'nao_iniciado', 'concluidos': 'concluido'}[current_filter]
    shown = [i for i in items if wanted is None or i['status'] == wanted]

    resume = None
    candidates = [i for i in items if i['info']['last_seen_at'] and i['info']['resume_lesson'] and i['status'] != 'concluido']
    if candidates:
        best = max(candidates, key=lambda i: i['info']['last_seen_at'])
        lesson = best['info']['resume_lesson']
        lessons = best['info']['lessons']
        module_ids = list(dict.fromkeys(l.module_id for l in lessons))
        seconds = best['info']['resume_seconds']
        resume = {**best, 'lesson': lesson, 'seconds': seconds,
                  'module_number': module_ids.index(lesson.module_id) + 1,
                  'position': next(i for i, l in enumerate(lessons, 1) if l.id == lesson.id),
                  'watched_pct': min(100, round(100 * seconds / lesson.duration_seconds)) if lesson.duration_seconds else 0,
                  'url': reverse('lesson_detail', args=[best['course'].slug, lesson.id])}

    live_total = sum(week.values())
    parts = []
    if items:
        parts.append(f'{len(items)} curso' + ('' if len(items) == 1 else 's') + ' na sua conta')
    if counts['concluidos']:
        parts.append(f'{counts["concluidos"]} concluído' + ('' if counts['concluidos'] == 1 else 's'))
    if live_total:
        parts.append(f'{live_total} aula' + ('' if live_total == 1 else 's') + ' ao vivo esta semana')

    shop = Course.objects.filter(status='published').exclude(id__in=course_ids).select_related('category')
    return render(request, 'courses/dashboard.html', {
        'greeting': greeting(), 'summary': ' · '.join(parts), 'resume': resume,
        'steps': _build_steps(user, profile, items, now), 'courses': shown, 'all_courses': items,
        'filter': current_filter, 'filter_counts': counts, 'shop': shop,
    })


def _step_key_or_404(key):
    if not step_store.is_valid_key(key):
        raise Http404
    return key


@login_required
@require_POST
def step_dismiss(request, key):
    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Acesso negado.'}, status=403)
    step_store.dismiss(request.user.student_profile, _step_key_or_404(key))
    return JsonResponse({'ok': True})


@login_required
@require_POST
def step_restore(request, key):
    if request.user.role != 'STUDENT':
        return JsonResponse({'error': 'Acesso negado.'}, status=403)
    step_store.restore(request.user.student_profile, _step_key_or_404(key))
    return JsonResponse({'ok': True})


def active_enrollment(user, course):
    """Matrícula ativa do aluno no curso, ou None."""
    if getattr(user, 'role', '') != 'STUDENT':
        return None
    return Enrollment.objects.filter(student=user.student_profile, course=course, is_active=True).first()


@login_required
def course_home(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    if request.user.role != 'STUDENT':
        return redirect('course_preview', course_slug=course.slug)
    enrollment = active_enrollment(request.user, course)
    if enrollment is None or course.status == 'archived':
        raise Http404
    profile = request.user.student_profile
    now = timezone.now()

    module_rows = list(Module.objects.filter(course=course))
    lessons = list(Lesson.objects.filter(module__course=course, status='published').select_related('module')
                   .annotate(materials_count=Count('materials')).order_by('module__order', 'module_id', 'order', 'id'))
    records = {r.lesson_id: r for r in Progress.objects.filter(student=profile, lesson__in=lessons)}
    info = build_progress(lessons, records)
    resume_id = info['resume_lesson'].id if info['resume_lesson'] else None
    started = bool(records)

    by_module = {}
    for position, lesson in enumerate(lessons, 1):
        lesson.position = position
        by_module.setdefault(lesson.module_id, []).append(lesson)
    modules = []
    for module in module_rows:
        module_lessons = by_module.get(module.id)
        if not module_lessons:
            continue
        released = module.is_released_for(enrollment)
        release_on = None if released else module.release_on(enrollment)
        done_count = 0
        for lesson in module_lessons:
            record = records.get(lesson.id)
            if not released:
                lesson.state, lesson.meta = 'locked', f'Libera em {release_on:%d/%m}' if release_on else 'Bloqueada'
            elif record and record.is_completed:
                lesson.state, lesson.meta = 'done', 'Concluída'
                done_count += 1
            else:
                lesson.state = 'current' if lesson.id == resume_id else 'todo'
                lesson.meta = f'Você parou em {_mmss(record.position_seconds)}' if record and record.position_seconds > 0 else 'Não assistida'
        module.lessons_list = module_lessons
        module.total_count = len(module_lessons)
        module.done_count = done_count
        module.released = released
        module.release_on = release_on
        if not released:
            module.state = 'locked'
        elif done_count == len(module_lessons):
            module.state = 'done'
        elif done_count or any(records.get(l.id) for l in module_lessons):
            module.state = 'progress'
        else:
            module.state = 'todo'
        modules.append(module)
        module.number = len(modules)

    materials = list(LessonMaterial.objects.filter(lesson__module__course=course, lesson__status='published', lesson__deleted_at__isnull=True)
                     .select_related('lesson').order_by('lesson__module__order', 'lesson__order', 'order', 'id'))
    positions = {l.id: l.position for l in lessons}
    for material in materials:
        material.lesson_position = positions.get(material.lesson_id)
        try:
            material.file_size_label = filesizeformat(material.file.size) if material.file else ''
        except (OSError, ValueError):
            material.file_size_label = ''

    visible_posts = CommunityPost.objects.filter(course=course, is_hidden=False)
    posts = list(visible_posts.select_related('author__student_profile', 'lesson').order_by('-created_at')[:5])
    for post in posts:
        post.author_name = first_name(post.author)
        post.lesson_position = positions.get(post.lesson_id)
    live_sessions = list(LiveSession.objects.filter(course=course, ends_at__gte=now).order_by('starts_at')[:5])

    data_ok = bool(profile.full_name and profile.cpf)
    access_ok = enrollment.expires_at is None or enrollment.expires_at > now
    cert_reqs = [
        {'ok': info['total'] > 0 and info['remaining'] == 0, 'key': 'lessons'},
        {'ok': data_ok, 'key': 'data'},
        {'ok': enrollment.is_active and access_ok, 'key': 'access'},
    ]
    unlocked = [lesson for lesson in lessons if lesson.state != 'locked']
    pending = [lesson for lesson in unlocked if not (records.get(lesson.id) and records[lesson.id].is_completed)]
    if info['total'] and info['done'] == info['total']:
        action = {'label': 'Rever aulas', 'lesson': unlocked[0] if unlocked else None}
    elif started and pending:
        resume = info['resume_lesson'] if info['resume_lesson'] in pending else pending[0]
        action = {'label': 'Continuar', 'lesson': resume}
    else:
        action = {'label': 'Começar curso', 'lesson': pending[0] if pending else None}
    aba = request.GET.get('aba') if request.GET.get('aba') in ('conteudo', 'materiais', 'duvidas', 'ao-vivo') else 'conteudo'
    return render(request, 'courses/course_home.html', {
        'course': course, 'enrollment': enrollment, 'progress': info, 'modules': modules, 'materials': materials,
        'posts': posts, 'posts_count': visible_posts.count(), 'live_sessions': live_sessions, 'cert_reqs': cert_reqs,
        'total_seconds': sum(l.duration_seconds for l in lessons), 'lessons_total': len(lessons), 'action': action,
        'aba': aba, 'data_ok': data_ok, 'origin': ORIGIN_PHRASE.get(enrollment.source, ''),
    })
