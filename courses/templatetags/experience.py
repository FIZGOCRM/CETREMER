from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def course_navigation(context):
    course = context.get("course")
    request = context["request"]
    current = getattr(request.resolver_match, "url_name", None)
    links = []
    for title, icon, route, section in (
        ("Início", "home", "course_home", None),
        ("Trilha", "route", "course_trail", "trilha"),
        ("E-books", "book", "course_ebooks", "ebooks"),
        ("Ao vivo", "live", "course_live", "ao-vivo"),
        ("Minha lista", "list", "course_saved", "minha-lista"),
    ):
        if course:
            url = reverse(route, args=[course.slug])
        elif section:
            url = reverse("choose_course", args=[section])
        elif request.session.get("active_course_slug"):
            url = reverse("choose_course", args=["inicio"])
        else:
            url = reverse("dashboard")
        active = current == route or (route == "course_home" and current == "dashboard")
        links.append({"url": url, "title": title, "icon": icon, "active": active})
    return links
