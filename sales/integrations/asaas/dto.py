"""Allowlisted financial metadata. No card or payer identity payloads are retained."""

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from .errors import AsaasError


def resource_id(value, prefix):
    if (
        not isinstance(value, str)
        or not re.fullmatch(re.escape(prefix) + r"[A-Za-z0-9_-]{1,95}", value)
        or len(value) > 100
    ):
        raise AsaasError("invalid_response")
    return value


@dataclass(frozen=True)
class PaymentSnapshot:
    gateway_id: str
    customer_id: str
    amount: Decimal
    status: str
    billing_type: str
    due_on: date
    external_reference: str
    subscription_id: Optional[str] = None

    @classmethod
    def from_payload(cls, data):
        if not isinstance(data, dict):
            raise AsaasError("invalid_response")
        try:
            if isinstance(data["value"], bool):
                raise ValueError
            amount = Decimal(str(data["value"]))
            if (
                not amount.is_finite()
                or amount < 0
                or amount > Decimal("99999999.99")
                or amount != amount.quantize(Decimal("0.01"))
            ):
                raise ValueError
            due = data["dueDate"]
            if not isinstance(due, str) or len(due) != 10:
                raise ValueError
            due_on = date.fromisoformat(due)
            status, billing = data["status"], data["billingType"]
            reference = data.get("externalReference") or ""
            if (
                not isinstance(status, str)
                or not re.fullmatch(r"[A-Z_]{1,60}", status)
                or not isinstance(billing, str)
                or not re.fullmatch(r"[A-Z_]{1,30}", billing)
                or not isinstance(reference, str)
                or len(reference) > 200
            ):
                raise ValueError
            subscription = data.get("subscription")
            return cls(
                resource_id(data["id"], "pay_"),
                resource_id(data["customer"], "cus_"),
                amount.quantize(Decimal("0.01")),
                status,
                billing,
                due_on,
                reference,
                resource_id(subscription, "sub_") if subscription else None,
            )
        except (KeyError, TypeError, ValueError, InvalidOperation):
            raise AsaasError("invalid_response") from None


@dataclass(frozen=True)
class PaymentPage:
    payments: tuple[PaymentSnapshot, ...]
    has_more: bool
