"""Pedidos (HANDOFF-v2 8.9). Só administrador."""
import csv
from datetime import timedelta
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.ajax import json_error, json_ok, wants_json
from core.decorators import painel_admin_required
from core.toasts import toast
from courses.models import Enrollment
from sales.models import Order
from users.display import full_name

from .access import report_access_delivery, try_access_email

PERIODS = (('30d', 'Últimos 30 dias'), ('mes', 'Este mês'), ('anterior', 'Mês passado'), ('ano', 'Este ano'))
STATUSES = (('todos', 'Todos', None), ('pagos', 'Pagos', Order.Status.COMPLETED), ('aguardando', 'Aguardando', Order.Status.PENDING),
            ('recusados', 'Recusados', Order.Status.FAILED), ('reembolsados', 'Reembolsados', Order.Status.REFUNDED))
STATUS_LABEL = {Order.Status.COMPLETED: 'Pago', Order.Status.PENDING: 'Aguardando', Order.Status.FAILED: 'Recusado', Order.Status.REFUNDED: 'Reembolsado'}
STATUS_BADGE = {Order.Status.COMPLETED: 'badge--success', Order.Status.PENDING: 'badge--warning', Order.Status.FAILED: 'badge--gray', Order.Status.REFUNDED: 'badge--blue'}
METHOD_LABEL = {Order.PaymentMethod.PIX: 'Pix', Order.PaymentMethod.CREDIT_CARD: 'Cartão'}
ENUM_BY_SLUG = {slug: value for slug, _, value in STATUSES}


def _period_range(period, now):
    start = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
    if period == 'mes':
        return start.replace(day=1), None
    if period == 'anterior':
        this_month = start.replace(day=1)
        return (this_month - timedelta(days=1)).replace(day=1), this_month
    if period == 'ano':
        return start.replace(month=1, day=1), None
    return now - timedelta(days=30), None


def _decorate(order):
    order.status_label = STATUS_LABEL.get(order.status, order.status)
    order.status_badge = STATUS_BADGE.get(order.status, 'badge--gray')
    order.method_label = METHOD_LABEL.get(order.payment_method, order.payment_method)
    order.student_name = full_name(order.student.user)
    return order


def drawer_context(order):
    order = _decorate(order)
    enrollment = Enrollment.objects.filter(student=order.student, course=order.course).first()
    events = [{'text': 'Pedido criado', 'when': order.created_at}]
    if order.status in (Order.Status.COMPLETED, Order.Status.REFUNDED):
        events.append({'text': f'Pagamento confirmado no {order.method_label}', 'when': order.created_at})
        if enrollment is not None:
            events.append({'text': 'Acesso liberado', 'when': enrollment.enrolled_at})
    if order.status == Order.Status.FAILED:
        events.append({'text': 'Pagamento recusado', 'when': order.created_at})
    if order.status == Order.Status.REFUNDED:
        events.append({'text': 'Pedido reembolsado', 'when': None})
    return {'order': order, 'events': events}


@painel_admin_required
def orders(request):
    now = timezone.now()
    period = request.GET.get('periodo', '30d')
    if period not in dict(PERIODS):
        period = '30d'
    slug = request.GET.get('status', 'todos')
    wanted = ENUM_BY_SLUG.get(slug, slug if slug in Order.Status.values else None)
    if wanted is not None and slug not in ENUM_BY_SLUG:
        slug = next(s for s, _, value in STATUSES if value == wanted)
    q = request.GET.get('q', '').strip()
    start, end = _period_range(period, now)
    base = Order.objects.select_related('student__user', 'course').filter(created_at__gte=start)
    if end is not None:
        base = base.filter(created_at__lt=end)
    if q:
        number = q.lstrip('#')
        cond = Q(student__user__email__icontains=q) | Q(student__full_name__icontains=q) | Q(course__title__icontains=q) | Q(course__short_name__icontains=q)
        if number.isdigit():
            cond |= Q(pk=int(number))
        base = base.filter(cond)
    paid = base.filter(status=Order.Status.COMPLETED)
    totals = paid.aggregate(total=Sum('amount'), n=Count('id'))
    revenue = totals['total'] or Decimal('0')
    paid_count = totals['n'] or 0
    metrics = {
        'revenue': revenue, 'paid': paid_count, 'pending': base.filter(status=Order.Status.PENDING).count(),
        'average': (revenue / paid_count).quantize(Decimal('0.01')) if paid_count else None,
    }
    status_list = [{'slug': slug_, 'label': label, 'count': base.filter(status=value).count() if value else base.count()}
                   for slug_, label, value in STATUSES]
    qs = base.filter(status=wanted) if wanted else base
    page = Paginator(qs.order_by('-created_at', '-id'), 25).get_page(request.GET.get('pagina'))
    rows = [_decorate(order) for order in page]
    selected = None
    if request.GET.get('pedido', '').isdigit():
        selected = Order.objects.select_related('student__user', 'course').filter(pk=request.GET['pedido']).first()
    if selected is not None and (wants_json(request) or request.GET.get('parcial')):
        return render(request, 'painel/_order_drawer.html', drawer_context(selected))
    context = {'rows': rows, 'page': page, 'period': period, 'periods': PERIODS, 'status': slug, 'statuses': status_list,
               'metrics': metrics, 'q': q, 'has_any': Order.objects.exists()}
    if selected is not None:
        context.update(drawer_context(selected))
        context['selected'] = selected
    return render(request, 'painel/orders.html', context)


@painel_admin_required
def orders_export(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="pedidos.csv"'
    writer = csv.writer(response)
    writer.writerow(['pedido', 'data', 'aluno', 'curso', 'forma', 'valor', 'status'])
    for order in Order.objects.select_related('student__user', 'course').order_by('-created_at'):
        writer.writerow([order.id, timezone.localtime(order.created_at).strftime('%d/%m/%Y %H:%M'), order.student.user.email,
                         order.course.title, METHOD_LABEL.get(order.payment_method, order.payment_method), str(order.amount),
                         STATUS_LABEL.get(order.status, order.status)])
    return response


@painel_admin_required
@require_POST
def order_action(request, order_id):
    order = get_object_or_404(Order.objects.select_related('student__user', 'course'), pk=order_id)
    action = request.POST.get('action') or request.GET.get('action')
    back = reverse('painel:orders') + f'?pedido={order.id}'
    user = order.student.user
    if action == 'resend_access':
        if try_access_email(request, user):
            toast(request, f'E-mail de acesso enviado para {user.email}')
        else:
            report_access_delivery(request, False)
    elif action == 'refund':
        if order.status != Order.Status.COMPLETED:
            message = 'Só pedidos pagos podem ser reembolsados.'
            if wants_json(request):
                return json_error(message)
            toast(request, message, level='error')
            return redirect(back)
        order.status = Order.Status.REFUNDED
        order.save(update_fields=['status'])
        other_paid = Order.objects.filter(student=order.student, course=order.course, status=Order.Status.COMPLETED).exists()
        if not other_paid:
            Enrollment.objects.filter(student=order.student, course=order.course).update(is_active=False)
        toast(request, f'Pedido #{order.id} reembolsado')
    else:
        message = 'Ação inválida.'
        if wants_json(request):
            return json_error(message)
        toast(request, message, level='error')
        return redirect(back)
    return json_ok(redirect=back) if wants_json(request) else redirect(back)
