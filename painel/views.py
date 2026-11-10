from django.shortcuts import render
from django.views.decorators.http import require_GET

from core.decorators import painel_required


@painel_required
@require_GET
def placeholder(request, page_title):
    return render(request, 'phase0/admin.html', {'page_title': page_title})
