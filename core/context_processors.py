from types import SimpleNamespace

from django.apps import apps


_FALLBACK_SITE = SimpleNamespace(
    school_name='CETREMER',
    whatsapp_url='https://wa.me/5567996494740',
    terms_url='',
    privacy_url='',
)


def site(request):
    """Expose site settings; phase 1 supplies the persistent model."""
    try:
        model = apps.get_model('users', 'SiteSettings')
    except LookupError:
        return {'site': _FALLBACK_SITE}
    return {'site': model.load()}
