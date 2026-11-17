from users.models import SiteSettings


def site(request):
    count=request.user.notifications.filter(read_at__isnull=True).count() if request.user.is_authenticated else 0
    return {'site': SiteSettings.load(), 'unread_notification_count':count}
