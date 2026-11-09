from django.db import models
from users.models import CreatorProfile, StudentProfile

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='courses/', null=True, blank=True)
    creator = models.ForeignKey(CreatorProfile, on_delete=models.CASCADE, related_name='courses')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_published = models.BooleanField(default=False)
    live_meet_url = models.URLField(blank=True, null=True, verbose_name="Link do Google Meet")
    live_schedule_embed = models.TextField(blank=True, null=True, verbose_name="Código de Incorporação da Agenda (Google Calendar)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

def get_embed_url(url):
    if not url:
        return ""
    if "/embed/" in url:
        return url
        
    # check youtu.be
    if "youtu.be/" in url:
        try:
            video_id = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        except Exception:
            pass
            
    # check youtube.com/watch
    if "watch?v=" in url:
        try:
            video_id = url.split("watch?v=")[1].split("&")[0].split("#")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        except Exception:
            pass
            
    # check youtube.com/shorts
    if "/shorts/" in url:
        try:
            video_id = url.split("/shorts/")[1].split("?")[0].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        except Exception:
            pass
            
    return url

class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    download_url = models.URLField(blank=True, null=True)
    download_name = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    def save(self, *args, **kwargs):
        if self.video_url:
            self.video_url = get_embed_url(self.video_url)
        super().save(*args, **kwargs)

class Progress(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='progress_records')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'lesson')
        verbose_name_plural = "Progress records"

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.student.user.username} - {self.lesson.title} ({status})"

class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"

class HeroBanner(models.Model):
    title = models.CharField(max_length=255, default="Torne-se preparado para salvar vidas em situações reais", verbose_name="Título do Banner")
    subtitle = models.TextField(default="Capacitação e simulação realística ministrada por médicos atuantes no SAMU e sala vermelha. Aprenda na prática a conduzir emergências cardiovasculares e suporte básico de vida.", verbose_name="Subtítulo")
    background_image = models.ImageField(upload_to='banners/', blank=True, null=True, verbose_name="Imagem de Fundo")
    background_video_url = models.URLField(blank=True, null=True, help_text="Link do YouTube ou arquivo MP4 (opcional)", verbose_name="URL de Vídeo de Fundo")
    primary_button_text = models.CharField(max_length=50, default="Explorar Cursos", verbose_name="Texto Botão Primário")
    primary_button_url = models.CharField(max_length=255, default="#catalog", verbose_name="Link Botão Primário")
    whatsapp_button_text = models.CharField(max_length=50, default="Falar pelo WhatsApp", verbose_name="Texto Botão WhatsApp")
    whatsapp_button_url = models.CharField(max_length=255, default="https://wa.me/5567996494740", verbose_name="Link Botão WhatsApp")
    is_active = models.BooleanField(default=True, verbose_name="Ativo?")

    def __str__(self):
        return f"Hero Banner: {self.title[:35]}"
