from urllib.parse import parse_qs, urlencode, urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

from users.models import CreatorProfile, StudentProfile


class Category(models.Model):
    COLOR_CHOICES = [("blue", "Azul"), ("teal", "Verde-azulado"), ("slate", "Cinza")]
    name = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default="blue")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    @property
    def badge_class(self):
        return {"blue": "badge--blue", "teal": "badge--teal", "slate": "badge--gray"}[
            self.color
        ]

    def __str__(self):
        return self.name


class Course(models.Model):
    plan_months = models.PositiveSmallIntegerField(default=12)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="courses/", null=True, blank=True)
    creator = models.ForeignKey(
        CreatorProfile, on_delete=models.CASCADE, related_name="courses"
    )
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL
    )
    short_name = models.CharField(max_length=12, blank=True)
    cover_color = models.CharField(
        max_length=10,
        blank=True,
        choices=[
            ("blue", "Azul"),
            ("blue-2", "Azul escuro"),
            ("teal", "Verde-azulado"),
            ("slate", "Cinza"),
            ("ink", "Escuro"),
        ],
    )
    workload_hours = models.PositiveIntegerField(null=True, blank=True)
    learning_objectives = models.TextField(blank=True)
    target_audience = models.TextField(blank=True)
    live_calendar_url = models.URLField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_published = models.BooleanField(default=False)
    live_meet_url = models.URLField(
        blank=True, null=True, verbose_name="Link do Google Meet"
    )
    live_schedule_embed = models.TextField(
        blank=True,
        null=True,
        verbose_name="Código de Incorporação da Agenda (Google Calendar)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def cover_class(self):
        color = self.cover_color or (self.category.color if self.category else "blue")
        return f"cover--{color}"

    @property
    def objectives_list(self):
        return [
            line.strip()
            for line in self.learning_objectives.splitlines()
            if line.strip()
        ]

    @property
    def calendar_embed_url(self):
        parsed = urlparse(self.live_calendar_url or "")
        if parsed.hostname != "calendar.google.com":
            return ""
        source = parse_qs(parsed.query).get("src", [""])[0]
        if not source:
            return ""
        params = {
            "src": source,
            "ctz": "America/Campo_Grande",
            "mode": "AGENDA",
            "showTitle": "0",
            "showPrint": "0",
            "showTabs": "0",
            "showCalendars": "0",
            "showTz": "0",
        }
        return "https://calendar.google.com/calendar/embed?" + urlencode(params)


class Module(models.Model):
    status = models.CharField(max_length=12, choices=[('draft', 'Rascunho'), ('published', 'Publicado')], default='published')
    release_month = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        constraints = [models.CheckConstraint(check=models.Q(release_month__gte=1), name='module_release_positive')]

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
    status = models.CharField(max_length=12, choices=[('draft', 'Rascunho'), ('published', 'Publicado')], default='published')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    vimeo_id = models.CharField(max_length=20, blank=True)
    vimeo_hash = models.CharField(max_length=40, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    def save(self, *args, **kwargs):
        if self.video_url:
            self.video_url = get_embed_url(self.video_url)
        parsed = urlparse(self.video_url)
        host = (parsed.hostname or "").lower()
        parts = [part for part in parsed.path.split("/") if part]
        self.vimeo_id = ""
        self.vimeo_hash = ""
        if host in ("vimeo.com", "www.vimeo.com") and parts and parts[0].isdigit():
            self.vimeo_id = parts[0]
            if len(parts) > 1:
                self.vimeo_hash = parts[1][:40]
        elif (
            host == "player.vimeo.com"
            and len(parts) >= 2
            and parts[0] == "video"
            and parts[1].isdigit()
        ):
            self.vimeo_id = parts[1]
            self.vimeo_hash = parse_qs(parsed.query).get("h", [""])[0][:40]
        super().save(*args, **kwargs)

    @property
    def player_url(self):
        if not self.vimeo_id:
            return ""
        hash_part = f"h={self.vimeo_hash}&" if self.vimeo_hash else ""
        return f"https://player.vimeo.com/video/{self.vimeo_id}?{hash_part}dnt=1&title=0&byline=0&portrait=0"

    @property
    def youtube_embed_url(self):
        host = (urlparse(self.video_url).hostname or "").lower()
        return (
            self.video_url
            if host in ("youtube.com", "www.youtube.com", "youtu.be")
            else ""
        )


class LessonMaterial(models.Model):
    lesson = models.ForeignKey(
        Lesson, related_name="materials", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=120)
    file = models.FileField(
        upload_to="materials/", blank=True, validators=[FileExtensionValidator(["pdf"])]
    )
    url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def clean(self):
        super().clean()
        if self.file:
            if (
                getattr(self.file.file, "content_type", "application/pdf")
                != "application/pdf"
            ):
                raise ValidationError({"file": "Envie um arquivo PDF."})
            if self.file.size > settings.MATERIAL_MAX_MB * 1024 * 1024:
                raise ValidationError(
                    {"file": f"O PDF deve ter no máximo {settings.MATERIAL_MAX_MB} MB."}
                )

    def __str__(self):
        return self.title


class Progress(models.Model):
    last_position_seconds = models.FloatField(default=0, validators=[MinValueValidator(0)])
    watched_seconds = models.PositiveIntegerField(default=0)
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="progress_records"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="student_progress"
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "lesson")
        verbose_name_plural = "Progress records"

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        return f"{self.student.user.username} - {self.lesson.title} ({status})"


class Quiz(models.Model):
    kind = models.CharField(max_length=10, choices=[('lesson', 'Da aula'), ('final', 'Avaliação final')])
    lesson = models.OneToOneField(Lesson, null=True, blank=True, on_delete=models.PROTECT, related_name='quiz')
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='quizzes')
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(kind='lesson', lesson__isnull=False) | models.Q(kind='final', lesson__isnull=True), name='quiz_kind_lesson_valid'),
            models.UniqueConstraint(fields=['course'], condition=models.Q(kind='final'), name='one_final_quiz_per_course'),
        ]

    def clean(self):
        if self.lesson_id and self.lesson.module.course_id != self.course_id:
            raise ValidationError('O quiz e a aula devem pertencer ao mesmo curso.')


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.PROTECT, related_name='questions')
    order = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    text = models.TextField()
    explanation = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        constraints = [models.UniqueConstraint(fields=['quiz', 'order'], condition=models.Q(is_active=True), name='active_question_order_unique')]


class QuizChoice(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.PROTECT, related_name='choices')
    order = models.PositiveSmallIntegerField()
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['question', 'order'], condition=models.Q(is_active=True), name='active_choice_order_unique'),
            models.UniqueConstraint(fields=['question'], condition=models.Q(is_correct=True, is_active=True), name='one_active_correct_choice'),
            models.CheckConstraint(check=models.Q(order__gte=1, order__lte=4), name='choice_order_one_to_four'),
        ]


class QuizAttempt(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.PROTECT, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    correct = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    score_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    answers = models.JSONField(default=dict)
    question_snapshot = models.JSONField(default=list)

    class Meta:
        ordering = ['-started_at', '-id']


class LessonNote(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='lesson_notes')
    lesson = models.ForeignKey(Lesson, on_delete=models.PROTECT, related_name='notes')
    position_seconds = models.PositiveIntegerField(default=0)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position_seconds', 'created_at', 'id']


class StudyDay(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name='study_days')
    date = models.DateField()
    seconds = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['student', 'date'], name='study_student_date_unique')]


class ActivityEvent(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name='activity_events')
    kind = models.CharField(max_length=40)
    lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.PROTECT)
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.PROTECT)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']


class Enrollment(models.Model):
    plan_started_on = models.DateField(null=True, blank=True)
    admin_note = models.TextField(blank=True)
    class AccessPolicy(models.TextChoices):
        UNRESTRICTED = "unrestricted", "Liberação administrativa sem prazo"
        PERIODS = "periods", "Acesso por períodos quitados"

    SOURCE_CHOICES = [
        ("purchase", "Compra no site"),
        ("import", "Importado"),
        ("manual", "Liberado pelo admin"),
        ("signup", "Cadastro no site"),
    ]
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default="manual")
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    access_policy = models.CharField(
        max_length=15, choices=AccessPolicy.choices, default=AccessPolicy.UNRESTRICTED
    )

    class Meta:
        unique_together = ("student", "course")

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"


class AccessPeriod(models.Model):
    """A paid or explicitly granted interval; ends_on is exclusive."""

    class Source(models.TextChoices):
        LEGACY = "legacy", "Quitado em outra plataforma"
        PAYMENT = "payment", "Pagamento confirmado"
        MANUAL = "manual", "Concessão administrativa"

    enrollment = models.ForeignKey(
        Enrollment, related_name="access_periods", on_delete=models.PROTECT
    )
    starts_on = models.DateField()
    ends_on = models.DateField()
    grace_days = models.PositiveSmallIntegerField(default=0)
    ended_early = models.BooleanField(default=False)
    source = models.CharField(max_length=12, choices=Source.choices)
    reference = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["starts_on", "id"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(ends_on__gt=models.F("starts_on")) | models.Q(ends_on=models.F('starts_on'), ended_early=True, grace_days=0),
                name="access_period_dates_valid",
            ),
            models.UniqueConstraint(
                fields=["enrollment", "source", "reference"],
                name="access_period_reference_unique",
            ),
        ]

    def clean(self):
        super().clean()
        empty_ended = self.ends_on == self.starts_on and self.ended_early and self.grace_days == 0
        if self.starts_on and self.ends_on and self.ends_on <= self.starts_on and not empty_ended:
            raise ValidationError("O fim do período deve ser posterior ao início.")


class AccessChange(models.Model):
    class Action(models.TextChoices):
        CREATED = 'created', 'Criado'
        ENDED = 'ended_early', 'Encerrado antecipadamente'
        REACTIVATED = 'reactivated', 'Reativado'
        CORRECTED = 'corrected', 'Datas corrigidas'

    enrollment = models.ForeignKey(Enrollment, on_delete=models.PROTECT, related_name='access_changes')
    action = models.CharField(max_length=20, choices=Action.choices)
    old_starts_on = models.DateField(null=True, blank=True)
    old_ends_on = models.DateField(null=True, blank=True)
    new_starts_on = models.DateField()
    new_ends_on = models.DateField()
    reason_code = models.CharField(max_length=30, blank=True)
    reason_text = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']


class Certificate(models.Model):
    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.PROTECT, related_name="certificate"
    )
    code = models.CharField(max_length=12, unique=True)
    student_name = models.CharField(max_length=200)
    student_cpf = models.CharField(max_length=11)
    course_title = models.CharField(max_length=200)
    workload_hours = models.PositiveIntegerField(null=True)
    completed_at = models.DateTimeField()
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} · {self.student_name}"


class HeroBanner(models.Model):
    title = models.CharField(
        max_length=255,
        default="Torne-se preparado para salvar vidas em situações reais",
        verbose_name="Título do Banner",
    )
    subtitle = models.TextField(
        default="Capacitação e simulação realística ministrada por médicos atuantes no SAMU e sala vermelha. Aprenda na prática a conduzir emergências cardiovasculares e suporte básico de vida.",
        verbose_name="Subtítulo",
    )
    background_image = models.ImageField(
        upload_to="banners/", blank=True, null=True, verbose_name="Imagem de Fundo"
    )
    background_video_url = models.URLField(
        blank=True,
        null=True,
        help_text="Link do YouTube ou arquivo MP4 (opcional)",
        verbose_name="URL de Vídeo de Fundo",
    )
    primary_button_text = models.CharField(
        max_length=50, default="Explorar Cursos", verbose_name="Texto Botão Primário"
    )
    primary_button_url = models.CharField(
        max_length=255, default="#catalog", verbose_name="Link Botão Primário"
    )
    whatsapp_button_text = models.CharField(
        max_length=50,
        default="Falar pelo WhatsApp",
        verbose_name="Texto Botão WhatsApp",
    )
    whatsapp_button_url = models.CharField(
        max_length=255,
        default="https://wa.me/5567996494740",
        verbose_name="Link Botão WhatsApp",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo?")

    def __str__(self):
        return f"Hero Banner: {self.title[:35]}"
