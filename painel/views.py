import csv
import io
import json
import secrets
import urllib.parse
import urllib.request
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from email.utils import parseaddr

from django.contrib import messages
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
from core.crypto import encrypt
from core.decorators import painel_required
from courses.models import Category, Course, Enrollment, Lesson, LessonMaterial, Module, Progress
from courses.student_views import progress_info
from sales.models import Order
from users.models import CreatorProfile, SiteSettings
from users.models import FirstAccessCode
from users.first_access import issue_code
from users.validators import validate_cpf

User = get_user_model()


def access_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = request.build_absolute_uri(reverse('password_reset_confirm', args=[uid, token]))
    return send_mail('Seu acesso à CETREMER', f'Olá! Defina sua senha para acessar a CETREMER: {url}',
                     None, [user.email], fail_silently=False)


def report_access_delivery(request, sent):
    if not sent:
        messages.error(request, 'O e-mail de acesso não foi enviado. Confira as configurações de SMTP.')
    elif django_settings.DEBUG and not SiteSettings.load().email_host:
        messages.info(request, 'Link de acesso gerado no console do servidor local. Nenhum e-mail chegou à caixa de entrada.')
    else:
        messages.success(request, 'E-mail de acesso enviado.')


def page(request, template, **context):
    return render(request, 'painel/' + template + '.html', context)


@painel_required
def dashboard(request):
    now = timezone.now()
    paid = Order.objects.filter(status=Order.Status.COMPLETED, created_at__year=now.year, created_at__month=now.month)
    context = {'month_revenue': paid.aggregate(total=Sum('amount'))['total'] or 0,
        'month_paid_count': paid.count(),
        'students_count': User.objects.filter(student_profile__enrollments__isnull=False).distinct().count(),
        'active_enrollments': Enrollment.objects.count(),
        'courses_with_enrollments': Course.objects.filter(enrollments__isnull=False).distinct().count(),
        'pending_questions': sum(not p.is_answered for p in CommunityPost.objects.filter(is_hidden=False)),
        'recent_enrollments': Enrollment.objects.select_related('student__user', 'course').order_by('-enrolled_at')[:5],
        'recent_orders': Order.objects.select_related('student__user', 'course').order_by('-created_at')[:5]}
    return page(request, 'dashboard', **context)


@painel_required
def courses(request):
    qs = Course.objects.select_related('category').annotate(lessons_count=Count('modules__lessons', distinct=True), students_count=Count('enrollments', distinct=True))
    q = request.GET.get('q', '').strip()
    category = request.GET.get('categoria', '')
    if q: qs = qs.filter(Q(title__icontains=q) | Q(short_name__icontains=q))
    if category: qs = qs.filter(category__slug=category)
    return page(request, 'courses', courses=qs, categories=Category.objects.all(), q=q, category=category)


def _creator(user):
    profile = CreatorProfile.objects.filter(user=user).first()
    return profile or CreatorProfile.objects.first() or CreatorProfile.objects.create(user=user)


@painel_required
def course_edit(request, course_id=None):
    course = get_object_or_404(Course, pk=course_id) if course_id else None
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'Informe o título do curso.')
        elif request.POST.get('live_calendar_url') and urllib.parse.urlparse(request.POST['live_calendar_url']).hostname != 'calendar.google.com':
            messages.error(request, 'Use o link público de uma agenda do Google')
        else:
            if course is None:
                base = slugify(title) or 'curso'
                slug = base
                index = 2
                while Course.objects.filter(slug=slug).exists():
                    slug = f'{base}-{index}'; index += 1
                course = Course(slug=slug, creator=_creator(request.user))
            course.title = title
            course.description = request.POST.get('description', '')
            course.category = Category.objects.filter(pk=request.POST.get('category')).first()
            course.short_name = request.POST.get('short_name', '')[:12]
            course.cover_color = request.POST.get('cover_color', '')
            try: course.workload_hours = int(request.POST.get('workload_hours') or 0) or None
            except ValueError: course.workload_hours = None
            try: course.price = Decimal(request.POST.get('price') or '0')
            except InvalidOperation: course.price = Decimal('0')
            course.learning_objectives = '\n'.join(x.strip() for x in request.POST.getlist('objectives') if x.strip())
            course.target_audience = request.POST.get('target_audience', '')
            course.live_meet_url = request.POST.get('live_meet_url', '')
            course.live_calendar_url = request.POST.get('live_calendar_url', '')
            course.is_published = bool(request.POST.get('is_published'))
            if request.FILES.get('cover_image'): course.cover_image = request.FILES['cover_image']
            course.save()
            messages.success(request, 'Curso salvo com sucesso.')
            return redirect('painel:course_edit', course_id=course.id)
    return page(request, 'course_edit', course=course, categories=Category.objects.all(),
        modules_count=Module.objects.filter(course=course).count() if course else 0,
        lessons_count=Lesson.objects.filter(module__course=course).count() if course else 0,
        students_count=Enrollment.objects.filter(course=course).count() if course else 0)


def _vimeo_duration(url):
    try:
        endpoint = 'https://vimeo.com/api/oembed.json?' + urllib.parse.urlencode({'url': url})
        with urllib.request.urlopen(endpoint, timeout=5) as response:
            return int(json.load(response).get('duration') or 0)
    except Exception:
        return 0


@painel_required
def course_lessons(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        action = request.POST.get('action', 'save_lesson')
        module = Module.objects.filter(pk=request.POST.get('module_id'), course=course).first() if request.POST.get('module_id') else None
        if action == 'new_module':
            title = request.POST.get('title', '').strip()
            if title: Module.objects.create(course=course, title=title, order=Module.objects.filter(course=course).count()+1)
        elif action == 'rename_module' and module:
            module.title = request.POST.get('title', module.title).strip() or module.title
            module.save(update_fields=['title'])
        elif action in ('save_lesson', 'delete_lesson'):
            lesson = Lesson.objects.filter(pk=request.POST.get('lesson_id'), module__course=course).first() if request.POST.get('lesson_id') else None
            if action == 'delete_lesson' and lesson:
                lesson.delete()
            elif module and request.POST.get('title', '').strip():
                if lesson is None: lesson = Lesson(module=module, order=Lesson.objects.filter(module=module).count()+1)
                old_url = lesson.video_url
                lesson.module = module
                lesson.title = request.POST['title'].strip()
                lesson.video_url = request.POST.get('video_url', '').strip()
                lesson.description = request.POST.get('description', '')
                if request.POST.get('duration_minutes'):
                    try: lesson.duration_seconds = int(request.POST['duration_minutes']) * 60
                    except ValueError: pass
                if lesson.video_url != old_url and 'vimeo.com' in lesson.video_url:
                    lesson.duration_seconds = _vimeo_duration(lesson.video_url) or lesson.duration_seconds
                lesson.save()
                for file in request.FILES.getlist('materials'):
                    material = LessonMaterial(lesson=lesson, title=file.name, file=file)
                    material.full_clean()
                    material.save()
        messages.success(request, 'Alterações salvas.')
        return redirect('painel:course_lessons', course_id=course.id)
    modules = list(Module.objects.filter(course=course).prefetch_related('lessons__materials'))
    for module in modules:
        module.lessons_list = list(module.lessons.all())
        for lesson in module.lessons_list: lesson.material_count = len(lesson.materials.all())
    selected = Lesson.objects.filter(pk=request.GET.get('aula'), module__course=course).first() if request.GET.get('aula') else None
    new_module = Module.objects.filter(pk=request.GET.get('nova'), course=course).first() if request.GET.get('nova') else None
    return page(request, 'course_lessons', course=course, modules=modules, selected_lesson=selected, new_lesson_module=new_module)


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

@painel_required
def students(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        email = request.POST.get('email', '').strip()
        selected_id = request.POST.get('student_id')
        user = User.objects.filter(pk=selected_id, role=User.Role.STUDENT).first() if selected_id else User.objects.filter(email__iexact=email, role=User.Role.STUDENT).first()
        if action == 'enroll':
            course = get_object_or_404(Course, pk=request.POST.get('course_id'))
            if user is None and email and User.objects.filter(email__iexact=email).exists():
                messages.error(request, 'Este e-mail pertence a outra conta e não pode ser matriculado como aluno.')
            elif user is None and email:
                base = slugify(email.split('@')[0]) or 'aluno'; username = base; n = 2
                while User.objects.filter(username=username).exists(): username = f'{base}{n}'; n += 1
                user = User.objects.create(username=username, email=email, role=User.Role.STUDENT)
                user.set_unusable_password(); user.save(update_fields=['password'])
                user.student_profile.full_name = request.POST.get('full_name', '').strip()
                user.student_profile.save(update_fields=['full_name'])
            if user:
                Enrollment.objects.get_or_create(student=user.student_profile, course=course, defaults={'source': 'manual'})
                messages.success(request, 'Acesso liberado com sucesso.')
                if not user.has_usable_password() and not FirstAccessCode.objects.filter(user=user).exists():
                    code = issue_code(user)
                    messages.info(request, f'Código de primeiro acesso: {code}. Entregue este código ao aluno por um canal seguro. Ele expira em 7 dias e aparece apenas agora.')
                if request.POST.get('send_email'):
                    try:
                        sent = access_email(request, user)
                    except Exception:
                        sent = 0
                    report_access_delivery(request, sent)
        elif action == 'unenroll' and user:
            enrollment = Enrollment.objects.filter(student=user.student_profile, course_id=request.POST.get('course_id')).first()
            if enrollment and hasattr(enrollment, 'certificate'):
                messages.error(request, 'Este acesso tem certificado emitido e precisa ser preservado.')
            elif enrollment:
                enrollment.delete()
                messages.success(request, 'Acesso removido. O progresso foi mantido.')
        elif action == 'resend_access' and user:
            try:
                sent = access_email(request, user)
            except Exception:
                sent = 0
            report_access_delivery(request, sent)
        elif action == 'generate_first_access' and user:
            if user.has_usable_password():
                messages.error(request, 'Este aluno já tem senha. Use a recuperação de senha se necessário.')
            else:
                code = issue_code(user)
                messages.info(request, f'Código de primeiro acesso: {code}. Entregue este código ao aluno por um canal seguro. Ele expira em 7 dias e aparece apenas agora.')
        return redirect(reverse('painel:students') + (f'?aluno={user.id}' if user else ''))
    qs = User.objects.filter(role=User.Role.STUDENT).select_related('student_profile').annotate(courses_count=Count('student_profile__enrollments', distinct=True))
    q = request.GET.get('q', '').strip(); course_id = request.GET.get('curso', '')
    if q: qs = qs.filter(Q(email__icontains=q) | Q(username__icontains=q) | Q(student_profile__full_name__icontains=q) | Q(student_profile__cpf__icontains=q))
    if course_id: qs = qs.filter(student_profile__enrollments__course_id=course_id)
    from django.core.paginator import Paginator
    students_page = Paginator(qs.order_by('id'), 25).get_page(request.GET.get('page'))
    for user in students_page:
        first = user.student_profile.enrollments.select_related('course').order_by('enrolled_at').first()
        user.first_enrollment_source = first.get_source_display() if first else ''
    selected = User.objects.filter(pk=request.GET.get('aluno'), role=User.Role.STUDENT).first() if request.GET.get('aluno') else None
    if selected:
        selected.enrollment_items = [progress_info(selected.student_profile, e.course) for e in Enrollment.objects.filter(student=selected.student_profile).select_related('course')]
        selected.available_courses = Course.objects.exclude(enrollments__student=selected.student_profile)
    return page(request, 'students', students=students_page, selected=selected, courses=Course.objects.all(), q=q)


@painel_required
def students_export(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="alunos.csv"'
    writer = csv.writer(response); writer.writerow(['nome', 'email', 'cpf', 'cursos'])
    for user in User.objects.filter(role=User.Role.STUDENT).select_related('student_profile').prefetch_related('student_profile__enrollments__course'):
        p = user.student_profile
        writer.writerow([p.full_name or '', user.email, p.cpf or '', ', '.join(e.course.title for e in p.enrollments.all())])
    return response


NAME_HEADERS = {'nome', 'name', 'nome completo', 'cliente', 'comprador', 'nome do comprador', 'nome do cliente'}
EMAIL_HEADERS = {'email', 'e-mail', 'email do comprador', 'email do cliente'}
CPF_HEADERS = {'cpf', 'documento', 'cpf/cnpj', 'documento do comprador'}


def _header(value):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFKD', value.lower().strip()) if not unicodedata.combining(c))


def _parse_csv(upload):
    raw = upload.read()
    try: text = raw.decode('utf-8-sig')
    except UnicodeDecodeError: text = raw.decode('latin-1')
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=',;')
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = {_header(h): h for h in (reader.fieldnames or [])}
    def key(choices): return next((headers.get(_header(c)) for c in choices if _header(c) in headers), None)
    name_key, email_key, cpf_key = key(NAME_HEADERS), key(EMAIL_HEADERS), key(CPF_HEADERS)
    if not email_key: raise ValueError('Coluna de e-mail ausente.')
    rows = []; seen = set()
    for row in reader:
        if len(rows) >= 5000: break
        email = (row.get(email_key) or '').strip().lower()
        name = (row.get(name_key) or '').strip() if name_key else ''
        cpf = (row.get(cpf_key) or '').strip() if cpf_key else ''
        status = 'Novo aluno'
        if not email or '@' not in parseaddr(email)[1] or parseaddr(email)[1] != email: status = 'E-mail inválido'
        elif email in seen: status = 'E-mail repetido no arquivo'
        elif User.objects.filter(email__iexact=email, role=User.Role.STUDENT).exists(): status = 'Já cadastrado'
        elif User.objects.filter(email__iexact=email).exists(): status = 'E-mail já usado por outra conta'
        seen.add(email)
        if cpf:
            try: cpf = validate_cpf(cpf)
            except Exception: cpf = ''
        rows.append({'name': name, 'email': email, 'cpf': cpf, 'status': status})
    return rows


@painel_required
def students_import(request):
    preview = request.session.get('import_preview')
    if request.method == 'POST' and request.POST.get('action') == 'confirm':
        if not preview: messages.error(request, 'Leia o arquivo antes de confirmar.')
        else:
            new_count = old_count = 0
            course_ids = preview['course_ids']
            with transaction.atomic():
                for row in preview['rows']:
                    if row['status'] not in ('Novo aluno', 'Já cadastrado'): continue
                    user = User.objects.filter(email__iexact=row['email'], role=User.Role.STUDENT).first()
                    if user is None:
                        base = slugify(row['email'].split('@')[0]) or 'aluno'; username = base; n = 2
                        while User.objects.filter(username=username).exists(): username = f'{base}{n}'; n += 1
                        user = User.objects.create(username=username, email=row['email'], role=User.Role.STUDENT)
                        user.set_unusable_password(); user.save(update_fields=['password']); new_count += 1
                    else: old_count += 1
                    profile = user.student_profile
                    if not profile.full_name: profile.full_name = row['name']
                    if not profile.cpf: profile.cpf = row['cpf']
                    profile.save()
                    for cid in course_ids: Enrollment.objects.get_or_create(student=profile, course_id=cid, defaults={'source': 'import'})
                    if request.POST.get('send_email'): access_email(request, user)
            del request.session['import_preview']
            messages.success(request, f'{new_count} alunos importados. {old_count} já existiam e receberam os cursos.')
            return redirect('painel:students')
    elif request.method == 'POST':
        course_ids = [int(x) for x in request.POST.getlist('courses') if x.isdigit()]
        course_ids = list(Course.objects.filter(id__in=course_ids).values_list('id', flat=True))
        upload = request.FILES.get('file')
        if not course_ids or not upload: messages.error(request, 'Escolha um curso e um arquivo CSV.')
        else:
            try: rows = _parse_csv(upload)
            except (ValueError, UnicodeDecodeError, csv.Error) as exc: messages.error(request, f'Arquivo inválido: {exc}')
            else:
                preview = {'rows': rows, 'course_ids': course_ids}
                request.session['import_preview'] = preview
    summary = {'new': 0, 'existing': 0, 'error': 0}
    if preview:
        for row in preview['rows']:
            if row['status'] == 'Novo aluno': summary['new'] += 1
            elif row['status'] == 'Já cadastrado': summary['existing'] += 1
            else: summary['error'] += 1
    return page(request, 'students_import', courses=Course.objects.all(), preview=preview, summary=summary)

@painel_required
def orders(request):
    qs = Order.objects.select_related('student__user', 'course').order_by('-created_at')
    q = request.GET.get('q', '').strip(); status = request.GET.get('status', '')
    period = request.GET.get('periodo', '30d')
    now = timezone.now()
    if q: qs = qs.filter(Q(student__user__email__icontains=q) | Q(course__title__icontains=q))
    if status: qs = qs.filter(status=status)
    if period == 'mes': qs = qs.filter(created_at__year=now.year, created_at__month=now.month)
    elif period == 'anterior':
        last = (now.replace(day=1) - timedelta(days=1))
        qs = qs.filter(created_at__year=last.year, created_at__month=last.month)
    else: qs = qs.filter(created_at__gte=now-timedelta(days=30))
    paid_total = qs.filter(status=Order.Status.COMPLETED).aggregate(total=Sum('amount'))['total'] or 0
    from django.core.paginator import Paginator
    return page(request, 'orders', orders=Paginator(qs, 25).get_page(request.GET.get('page')),
        paid_total=paid_total, pending_count=qs.filter(status=Order.Status.PENDING).count(),
        failed_count=qs.filter(status=Order.Status.FAILED).count(), q=q, status=status, period=period)


@painel_required
def orders_export(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="pedidos.csv"'
    writer = csv.writer(response); writer.writerow(['data', 'aluno', 'curso', 'forma', 'valor', 'status'])
    for order in Order.objects.select_related('student__user', 'course').order_by('-created_at'):
        writer.writerow([timezone.localtime(order.created_at).strftime('%d/%m/%Y %H:%M'), order.student.user.email,
            order.course.title, order.get_payment_method_display(), str(order.amount), order.get_status_display()])
    return response


@painel_required
def community(request):
    if request.method == 'POST':
        post = get_object_or_404(CommunityPost, pk=request.POST.get('post_id'))
        action = request.POST.get('action')
        if action == 'reply' and request.POST.get('content', '').strip():
            Comment.objects.create(post=post, author=request.user, content=request.POST['content'].strip())
            messages.success(request, 'Resposta publicada.')
        elif action == 'hide': post.is_hidden = True; post.save(update_fields=['is_hidden']); messages.success(request, 'Tópico ocultado.')
        elif action == 'show': post.is_hidden = False; post.save(update_fields=['is_hidden']); messages.success(request, 'Tópico publicado.')
        return redirect(reverse('painel:community') + '?aba=' + request.GET.get('aba', 'pendentes'))
    tab = request.GET.get('aba', 'pendentes')
    posts = CommunityPost.objects.select_related('author', 'course', 'lesson').prefetch_related('comments__author')
    if tab == 'ocultos': posts = posts.filter(is_hidden=True)
    elif tab == 'respondidos': posts = [p for p in posts.filter(is_hidden=False) if p.is_answered]
    else: posts = [p for p in posts.filter(is_hidden=False) if not p.is_answered]
    pending_count = sum(not p.is_answered for p in CommunityPost.objects.filter(is_hidden=False))
    return page(request, 'community', posts=posts, tab=tab, pending_count=pending_count)


@painel_required
def settings(request):
    site = SiteSettings.load()
    if request.method == 'POST':
        for field in ('school_name', 'whatsapp', 'terms_url', 'privacy_url', 'gateway_name',
                      'email_from_name', 'email_from', 'email_host', 'email_username', 'signer_name', 'signer_role'):
            if field in request.POST: setattr(site, field, request.POST[field].strip())
        try: site.email_port = int(request.POST.get('email_port') or 587)
        except ValueError: site.email_port = 587
        site.gateway_sandbox = bool(request.POST.get('gateway_sandbox'))
        site.email_use_tls = bool(request.POST.get('email_use_tls'))
        for field in ('logo', 'signature_image'):
            if request.FILES.get(field): setattr(site, field, request.FILES[field])
        if request.POST.get('gateway_key'): site.gateway_key_encrypted = encrypt(request.POST['gateway_key'])
        if request.POST.get('email_password'): site.email_password_encrypted = encrypt(request.POST['email_password'])
        site.save()
        if request.POST.get('action') == 'test_email':
            try:
                count = send_mail('Teste de e-mail CETREMER', 'Configuração de e-mail funcionando.', None,
                                  [request.user.email], fail_silently=False)
                if count: messages.success(request, 'E-mail de teste enviado.')
                else: messages.error(request, 'SMTP não configurado.')
            except Exception as exc: messages.error(request, f'Erro no SMTP: {exc}')
        else: messages.success(request, 'Configurações salvas.')
        return redirect('painel:settings')
    from core.crypto import decrypt
    last4 = decrypt(site.gateway_key_encrypted)[-4:] if site.gateway_key_encrypted else None
    return page(request, 'settings', site=site, gateway_key_last4=last4,
        email_password_set=bool(site.email_password_encrypted))
