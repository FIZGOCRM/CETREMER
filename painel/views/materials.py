from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from core.decorators import painel_required
from courses.models import Course, CourseMaterial, LessonMaterial
from courses.services import save_course_material, remove_course_material
from painel.forms import CourseMaterialForm, MaterialCoverForm
from django.http import Http404
from .common import page
from .course_order import reorder_items


@painel_required
def course_materials(request, course_id):
    if request.user.role not in ('ADMIN','CREATOR'):
        raise PermissionDenied
    course = get_object_or_404(Course,pk=course_id)
    lesson_materials = LessonMaterial.objects.filter(lesson__module__course=course).select_related(
        'lesson__module').order_by('lesson__module__order','lesson__module_id','lesson__order','lesson_id','order','pk')
    active = course.materials.filter(is_active=True)
    if request.method == "POST" and request.content_type == "application/json":
        return reorder_items(request, course, active)
    material = None
    raw = request.POST.get('material_id') if request.method == 'POST' else request.GET.get('editar')
    if raw:
        if not raw.isdigit() or len(raw)>18:
            raise PermissionDenied('Identificador inválido.')
        material = get_object_or_404(CourseMaterial, pk=int(raw),course=course)
    form = CourseMaterialForm(request.POST or None,request.FILES or None,instance=material)
    if request.method == 'POST':
        try:
            if request.POST.get("action") == "upload":
                uploads = request.FILES.getlist("pdfs")
                if not uploads:
                    raise ValidationError("Escolha ao menos um PDF.")
                with transaction.atomic():
                    Course.objects.select_for_update().get(pk=course.pk)
                    last = active.aggregate(last=Max("order"))["last"] or 0
                    pending = [CourseMaterial(course=course, title=upload.name[:120], file=upload, order=last + index)
                               for index, upload in enumerate(uploads, start=1)]
                    for item in pending:
                        item.full_clean()
                    for item in pending:
                        save_course_material(item, actor=request.user)
            elif request.POST.get('action') == 'remove' and material:
                remove_course_material(material,actor=request.user)
            elif form.is_valid():
                item=form.save(commit=False);item.course=course
                save_course_material(item,actor=request.user)
            else:
                return page(request,'course_materials',course=course,materials=active,lesson_materials=lesson_materials,form=form,material=material)
        except ValidationError as exc:
            form.add_error(None,exc)
        else:
            messages.success(request,'Material atualizado. Histórico preservado.')
            return redirect('painel:course_materials',course_id=course.pk)
    return page(request,'course_materials',course=course,materials=active,lesson_materials=lesson_materials,form=form,material=material)


@painel_required
def material_cover(request, course_id, kind, material_id):
    course = get_object_or_404(Course, pk=course_id)
    if kind == 'lesson':
        material = get_object_or_404(LessonMaterial, pk=material_id, lesson__module__course=course)
    elif kind == 'course':
        material = get_object_or_404(CourseMaterial, pk=material_id, course=course, is_active=True)
    else:
        raise Http404
    form = MaterialCoverForm(request.POST if request.method == 'POST' else None, request.FILES)
    if request.method == 'POST':
        remove = request.POST.get('action') == 'remove'
        if remove or form.is_valid():
            material.cover = '' if remove else form.cleaned_data['cover']
            material.save(update_fields=['cover'])
            messages.success(request, 'Capa removida.' if remove else 'Capa do e-book atualizada.')
            return redirect('painel:course_materials', course_id=course_id)
    return page(request, 'material_cover', course=course, material=material, form=form)
