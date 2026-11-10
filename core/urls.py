from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from users import views as user_views
from courses import views as course_views
from sales import views as sales_views
from community import views as community_views
from courses import student_views
from courses import certificate_views
from courses import home_views, live_views, search_views
from users import account, notification_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('painel/', include('painel.urls')),
    path('ao-vivo/', live_views.live_classes, name='live_classes'),
    path('ao-vivo/<int:session_id>/convite.ics', live_views.live_session_ics, name='live_session_ics'),
    path('busca/', search_views.search, name='search'),
    path('avisos/lidos/', notification_views.notifications_read_all, name='notifications_read_all'),
    path('avisos/<int:notification_id>/', notification_views.notification_open, name='notification_open'),
    path('meus-cursos/<slug:course_slug>/', home_views.course_home, name='course_home'),
    path('passos/<str:key>/dispensar/', home_views.step_dismiss, name='step_dismiss'),
    path('passos/<str:key>/restaurar/', home_views.step_restore, name='step_restore'),
    path('certificados/', certificate_views.certificates, name='certificates'),
    path('certificados/<slug:course_slug>/emitir/', certificate_views.certificate_issue, name='certificate_issue'),
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
    path('creator/course/<int:course_id>/edit/', RedirectView.as_view(pattern_name='painel:course_settings', permanent=True), name='course_edit'),
    path('creator/course/<int:course_id>/builder/', RedirectView.as_view(pattern_name='painel:course_content', permanent=True), name='course_builder'),
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
    path('dashboard/', home_views.dashboard, name='dashboard'),
    path('settings/', account.settings_view, name='settings'),
    path('settings/sair-outros/', account.logout_others, name='logout_others'),
    path('settings/email/<str:token>/', account.email_confirm, name='email_confirm'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/', student_views.lesson_detail, name='lesson_detail'),
    path('courses/lesson/<int:lesson_id>/toggle/', student_views.toggle_progress, name='toggle_progress'),
    path('courses/lesson/<int:lesson_id>/position/', student_views.save_position, name='save_position'),
    path('courses/<slug:course_slug>/certificate/', certificate_views.issue_certificate, name='issue_certificate'),
    
    # Discussion Forums
    path('community/', community_views.community, name='community'),
    path('community/nova/', community_views.community_create, name='community_create'),
    path('community/sugestoes/', community_views.community_suggest, name='community_suggest'),
    path('community/<int:post_id>/responder/', community_views.community_reply, name='community_reply'),
    path('community/<int:post_id>/resolvida/', community_views.community_resolve, name='community_resolve'),
    path('community/<int:post_id>/apagar/', community_views.community_delete_own, name='community_delete_own'),
    path('courses/<slug:course_slug>/community/post/', community_views.create_post, name='create_post'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "core.error_views.permission_denied"
