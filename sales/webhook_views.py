"""Narrow CSRF-exempt adapter authenticated using the webhook's own secret."""

import json
from decimal import Decimal

from django.db import DatabaseError
from django.http import JsonResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.http import json_error

from .integrations.asaas.config import AsaasConfig
from .integrations.asaas.errors import AsaasError
from .webhook_services import EventConflict, receive_event

MAX_WEBHOOK_BYTES = 128 * 1024


@csrf_exempt
@require_POST
def asaas_webhook(request):
    config = AsaasConfig.from_settings()
    try:
        config.validate_webhook()
    except AsaasError:
        return json_error(
            "Recepção de eventos indisponível.", status=503, code="webhook_unavailable"
        )
    if not constant_time_compare(
        request.headers.get("asaas-access-token", ""), config.webhook_token
    ):
        return json_error(
            "Autenticação inválida.", status=401, code="invalid_webhook_token"
        )
    if config.environment == "production" and not request.is_secure():
        return json_error("HTTPS obrigatório.", status=400, code="https_required")
    if request.content_type != "application/json":
        return json_error("Envie JSON.", status=415, code="json_required")
    try:
        length = int(request.META.get("CONTENT_LENGTH") or 0)
        if length > MAX_WEBHOOK_BYTES:
            return json_error(
                "Evento muito grande.", status=413, code="event_too_large"
            )
        body = request.read(MAX_WEBHOOK_BYTES + 1)
        if len(body) > MAX_WEBHOOK_BYTES:
            return json_error(
                "Evento muito grande.", status=413, code="event_too_large"
            )
        payload = json.loads(body, parse_float=Decimal)
        _, duplicate = receive_event(payload, environment=config.environment)
    except (ValueError, UnicodeError, RecursionError, AsaasError):
        return json_error("Evento inválido.", status=400, code="invalid_event")
    except EventConflict:
        return json_error(
            "Identificador de evento conflitante.", status=409, code="event_conflict"
        )
    except DatabaseError:
        return json_error(
            "Não foi possível persistir o evento.",
            status=503,
            code="event_not_persisted",
        )
    return JsonResponse({"received": True, "duplicate": duplicate})
