"""Management HTTP adapters: overview."""

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone

from community.models import CommunityPost
from core.decorators import painel_required
from courses.models import Course, Enrollment
from sales.models import Order

User = get_user_model()

from .common import page


@painel_required
def dashboard(request):
    now = timezone.now()
    paid = Order.objects.filter(
        status=Order.Status.COMPLETED,
        created_at__year=now.year,
        created_at__month=now.month,
    )
    context = {
        "month_revenue": paid.aggregate(total=Sum("amount"))["total"] or 0,
        "month_paid_count": paid.count(),
        "students_count": User.objects.filter(
            student_profile__enrollments__isnull=False
        )
        .distinct()
        .count(),
        "active_enrollments": Enrollment.objects.count(),
        "courses_with_enrollments": Course.objects.filter(enrollments__isnull=False)
        .distinct()
        .count(),
        "pending_questions": sum(
            not p.is_answered for p in CommunityPost.objects.filter(is_hidden=False)
        ),
        "recent_enrollments": Enrollment.objects.select_related(
            "student__user", "course"
        ).order_by("-enrolled_at")[:5],
        "recent_orders": Order.objects.select_related(
            "student__user", "course"
        ).order_by("-created_at")[:5],
    }
    return page(request, "dashboard", **context)
