from datetime import timedelta
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from core.decorators import painel_required
from courses.models import Enrollment
from courses.selectors import progress_info
from courses.services import create_plan, end_plan_early, reactivate_plan, correct_plan_dates, plan_status
from painel.forms import PlanForm
from .common import page


@painel_required
def plan_manage(request, enrollment_id):
    if request.user.role not in ('ADMIN', 'CREATOR'):
        raise PermissionDenied
    enrollment = get_object_or_404(Enrollment.objects.select_related('student__user', 'course'), pk=enrollment_id)
    form = PlanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        end = data['last_day'] + timedelta(days=1) if data['last_day'] else None
        try:
            action = data['action']
            if action == 'create':
                create_plan(enrollment, data['starts_on'], end, actor=request.user)
            elif action == 'end':
                end_plan_early(enrollment, data['end_date'], data['reason_code'], actor=request.user, reason_text=data['reason_text'])
            elif action == 'reactivate':
                reactivate_plan(enrollment, end, actor=request.user)
            elif action == 'correct':
                correct_plan_dates(enrollment, data['starts_on'], end, data['reason_text'], actor=request.user)
            elif action == 'note':
                enrollment.admin_note = data['admin_note']
                enrollment.save(update_fields=['admin_note'])
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, 'Plano atualizado. Histórico preservado.')
            return redirect('painel:plan_manage', enrollment_id=enrollment.pk)
    return page(request, 'plan', enrollment=enrollment, plan=plan_status(enrollment), form=form,
                changes=enrollment.access_changes.select_related('actor'))


@painel_required
def expirations(request):
    today = timezone.localdate()
    items = []
    for enrollment in Enrollment.objects.select_related('student__user', 'course').prefetch_related('access_periods', 'access_changes'):
        plan = plan_status(enrollment)
        if plan.get('ends_on') and today <= plan['ends_on'] <= today + timedelta(days=60):
            items.append({'enrollment': enrollment, 'plan': plan, 'progress': progress_info(enrollment.student, enrollment.course)})
    items.sort(key=lambda item: item['plan']['ends_on'])
    from users.notifications import pending_email_count
    return page(request, 'expirations', items=items, pending_email_count=pending_email_count())
