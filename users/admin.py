from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, CreatorProfile

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Meta', {'fields': ('role', 'avatar', 'bio')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile Meta', {'fields': ('role', 'avatar', 'bio')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')

admin.site.register(User, CustomUserAdmin)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'level', 'title')
    search_fields = ('user__username', 'title')

@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'bank_name', 'pix_key', 'gateway_name')
    search_fields = ('user__username', 'company_name', 'pix_key')
