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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('painel/', include('painel.urls')),
    path('ao-vivo/', student_views.live_classes, name='live_classes'),
    path('certificados/', certificate_views.certificates, name='certificates'),
    path('certificado/verificar/', certificate_views.verify_certificate, name='verify_certificate'),
    path('senha/esqueci/', user_views.PasswordResetView.as_view(), name='password_reset'),
    path('senha/enviado/', user_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('senha/nova/<uidb64>/<token>/', user_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('senha/pronto/', user_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
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
    path('settings/', user_views.settings_view, name='settings'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/', student_views.lesson_detail, name='lesson_detail'),
    path('courses/lesson/<int:lesson_id>/toggle-progress/', course_views.toggle_progress, name='toggle_progress'),
    path('courses/<slug:course_slug>/certificate/', certificate_views.issue_certificate, name='issue_certificate'),
    
    # Discussion Forums
    path('community/', community_views.community_hub, name='community_hub'),
    path('community/post/new/', community_views.create_hub_post, name='create_hub_post'),
    path('courses/<slug:course_slug>/community/post/', community_views.create_post, name='create_post'),
    path('community/posts/<int:post_id>/comment/', community_views.create_comment, name='create_comment'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
