from django.db.models import Q
from django.core.paginator import Paginator
from core.decorators import painel_required
from courses.models import Certificate,Course
from .common import page

@painel_required
def certificates(request):
    qs=Certificate.objects.select_related('enrollment__course','enrollment__student__user').order_by('-issued_at')
    q=request.GET.get('q','').strip()
    if q:qs=qs.filter(Q(student_name__icontains=q)|Q(code__icontains=q)|Q(course_title__icontains=q))
    if request.GET.get('curso','').isdigit():qs=qs.filter(enrollment__course_id=request.GET['curso'])
    return page(request,'certificates',certificates=Paginator(qs,50).get_page(request.GET.get('page')),courses=Course.objects.all(),q=q)
