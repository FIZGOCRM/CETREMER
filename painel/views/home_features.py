from django import forms
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods

from core.decorators import painel_required
from courses.models import Course, HomeFeature, Lesson, LessonMaterial, LiveEvent
from painel.analytics_forms import CardArtworkField
from .common import page


class FeatureForm(forms.Form):
    target = forms.ChoiceField(label="Conteúdo")
    position = forms.IntegerField(label="Ordem na seção", min_value=1, max_value=32767, initial=1)
    artwork = CardArtworkField(label="Arte do card (opcional)", required=False)

    def __init__(self, *args, course, **kwargs):
        super().__init__(*args, **kwargs)
        lessons = Lesson.objects.filter(module__course=course, module__status="published", status="published")
        materials = LessonMaterial.objects.filter(lesson__in=lessons).exclude(Q(file="") & Q(url=""))
        recordings = LiveEvent.objects.filter(Q(course=course) | Q(course__isnull=True), is_active=True).exclude(recording_url="")
        offers = Course.objects.filter(is_published=True).exclude(pk=course.pk)
        choices = [("", "Escolha um conteúdo")]
        for key, label, rows in [
            ("lesson", "Novidades · Aulas", lessons.select_related("module")),
            ("material", "Novidades · E-books", materials.select_related("lesson")),
            ("recording", "Novidades · Gravações", recordings),
            ("offer", "Outros cursos", offers.order_by("title")),
        ]:
            choices.append((label, [(f"{key}:{obj.pk}", str(obj) if key == "lesson" else obj.title) for obj in rows]))
        self.fields["target"].choices = choices


@painel_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def features(request, course_id):
    courses = Course.objects.select_for_update() if request.method == "POST" else Course.objects.all()
    course = get_object_or_404(courses, pk=course_id)
    entries = course.home_features.select_related("lesson", "material", "recording", "offer")
    entry_id = request.POST.get("item") if request.method == "POST" else request.GET.get("item")
    if entry_id and not entry_id.isdecimal():
        raise Http404
    entry = get_object_or_404(entries, pk=entry_id) if entry_id else None
    if request.method == "POST" and request.POST.get("action") == "remove":
        if entry:
            entry.delete()
        return redirect("painel:home_features", course_id)
    initial = {}
    if entry:
        key = next(key for key in ("lesson", "material", "recording", "offer") if getattr(entry, key + "_id"))
        initial = {"target": f"{key}:{entry.target.pk}", "position": entry.position, "artwork": entry.artwork}
    form = FeatureForm(request.POST if request.method == "POST" else None, request.FILES or None, initial=initial, course=course)
    if request.method == "POST" and form.is_valid():
        key, pk = form.cleaned_data["target"].split(":")
        duplicates = entries.filter(**{key + "_id": pk})
        if entry:
            duplicates = duplicates.exclude(pk=entry.pk)
        if duplicates.exists():
            form.add_error("target", "Este conteúdo já está na seção. Edite o card existente.")
        else:
            item = entry or HomeFeature(course=course)
            for field in ("lesson", "material", "recording", "offer"):
                setattr(item, field + "_id", int(pk) if field == key else None)
            item.position = form.cleaned_data["position"]
            item.artwork = form.cleaned_data["artwork"] or ""
            item.save()
            messages.success(request, "Card salvo na página inicial do curso.")
            return redirect("painel:home_features", course_id)
    items = list(entries)
    return page(request, "home_features", course=course, form=form, entry=entry, entries=items,
                news=[item for item in items if not item.offer_id], offers=[item for item in items if item.offer_id])
