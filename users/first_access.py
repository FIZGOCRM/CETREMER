import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from users.models import FirstAccessCode


def issue_code(user):
    """Return a code once for an administrator to deliver outside the platform."""
    code = f'{secrets.randbelow(10**10):010d}'
    FirstAccessCode.objects.update_or_create(
        user=user,
        defaults={
            'code_hash': make_password(code),
            'expires_at': timezone.now() + timedelta(days=7),
            'failed_attempts': 0,
        },
    )
    return code


def verify_code(credential, code):
    if credential.expires_at <= timezone.now() or credential.failed_attempts >= 5:
        return False
    if not check_password(code, credential.code_hash):
        credential.failed_attempts += 1
        credential.save(update_fields=['failed_attempts'])
        return False
    return True
