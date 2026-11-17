"""Management HTTP adapters: orders."""

import csv
from datetime import timedelta

from django.db.models import Q, Sum
from django.http import HttpResponse
from django.utils import timezone

from core.decorators import painel_required
from sales.models import Order

from .common import page


@painel_required
def orders(request):
    qs = Order.objects.select_related("student__user", "course").order_by("-created_at")
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    period = request.GET.get("periodo", "30d")
    now = timezone.now()
    if q:
        qs = qs.filter(
            Q(student__user__email__icontains=q) | Q(course__title__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if period == "mes":
        qs = qs.filter(created_at__year=now.year, created_at__month=now.month)
    elif period == "anterior":
        last = now.replace(day=1) - timedelta(days=1)
        qs = qs.filter(created_at__year=last.year, created_at__month=last.month)
    else:
        qs = qs.filter(created_at__gte=now - timedelta(days=30))
    paid_total = (
        qs.filter(status=Order.Status.COMPLETED).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    from django.core.paginator import Paginator

    return page(
        request,
        "orders",
        orders=Paginator(qs, 25).get_page(request.GET.get("page")),
        paid_total=paid_total,
        pending_count=qs.filter(status=Order.Status.PENDING).count(),
        failed_count=qs.filter(status=Order.Status.FAILED).count(),
        q=q,
        status=status,
        period=period,
    )


@painel_required
def orders_export(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="pedidos.csv"'
    writer = csv.writer(response)
    writer.writerow(["data", "aluno", "curso", "forma", "valor", "status"])
    for order in Order.objects.select_related("student__user", "course").order_by(
        "-created_at"
    ):
        writer.writerow(
            [
                timezone.localtime(order.created_at).strftime("%d/%m/%Y %H:%M"),
                order.student.user.email,
                order.course.title,
                order.get_payment_method_display(),
                str(order.amount),
                order.get_status_display(),
            ]
        )
    return response
