import io
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from courses import test_access_periods as fixtures
from courses.models import Enrollment
from sales.models import Order
from users.models import User


class MigrationTests(TestCase):
    setUp = fixtures.AccessPeriodTests.setUp

    def row(self, *, course=None, email="imported@example.com"):
        return {
            "nome": "Aluno Importado",
            "email": email,
            "curso": (course or self.course).slug,
            "pago_de": (self.today - timedelta(days=12)).isoformat(),
            "pago_ate": (self.today + timedelta(days=17)).isoformat(),
            "proximo_vencimento": (self.today + timedelta(days=18)).isoformat(),
            "mensalidade": "89.90",
            "plataforma": "eduzz",
            "assinatura_anterior": "old-123",
            "renovacao_anterior": "pendente",
        }

    def csv(self, rows):
        import csv

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0]), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
        return SimpleUploadedFile("migration.csv", output.getvalue().encode("utf-8"))

    def parse(self, rows):
        from sales.migration_import import parse_subscription_csv

        return parse_subscription_csv(self.csv(rows))

    def test_preview_is_read_only_and_import_preserves_paid_period_without_orders(self):
        from courses.access import access_decision
        from sales.migration_services import import_subscription_periods
        from sales.models import Subscription

        rows = self.parse([self.row()])
        self.assertFalse(User.objects.filter(email="imported@example.com").exists())
        result = import_subscription_periods(rows, actor=self.creator)
        enrollment = Enrollment.objects.get(student__user__email="imported@example.com")
        self.assertEqual(enrollment.access_policy, "periods")
        self.assertTrue(access_decision(enrollment, on=self.today).allowed)
        self.assertEqual(
            enrollment.access_periods.get().ends_on, self.today + timedelta(days=18)
        )
        subscription = Subscription.objects.get(enrollment=enrollment)
        self.assertEqual(subscription.status, "migrating")
        self.assertEqual(subscription.amount, Decimal("89.90"))
        self.assertEqual(subscription.next_due_on, self.today + timedelta(days=18))
        self.assertEqual(subscription.offer.term_type, "unknown")
        self.assertFalse(subscription.offer.is_active)
        self.assertFalse(subscription.gateway_id)
        self.assertFalse(Order.objects.exists())
        self.assertEqual(result.imported, 1)

    def test_reimport_is_idempotent_but_conflicting_dates_are_rejected(self):
        from sales.migration_services import import_subscription_periods

        rows = self.parse([self.row()])
        import_subscription_periods(rows)
        import_subscription_periods(rows)
        enrollment = Enrollment.objects.get(student__user__email="imported@example.com")
        self.assertEqual(enrollment.access_periods.count(), 1)
        changed = self.row()
        changed["pago_ate"] = (self.today + timedelta(days=20)).isoformat()
        changed["proximo_vencimento"] = (self.today + timedelta(days=21)).isoformat()
        with self.assertRaises(ValidationError):
            import_subscription_periods(self.parse([changed]))
        self.assertEqual(enrollment.access_periods.count(), 1)

    def test_different_courses_can_use_same_email_and_distinct_dates(self):
        from courses.models import Course
        from sales.migration_services import import_subscription_periods
        from sales.models import Subscription

        other = Course.objects.create(
            title="Other", slug="other-migration", creator=self.creator.creator_profile
        )
        first, second = self.row(), self.row(course=other)
        second["pago_ate"] = (self.today + timedelta(days=25)).isoformat()
        second["proximo_vencimento"] = (self.today + timedelta(days=26)).isoformat()
        rows = self.parse([first, second])
        self.assertTrue(all(row["valid"] for row in rows))
        import_subscription_periods(rows)
        self.assertEqual(Subscription.objects.count(), 2)

    def test_invalid_dates_or_price_never_create_accounts(self):
        from sales.migration_services import import_subscription_periods

        for changes in [
            {"pago_ate": ""},
            {"proximo_vencimento": "2020-01-01"},
            {"pago_de": "31/02/2026"},
            {"mensalidade": "-2"},
            {"mensalidade": "NaN"},
            {"renovacao_anterior": "cancelada-talvez"},
        ]:
            with self.subTest(changes=changes):
                rows = self.parse([{**self.row(), **changes}])
                self.assertFalse(rows[0]["valid"])
                import_subscription_periods(rows)
                self.assertFalse(
                    User.objects.filter(email="imported@example.com").exists()
                )

    def test_existing_unrestricted_enrollment_is_not_silently_changed(self):
        from sales.migration_services import import_subscription_periods

        rows = self.parse([self.row(email=self.user.email)])
        with self.assertRaises(ValidationError):
            import_subscription_periods(rows)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.access_policy, "unrestricted")

    def test_monthly_offer_cannot_be_enabled_with_unknown_terms(self):
        from sales.models import Offer

        offer = Offer(
            course=self.course,
            code="monthly",
            name="Mensalidade",
            kind="monthly",
            amount="89.90",
            is_active=True,
        )
        with self.assertRaises(ValidationError):
            offer.full_clean()

    def test_import_view_requires_preview_and_does_not_reuse_old_preview_on_bad_upload(
        self,
    ):
        self.creator.is_staff = True
        self.creator.save()
        self.client.force_login(self.creator)
        url = reverse("painel:students_import")
        response = self.client.post(
            url, {"mode": "subscriptions", "file": self.csv([self.row()])}
        )
        self.assertContains(response, "89.90")
        self.assertFalse(User.objects.filter(email="imported@example.com").exists())
        self.client.post(
            url,
            {
                "mode": "subscriptions",
                "file": SimpleUploadedFile("bad.csv", b"wrong;headers\n1;2\n"),
            },
        )
        self.assertNotIn("import_preview", self.client.session)
        self.client.post(url, {"action": "confirm"})
        self.assertFalse(User.objects.filter(email="imported@example.com").exists())

    def test_confirm_requires_review_and_imports_without_charging_or_sending_email(
        self,
    ):
        from django.core import mail

        from sales.models import Subscription

        self.creator.is_staff = True
        self.creator.save()
        self.client.force_login(self.creator)
        url = reverse("painel:students_import")
        self.client.post(url, {"mode": "subscriptions", "file": self.csv([self.row()])})
        self.client.post(url, {"action": "confirm"})
        self.assertFalse(Subscription.objects.exists())
        self.client.post(url, {"action": "confirm", "confirm_periods": "on"})
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertNotIn("import_preview", self.client.session)
        self.assertFalse(Order.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_migration_csv_cannot_accidentally_grant_unrestricted_access(self):
        self.client.force_login(self.creator)
        url = reverse("painel:students_import")
        self.client.post(
            url,
            {
                "mode": "students",
                "courses": [self.course.id],
                "file": self.csv([self.row()]),
            },
        )
        self.assertNotIn("import_preview", self.client.session)
        self.client.post(url, {"action": "confirm"})
        self.assertFalse(User.objects.filter(email="imported@example.com").exists())

    def test_equivalent_amount_format_is_idempotent(self):
        from sales.migration_services import import_subscription_periods

        import_subscription_periods(self.parse([self.row()]))
        result = import_subscription_periods(
            self.parse([{**self.row(), "mensalidade": "89.9"}])
        )
        self.assertEqual(result.unchanged, 1)

    def test_conflicting_duplicates_in_same_csv_are_both_rejected(self):
        from sales.migration_services import import_subscription_periods

        second = {**self.row(), "mensalidade": "99.90"}
        rows = self.parse([self.row(), second])
        self.assertTrue(all(not row["valid"] for row in rows))
        import_subscription_periods(rows)
        self.assertFalse(User.objects.filter(email="imported@example.com").exists())

    def test_active_offer_with_reserved_code_is_not_reused_or_modified(self):
        from sales.migration_services import import_subscription_periods
        from sales.models import Offer

        offer = Offer.objects.create(
            course=self.course,
            code="legacy-89-90",
            name="Existing",
            kind="monthly",
            amount="89.90",
            term_type="continuous",
            is_active=True,
        )
        with self.assertRaises(ValidationError):
            import_subscription_periods(self.parse([self.row()]))
        offer.refresh_from_db()
        self.assertTrue(offer.is_active)
        self.assertFalse(User.objects.filter(email="imported@example.com").exists())
