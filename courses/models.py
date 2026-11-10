from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from datetime import timedelta
from urllib.parse import parse_qs, urlparse, urlencode
from django.utils import timezone
from users.models import CreatorProfile, StudentProfile

class Category(models.Model):
    COLOR_CHOICES = [('blue', 'Azul'), ('teal', 'Verde-azulado'), ('slate', 'Cinza')]
    name = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='blue')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    @property
    def badge_class(self):
        return {'blue': 'badge--blue', 'teal': 'badge--teal', 'slate': 'badge--gray'}[self.color]

    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='courses/', null=True, blank=True)
    creator = models.ForeignKey(CreatorProfile, on_delete=models.CASCADE, related_name='courses')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    short_name = models.CharField(max_length=12, blank=True)
    cover_color = models.CharField(max_length=10, blank=True, choices=[
        ('blue', 'Azul'), ('blue-2', 'Azul escuro'), ('teal', 'Verde-azulado'),
        ('slate', 'Cinza'), ('ink', 'Escuro'),
    ])
    workload_hours = models.PositiveIntegerField(null=True, blank=True)
    learning_objectives = models.TextField(blank=True)
    target_audience = models.TextField(blank=True)
    live_calendar_url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    STATUS_CHOICES = [('draft', 'Rascunho'), ('published', 'Publicado'), ('archived', 'Arquivado')]
    ACCESS_CHOICES = [(None, 'Vitalício'), (6, '6 meses'), (12, '12 meses'), (24, '24 meses')]
    RELEASE_CHOICES = [('all', 'Tudo na matrícula'), ('scheduled', 'Programada por módulo')]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    tagline = models.CharField(max_length=160, blank=True, verbose_name='Chamada curta')
    access_months = models.PositiveSmallIntegerField(null=True, blank=True, choices=ACCESS_CHOICES, verbose_name='Prazo de acesso')
    release_mode = models.CharField(max_length=10, choices=RELEASE_CHOICES, default='all')
    notify_module_release = models.BooleanField(default=True)
    certificate_enabled = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    live_meet_url = models.URLField(blank=True, null=True, verbose_name="Link do Google Meet")
    live_schedule_embed = models.TextField(blank=True, null=True, verbose_name="Código de Incorporação da Agenda (Google Calendar)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_published(self):
        return self.status == 'published'

    @is_published.setter
    def is_published(self, value):
        if value:
            self.status = 'published'
        elif self.status == 'published':
            self.status = 'draft'

    @property
    def cover_class(self):
        color = self.cover_color or (self.category.color if self.category else 'blue')
        return f'cover--{color}'

    @property
    def objectives_list(self):
        return [line.strip() for line in self.learning_objectives.splitlines() if line.strip()]

    @property
    def calendar_embed_url(self):
        parsed = urlparse(self.live_calendar_url or '')
        if parsed.hostname != 'calendar.google.com':
            return ''
        source = parse_qs(parsed.query).get('src', [''])[0]
        if not source:
            return ''
        params = {'src': source, 'ctz': 'America/Campo_Grande', 'mode': 'AGENDA',
                  'showTitle': '0', 'showPrint': '0', 'showTabs': '0',
                  'showCalendars': '0', 'showTz': '0'}
        return 'https://calendar.google.com/calendar/embed?' + urlencode(params)

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    release_after_days = models.PositiveSmallIntegerField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def release_on(self, enrollment):
        """Data em que o módulo libera para a matrícula, ou None quando já nasce liberado."""
        if self.course.release_mode == 'all':
            return None
        if self.release_date:
            return self.release_date
        if self.release_after_days is not None:
            return timezone.localtime(enrollment.enrolled_at + timedelta(days=self.release_after_days)).date()
        return None

    def is_released_for(self, enrollment):
        """Liberação do módulo para uma matrícula (HANDOFF-v2 6.1)."""
        if self.course.release_mode == 'all':
            return True
        if self.release_date:
            return timezone.localdate() >= self.release_date
        if self.release_after_days is not None:
            return timezone.now() >= enrollment.enrolled_at + timedelta(days=self.release_after_days)
        return True

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

class ActiveLessonManager(models.Manager):
    """Manager padrão: esconde aulas excluídas com Desfazer (deleted_at preenchido)."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class Lesson(models.Model):
    STATUS_CHOICES = [('draft', 'Rascunho'), ('published', 'Publicada')]
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    vimeo_id = models.CharField(max_length=20, blank=True)
    vimeo_hash = models.CharField(max_length=40, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published')
    is_free_preview = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = ActiveLessonManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    @property
    def is_published(self):
        return self.status == 'published'

    def save(self, *args, **kwargs):
        if self.video_url:
            self.video_url = get_embed_url(self.video_url)
        parsed = urlparse(self.video_url)
        host = (parsed.hostname or '').lower()
        parts = [part for part in parsed.path.split('/') if part]
        self.vimeo_id = ''
        self.vimeo_hash = ''
        if host in ('vimeo.com', 'www.vimeo.com') and parts and parts[0].isdigit():
            self.vimeo_id = parts[0]
            if len(parts) > 1:
                self.vimeo_hash = parts[1][:40]
        elif host == 'player.vimeo.com' and len(parts) >= 2 and parts[0] == 'video' and parts[1].isdigit():
            self.vimeo_id = parts[1]
            self.vimeo_hash = parse_qs(parsed.query).get('h', [''])[0][:40]
        super().save(*args, **kwargs)

    @property
    def player_url(self):
        if not self.vimeo_id:
            return ''
        hash_part = f'h={self.vimeo_hash}&' if self.vimeo_hash else ''
        return f'https://player.vimeo.com/video/{self.vimeo_id}?{hash_part}dnt=1&title=0&byline=0&portrait=0'

    @property
    def youtube_embed_url(self):
        host = (urlparse(self.video_url).hostname or '').lower()
        return self.video_url if host in ('youtube.com', 'www.youtube.com', 'youtu.be') else ''


class LessonMaterial(models.Model):
    lesson = models.ForeignKey(Lesson, related_name='materials', on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    file = models.FileField(upload_to='materials/', blank=True, validators=[FileExtensionValidator(['pdf'])])
    url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def clean(self):
        super().clean()
        if self.file:
            if getattr(self.file.file, 'content_type', 'application/pdf') != 'application/pdf':
                raise ValidationError({'file': 'Envie um arquivo PDF.'})
            if self.file.size > settings.MATERIAL_MAX_MB * 1024 * 1024:
                raise ValidationError({'file': f'O PDF deve ter no máximo {settings.MATERIAL_MAX_MB} MB.'})

    def __str__(self):
        return self.title

class Progress(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='progress_records')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now=True)
    position_seconds = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'lesson')
        verbose_name_plural = "Progress records"

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.student.user.username} - {self.lesson.title} ({status})"

class Enrollment(models.Model):
    SOURCE_CHOICES = [
        ('purchase', 'Compra no site'), ('import', 'Importado'),
        ('manual', 'Liberado pelo admin'), ('signup', 'Cadastro no site'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual')
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    external_ref = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"


class LiveSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_sessions')
    title = models.CharField(max_length=160)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    host_name = models.CharField(max_length=80, blank=True)
    meet_url = models.URLField(blank=True)
    recording_url = models.URLField(blank=True)
    recording_until = models.DateField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['starts_at']

    def __str__(self):
        return f'{self.course.title} · {self.title}'

    @property
    def join_url(self):
        return self.meet_url or self.course.live_meet_url or ''

    def state(self, now=None):
        now = now or timezone.now()
        if now > self.ends_at:
            return 'ended'
        if now >= self.starts_at:
            return 'live'
        if now >= self.starts_at - timedelta(minutes=15):
            return 'soon'
        return 'scheduled'


class CourseFAQ(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=160)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.question


class CourseSlugRedirect(models.Model):
    old_slug = models.SlugField(unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='slug_redirects')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.old_slug} -> {self.course_id}'


class Certificate(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.PROTECT, related_name='certificate')
    code = models.CharField(max_length=12, unique=True)
    student_name = models.CharField(max_length=200)
    student_cpf = models.CharField(max_length=11)
    course_title = models.CharField(max_length=200)
    workload_hours = models.PositiveIntegerField(null=True)
    completed_at = models.DateTimeField()
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.code} · {self.student_name}'

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
