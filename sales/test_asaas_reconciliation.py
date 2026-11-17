from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from django.test import TestCase

from courses import test_access_periods as fixtures
from courses.models import AccessPeriod
from sales.models import Order


class ReconciliationTests(TestCase):
    def setUp(self):
        fixtures.AccessPeriodTests.setUp(self)
        self.order = Order.objects.create(
            student=self.user.student_profile,
            course=self.course,
            amount="89.90",
            payment_method="PIX",
        )

    def prepare(self):
        from sales.payment_services import prepare_charge

        return prepare_charge(
            self.order,
            environment="sandbox",
            customer_id="cus_test123",
            due_on=date(2026, 12, 10),
        )

    def snapshot(self, charge, **changes):
        from sales.integrations.asaas.dto import PaymentSnapshot

        data = dict(
            gateway_id="pay_test123",
            customer_id="cus_test123",
            amount=Decimal("89.90"),
            status="RECEIVED",
            billing_type="PIX",
            due_on=date(2026, 12, 10),
            external_reference=str(charge.reference),
        )
        return PaymentSnapshot(**{**data, **changes})

    def test_prepare_is_local_idempotent_and_keeps_order_pending(self):
        from sales.models import GatewayCharge

        first, second = self.prepare(), self.prepare()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(GatewayCharge.objects.count(), 1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PENDING")
        self.assertIsNone(first.gateway_id)

    def test_recovery_by_reference_records_observation_without_approving_order(self):
        from sales.integrations.asaas.dto import PaymentPage
        from sales.payment_services import reconcile_charge

        charge = self.prepare()
        client = Mock()
        client.config.environment = "sandbox"
        client.find_payments.return_value = PaymentPage((self.snapshot(charge),), False)
        result = reconcile_charge(charge.pk, client=client)
        charge.refresh_from_db()
        self.assertEqual(result, "verified")
        self.assertEqual(charge.gateway_id, "pay_test123")
        self.assertEqual(charge.provider_status, "RECEIVED")
        self.assertEqual(charge.attempts.count(), 1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "PENDING")
        self.assertFalse(AccessPeriod.objects.exists())

    def test_mismatched_snapshot_is_quarantined_without_binding_gateway_id(self):
        from sales.integrations.asaas.dto import PaymentPage
        from sales.payment_services import reconcile_charge

        charge = self.prepare()
        for changes in [
            dict(amount=Decimal("1")),
            dict(customer_id="cus_other"),
            dict(external_reference="other"),
            dict(billing_type="CREDIT_CARD"),
            dict(due_on=date(2027, 1, 1)),
            dict(subscription_id="sub_unexpected"),
        ]:
            with self.subTest(changes=changes):
                client = Mock()
                client.config.environment = "sandbox"
                client.find_payments.return_value = PaymentPage(
                    (self.snapshot(charge, **changes),), False
                )
                self.assertEqual(reconcile_charge(charge.pk, client=client), "review")
                charge.refresh_from_db()
                self.assertIsNone(charge.gateway_id)

    def test_timeout_is_recorded_without_sensitive_error_or_creation_retry(self):
        from sales.integrations.asaas.errors import AsaasError
        from sales.payment_services import reconcile_charge

        charge = self.prepare()
        charge.gateway_id = "pay_test123"
        charge.save()
        client = Mock()
        client.config.environment = "sandbox"
        client.get_payment.side_effect = AsaasError("network_error")
        self.assertEqual(reconcile_charge(charge.pk, client=client), "error")
        self.assertEqual(charge.attempts.get().error_code, "network_error")
        client.get_payment.assert_called_once()
        client.create_payment.assert_not_called()

    def test_wrong_environment_is_rejected_before_network_access(self):
        from sales.integrations.asaas.errors import AsaasError
        from sales.payment_services import reconcile_charge

        charge = self.prepare()
        client = Mock()
        client.config.environment = "production"
        with self.assertRaises(AsaasError):
            reconcile_charge(charge.pk, client=client)
        client.get_payment.assert_not_called()
        client.find_payments.assert_not_called()

    def test_ambiguous_or_missing_reference_never_creates_a_payment(self):
        from sales.integrations.asaas.dto import PaymentPage
        from sales.payment_services import reconcile_charge

        charge = self.prepare()
        client = Mock()
        client.config.environment = "sandbox"
        client.find_payments.return_value = PaymentPage((), False)
        self.assertEqual(reconcile_charge(charge.pk, client=client), "error")
        client.find_payments.return_value = PaymentPage((self.snapshot(charge),), True)
        self.assertEqual(reconcile_charge(charge.pk, client=client), "review")
        charge.refresh_from_db()
        self.assertIsNone(charge.gateway_id)
        client.create_payment.assert_not_called()

    def test_local_preparation_rejects_changed_inputs(self):
        from django.core.exceptions import ValidationError

        from sales.payment_services import prepare_charge

        charge = self.prepare()
        with self.assertRaises(ValidationError):
            prepare_charge(
                self.order,
                environment="sandbox",
                customer_id="cus_changed",
                due_on=charge.due_on,
            )
        charge.refresh_from_db()
        self.assertEqual(charge.customer_id, "cus_test123")
