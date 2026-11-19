import json

from django.db import transaction
from django.db.models import F
from django.http import JsonResponse


@transaction.atomic
def reorder_items(request, parent, items):
    """Persist a permutation of the current scoped list, including inactive questions."""
    try:
        ids = json.loads(request.body)["ids"]
        if not isinstance(ids, list) or any(not isinstance(pk, str) or not pk.isascii()
                                             or not pk.isdecimal() or len(pk) > 18 for pk in ids):
            raise ValueError
        ids = [int(pk) for pk in ids]
    except (TypeError, ValueError, KeyError):
        return JsonResponse({"ok": False}, status=400)
    parent.__class__.objects.select_for_update().get(pk=parent.pk)
    current = {item.pk: item for item in items.select_for_update()}
    if len(ids) != len(current) or set(ids) != current.keys():
        return JsonResponse({"ok": False}, status=409)
    if ids:
        # Reserve free positions first to satisfy the unique active-question order.
        offset = max(max(item.order for item in current.values()), len(ids)) + 1
        items.update(order=F("order") + offset)
        ordered = [current[pk] for pk in ids]
        for position, item in enumerate(ordered, start=1):
            item.order = position
        items.model.objects.bulk_update(ordered, ["order"])
    return JsonResponse({"ok": True})
