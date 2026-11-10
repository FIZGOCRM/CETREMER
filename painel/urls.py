from django.urls import path
from . import views

app_name = 'painel'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('cursos/', views.courses, name='courses'),
    path('cursos/novo/', views.course_edit, name='course_new'),
    path('cursos/<int:course_id>/', views.course_edit, name='course_edit'),
    path('cursos/<int:course_id>/aulas/', views.course_lessons, name='course_lessons'),
    path('cursos/<int:course_id>/aulas/ordem/', views.course_reorder, name='course_reorder'),
    path('alunos/', views.students, name='students'),
    path('alunos/exportar/', views.students_export, name='students_export'),
    path('alunos/importar/', views.students_import, name='students_import'),
    path('pedidos/', views.orders, name='orders'),
    path('pedidos/exportar/', views.orders_export, name='orders_export'),
    path('comunidade/', views.community, name='community'),
    path('configuracoes/', views.settings, name='settings'),
]
