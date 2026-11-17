"""Import externally paid access, without scheduling or simulating payments."""

import hashlib
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction

from courses.models import AccessPeriod, Course, Enrollment
from users.services import enroll_student

from .migration_import import validate_migration_row
from .models import Offer, Subscription


@dataclass(frozen=True)
class MigrationResult:
    imported: int
    unchanged: int
    skipped: int


@transaction.atomic
def import_subscription_periods(rows, *, actor=None):
    validated = [validate_migration_row(row) for row in rows if row.get("valid")]
    imported = unchanged = 0
    for data in validated:
        course = Course.objects.get(slug=data["curso"])
        prior = Enrollment.objects.filter(
            student__user__email__iexact=data["email"], course=course
        ).first()
        if prior and prior.access_policy == Enrollment.AccessPolicy.UNRESTRICTED:
            raise ValidationError(
                f"{data['email']} já tem liberação sem prazo para {course.title}. Revise a matrícula antes de migrar."
            )
        user = enroll_student(
            course=course, email=data["email"], full_name=data["nome"], source="import"
        )
        enrollment = Enrollment.objects.get(student=user.student_profile, course=course)
        subscription = Subscription.objects.filter(enrollment=enrollment).first()
        fingerprint = "|".join(str(data[k]) for k in sorted(data) if k != "nome")
        reference = hashlib.sha256(fingerprint.encode()).hexdigest()
        existing = AccessPeriod.objects.filter(
            enrollment=enrollment,
            source=AccessPeriod.Source.LEGACY,
            reference=reference,
        ).first()
        if (
            existing
            and subscription
            and subscription.status == Subscription.Status.MIGRATING
        ):
            unchanged += 1
            continue
        if subscription or enrollment.access_periods.exists():
            raise ValidationError(
                f"{data['email']}: já existe um contrato ou período diferente. Revise antes de importar novamente."
            )
        code = "legacy-" + format(data["mensalidade"], ".2f").replace(".", "-")
        offer, _ = Offer.objects.get_or_create(
            course=course,
            code=code,
            defaults={
                "name": "Mensalidade importada",
                "kind": Offer.Kind.MONTHLY,
                "amount": data["mensalidade"],
                "term_type": Offer.TermType.UNKNOWN,
                "is_active": False,
                "grace_days": 3,
            },
        )
        if (
            offer.kind != Offer.Kind.MONTHLY
            or offer.amount != data["mensalidade"]
            or offer.is_active
            or offer.term_type != Offer.TermType.UNKNOWN
            or offer.payment_count is not None
            or offer.grace_days != 3
        ):
            raise ValidationError(
                f"A oferta reservada para migração de {course.title} foi alterada. Revise antes de importar; nenhuma oferta existente foi sobrescrita."
            )
        enrollment.access_policy = Enrollment.AccessPolicy.PERIODS
        enrollment.save(update_fields=["access_policy"])
        period = AccessPeriod(
            enrollment=enrollment,
            starts_on=data["pago_de"],
            ends_on=data["proximo_vencimento"],
            grace_days=3,
            source=AccessPeriod.Source.LEGACY,
            reference=reference,
            created_by=actor,
        )
        period.full_clean()
        period.save()
        subscription = Subscription(
            enrollment=enrollment,
            offer=offer,
            status=Subscription.Status.MIGRATING,
            amount=data["mensalidade"],
            next_due_on=data["proximo_vencimento"],
            legacy_provider=data["plataforma"],
            legacy_subscription_id=data["assinatura_anterior"],
            legacy_renewal_status=data["renovacao_anterior"],
        )
        subscription.full_clean()
        subscription.save()
        imported += 1
    return MigrationResult(imported, unchanged, len(rows) - len(validated))
