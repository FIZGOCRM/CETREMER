"""Importar alunos em 4 passos (HANDOFF-v2 8.8): Arquivo, Colunas, Cursos, Revisar. O estado fica na sessão; o passo vai em `?passo=`."""
import csv
import io
import unicodedata
from email.utils import parseaddr

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.functions import Lower
from django.shortcuts import redirect, render
from django.urls import reverse

from core.activity import log
from core.decorators import painel_required
from core.toasts import toast
from courses.models import Course
from users.validators import validate_cpf

from .access import create_student, grant, try_access_email

User = get_user_model()
SESSION_KEY = 'student_import'
MAX_ROWS = 5000
MAX_BYTES = 5 * 1024 * 1024
ORIGINS = (('eduzz', 'Eduzz'), ('hotmart', 'Hotmart'), ('outra', 'Outra planilha'))
ROLES = (('name', 'Nome completo'), ('email', 'E-mail'), ('cpf', 'CPF'), ('order', 'Código do pedido'), ('ignore', 'Ignorar'))
STEPS = ('Arquivo', 'Colunas', 'Cursos', 'Revisar')

HEADER_SETS = {
    'name': {'nome', 'name', 'nome completo', 'cliente', 'comprador', 'nome do comprador', 'nome do cliente'},
    'email': {'email', 'e-mail', 'email do comprador', 'email do cliente'},
    'cpf': {'cpf', 'documento', 'cpf/cnpj', 'documento do comprador'},
    'order': {'codigo do pedido', 'pedido', 'id do pedido', 'transacao', 'codigo da transacao', 'fatura', 'cod. fatura', 'codigo da fatura'},
}
STATUS_TEXT = {
    'invalid': 'E-mail inválido', 'duplicate': 'E-mail repetido no arquivo', 'other_account': 'E-mail já usado por outra conta',
}


def _norm(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', (value or '').lower().strip()) if not unicodedata.combining(c))


def parse_upload(upload):
    """Lê o CSV e devolve (cabeçalhos, linhas). Levanta ValueError com a mensagem para a pessoa."""
    raw = upload.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('O arquivo passa de 5 MB. Divida a planilha em partes.')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('latin-1')
    if not text.strip():
        raise ValueError('O arquivo está vazio.')
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=',;\t')
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect=dialect)
    try:
        headers = [h.strip() for h in next(reader)]
    except StopIteration:
        raise ValueError('O arquivo está vazio.')
    if len(headers) < 2 and not any(headers):
        raise ValueError('Não encontramos as colunas do arquivo.')
    rows = []
    for row in reader:
        if not any(cell.strip() for cell in row):
            continue
        rows.append([cell.strip() for cell in row] + [''] * (len(headers) - len(row)))
        if len(rows) >= MAX_ROWS:
            break
    if not rows:
        raise ValueError('O arquivo não tem nenhuma linha de alunos.')
    return headers, rows


def guess_mapping(headers):
    mapping, used = {}, set()
    for index, header in enumerate(headers):
        role = next((r for r, names in HEADER_SETS.items() if _norm(header) in names and r not in used), 'ignore')
        if role != 'ignore':
            used.add(role)
        mapping[str(index)] = role
    return mapping


def evaluate(rows, mapping):
    """Classifica cada linha: new, existing (já é aluno) ou ignorada (invalid, duplicate, other_account)."""
    index = {role: int(col) for col, role in mapping.items() if role != 'ignore'}
    parsed = []
    for line, row in enumerate(rows, 2):
        parsed.append({
            'line': line, 'email': (row[index['email']] if 'email' in index else '').strip().lower(),
            'name': row[index['name']].strip() if 'name' in index else '', 'cpf': row[index['cpf']].strip() if 'cpf' in index else '',
            'order': row[index['order']].strip()[:40] if 'order' in index else '', 'note': '',
        })
    emails = {r['email'] for r in parsed if r['email']}
    by_email = {u.email.lower(): u for u in User.objects.annotate(lowered=Lower('email')).filter(lowered__in=emails)}
    seen = set()
    for r in parsed:
        email = r['email']
        address = parseaddr(email)[1]
        user = by_email.get(email)
        if not email or '@' not in address or address != email:
            r['status'] = 'invalid'
        elif email in seen:
            r['status'] = 'duplicate'
        elif user is not None and user.role != User.Role.STUDENT:
            r['status'] = 'other_account'
        elif user is not None:
            r['status'] = 'existing'
        else:
            r['status'] = 'new'
        seen.add(email)
        if r['cpf']:
            try:
                r['cpf'] = validate_cpf(r['cpf'])
            except Exception:
                r['cpf'] = ''
                r['note'] = 'CPF inválido, não será importado'
    return parsed


def summarize(parsed):
    counts = {'new': 0, 'existing': 0, 'invalid': 0, 'duplicate': 0, 'other_account': 0}
    for r in parsed:
        counts[r['status']] += 1
    ignored = counts['invalid'] + counts['duplicate'] + counts['other_account']
    problems = [r for r in parsed if r['status'] in STATUS_TEXT or r['note']]
    for r in problems:
        r['reason'] = STATUS_TEXT.get(r['status'], r['note'])
    return {**counts, 'ignored': ignored, 'total_ok': counts['new'] + counts['existing'], 'problems': problems[:50],
            'problems_total': len(problems)}


def _state(request):
    return request.session.get(SESSION_KEY)


def _allowed_step(state):
    if not state:
        return 1
    if not state.get('mapped'):
        return 2
    if not state.get('course_ids'):
        return 3
    return 4


def _go(step):
    return redirect(reverse('painel:students_import') + (f'?passo={step}' if step != 1 else ''))


@painel_required
def students_import(request):
    state = _state(request)
    allowed = _allowed_step(state)
    try:
        step = int(request.GET.get('passo', allowed if request.method == 'GET' and state else 1))
    except ValueError:
        step = 1
    step = min(max(step, 1), allowed)

    if request.method == 'POST':
        return _handle_post(request, state, step)

    context = {'step': step, 'steps': list(enumerate(STEPS, 1)), 'origins': ORIGINS, 'state': state, 'roles': ROLES,
               'courses': Course.objects.exclude(status='archived').order_by('title')}
    if state:
        headers = state['headers']
        sample = state['rows'][0] if state['rows'] else []
        context['columns'] = [{'index': i, 'header': h or f'Coluna {i + 1}', 'example': sample[i] if i < len(sample) else '',
                               'role': state['mapping'].get(str(i), 'ignore')} for i, h in enumerate(headers)]
        context['recognized'] = sum(1 for c in context['columns'] if c['role'] != 'ignore')
        context['total_columns'] = len(headers)
    if state and step == 4:
        parsed = evaluate(state['rows'], state['mapping'])
        context['summary'] = summarize(parsed)
        context['selected_courses'] = list(Course.objects.filter(pk__in=state['course_ids']))
    return render(request, 'painel/students_import.html', context)


def _handle_post(request, state, step):
    if request.POST.get('action') == 'restart':
        request.session.pop(SESSION_KEY, None)
        return _go(1)
    if step == 1:
        return _post_file(request)
    if state is None:
        return _go(1)
    if step == 2:
        return _post_columns(request, state)
    if step == 3:
        return _post_courses(request, state)
    return _post_confirm(request, state)


def _post_file(request):
    origin = request.POST.get('origin', 'outra')
    origin = origin if origin in dict(ORIGINS) else 'outra'
    upload = request.FILES.get('file')
    if upload is None:
        toast(request, 'Escolha o arquivo CSV para continuar.', level='error')
        return _go(1)
    try:
        headers, rows = parse_upload(upload)
    except (ValueError, UnicodeDecodeError, csv.Error) as exc:
        toast(request, str(exc) if isinstance(exc, ValueError) else 'Não foi possível ler o arquivo. Envie um CSV.', level='error')
        return _go(1)
    request.session[SESSION_KEY] = {'origin': origin, 'filename': upload.name, 'headers': headers, 'rows': rows,
                                    'mapping': guess_mapping(headers), 'mapped': False, 'course_ids': [], 'send_email': False}
    return _go(2)


def _post_columns(request, state):
    mapping = {}
    valid = {key for key, _ in ROLES}
    for index in range(len(state['headers'])):
        role = request.POST.get(f'col_{index}', 'ignore')
        mapping[str(index)] = role if role in valid else 'ignore'
    chosen = [role for role in mapping.values() if role != 'ignore']
    state['mapping'] = mapping
    if 'email' not in chosen:
        request.session[SESSION_KEY] = state
        toast(request, 'Escolha qual coluna é o e-mail.', level='error')
        return _go(2)
    if len(chosen) != len(set(chosen)):
        request.session[SESSION_KEY] = state
        toast(request, 'Cada tipo de coluna só pode ser usado uma vez.', level='error')
        return _go(2)
    state['mapped'] = True
    request.session[SESSION_KEY] = state
    return _go(3)


def _post_courses(request, state):
    ids = [int(i) for i in request.POST.getlist('courses') if i.isdigit()]
    ids = list(Course.objects.filter(pk__in=ids).exclude(status='archived').values_list('id', flat=True))
    if not ids:
        toast(request, 'Escolha pelo menos um curso.', level='error')
        return _go(3)
    state['course_ids'] = ids
    state['send_email'] = bool(request.POST.get('send_email'))
    request.session[SESSION_KEY] = state
    return _go(4)


def _plural(n, one, many):
    return f'{n} {one if n == 1 else many}'


def _post_confirm(request, state):
    parsed = evaluate(state['rows'], state['mapping'])
    courses = list(Course.objects.filter(pk__in=state['course_ids']))
    new_count = existing_count = 0
    summary = summarize(parsed)
    with transaction.atomic():
        for r in parsed:
            if r['status'] not in ('new', 'existing'):
                continue
            user = User.objects.filter(email__iexact=r['email'], role=User.Role.STUDENT).first()
            created = user is None
            if created:
                user = create_student(r['email'], r['name'], r['cpf'])
                new_count += 1
            else:
                existing_count += 1
                profile = user.student_profile
                changed = False
                if r['name'] and not profile.full_name:
                    profile.full_name, changed = r['name'], True
                if r['cpf'] and not profile.cpf:
                    profile.cpf, changed = r['cpf'], True
                if changed:
                    profile.save()
            for course in courses:
                grant(user, course, source='import', ref=r['order'], actor=request.user)
            r['mail'] = created or not user.has_usable_password()
    if state.get('send_email'):
        for r in parsed:
            if r.get('mail'):
                user = User.objects.filter(email__iexact=r['email']).first()
                if user:
                    try_access_email(request, user)
    log('imported', f'{_plural(new_count + existing_count, "aluno importado", "alunos importados")}', actor=request.user)
    request.session.pop(SESSION_KEY, None)
    ignored = summary['ignored']
    toast(request, f"{_plural(new_count, 'novo', 'novos')}, "
                   f"{existing_count} {'já existia e recebeu' if existing_count == 1 else 'já existiam e receberam'} os cursos, "
                   f"{_plural(ignored, 'ignorado', 'ignorados')}")
    return redirect(reverse('painel:students') + '?filtro=importados-hoje')
