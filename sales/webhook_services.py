"""Authenticate at the HTTP boundary; persist only allowlisted event metadata here."""

import hashlib
import json
import re
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .gateway_models import WebhookEvent
from .integrations.asaas.errors import AsaasError


class EventConflict(Exception):
    pass


def _text(value, limit):
    if (
        not isinstance(value, str)
        or not value
        or len(value) > limit
        or any(ord(c) < 32 for c in value)
    ):
        raise AsaasError("invalid_event")
    return value


def _money(value, *, signed=False):
    try:
        if isinstance(value, bool):
            raise ValueError
        amount = Decimal(str(value))
        minimum = Decimal("-99999999.99") if signed else Decimal("0")
        if (
            not amount.is_finite()
            or not minimum <= amount <= Decimal("99999999.99")
            or amount != amount.quantize(Decimal("0.01"))
        ):
            raise ValueError
        return format(amount, ".2f")
    except (InvalidOperation, ValueError):
        raise AsaasError("invalid_event") from None


def _financial_metadata(resource):
    clean = {}
    for key in ["value", "netValue", "originalValue", "interestValue"]:
        if resource.get(key) is not None:
            clean[key] = _money(resource[key], signed=key == "netValue")
    for key in [
        "originalDueDate",
        "confirmedDate",
        "paymentDate",
        "clientPaymentDate",
        "creditDate",
        "estimatedCreditDate",
    ]:
        if resource.get(key):
            clean[key] = _text(resource[key], 10)
    for key in ["deleted", "anticipated"]:
        if resource.get(key) is not None:
            if type(resource[key]) is not bool:
                raise AsaasError("invalid_event")
            clean[key] = resource[key]
    for key in ["discount", "fine", "interest", "chargeback"]:
        if resource.get(key) is None:
            continue
        value = resource[key]
        if not isinstance(value, dict):
            raise AsaasError("invalid_event")
        fields = {}
        for text_key in ["type", "status", "reason", "limitedDate"]:
            if value.get(text_key):
                fields[text_key] = _text(value[text_key], 100)
        if value.get("value") is not None:
            fields["value"] = _money(value["value"])
        if value.get("dueDateLimitDays") is not None:
            if (
                type(value["dueDateLimitDays"]) is not int
                or not 0 <= value["dueDateLimitDays"] <= 36500
            ):
                raise AsaasError("invalid_event")
            fields["dueDateLimitDays"] = value["dueDateLimitDays"]
        clean[key] = fields
    if resource.get("refunds") is not None:
        if not isinstance(resource["refunds"], list):
            raise AsaasError("invalid_event")
        refunds = []
        for refund in resource["refunds"]:
            if not isinstance(refund, dict):
                raise AsaasError("invalid_event")
            item = {}
            if refund.get("value") is not None:
                item["value"] = _money(refund["value"])
            for key in ["id", "status", "dateCreated"]:
                if refund.get(key):
                    item[key] = _text(refund[key], 100)
            refunds.append(item)
        clean["refunds"] = refunds
    return clean


def minimize_event(payload):
    if not isinstance(payload, dict):
        raise AsaasError("invalid_event")
    event_id = _text(payload.get("id"), 200)
    event_type = _text(payload.get("event"), 100)
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", event_type):
        raise AsaasError("invalid_event")
    result = {"id": event_id, "event": event_type}
    if payload.get("dateCreated") is not None:
        result["dateCreated"] = _text(payload["dateCreated"], 40)
    resource_id = ""
    for name in ["payment", "subscription"]:
        if name not in payload:
            continue
        resource = payload[name]
        if not isinstance(resource, dict):
            raise AsaasError("invalid_event")
        clean = {"id": _text(resource.get("id"), 100)}
        for key, limit in [
            ("customer", 100),
            ("externalReference", 200),
            ("subscription", 100),
            ("status", 60),
            ("billingType", 30),
            ("dueDate", 10),
        ]:
            if resource.get(key) not in (None, ""):
                clean[key] = _text(resource[key], limit)
        clean.update(_financial_metadata(resource))
        result[name] = clean
        resource_id = resource_id or clean["id"]
    if event_type.startswith("PAYMENT_") and "payment" not in result:
        raise AsaasError("invalid_event")
    return result, resource_id


@transaction.atomic
def receive_event(payload, *, environment):
    if environment not in {"sandbox", "production"}:
        raise AsaasError("invalid_configuration")
    clean, resource_id = minimize_event(payload)
    fingerprint = hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    event, created = WebhookEvent.objects.get_or_create(
        environment=environment,
        event_id=clean["id"],
        defaults={
            "event_type": clean["event"],
            "resource_id": resource_id,
            "payload": clean,
            "fingerprint": fingerprint,
        },
    )
    if not created and event.fingerprint != fingerprint:
        raise EventConflict("Conflicting webhook ID")
    return event, not created
