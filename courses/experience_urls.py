from django.urls import path

from . import experience_views as views

prefix = "dashboard/cursos/<slug:course_slug>/"
urlpatterns = [
    path("dashboard/escolher/<slug:section>/", views.choose_course, name="choose_course"),
    path(prefix + "inicio/", views.home, name="course_home"),
    path(prefix + "trilha/", views.trail, name="course_trail"),
    path(prefix + "ebooks/", views.ebooks, name="course_ebooks"),
    path(prefix + "novidades/", views.news, name="course_news"),
    path(prefix + "minha-lista/", views.saved, name="course_saved"),
    path(prefix + "ao-vivo/", views.live, name="course_live"),
]
