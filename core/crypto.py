from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _fernet():
    if not settings.FIELD_ENCRYPTION_KEY:
        raise ImproperlyConfigured('Defina FIELD_ENCRYPTION_KEY no ambiente ou no arquivo .env.')
    return Fernet(settings.FIELD_ENCRYPTION_KEY.encode('ascii'))


def encrypt(text):
    return _fernet().encrypt(text.encode('utf-8')).decode('ascii')


def decrypt(token):
    return _fernet().decrypt(token.encode('ascii')).decode('utf-8')
