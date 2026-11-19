"""Public HTTPS portals. Tunnel-only homologation keeps settings_deploy."""
import re
from .settings import *  # noqa: F403


def public_host(name):
    value = os.environ.get(name, '').strip().lower()
    if not re.fullmatch(r'(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}', value):
        raise ImproperlyConfigured(f'{name} must be an explicit DNS hostname without scheme, port or wildcard.')
    return value


PUBLIC_PORTALS = {'student': public_host('GOMUT_STUDENT_HOST'), 'producer': public_host('GOMUT_PRODUCER_HOST')}
if len(set(PUBLIC_PORTALS.values())) != 2:
    raise ImproperlyConfigured('Student and producer hosts must be different.')
if not os.environ.get('FIELD_ENCRYPTION_KEY'):
    raise ImproperlyConfigured('FIELD_ENCRYPTION_KEY is required.')
for name in ('DJANGO_DATABASE_PATH', 'DJANGO_MEDIA_ROOT'):
    if not os.environ.get(name) or not Path(os.environ[name]).is_absolute():
        raise ImproperlyConfigured(f'{name} must be an absolute persistent path.')
DEBUG = False
GOMUT_DEMO_MODE = False
ALLOWED_HOSTS = [*PUBLIC_PORTALS.values(), '127.0.0.1', 'localhost', '[::1]']
CSRF_TRUSTED_ORIGINS = ['https://' + host for host in PUBLIC_PORTALS.values()]
MEDIA_ROOT = Path(os.environ['DJANGO_MEDIA_ROOT'])
ROOT_URLCONF = 'core.urls_deploy'
MIDDLEWARE = [MIDDLEWARE[0], 'whitenoise.middleware.WhiteNoiseMiddleware', *MIDDLEWARE[1:]]
_position = MIDDLEWARE.index('users.preview_middleware.MemberPreviewMiddleware') + 1
MIDDLEWARE.insert(_position, 'core.portal_routing.PublicPortalMiddleware')
STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'}}
USE_X_FORWARDED_HOST = False
# Public requests arrive through Traefik, which sets this header itself.
# No direct public Gunicorn port is published. Local Docker workloads are part
# of the trusted VPS boundary, not independent untrusted tenants.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r'^healthz/$']
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_NAME = '__Host-gomut_session'
CSRF_COOKIE_NAME = '__Host-gomut_csrf'
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None
SESSION_COOKIE_PATH = '/'
CSRF_COOKIE_PATH = '/'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
ASAAS_API_ENABLED = False
ASAAS_WEBHOOK_ENABLED = False
ASAAS_API_KEY = ''
ASAAS_WEBHOOK_TOKEN = ''
