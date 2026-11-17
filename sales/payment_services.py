"""Local preparation and read-only reconciliation. No financial or access approval."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from .gateway_models import GatewayAttempt, GatewayCharge
from .integrations.asaas.client import AsaasClient
from .integrations.asaas.dto import resource_id
from .integrations.asaas.errors import AsaasError
from .models import Order


@transaction.atomic
def prepare_charge(order, *, environment, customer_id, due_on, subscription=None):
    if order.status != Order.Status.PENDING:
        raise ValidationError("A preparação exige um pedido pendente.")
    resource_id(customer_id, "cus_")
    charge = GatewayCharge(
        order=order,
        environment=environment,
        customer_id=customer_id,
        due_on=due_on,
        amount=order.amount,
        billing_type=order.payment_method,
        subscription=subscription,
    )
    charge.full_clean(validate_unique=False, validate_constraints=False)
    existing = GatewayCharge.objects.filter(
        environment=environment, order=order
    ).first()
    if existing:
        fields = ["customer_id", "due_on", "amount", "billing_type", "subscription_id"]
        if any(getattr(existing, name) != getattr(charge, name) for name in fields):
            raise ValidationError(
                "O pedido já tem uma preparação diferente; revise antes de continuar."
            )
        return existing
    charge.save()
    return charge


def _matches(charge, payment):
    expected_subscription = (
        charge.subscription.gateway_id if charge.subscription_id else None
    )
    return (
        (not charge.gateway_id or charge.gateway_id == payment.gateway_id)
        and charge.customer_id == payment.customer_id
        and charge.amount == payment.amount
        and str(charge.reference) == payment.external_reference
        and charge.billing_type == payment.billing_type
        and charge.due_on == payment.due_on
        and expected_subscription == payment.subscription_id
        and (not charge.subscription_id or bool(expected_subscription))
    )


@transaction.atomic
def _record_result(charge_id, state, *, payment=None, error_code="", http_status=None):
    charge = GatewayCharge.objects.select_related("subscription").get(pk=charge_id)
    if payment is not None:
        if (
            not _matches(charge, payment)
            or GatewayCharge.objects.filter(
                environment=charge.environment, gateway_id=payment.gateway_id
            )
            .exclude(pk=charge.pk)
            .exists()
        ):
            state, error_code = "review", "snapshot_mismatch"
        elif state == "verified":
            charge.gateway_id = payment.gateway_id
            charge.provider_status = payment.status
    charge.sync_state = state
    charge.last_error_code = error_code
    charge.checked_at = timezone.now()
    charge.save(
        update_fields=[
            "gateway_id",
            "provider_status",
            "sync_state",
            "last_error_code",
            "checked_at",
        ]
    )
    GatewayAttempt.objects.create(
        charge=charge,
        operation="reconcile_payment",
        result=state,
        error_code=error_code,
        http_status=http_status,
    )
    return state


def reconcile_charge(charge_id, *, client=None):
    client = client or AsaasClient()
    charge = GatewayCharge.objects.select_related("subscription").get(pk=charge_id)
    if client.config.environment != charge.environment:
        raise AsaasError("environment_mismatch")
    try:
        if charge.gateway_id:
            payment = client.get_payment(charge.gateway_id)
        else:
            page = client.find_payments(str(charge.reference), limit=2)
            if page.has_more or len(page.payments) > 1:
                return _record_result(
                    charge.pk, "review", error_code="ambiguous_reference"
                )
            if not page.payments:
                return _record_result(charge.pk, "error", error_code="not_found")
            payment = page.payments[0]
    except AsaasError as exc:
        return _record_result(
            charge.pk, "error", error_code=exc.code, http_status=exc.http_status
        )
    try:
        return _record_result(charge.pk, "verified", payment=payment, http_status=200)
    except IntegrityError:
        return _record_result(
            charge.pk, "review", error_code="gateway_identity_conflict"
        )
