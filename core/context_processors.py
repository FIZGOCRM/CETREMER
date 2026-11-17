from users.models import SiteSettings


def site(request):
    count=request.user.notifications.filter(read_at__isnull=True).count() if request.user.is_authenticated else 0
    context={'site': SiteSettings.load(), 'unread_notification_count':count}
    if request.user.is_authenticated and request.user.role in ('ADMIN','CREATOR') and request.path.startswith('/painel/'):
        from painel.selectors import panel_counts
        context['panel_counts']=panel_counts()
    return context
