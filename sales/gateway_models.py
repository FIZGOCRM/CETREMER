"""Technical gateway records, separate from business approval and access grants."""

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class GatewayEnvironment(models.TextChoices):
    SANDBOX = "sandbox", "Sandbox"
    PRODUCTION = "production", "Produção"


class GatewayCharge(models.Model):
    class SyncState(models.TextChoices):
        PENDING = "pending", "Aguardando consulta"
        VERIFIED = "verified", "Correspondência conferida, sem aprovação financeira"
        REVIEW = "review", "Revisão necessária"
        ERROR = "error", "Falha na consulta"

    order = models.ForeignKey(
        "sales.Order", on_delete=models.PROTECT, related_name="gateway_charges"
    )
    subscription = models.ForeignKey(
        "sales.Subscription",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="gateway_charges",
    )
    environment = models.CharField(max_length=12, choices=GatewayEnvironment.choices)
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    gateway_id = models.CharField(max_length=100, null=True, blank=True)
    customer_id = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    billing_type = models.CharField(
        max_length=15, choices=[("PIX", "Pix"), ("CREDIT_CARD", "Cartão")]
    )
    due_on = models.DateField()
    provider_status = models.CharField(max_length=60, blank=True)
    sync_state = models.CharField(
        max_length=12, choices=SyncState.choices, default=SyncState.PENDING
    )
    last_error_code = models.CharField(max_length=60, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "order"], name="charge_environment_order_unique"
            ),
            models.UniqueConstraint(
                fields=["environment", "gateway_id"],
                name="charge_environment_id_unique",
            ),
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="charge_amount_positive"
            ),
        ]

    def clean(self):
        super().clean()
        if self.subscription_id and self.order_id:
            enrollment = self.subscription.enrollment
            if (
                enrollment.student_id != self.order.student_id
                or enrollment.course_id != self.order.course_id
            ):
                raise ValidationError(
                    "Pedido e assinatura precisam corresponder ao mesmo aluno/curso."
                )

    def __str__(self):
        return f"{self.reference} · {self.environment} · {self.sync_state}"


class GatewayAttempt(models.Model):
    charge = models.ForeignKey(
        GatewayCharge, on_delete=models.PROTECT, related_name="attempts"
    )
    operation = models.CharField(max_length=30)
    result = models.CharField(max_length=12, choices=GatewayCharge.SyncState.choices)
    error_code = models.CharField(max_length=60, blank=True)
    http_status = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class WebhookEvent(models.Model):
    environment = models.CharField(max_length=12, choices=GatewayEnvironment.choices)
    event_id = models.CharField(max_length=200)
    event_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, blank=True)
    payload = models.JSONField(default=dict)
    fingerprint = models.CharField(max_length=64)
    status = models.CharField(
        max_length=12,
        default="received",
        choices=[("received", "Recebido, sem efeito financeiro")],
    )
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "event_id"],
                name="webhook_environment_event_unique",
            )
        ]

    def __str__(self):
        return f"{self.environment} · {self.event_id} · {self.event_type}"
