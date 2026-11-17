from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from courses.models import Course
from users.models import StudentProfile

from .gateway_models import GatewayAttempt as GatewayAttempt
from .gateway_models import GatewayCharge as GatewayCharge
from .gateway_models import WebhookEvent as WebhookEvent


class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = "CREDIT_CARD", "Credit Card"
        PIX = "PIX", "Pix"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Reembolsado"

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="orders"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="orders")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=15, choices=PaymentMethod.choices, default=PaymentMethod.CREDIT_CARD
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.student.user.username} - {self.course.title} ({self.status})"


class OrderBump(models.Model):
    parent_course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="order_bumps"
    )
    bump_course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="as_order_bump"
    )
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Bump: Buy {self.parent_course.title} and get {self.bump_course.title} for ${self.discount_price}"


class Offer(models.Model):
    class Kind(models.TextChoices):
        MONTHLY = "monthly", "Mensalidade"
        ONE_OFF = "one_off", "Compra avulsa"

    class TermType(models.TextChoices):
        UNKNOWN = "unknown", "A confirmar"
        CONTINUOUS = "continuous", "Contínua"
        FIXED = "fixed", "Quantidade fixa de mensalidades"

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="offers")
    code = models.SlugField(max_length=60)
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    term_type = models.CharField(
        max_length=12, choices=TermType.choices, default=TermType.UNKNOWN
    )
    payment_count = models.PositiveIntegerField(null=True, blank=True)
    access_days = models.PositiveIntegerField(null=True, blank=True)
    grace_days = models.PositiveSmallIntegerField(default=3)
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course", "code"], name="offer_course_code_unique"
            ),
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="offer_amount_positive"
            ),
        ]

    def clean(self):
        super().clean()
        if self.kind == self.Kind.MONTHLY:
            if self.term_type == self.TermType.FIXED and not self.payment_count:
                raise ValidationError("Informe a quantidade de mensalidades.")
            if self.term_type != self.TermType.FIXED and self.payment_count is not None:
                raise ValidationError(
                    "Quantidade de mensalidades só se aplica ao prazo fixo."
                )
            if self.is_active and self.term_type == self.TermType.UNKNOWN:
                raise ValidationError(
                    "Confirme o tipo de recorrência antes de ativar a oferta."
                )
        if self.kind == self.Kind.ONE_OFF and self.is_active and not self.access_days:
            raise ValidationError("Defina o prazo de acesso da compra avulsa.")

    def __str__(self):
        return f"{self.course.title} · {self.name}"


class Subscription(models.Model):
    class Status(models.TextChoices):
        MIGRATING = "migrating", "Em migração, sem cobrança configurada"
        DRAFT = "draft", "Rascunho"
        ACTIVE = "active", "Ativa"
        CANCELED = "canceled", "Cancelada"

    enrollment = models.OneToOneField(
        "courses.Enrollment", on_delete=models.PROTECT, related_name="subscription"
    )
    offer = models.ForeignKey(
        Offer, on_delete=models.PROTECT, related_name="subscriptions"
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    next_due_on = models.DateField()
    gateway_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    legacy_provider = models.CharField(max_length=30, blank=True)
    legacy_subscription_id = models.CharField(max_length=100, blank=True)
    legacy_renewal_status = models.CharField(
        max_length=12,
        choices=[
            ("pendente", "A conferir"),
            ("ativa", "Ainda ativa"),
            ("encerrada", "Encerramento informado"),
        ],
        default="pendente",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="subscription_amount_positive"
            )
        ]

    def clean(self):
        super().clean()
        if self.offer_id and self.enrollment_id:
            if self.offer.course_id != self.enrollment.course_id:
                raise ValidationError(
                    "A oferta precisa pertencer ao curso da matrícula."
                )
            if self.offer.kind != Offer.Kind.MONTHLY:
                raise ValidationError("Assinatura exige uma oferta mensal.")
        if self.status == self.Status.ACTIVE and (
            not self.gateway_id or self.offer.term_type == Offer.TermType.UNKNOWN
        ):
            raise ValidationError(
                "Uma assinatura ativa exige gateway configurado e recorrência definida."
            )

    def __str__(self):
        return f"{self.enrollment} · {self.get_status_display()}"
