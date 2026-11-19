from users import notification_views
from courses import live_views
from support import views as support_views
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from users import views as user_views
from courses import views as course_views
from sales import views as sales_views
from sales.webhook_views import asaas_webhook
from community import views as community_views
from courses import student_views
from courses import certificate_views
from courses import player_views
from courses import note_views
from courses import quiz_views
from courses import material_views

urlpatterns = [
    path('', include('courses.experience_urls')),
    path('courses/lesson/<int:lesson_id>/reaction/<slug:kind>/', player_views.lesson_reaction, name='lesson_reaction'),
    path('dashboard/meus-cursos/',student_views.my_courses,name='my_courses'),
    path('buscar/',student_views.search,name='member_search'),
    path('notificacoes/',notification_views.notifications,name='notifications'),
    path('notificacoes/lidas/',notification_views.read_all,name='notifications_read_all'),
    path('ao-vivo/<int:event_id>/lembrete/',live_views.remind,name='live_remind'),
    path('ao-vivo/<int:event_id>/<slug:kind>/',live_views.open_link,name='live_link'),
    path('suporte/',support_views.hub,name='support'),
    path('suporte/novo/',support_views.new_ticket,name='support_new'),
    path('suporte/chamados/<int:ticket_id>/',support_views.ticket_detail,name='support_ticket'),
    path('suporte/chamados/<int:ticket_id>/voto/',support_views.vote,name='support_vote'),
    re_path(r'^media/materials/', material_views.deny_direct_material),
    path('materiais/<slug:kind>/<int:material_id>/', material_views.open_material, name='material_open'),
    path('dashboard/ebooks/', material_views.ebooks, name='ebooks'),
    path('dashboard/cursos/<slug:course_slug>/avaliacao/', quiz_views.final_assessment, name='final_assessment'),
    path('quizzes/tentativas/<int:attempt_id>/submit-final/', quiz_views.submit_final, name='submit_final_quiz'),
    path('quizzes/<int:quiz_id>/start/', quiz_views.start, name='quiz_start'),
    path('quizzes/tentativas/<int:attempt_id>/answer/', quiz_views.answer, name='quiz_answer'),
    path('quizzes/tentativas/<int:attempt_id>/finish/', quiz_views.finish, name='quiz_finish'),
    path('quizzes/tentativas/<int:attempt_id>/', quiz_views.result, name='quiz_result'),
    path('courses/lesson/<int:lesson_id>/notes/', note_views.notes, name='lesson_notes'),
    path('courses/lesson/<int:lesson_id>/notes/<int:note_id>/delete/', note_views.delete_note, name='delete_lesson_note'),
    path('courses/lesson/<int:lesson_id>/heartbeat/', player_views.heartbeat, name='lesson_heartbeat'),
    path('courses/lesson/<int:lesson_id>/ended/', player_views.ended, name='lesson_ended'),
    path('webhooks/asaas/', asaas_webhook, name='asaas_webhook'),
    path('admin/', admin.site.urls),
    path('painel/', include('painel.urls')),
    path('ao-vivo/', live_views.agenda, name='live_classes'),
    path('certificados/', certificate_views.certificates, name='certificates'),
    path('certificado/verificar/', certificate_views.verify_certificate, name='verify_certificate'),
    path('senha/esqueci/', user_views.PasswordResetView.as_view(), name='password_reset'),
    path('senha/enviado/', user_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('senha/nova/<uidb64>/<token>/', user_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('senha/pronto/', user_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('primeiro-acesso/', user_views.first_access_view, name='first_access'),
    path('courses/lesson/<int:lesson_id>/complete/', student_views.complete_lesson, name='complete_lesson'),
    
    # Creator Portal
    path('creator/', RedirectView.as_view(pattern_name='painel:dashboard', permanent=True), name='creator_dashboard'),
    path('creator/course/new/', RedirectView.as_view(pattern_name='painel:course_new', permanent=True), name='course_create'),
    path('creator/course/<int:course_id>/edit/', RedirectView.as_view(pattern_name='painel:course_edit', permanent=True), name='course_edit'),
    path('creator/course/<int:course_id>/builder/', RedirectView.as_view(pattern_name='painel:course_lessons', permanent=True), name='course_builder'),
    path('creator/payments/', RedirectView.as_view(pattern_name='painel:settings', permanent=True), name='creator_payments'),
    path('creator/integrations/', RedirectView.as_view(pattern_name='painel:settings', permanent=True), name='creator_integrations'),
    
    # Landing & Main Catalog
    path('', course_views.landing, name='landing'),
    
    # User Authentication
    path('login/', user_views.login_view, name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('register/', user_views.register_view, name='register'),
    
    # Sales Checkouts
    path('courses/<slug:course_slug>/checkout/', sales_views.checkout, name='checkout'),
    path('courses/<slug:course_slug>/checkout/process/', sales_views.process_checkout, name='process_checkout'),
    
    # Public Course Preview
    path('courses/<slug:course_slug>/', course_views.course_preview, name='course_preview'),
    
    # Student Area & Player
    path('dashboard/', student_views.dashboard, name='dashboard'),
    path('dashboard/cursos/<slug:course_slug>/', student_views.member_course, name='member_course'),
    path('dashboard/recursos/<slug:section>/', student_views.member_section, name='member_section'),
    path('settings/', user_views.settings_view, name='settings'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/', student_views.lesson_detail, name='lesson_detail'),
    path('courses/lesson/<int:lesson_id>/toggle-progress/', student_views.toggle_progress, name='toggle_progress'),
    path('courses/<slug:course_slug>/certificate/', certificate_views.issue_certificate, name='issue_certificate'),
    
    path('community/new/', community_views.new_topic, name='community_new'),
    path('community/posts/<int:post_id>/', community_views.topic, name='community_topic'),
    path('community/posts/<int:post_id>/action/', community_views.topic_action, name='community_action'),
    # Discussion Forums
    path('community/', community_views.community_hub, name='community_hub'),
    path('community/post/new/', community_views.create_hub_post, name='create_hub_post'),
    path('courses/<slug:course_slug>/community/post/', community_views.create_post, name='create_post'),
    path('community/posts/<int:post_id>/comment/', community_views.create_comment, name='create_comment'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
