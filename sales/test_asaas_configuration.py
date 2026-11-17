import io
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from core.crypto import encrypt
from painel import tests as panel_fixtures
from sales import test_asaas_reconciliation as charge_fixtures
from users.models import SiteSettings


class GatewayPanelConfigurationTests(TestCase):
    setUp = panel_fixtures.PanelFlowTests.setUp

    @override_settings(
        ASAAS_ENVIRONMENT="sandbox",
        ASAAS_API_ENABLED=False,
        ASAAS_API_KEY="server-only-secret",
        ASAAS_WEBHOOK_ENABLED=False,
        ASAAS_WEBHOOK_TOKEN="server-webhook-secret",
    )
    def test_legacy_fields_are_preserved_but_not_editable_or_used(self):
        site = SiteSettings.load()
        site.gateway_name = "LEGACY_PROVIDER"
        site.gateway_key_encrypted = encrypt("legacy-sensitive-value")
        site.gateway_sandbox = True
        site.save()
        previous = site.gateway_key_encrypted
        self.client.post(
            reverse("painel:settings"),
            {
                "gateway_name": "ATTACKER_PROVIDER",
                "gateway_key": "replacement-key",
                "gateway_sandbox": "",
                "school_name": "CETREMER",
            },
        )
        site.refresh_from_db()
        self.assertEqual(site.gateway_key_encrypted, previous)
        self.assertEqual(site.gateway_name, "LEGACY_PROVIDER")
        self.assertTrue(site.gateway_sandbox)
        response = self.client.get(reverse("painel:settings"))
        self.assertTemplateUsed(response, "base_painel_gomut.html")
        for secret in [
            "server-only-secret",
            "server-webhook-secret",
            "legacy-sensitive-value",
            "replacement-key",
        ]:
            self.assertNotContains(response, secret)
        self.assertNotContains(response, 'name="gateway_key"')

    def test_django_admin_also_hides_legacy_gateway_configuration(self):
        from django.contrib import admin
        from django.test import RequestFactory

        from users.models import CreatorProfile

        request = RequestFactory().get("/admin/")
        request.user = self.admin
        for model, names in [
            (
                SiteSettings,
                ["gateway_name", "gateway_key_encrypted", "gateway_sandbox"],
            ),
            (
                CreatorProfile,
                ["gateway_name", "gateway_api_key", "asaas_token", "asaas_sandbox"],
            ),
        ]:
            form = admin.site._registry[model].get_form(request)
            for name in names:
                self.assertNotIn(name, form.base_fields)


@override_settings(ASAAS_ENVIRONMENT="sandbox", ASAAS_API_ENABLED=False)
class ReconciliationCommandTests(TestCase):
    def setUp(self):
        charge_fixtures.ReconciliationTests.setUp(self)

    def test_dry_run_does_not_call_api_or_change_records(self):
        from sales.models import GatewayAttempt

        charge = charge_fixtures.ReconciliationTests.prepare(self)
        output = io.StringIO()
        with patch("sales.payment_services.AsaasClient") as client:
            call_command("reconcile_asaas_charges", dry_run=True, stdout=output)
        client.assert_not_called()
        self.assertIn("1", output.getvalue())
        self.assertFalse(GatewayAttempt.objects.exists())
        charge.refresh_from_db()
        self.assertEqual(charge.sync_state, "pending")

    def test_disabled_configuration_and_invalid_limits_fail_safely(self):
        for options in [{}, {"limit": 0}, {"limit": 101}, {"charge": -1}]:
            with self.subTest(options=options), self.assertRaises(CommandError):
                call_command("reconcile_asaas_charges", **options)
