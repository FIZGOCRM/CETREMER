import re

from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse

from core.decorators import is_painel_admin, painel_required
from courses.models import Course, Lesson
from sales.models import Order
from users.display import full_name
from users.models import StudentProfile

LIMIT = 5


def _actions():
    return [
        {'url': reverse('painel:courses') + '?abrir=dlg-new-course', 'icon': 'plus', 'title': 'Novo curso', 'sub': 'Começa como rascunho'},
        {'url': reverse('painel:students') + '?abrir=dlg-enroll', 'icon': 'user', 'title': 'Matricular aluno', 'sub': 'Libera um curso por e-mail'},
        {'url': reverse('painel:students_import'), 'icon': 'download', 'title': 'Importar alunos', 'sub': 'CSV da Eduzz ou Hotmart'},
        {'url': reverse('painel:students_export'), 'icon': 'download', 'title': 'Exportar alunos', 'sub': 'Baixa um CSV'},
    ]


@painel_required
def painel_search(request):
    """Busca do Ctrl K do painel (HANDOFF-v2 9, `/painel/busca/`). Grupos: Alunos, Cursos, Aulas, Pedidos, Ações."""
    q = request.GET.get('q', '').strip()
    admin = is_painel_admin(request.user)
    actions = _actions()
    if not q:
        return render(request, 'partials/cmdk_results.html', {'groups': [{'label': 'Ações', 'items': actions}]})

    groups = []
    digits = re.sub(r'\D', '', q)
    student_q = Q(user__email__icontains=q) | Q(full_name__icontains=q) | Q(display_name__icontains=q)
    if len(digits) >= 3:
        student_q |= Q(cpf__contains=digits)
    students = (StudentProfile.objects.filter(student_q).select_related('user').order_by('full_name', 'user__email')[:LIMIT])
    items = [{'url': reverse('painel:student_detail', args=[s.user_id]), 'icon': 'user',
              'title': full_name(s.user), 'sub': s.user.email} for s in students]
    if items:
        groups.append({'label': 'Alunos', 'items': items})

    courses = Course.objects.filter(Q(title__icontains=q) | Q(short_name__icontains=q)).order_by('title')[:LIMIT]
    items = [{'url': reverse('painel:course_content', args=[c.id]), 'icon': 'course', 'title': c.title,
              'sub': c.get_status_display()} for c in courses]
    if items:
        groups.append({'label': 'Cursos', 'items': items})

    lessons = (Lesson.objects.filter(title__icontains=q).select_related('module__course')
               .order_by('module__course__title', 'module__order', 'order')[:LIMIT])
    items = [{'url': reverse('painel:course_content', args=[l.module.course_id]) + f'?aula={l.id}', 'icon': 'play',
              'title': l.title, 'sub': f'{l.module.course.title} · {l.module.title}'} for l in lessons]
    if items:
        groups.append({'label': 'Aulas', 'items': items})

    match = re.fullmatch(r'#?\s*(\d{1,9})', q)
    if admin and match:
        orders = Order.objects.filter(pk=int(match.group(1))).select_related('student__user', 'course')
        items = [{'url': reverse('painel:orders') + f'?pedido={o.id}', 'icon': 'receipt', 'title': f'Pedido #{o.id}',
                  'sub': f'{o.course.title} · {o.student.user.email}'} for o in orders]
        if items:
            groups.append({'label': 'Pedidos', 'items': items})

    needle = q.lower()
    found = [a for a in actions if needle in a['title'].lower() or needle in a['sub'].lower()]
    if found:
        groups.append({'label': 'Ações', 'items': found})
    return render(request, 'partials/cmdk_results.html', {'groups': groups})
