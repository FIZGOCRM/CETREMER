from users.models import SiteSettings


def site(request):
    return {'site': SiteSettings.load()}
