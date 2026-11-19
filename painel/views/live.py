from django.db.models import Q
from courses.models import Course
from django.contrib import messages
from django.core.exceptions import PermissionDenied,ValidationError
from django.shortcuts import get_object_or_404,redirect
from django.urls import reverse
from django.utils import timezone
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
    agenda = reverse('painel:live') + (f'?curso={course.pk}' if course else '')
    form=LiveEventForm(request.POST or None,instance=instance,initial={'course':course.pk} if course and not instance else None)
    if request.method=='POST':
        if request.POST.get('action')=='remove':
            remove_event(request.user,get_object_or_404(LiveEvent,pk=request.POST.get('event_id')))
            return redirect(agenda)
        if form.is_valid():
            try:
                save_event(request.user,form.save(commit=False));messages.success(request,'Encontro salvo.')
                return redirect(agenda)
            except ValidationError as exc:form.add_error(None,exc)
    events=LiveEvent.objects.select_related('course')
    if course:events=events.filter(Q(course=course)|Q(course__isnull=True))
    now = timezone.now()
    groups = {"proximos": events.filter(is_active=True,starts_at__gte=now),
              "passados": events.filter(is_active=True,starts_at__lt=now), "desativados": events.filter(is_active=False)}
    tab = request.GET.get("aba","proximos")
    if tab not in groups:
        tab = "proximos"
    tabs = [(key, label, groups[key].count()) for key,label in
            (("proximos","Próximos"),("passados","Passados"),("desativados","Desativados"))]
    return page(request,'live',events=groups[tab].order_by('-starts_at' if tab == 'passados' else 'starts_at','pk'),
                form=form,course=course,tab=tab,tabs=tabs,courses=Course.objects.order_by('title'))
