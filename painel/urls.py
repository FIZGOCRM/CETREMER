from django.urls import path

from . import views

app_name = 'painel'

urlpatterns = [
    path('', views.placeholder, {'page_title': 'Painel'}, name='dashboard'),
    path('cursos/', views.placeholder, {'page_title': 'Cursos'}, name='courses'),
    path('alunos/', views.placeholder, {'page_title': 'Alunos'}, name='students'),
    path('pedidos/', views.placeholder, {'page_title': 'Pedidos'}, name='orders'),
    path('comunidade/', views.placeholder, {'page_title': 'Comunidade'}, name='community'),
    path('configuracoes/', views.placeholder, {'page_title': 'Configurações'}, name='settings'),
]
