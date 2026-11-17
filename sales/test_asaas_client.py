import io
import json
from decimal import Decimal
from unittest.mock import Mock
from urllib.error import HTTPError

from django.test import SimpleTestCase, override_settings

PAYMENT = {
    "id": "pay_test123",
    "customer": "cus_test123",
    "value": 89.90,
    "status": "CONFIRMED",
    "billingType": "PIX",
    "dueDate": "2026-12-10",
    "externalReference": "local-reference",
    "subscription": None,
}


class Response(io.BytesIO):
    status = 200


class AsaasClientTests(SimpleTestCase):
    def make_client(self, *, environment="sandbox", enabled=True, response=None):
        from sales.integrations.asaas.client import AsaasClient
        from sales.integrations.asaas.config import AsaasConfig

        config = AsaasConfig(
            environment=environment,
            api_enabled=enabled,
            api_key="test-only-api-key",
            timeout=7,
        )
        transport = Mock(
            return_value=Response(json.dumps(response or PAYMENT).encode())
        )
        return AsaasClient(config, transport=transport), transport

    def test_get_payment_uses_fixed_https_host_headers_and_timeout(self):
        client, transport = self.make_client()
        payment = client.get_payment("pay_test123")
        request = transport.call_args.args[0]
        self.assertEqual(
            request.full_url, "https://api-sandbox.asaas.com/v3/payments/pay_test123"
        )
        self.assertEqual(request.get_header("Access_token"), "test-only-api-key")
        self.assertIn("CETREMER", request.get_header("User-agent"))
        self.assertEqual(request.get_method(), "GET")
        self.assertIsNone(request.data)
        self.assertEqual(transport.call_args.kwargs["timeout"], 7)
        self.assertEqual(payment.amount, Decimal("89.90"))
        self.assertEqual(payment.gateway_id, "pay_test123")

    def test_environment_is_explicit_and_secrets_are_not_in_repr(self):
        from sales.integrations.asaas.config import AsaasConfig

        client, transport = self.make_client(environment="production")
        client.get_payment("pay_test123")
        self.assertTrue(
            transport.call_args.args[0].full_url.startswith("https://api.asaas.com/v3/")
        )
        config = AsaasConfig(
            api_key="test-only-api-key", webhook_token="sensitive-webhook-token"
        )
        self.assertNotIn("test-only-api-key", repr(config))
        self.assertNotIn("sensitive-webhook-token", repr(config))

    def test_disabled_client_never_connects(self):
        from sales.integrations.asaas.errors import AsaasError

        client, transport = self.make_client(enabled=False)
        with self.assertRaises(AsaasError) as caught:
            client.get_payment("pay_test123")
        self.assertEqual(caught.exception.code, "integration_disabled")
        transport.assert_not_called()

    def test_create_payment_and_subscription_remain_blocked(self):
        from sales.integrations.asaas.errors import AsaasError

        client, transport = self.make_client()
        for method in [client.create_payment, client.create_subscription]:
            with self.assertRaises(AsaasError) as caught:
                method()
            self.assertEqual(caught.exception.code, "billing_not_enabled")
        transport.assert_not_called()

    def test_errors_are_safe_and_timeout_does_not_retry(self):
        from sales.integrations.asaas.errors import AsaasError

        for status, code in [
            (401, "authentication_failed"),
            (403, "authentication_failed"),
            (404, "not_found"),
            (429, "rate_limited"),
            (503, "provider_unavailable"),
            (302, "redirect_blocked"),
        ]:
            with self.subTest(status=status):
                client, transport = self.make_client()
                transport.side_effect = HTTPError(
                    "https://api-sandbox.asaas.com/v3/payments/pay_test123",
                    status,
                    "test-only-api-key",
                    {},
                    io.BytesIO(b"sensitive-body"),
                )
                with self.assertRaises(AsaasError) as caught:
                    client.get_payment("pay_test123")
                self.assertEqual(caught.exception.code, code)
                self.assertNotIn("test-only-api-key", str(caught.exception))
                self.assertNotIn("sensitive-body", str(caught.exception))
                transport.assert_called_once()
        client, transport = self.make_client()
        transport.side_effect = TimeoutError("test-only-api-key")
        with self.assertRaises(AsaasError) as caught:
            client.get_payment("pay_test123")
        self.assertEqual(caught.exception.code, "network_error")
        transport.assert_called_once()

    def test_invalid_ids_and_payloads_do_not_become_valid_payments(self):
        from sales.integrations.asaas.errors import AsaasError

        client, transport = self.make_client()
        with self.assertRaises(AsaasError):
            client.get_payment("https://attacker.invalid/key")
        transport.assert_not_called()
        for changes in [
            {"id": "pay_other"},
            {"value": "NaN"},
            {"value": -1},
            {"value": "1.001"},
            {"dueDate": "invalid"},
        ]:
            with self.subTest(changes=changes):
                client, _ = self.make_client(response={**PAYMENT, **changes})
                with self.assertRaises(AsaasError):
                    client.get_payment("pay_test123")

    def test_reference_search_is_bounded_and_encoded(self):
        client, transport = self.make_client(
            response={"data": [PAYMENT], "hasMore": False}
        )
        page = client.find_payments("local-reference", limit=2)
        self.assertEqual(len(page.payments), 1)
        self.assertFalse(page.has_more)
        self.assertIn(
            "externalReference=local-reference", transport.call_args.args[0].full_url
        )
        self.assertIn("limit=2", transport.call_args.args[0].full_url)

    @override_settings(
        ASAAS_API_ENABLED=False,
        ASAAS_ENVIRONMENT="sandbox",
        ASAAS_API_KEY="",
        ASAAS_WEBHOOK_ENABLED=False,
        ASAAS_WEBHOOK_TOKEN="",
        ASAAS_TIMEOUT="10",
    )
    def test_server_configuration_defaults_to_disabled(self):
        from sales.integrations.asaas.config import AsaasConfig

        config = AsaasConfig.from_settings()
        self.assertFalse(config.api_enabled)
        self.assertFalse(config.webhook_enabled)

    def test_bad_json_and_redirect_handler_are_fail_closed(self):
        from sales.integrations.asaas.client import NoRedirect
        from sales.integrations.asaas.errors import AsaasError

        self.assertIsNone(
            NoRedirect().redirect_request(
                None, None, 302, "", {}, "https://attacker.invalid/"
            )
        )
        client, transport = self.make_client()
        transport.return_value = Response(b"not-json")
        with self.assertRaises(AsaasError) as caught:
            client.get_payment("pay_test123")
        self.assertEqual(caught.exception.code, "invalid_response")

    def test_recognized_production_key_is_not_sent_to_sandbox(self):
        from sales.integrations.asaas.client import AsaasClient
        from sales.integrations.asaas.config import AsaasConfig
        from sales.integrations.asaas.errors import AsaasError

        transport = Mock()
        config = AsaasConfig(
            api_enabled=True, api_key="$aact_prod_test-key", environment="sandbox"
        )
        with self.assertRaises(AsaasError):
            AsaasClient(config, transport=transport).get_payment("pay_test123")
        transport.assert_not_called()

    def test_incomplete_http_response_is_a_safe_network_failure(self):
        from http.client import IncompleteRead

        from sales.integrations.asaas.errors import AsaasError

        client, transport = self.make_client()
        transport.side_effect = IncompleteRead(b"private-response-fragment")
        with self.assertRaises(AsaasError) as caught:
            client.get_payment("pay_test123")
        self.assertEqual(caught.exception.code, "network_error")
        self.assertNotIn("private-response-fragment", str(caught.exception))
