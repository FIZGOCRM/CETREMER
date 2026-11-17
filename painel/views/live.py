from django.db.models import Q
from courses.models import Course
from django.contrib import messages
from django.core.exceptions import PermissionDenied,ValidationError
from django.shortcuts import get_object_or_404,redirect
from community.access import is_team
from core.decorators import painel_required
from courses.models import LiveEvent
from courses.live_services import save_event,remove_event
from painel.live_forms import LiveEventForm
from .common import page

@painel_required
def live(request):
    if not is_team(request.user):raise PermissionDenied
    course=get_object_or_404(Course,pk=request.GET['curso']) if request.GET.get('curso','').isdigit() else None
    instance=get_object_or_404(LiveEvent,pk=request.GET['id']) if request.GET.get('id') else None
    form=LiveEventForm(request.POST or None,instance=instance,initial={'course':course.pk} if course and not instance else None)
    if request.method=='POST':
        if request.POST.get('action')=='remove':
            remove_event(request.user,get_object_or_404(LiveEvent,pk=request.POST.get('event_id')))
            return redirect('painel:live')
        if form.is_valid():
            try:
                save_event(request.user,form.save(commit=False));messages.success(request,'Encontro salvo.')
                return redirect('painel:live')
            except ValidationError as exc:form.add_error(None,exc)
    events=LiveEvent.objects.select_related('course')
    if course:events=events.filter(Q(course=course)|Q(course__isnull=True))
    return page(request,'live',events=events,form=form,course=course)
