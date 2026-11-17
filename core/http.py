"""JSON error contract for application endpoints."""

from django.http import JsonResponse


def json_error(message, *, status, code):
    return JsonResponse(
        {"status": "error", "code": code, "message": message, "error": message},
        status=status,
    )
