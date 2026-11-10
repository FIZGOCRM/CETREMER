"""Alunos (HANDOFF-v2 8.6), matrícula, ficha do aluno (8.7), ações, anotações e exportação."""
import csv
import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.ajax import json_error, json_ok, wants_json
from core.decorators import painel_required
from core.models import ActivityLog
from core.toasts import toast
from courses.models import Certificate, Course, Enrollment, Lesson, Module, Progress
from sales.models import Order
from users.display import full_name
from users.first_access import issue_code
from users.models import FirstAccessCode
from users.validators import validate_cpf

from . import students_stats
from .access import access_email, create_student, grant, report_access_delivery, try_access_email

User = get_user_model()
PAGE_SIZE = 25
BULK_CONFIRM = 'REMOVER'
TABS = ('cursos', 'pedidos', 'certificados', 'atividade')


def _label(course):
    return course.short_name or course.title


def _students_url(**params):
    base = reverse('painel:students')
    query = '&'.join(f'{k}={v}' for k, v in params.items() if v)
    return f'{base}?{query}' if query else base


def _safe_next(request, default):
    target = request.POST.get('next', '')
    return target if target.startswith(reverse('painel:students')) else default


# ------------------------------------------------------------------ Lista


@painel_required
def students(request):
    if request.method == 'POST':
        return _bulk(request)
    name = request.GET.get('filtro', 'todos')
    if name not in students_stats.FILTERS:
        name = 'todos'
    q = request.GET.get('q', '').strip()
    course_param = request.GET.get('curso', '')
    course = Course.objects.filter(pk=course_param).first() if course_param.isdigit() else Course.objects.filter(slug=course_param).first() if course_param else None
    qs = students_stats.filtered(name)
    if q:
        digits = re.sub(r'\D', '', q)
        cond = Q(email__icontains=q) | Q(student_profile__full_name__icontains=q) | Q(student_profile__display_name__icontains=q)
        if len(digits) >= 3:
            cond |= Q(student_profile__cpf__contains=digits)
        qs = qs.filter(cond)
    if course:
        qs = qs.filter(student_profile__enrollments__course=course, student_profile__enrollments__is_active=True)
    qs = qs.distinct().order_by('student_profile__full_name', 'email')
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get('pagina'))
    profiles = [user.student_profile for user in page]
    info = students_stats.summaries(profiles)
    rows = [{'user': user, 'profile': user.student_profile, 'name': full_name(user), **info[user.student_profile.id]} for user in page]
    counts = {key.replace('-', '_'): value for key, value in students_stats.filter_counts().items()}
    totals = students_stats.totals_line()
    return render(request, 'painel/students.html', {
        'rows': rows, 'page': page, 'q': q, 'course': course, 'filtro': name, 'counts': counts, 'totals': totals,
        'courses': Course.objects.exclude(status='archived').order_by('title'), 'filtered': bool(q or course or name != 'todos'),
        'has_any': totals['students'] > 0, 'next_url': request.get_full_path(),
    })


def _course_for_bulk(post, key='course'):
    return Course.objects.filter(pk=post.get(key) or None).first()


def _bulk(request):
    back = _safe_next(request, reverse('painel:students'))
    action = request.POST.get('action', '')
    ids = [int(i) for i in request.POST.getlist('ids') if i.isdigit()]
    users = list(User.objects.filter(pk__in=ids, role=User.Role.STUDENT).select_related('student_profile'))
    if not users:
        toast(request, 'Selecione pelo menos um aluno.', level='error')
        return redirect(back)
    if action == 'export':
        return _export(users)
    failures = []
    if action == 'resend':
        sent = 0
        for user in users:
            if try_access_email(request, user):
                sent += 1
            else:
                failures.append((user.email, 'E-mail de acesso não enviado'))
        toast(request, f"Acesso reenviado para {sent} {'aluno' if sent == 1 else 'alunos'}", level='success' if sent else 'error')
    elif action in ('enroll', 'unenroll'):
        course = _course_for_bulk(request.POST, 'course' if action == 'enroll' else 'remove_course')
        if course is None:
            toast(request, 'Escolha um curso.', level='error')
            return redirect(back)
        label = _label(course)
        if action == 'enroll':
            done = 0
            for user in users:
                grant(user, course, actor=request.user)
                done += 1
            toast(request, f"{done} {'aluno recebeu' if done == 1 else 'alunos receberam'} o {label}")
        else:
            if request.POST.get('confirmar', '').strip().upper() != BULK_CONFIRM:
                toast(request, f'Digite {BULK_CONFIRM} para confirmar a remoção de acesso.', level='error')
                return redirect(back)
            removed = 0
            for user in users:
                enrollment = Enrollment.objects.filter(student=user.student_profile, course=course, is_active=True).first()
                if enrollment is None:
                    failures.append((user.email, f'Não tinha acesso ao {label}'))
                    continue
                enrollment.is_active = False
                enrollment.save(update_fields=['is_active'])
                removed += 1
                if request.POST.get('notify'):
                    _mail_removed(user, course)
            toast(request, f"{removed} {'aluno perdeu' if removed == 1 else 'alunos perderam'} o acesso ao {label}. O progresso foi guardado.")
    else:
        toast(request, 'Ação inválida.', level='error')
        return redirect(back)
    if failures:
        request.session['bulk_failures'] = failures
        toast(request, f"{len(failures)} {'aluno falhou' if len(failures) == 1 else 'alunos falharam'}.", level='error',
              action=('Baixar relatório', reverse('painel:students_report')))
    return redirect(back)


def _mail_removed(user, course):
    try:
        send_mail(f'Seu acesso ao {course.title} foi removido',
                  f'Olá! Seu acesso ao curso {course.title} foi removido pela equipe da CETREMER. '
                  'Se isso for um engano, responda este e-mail.', None, [user.email], fail_silently=True)
    except Exception:
        pass


def _export(users):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="alunos.csv"'
    writer = csv.writer(response)
    writer.writerow(['nome', 'email', 'cpf', 'cursos'])
    for user in users:
        profile = user.student_profile
        courses = ', '.join(e.course.title for e in profile.enrollments.filter(is_active=True).select_related('course'))
        writer.writerow([profile.full_name or '', user.email, profile.cpf or '', courses])
    return response


@painel_required
def students_export(request):
    users = students_stats.students().prefetch_related('student_profile__enrollments__course')
    return _export(users)


@painel_required
def students_report(request):
    rows = request.session.pop('bulk_failures', [])
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="relatorio-acao-em-massa.csv"'
    writer = csv.writer(response)
    writer.writerow(['email', 'motivo'])
    writer.writerows(rows)
    return response


# ------------------------------------------------------------------ Matrícula (diálogo)


def _field_error(request, field, message, back):
    if wants_json(request):
        return JsonResponse({'ok': False, 'errors': {field: [message]}, 'error': message}, status=400)
    toast(request, message, level='error')
    return redirect(back)


@painel_required
@require_POST
def student_enroll(request):
    back = request.META.get('HTTP_REFERER') or reverse('painel:students')
    if not back.startswith(('/', 'http')):
        back = reverse('painel:students')
    email = request.POST.get('email', '').strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        return _field_error(request, 'email', 'Informe um e-mail válido.', back)
    course = Course.objects.filter(pk=request.POST.get('course') or None).first()
    if course is None:
        return _field_error(request, 'course', 'Escolha um curso.', back)
    user = User.objects.filter(email__iexact=email).first()
    if user is not None and user.role != User.Role.STUDENT:
        return _field_error(request, 'email', 'Este e-mail pertence a outra conta e não pode ser matriculado como aluno.', back)
    created_user = user is None
    if created_user:
        user = create_student(email, request.POST.get('full_name', '').strip())
    new_access = grant(user, course, actor=request.user)
    label = _label(course)
    sent = False
    if request.POST.get('send_email'):
        sent = try_access_email(request, user)
        if not sent:
            report_access_delivery(request, False)
    if not user.has_usable_password() and not FirstAccessCode.objects.filter(user=user).exists():
        code = issue_code(user)
        toast(request, f'Código de primeiro acesso: {code}. Entregue este código ao aluno por um canal seguro. Ele expira em 7 dias e aparece apenas agora.', level='info')
    if not new_access:
        toast(request, f'{full_name(user)} já tem acesso ao {label}.', level='info')
    elif sent:
        toast(request, f'Curso liberado. E-mail enviado para {email}')
    else:
        toast(request, 'Curso liberado')
    url = reverse('painel:student_detail', args=[user.id])
    return json_ok(redirect=url) if wants_json(request) else redirect(url)


# ------------------------------------------------------------------ Ficha


def _lesson_rows(profile, enrollment):
    modules = list(Module.objects.filter(course=enrollment.course).prefetch_related('lessons'))
    progress = {p.lesson_id: p for p in Progress.objects.filter(student=profile, lesson__module__course=enrollment.course)}
    rows, done, total = [], 0, 0
    for module in modules:
        for lesson in module.lessons.all():
            record = progress.get(lesson.id)
            published = lesson.status == 'published'
            completed = bool(record and record.is_completed)
            if published:
                total += 1
                done += 1 if completed else 0
            rows.append({'lesson': lesson, 'module': module, 'published': published, 'completed': completed,
                         'when': record.updated_at if completed else None})
    return rows, done, total


def course_block(profile, enrollment):
    rows, done, total = _lesson_rows(profile, enrollment)
    return {'enrollment': enrollment, 'course': enrollment.course, 'rows': rows, 'done': done, 'total': total,
            'pct': min(round(done / total * 100), 100) if total else 0}


def _detail_context(request, user, aba):
    profile = user.student_profile
    enrollments = list(Enrollment.objects.filter(student=profile).select_related('course').order_by('enrolled_at'))
    blocks = [course_block(profile, e) for e in enrollments]
    orders = list(Order.objects.filter(student=profile).select_related('course').order_by('-created_at'))
    certificates = list(Certificate.objects.filter(enrollment__student=profile).select_related('enrollment__course').order_by('-issued_at'))
    activity = list(ActivityLog.objects.filter(student=user).order_by('-created_at')[:30])
    info = students_stats.summaries([profile])[profile.id]
    source = enrollments[0].get_source_display() if enrollments else ''
    active_ids = {e.course_id for e in enrollments if e.is_active}
    return {
        'student': user, 'profile': profile, 'name': full_name(user), 'aba': aba, 'blocks': blocks, 'orders': orders,
        'certificates': certificates, 'activity': activity, 'status': info['status'], 'last_seen': info['last_seen'],
        'source': source, 'courses_open': Course.objects.exclude(status='archived').exclude(pk__in=active_ids).order_by('title'),
        'has_password': user.has_usable_password(),
        'missing_cpf': not profile.cpf, 'missing_name': not (profile.full_name or '').strip(),
        'counts': {'cursos': sum(1 for e in enrollments if e.is_active), 'pedidos': len(orders),
                   'certificados': len(certificates), 'atividade': len(activity)},
    }


@painel_required
def student_detail(request, student_id):
    user = get_object_or_404(students_stats.students(), pk=student_id)
    aba = request.GET.get('aba', 'cursos')
    if aba not in TABS:
        aba = 'cursos'
    return render(request, 'painel/student_detail.html', _detail_context(request, user, aba))


def _arg(request, key, default=''):
    return request.POST.get(key) or request.GET.get(key) or default


def _done(request, url):
    return json_ok(redirect=url) if wants_json(request) else redirect(url)


@painel_required
@require_POST
def student_action(request, student_id):
    user = get_object_or_404(students_stats.students(), pk=student_id)
    profile = user.student_profile
    action = _arg(request, 'action')
    aba = _arg(request, 'aba', 'cursos')
    back = reverse('painel:student_detail', args=[user.id]) + (f'?aba={aba}' if aba != 'cursos' else '')
    name = full_name(user)

    if action in ('resend_access', 'reset_password'):
        if try_access_email(request, user):
            toast(request, f'E-mail de acesso enviado para {user.email}' if action == 'resend_access'
                  else f'Link para criar nova senha enviado para {user.email}')
        else:
            report_access_delivery(request, False)
        return _done(request, back)

    if action == 'generate_first_access':
        if user.has_usable_password():
            toast(request, 'Este aluno já tem senha. Use o link para criar nova senha.', level='error')
        else:
            code = issue_code(user)
            toast(request, f'Código de primeiro acesso: {code}. Entregue este código ao aluno por um canal seguro. Ele expira em 7 dias e aparece apenas agora.', level='info')
        return _done(request, back)

    if action == 'request_data':
        link = request.build_absolute_uri(reverse('settings') + '?secao=certificado')
        try:
            send_mail('Complete seus dados na CETREMER',
                      f'Olá! Para emitir seu certificado precisamos do seu nome completo e CPF. Preencha em Minha conta: {link}',
                      None, [user.email], fail_silently=False)
            toast(request, f'Pedido enviado para {user.email}')
        except Exception:
            toast(request, 'O e-mail não foi enviado. Confira as configurações de SMTP.', level='error')
        return _done(request, back)

    if action == 'edit':
        return _edit(request, user, back)

    course = Course.objects.filter(pk=_arg(request, 'course_id') or None).first()
    if action == 'unenroll':
        enrollment = Enrollment.objects.filter(student=profile, course=course, is_active=True).first() if course else None
        if enrollment is None:
            return json_error('Este aluno não tem acesso a esse curso.') if wants_json(request) else (toast(request, 'Este aluno não tem acesso a esse curso.', level='error') or redirect(back))
        enrollment.is_active = False
        enrollment.save(update_fields=['is_active'])
        if request.POST.get('notify'):
            _mail_removed(user, course)
        toast(request, 'Acesso removido. O progresso foi mantido.')
        return _done(request, back)

    if action == 'reset_progress':
        if course is None:
            return json_error('Curso inválido.') if wants_json(request) else redirect(back)
        removed, _ = Progress.objects.filter(student=profile, lesson__module__course=course).delete()
        toast(request, f'Progresso de {name} zerado no {_label(course)}')
        return _done(request, back)

    if action == 'toggle_lesson':
        return _toggle_lesson(request, user, name, back)
    return json_error('Ação inválida.') if wants_json(request) else (toast(request, 'Ação inválida.', level='error') or redirect(back))


def _toggle_lesson(request, user, name, back):
    profile = user.student_profile
    lesson = Lesson.objects.filter(pk=_arg(request, 'lesson') or None, status='published').select_related('module__course').first()
    enrollment = Enrollment.objects.filter(student=profile, course=lesson.module.course).first() if lesson else None
    if lesson is None or enrollment is None:
        return json_error('Aula inválida.') if wants_json(request) else redirect(back)
    record, created = Progress.objects.get_or_create(student=profile, lesson=lesson)
    record.is_completed = True if created else not record.is_completed
    record.save(update_fields=['is_completed', 'completed_at', 'updated_at'])
    undo = f"{reverse('painel:student_action', args=[user.id])}?action=toggle_lesson&lesson={lesson.id}&desfazer=1"
    text = f'Aula marcada como concluída para {name}' if record.is_completed else f'Aula desmarcada para {name}'
    if request.GET.get('desfazer') == '1':
        toast(request, 'Alteração desfeita')
        return _done(request, back)
    if wants_json(request):
        block = course_block(profile, enrollment)
        from django.template.loader import render_to_string
        html = render_to_string('painel/_student_course_progress.html', {'block': block, 'student': user, 'open': True}, request=request)
        return json_ok(toast=text, undo_url=undo, replace={f'#scourse-progress-{enrollment.course_id}': html})
    toast(request, text, undo_url=undo)
    return redirect(back)


def _edit(request, user, back):
    profile = user.student_profile
    errors = {}
    name = request.POST.get('full_name', '').strip()
    email = request.POST.get('email', '').strip().lower()
    cpf = request.POST.get('cpf', '').strip()
    try:
        validate_email(email)
    except ValidationError:
        errors['email'] = 'Informe um e-mail válido.'
    else:
        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            errors['email'] = 'Este e-mail já está em uso em outra conta.'
    if cpf:
        try:
            cpf = validate_cpf(cpf)
        except ValidationError:
            errors['cpf'] = 'CPF inválido. Confira os números.'
    if len(name) > 255:
        errors['full_name'] = 'Use até 255 caracteres no nome.'
    if errors:
        if wants_json(request):
            total = len(errors)
            return JsonResponse({'ok': False, 'errors': {k: [v] for k, v in errors.items()},
                                 'error': 'Corrija 1 campo para salvar.' if total == 1 else f'Corrija {total} campos para salvar.'}, status=400)
        toast(request, next(iter(errors.values())), level='error')
        return redirect(back)
    profile.full_name = name
    profile.cpf = cpf or None
    profile.save(update_fields=['full_name', 'cpf'])
    if email != user.email:
        user.email = email
        user.save(update_fields=['email'])
    toast(request, 'Dados salvos')
    return _done(request, back)


@painel_required
@require_POST
def student_notes(request, student_id):
    user = get_object_or_404(students_stats.students(), pk=student_id)
    profile = user.student_profile
    profile.staff_notes = request.POST.get('notes', '')[:5000]
    profile.save(update_fields=['staff_notes'])
    return JsonResponse({'ok': True})
