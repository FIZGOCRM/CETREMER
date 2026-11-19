from django.urls import path
from . import views
from .views import plans
from .views import quizzes
from .views import materials
from .views import preview
from .views import reports
from .views import weekly
from .views import home_features
from .views import certificates
from .views import lessons
from .views.course_management import course_overview_view
from .views import live
from .views import support

app_name = 'painel'
urlpatterns = [
    path('visualizar/',preview.preview_choose,name='preview_choose'),
    path('visualizar/encerrar/',preview.preview_end,name='preview_end'),
    path('visualizar/<int:student_id>/',preview.preview_start,name='preview_start'),
    path('relatorios/',reports.reports,name='reports'),
    path('relatorios/aulas/', reports.lesson_report, name='lesson_metrics'),
    path('cursos/<int:course_id>/top-10/', weekly.weekly_selection, name='weekly_selection'),
    path('cursos/<int:course_id>/inicio/', home_features.features, name='home_features'),
    path('relatorios/exportar/',reports.export_reports,name='reports_export'),
    path('certificados/',certificates.certificates,name='certificates'),
    path('aulas/<int:lesson_id>/editar/',lessons.lesson_edit,name='lesson_edit'),
    path('cursos/<int:course_id>/aulas/nova/', lessons.lesson_edit, name='lesson_new'),
    path('cursos/<int:course_id>/visao-geral/',course_overview_view,name='course_overview'),
    path('ao-vivo/',live.live,name='live'),
    path('chamados/',support.tickets,name='tickets'),
    path('ajuda/<slug:kind>/',support.support_settings,name='support_settings'),
    path('cursos/<int:course_id>/materiais/', materials.course_materials, name='course_materials'),
    path('cursos/<int:course_id>/materiais/<slug:kind>/<int:material_id>/capa/', materials.material_cover, name='material_cover'),
    path('cursos/<int:course_id>/avaliacao/', quizzes.final_quiz, name='final_quiz'),
    path('aulas/<int:lesson_id>/quiz/', quizzes.lesson_quiz, name='lesson_quiz'),
    path('planos/<int:enrollment_id>/', plans.plan_manage, name='plan_manage'),
    path('vencimentos/', plans.expirations, name='expirations'),
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
