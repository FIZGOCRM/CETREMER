from django.contrib import admin

from .models import (
    GatewayAttempt,
    GatewayCharge,
    Offer,
    Order,
    OrderBump,
    Subscription,
    WebhookEvent,
)

admin.site.register(Order)
admin.site.register(OrderBump)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("course", "name", "kind", "amount", "term_type", "is_active")
    list_filter = ("kind", "is_active", "term_type")
    search_fields = ("course__title", "code")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "enrollment",
        "status",
        "amount",
        "next_due_on",
        "legacy_provider",
        "legacy_renewal_status",
    )
    list_filter = ("status", "legacy_provider", "legacy_renewal_status")
    search_fields = ("enrollment__student__user__email", "legacy_subscription_id")
    readonly_fields = tuple(
        field.name
        for field in Subscription._meta.fields
        if field.name != "legacy_renewal_status"
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class TechnicalRecordAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GatewayCharge)
class GatewayChargeAdmin(TechnicalRecordAdmin):
    list_display = (
        "reference",
        "environment",
        "order",
        "amount",
        "sync_state",
        "provider_status",
        "last_error_code",
    )
    list_filter = ("environment", "sync_state")
    search_fields = ("gateway_id", "customer_id", "order__student__user__email")


@admin.register(GatewayAttempt)
class GatewayAttemptAdmin(TechnicalRecordAdmin):
    list_display = (
        "charge",
        "operation",
        "result",
        "error_code",
        "http_status",
        "created_at",
    )
    list_filter = ("result",)


@admin.register(WebhookEvent)
class WebhookEventAdmin(TechnicalRecordAdmin):
    list_display = (
        "event_id",
        "environment",
        "event_type",
        "resource_id",
        "status",
        "received_at",
    )
    list_filter = ("environment", "event_type", "status")
    search_fields = ("event_id", "resource_id")
