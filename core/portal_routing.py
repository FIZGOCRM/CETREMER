"""Public host boundaries; authentication and the validated preview remain mandatory."""
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

PRODUCER_ROLES = {'ADMIN', 'CREATOR'}
SHARED_VIEWS = {'login', 'logout', 'password_reset', 'password_reset_done',
                'password_reset_confirm', 'password_reset_complete',
                'verify_certificate', 'material_open', 'course_preview'}


def allows_user(portal, user):
    return not portal or (user.role in PRODUCER_ROLES if portal == 'producer' else user.role == 'STUDENT')


def user_access_url(request, user, path):
    portals = getattr(settings, 'PUBLIC_PORTALS', None)
    if not portals:
        return request.build_absolute_uri(path)
    portal = 'student' if user.role == 'STUDENT' else 'producer'
    return 'https://' + portals[portal] + path


def allows_path(portal, path, *, preview=False):
    if path.startswith(('/static/', '/media/')):
        return True
    try:
        match = resolve(path, urlconf='core.urls_deploy')
    except Resolver404:
        return False
    administrative = bool(set(match.namespaces) & {'painel', 'admin'}) or path.startswith('/creator/')
    if portal == 'student':
        return not administrative
    return administrative or match.url_name in SHARED_VIEWS or preview


def allows_next(portal, path):
    return not portal or (path not in ('/', '/login/', '/logout/') and allows_path(portal, path))


class PublicPortalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        portals = getattr(settings, 'PUBLIC_PORTALS', None)
        if not portals:
            return self.get_response(request)
        host = request.get_host().split(':', 1)[0].lower()
        portal = next((name for name, hostname in portals.items() if hostname == host), None)
        if request.path_info == '/healthz/' and request.method in ('GET', 'HEAD'):
            return HttpResponse('ok', content_type='text/plain')
        if not portal:
            return HttpResponseNotFound()
        request.portal = portal
        actor = getattr(request, 'preview_admin', request.user)
        if actor.is_authenticated and not allows_user(portal, actor) and request.path_info != '/logout/':
            return HttpResponseForbidden('Este acesso não está disponível neste endereço.')
        preview = bool(getattr(request, 'member_preview', False)) and portal == 'producer'
        if request.path_info == '/':
            return redirect('/dashboard/' if preview or (actor.is_authenticated and portal == 'student')
                            else '/painel/' if actor.is_authenticated else '/login/')
        if not allows_path(portal, request.path_info, preview=preview):
            return HttpResponseNotFound()
        response = self.get_response(request)
        if actor.is_authenticated or request.path_info.startswith(('/login/', '/senha/')):
            response['Cache-Control'] = 'private, no-store'
        return response
