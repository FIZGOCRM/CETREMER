from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from core.decorators import painel_required
from courses.models import Course, CourseMaterial
from courses.services import save_course_material, remove_course_material
from painel.forms import CourseMaterialForm
from .common import page


@painel_required
def course_materials(request, course_id):
    if request.user.role not in ('ADMIN','CREATOR'):
        raise PermissionDenied
    course = get_object_or_404(Course,pk=course_id)
    material = None
    raw = request.POST.get('material_id') if request.method == 'POST' else request.GET.get('editar')
    if raw:
        if not raw.isdigit() or len(raw)>18:
            raise PermissionDenied('Identificador inválido.')
        material = get_object_or_404(CourseMaterial, pk=int(raw),course=course)
    form = CourseMaterialForm(request.POST or None,request.FILES or None,instance=material)
    if request.method == 'POST':
        try:
            if request.POST.get('action') == 'remove' and material:
                remove_course_material(material,actor=request.user)
            elif form.is_valid():
                item=form.save(commit=False);item.course=course
                save_course_material(item,actor=request.user)
            else:
                return page(request,'course_materials',course=course,materials=course.materials.filter(is_active=True),form=form,material=material)
        except ValidationError as exc:
            form.add_error(None,exc)
        else:
            messages.success(request,'Material atualizado. Histórico preservado.')
            return redirect('painel:course_materials',course_id=course.pk)
    return page(request,'course_materials',course=course,materials=course.materials.filter(is_active=True),form=form,material=material)
