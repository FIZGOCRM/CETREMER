"""Serve uploaded images only; private materials keep authenticated endpoints."""
import mimetypes
from pathlib import Path

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import FileResponse, Http404

PUBLIC_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "ico", "avif"}


def uploaded_image(request, path):
    parts=Path(path).parts
    if not parts or parts[0] not in {'courses','banners','logos','site','avatars'} or '..' in parts:
        raise Http404
    if parts[0]=='avatars' and not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    root=Path(settings.MEDIA_ROOT).resolve()
    target=(root/path).resolve()
    if not target.is_relative_to(root) or target.suffix.lower().lstrip('.') not in PUBLIC_IMAGE_EXTENSIONS:
        raise Http404
    try:
        stream=target.open('rb')
    except (OSError, ValueError):
        raise Http404
    response=FileResponse(stream,content_type=mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
    response['X-Content-Type-Options']='nosniff'
    response['Cache-Control']='private, no-store'
    return response
