from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from users import views as user_views
from courses import views as course_views
from sales import views as sales_views
from community import views as community_views
from courses import creator_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Creator Portal
    path('creator/', creator_views.creator_dashboard, name='creator_dashboard'),
    path('creator/course/new/', creator_views.course_create_or_edit, name='course_create'),
    path('creator/course/<int:course_id>/edit/', creator_views.course_create_or_edit, name='course_edit'),
    path('creator/course/<int:course_id>/builder/', creator_views.course_builder, name='course_builder'),
    path('creator/payments/', creator_views.creator_payments, name='creator_payments'),
    path('creator/integrations/', creator_views.creator_integrations, name='creator_integrations'),
    
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
    path('dashboard/', course_views.dashboard, name='dashboard'),
    path('settings/', user_views.settings_view, name='settings'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/', course_views.lesson_detail, name='lesson_detail'),
    path('courses/lesson/<int:lesson_id>/toggle-progress/', course_views.toggle_progress, name='toggle_progress'),
    path('courses/<slug:course_slug>/certificate/', course_views.issue_certificate, name='issue_certificate'),
    
    # Discussion Forums
    path('community/', community_views.community_hub, name='community_hub'),
    path('community/post/new/', community_views.create_hub_post, name='create_hub_post'),
    path('courses/<slug:course_slug>/community/post/', community_views.create_post, name='create_post'),
    path('community/posts/<int:post_id>/comment/', community_views.create_comment, name='create_comment'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
