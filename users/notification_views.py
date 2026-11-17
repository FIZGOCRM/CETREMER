from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect,render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Notification

@login_required
def notifications(request):
    if request.user.role!='STUDENT':return redirect('painel:dashboard')
    return render(request,'users/notifications.html',{'notifications':Notification.objects.filter(user=request.user)[:100]})

@login_required
@require_POST
def read_all(request):
    Notification.objects.filter(user=request.user,read_at__isnull=True).update(read_at=timezone.now())
    return redirect('notifications')
