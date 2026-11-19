"""KVM4 tunnel phase. Not a public HTTP deployment configuration."""
from .settings import *  # noqa: F403

if os.environ.get('GOMUT_TUNNEL_ONLY') != 'True':
    raise ImproperlyConfigured('This release requires GOMUT_TUNNEL_ONLY=True and loopback-only Docker publication.')
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS','').split(',') if h.strip()]
if not ALLOWED_HOSTS or any(h not in {'127.0.0.1','localhost','[::1]'} for h in ALLOWED_HOSTS):
    raise ImproperlyConfigured('Set explicit loopback hosts for this SSH tunnel deployment.')
if not os.environ.get('FIELD_ENCRYPTION_KEY'):
    raise ImproperlyConfigured('FIELD_ENCRYPTION_KEY is required for persistent encrypted settings.')
for name in ('DJANGO_DATABASE_PATH','DJANGO_MEDIA_ROOT'):
    if not os.environ.get(name) or not Path(os.environ[name]).anchor:
        raise ImproperlyConfigured(f'{name} must be an explicit absolute persistent path.')

DEBUG = False
MEDIA_ROOT = Path(os.environ['DJANGO_MEDIA_ROOT'])
STATIC_ROOT = BASE_DIR / 'staticfiles'
ROOT_URLCONF = 'core.urls_deploy'
MIDDLEWARE = [MIDDLEWARE[0], 'whitenoise.middleware.WhiteNoiseMiddleware', *MIDDLEWARE[1:]]
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS','').split(',') if origin.strip()]
USE_X_FORWARDED_HOST = False
SECURE_PROXY_SSL_HEADER = None
# SSH provides transport encryption; browser HTTP terminates on local loopback.
# These four security-check warnings are reviewed explicitly, never silenced.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
_environment = os.environ.get('GOMUT_ENVIRONMENT','production')
if _environment not in {'production','homolog'}:
    raise ImproperlyConfigured('Unknown GOMUT_ENVIRONMENT')
SESSION_COOKIE_NAME = f'gomut_{_environment}_session'
CSRF_COOKIE_NAME = f'gomut_{_environment}_csrf'
SECURE_CONTENT_TYPE_NOSNIFF = True
ASAAS_API_ENABLED = False
ASAAS_WEBHOOK_ENABLED = False
ASAAS_API_KEY = ''
ASAAS_WEBHOOK_TOKEN = ''
