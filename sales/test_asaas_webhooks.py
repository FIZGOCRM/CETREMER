import json

from django.test import Client, TestCase, override_settings

TOKEN = "whsec_test_Q7p9v2j4r8n6c3t1b5d0a9z8x7w6"


@override_settings(
    ASAAS_ENVIRONMENT="sandbox",
    ASAAS_API_KEY="",
    ASAAS_API_ENABLED=False,
    ASAAS_WEBHOOK_ENABLED=True,
    ASAAS_WEBHOOK_TOKEN=TOKEN,
)
class AsaasWebhookTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.url = "/webhooks/asaas/"
        self.payload = {
            "id": "evt_test123",
            "event": "PAYMENT_RECEIVED",
            "dateCreated": "2026-11-13 12:00:00",
            "payment": {
                "id": "pay_test123",
                "customer": "cus_test123",
                "value": 89.90,
                "status": "RECEIVED",
                "billingType": "PIX",
                "externalReference": "local-reference",
                "creditCard": {"creditCardToken": "sensitive-card-token"},
                "cpfCnpj": "sensitive-document",
            },
        }

    def post(self, payload=None, *, token=TOKEN, secure=False):
        return self.client.post(
            self.url,
            json.dumps(payload or self.payload),
            content_type="application/json",
            HTTP_ASAAS_ACCESS_TOKEN=token,
            secure=secure,
        )

    def test_authentication_precedes_persistence(self):
        from sales.models import WebhookEvent

        for token in ["", "invalid"]:
            self.assertEqual(self.post(token=token).status_code, 401)
        self.assertFalse(WebhookEvent.objects.exists())

    def test_authenticated_event_is_minimized_and_never_grants_access(self):
        from courses.models import AccessPeriod, Enrollment
        from sales.models import Order, WebhookEvent

        self.assertEqual(self.post().status_code, 200)
        event = WebhookEvent.objects.get()
        self.assertEqual(event.status, "received")
        self.assertEqual(event.resource_id, "pay_test123")
        self.assertNotIn("sensitive-card-token", json.dumps(event.payload))
        self.assertNotIn("sensitive-document", json.dumps(event.payload))
        self.assertNotIn(TOKEN, json.dumps(event.payload))
        self.assertFalse(AccessPeriod.objects.exists())
        self.assertFalse(Enrollment.objects.exists())
        self.assertFalse(Order.objects.exists())

    def test_duplicate_is_accepted_once_and_conflict_preserves_first(self):
        from sales.models import WebhookEvent

        self.assertEqual(self.post().status_code, 200)
        self.assertTrue(self.post().json()["duplicate"])
        changed = {**self.payload, "payment": {**self.payload["payment"], "value": 999}}
        self.assertEqual(self.post(changed).status_code, 409)
        self.assertEqual(WebhookEvent.objects.count(), 1)
        self.assertEqual(
            WebhookEvent.objects.get().payload["payment"]["value"], "89.90"
        )

    def test_environments_do_not_share_deduplication_keys(self):
        from sales.models import WebhookEvent

        self.post()
        with override_settings(ASAAS_ENVIRONMENT="production"):
            self.assertEqual(self.post(secure=True).status_code, 200)
        self.assertEqual(WebhookEvent.objects.count(), 2)

    def test_disabled_or_invalid_configuration_fails_closed(self):
        for config in [
            dict(ASAAS_WEBHOOK_ENABLED=False),
            dict(ASAAS_WEBHOOK_TOKEN=""),
            dict(ASAAS_WEBHOOK_TOKEN=TOKEN, ASAAS_API_KEY=TOKEN),
        ]:
            with self.subTest(config=config), override_settings(**config):
                self.assertEqual(self.post().status_code, 503)

    def test_production_requires_https_and_only_post_is_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        with override_settings(ASAAS_ENVIRONMENT="production"):
            self.assertEqual(self.post().status_code, 400)

    def test_malformed_or_oversized_body_does_not_persist(self):
        from sales.models import WebhookEvent

        for body in [b"not-json", b"[]", b"{}", b"x" * (128 * 1024 + 1)]:
            response = self.client.post(
                self.url,
                body,
                content_type="application/json",
                HTTP_ASAAS_ACCESS_TOKEN=TOKEN,
            )
            self.assertIn(response.status_code, (400, 413))
        self.assertFalse(WebhookEvent.objects.exists())

    def test_unrecognized_event_is_retained_without_financial_effects(self):
        from sales.models import WebhookEvent

        self.assertEqual(
            self.post(
                {
                    "id": "evt_future",
                    "event": "FUTURE_PROVIDER_EVENT",
                    "unknown": {"secret": TOKEN},
                }
            ).status_code,
            200,
        )
        self.assertEqual(
            WebhookEvent.objects.get().payload,
            {"id": "evt_future", "event": "FUTURE_PROVIDER_EVENT"},
        )

    def test_database_failure_is_not_acknowledged_as_received(self):
        from unittest.mock import patch

        from django.db import DatabaseError

        with patch(
            "sales.webhook_views.receive_event",
            side_effect=DatabaseError("internal detail"),
        ):
            response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "internal detail", status_code=503)
        self.assertNotIn("received", response.json())

    def test_csrf_exemption_is_limited_to_webhook(self):
        response = self.client.post(
            "/courses/any-course/checkout/process/", {"name": "Student"}
        )
        self.assertEqual(response.status_code, 403)

    def test_changed_net_value_or_refund_is_not_silently_deduplicated(self):
        for field, initial, changed in [
            ("netValue", 80, 20),
            (
                "refunds",
                [{"value": 10, "status": "DONE"}],
                [{"value": 20, "status": "DONE"}],
            ),
        ]:
            with self.subTest(field=field):
                event = {
                    **self.payload,
                    "id": "evt_" + field,
                    "payment": {**self.payload["payment"], field: initial},
                }
                self.assertEqual(self.post(event).status_code, 200)
                event["payment"][field] = changed
                self.assertEqual(self.post(event).status_code, 409)
