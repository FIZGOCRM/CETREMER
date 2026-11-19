from django.urls import path
from django.http import Http404

from .urls import urlpatterns as application_patterns
from .deploy_media import uploaded_image

def registration_disabled(request):
    raise Http404


urlpatterns = [path('register/', registration_disabled), *application_patterns, path('media/<path:path>', uploaded_image)]
