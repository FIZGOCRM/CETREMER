from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied,ValidationError
from django.shortcuts import get_object_or_404,redirect,render
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST,require_GET
from .models import LiveEvent
from .live_selectors import live_agenda
from .live_services import require_event_access,room_available,toggle_reminder

@login_required
@require_GET
def agenda(request):
    if request.user.role!='STUDENT':return redirect('painel:live')
    upcoming,past=live_agenda(request.user.student_profile)
    return render(request,'courses/live_classes.html',{'upcoming':upcoming,'past':past})

@login_required
@require_POST
def remind(request,event_id):
    event=get_object_or_404(LiveEvent,pk=event_id)
    ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    try:
        created=toggle_reminder(request.user,event)
        if ajax:
            return JsonResponse({"active": created})
        messages.success(request,'Lembrete ativado.' if created else 'Lembrete removido.')
    except ValidationError as exc:
        if ajax:
            return JsonResponse({"error": " ".join(exc.messages)}, status=400)
        messages.error(request,' '.join(exc.messages))
    return redirect('live_classes')

@login_required
@require_GET
def open_link(request,event_id,kind):
    event=get_object_or_404(LiveEvent,pk=event_id);require_event_access(request.user,event)
    if kind=='sala':
        if not room_available(event):raise PermissionDenied('A sala fica disponível a partir de 10 minutos antes do encontro e durante sua duração.')
        return redirect(event.room_url)
    if kind!='gravacao' or event.starts_at+timedelta(minutes=event.duration_minutes)>timezone.now() or not event.recording_url:raise PermissionDenied('Gravação ainda indisponível.')
    return redirect(event.recording_url)
