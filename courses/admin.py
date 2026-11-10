from django.contrib import admin
from .models import Category, Course, Module, Lesson, LessonMaterial, Progress, Enrollment, HeroBanner, Certificate

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'order', 'duration_seconds', 'video_url')

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    inlines = [LessonInline]
    ordering = ('course', 'order')

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ('title', 'order')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'is_published', 'live_meet_url', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'cover_image', 'creator', 'is_published')
        }),
        ('Preços e Vendas', {
            'fields': ('price',)
        }),
        ('Aulas Ao Vivo e Agendamento', {
            'fields': ('live_meet_url', 'live_schedule_embed'),
            'description': 'Configure as aulas ao vivo pelo Google Meet e insira o código de incorporação do Google Calendar para a agenda dos alunos.'
        }),
    )

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order', 'duration_seconds')
    list_filter = ('module__course', 'module')
    search_fields = ('title', 'description')

@admin.register(LessonMaterial)
class LessonMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'order')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color', 'order')

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('code', 'student_name', 'course_title', 'issued_at')

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'completed_at', 'lesson__module__course')
    search_fields = ('student__user__username', 'lesson__title')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')
    list_filter = ('course', 'enrolled_at')
    search_fields = ('student__user__username', 'course__title')

@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('title', 'subtitle')
