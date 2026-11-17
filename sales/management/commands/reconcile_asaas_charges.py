"""Explicit, bounded reconciliation; never run implicitly when receiving a webhook."""

from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from sales.gateway_models import GatewayCharge
from sales.integrations.asaas.client import AsaasClient
from sales.integrations.asaas.config import AsaasConfig
from sales.integrations.asaas.errors import AsaasError
from sales.payment_services import reconcile_charge


class Command(BaseCommand):
    help = "Confere cobranças no Asaas sem aprovar pedidos, gerar cobranças ou liberar acesso."

    def add_arguments(self, parser):
        parser.add_argument(
            "--charge", type=int, help="ID local de uma cobrança específica."
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Limite de consultas por execução (1–100).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas conta registros locais, sem acessar API ou gravar.",
        )

    def handle(self, *args, **options):
        limit, charge_id = options["limit"], options["charge"]
        if (
            type(limit) is not int
            or not 1 <= limit <= 100
            or (charge_id is not None and (type(charge_id) is not int or charge_id < 1))
        ):
            raise CommandError("Informe limite de 1 a 100 e identificador positivo.")
        config = AsaasConfig.from_settings()
        try:
            config.base_url
            if not options["dry_run"]:
                config.validate_api()
        except AsaasError as exc:
            raise CommandError(exc.code) from None
        records = GatewayCharge.objects.filter(environment=config.environment)
        if charge_id:
            records = records.filter(pk=charge_id)
            if not records.exists():
                raise CommandError("Cobrança não encontrada neste ambiente.")
        else:
            records = records.filter(sync_state__in=["pending", "error"])
        ids = list(
            records.order_by("checked_at", "id").values_list("id", flat=True)[:limit]
        )
        if options["dry_run"]:
            self.stdout.write(
                f"{len(ids)} cobranças locais selecionadas; nenhuma consulta ou gravação realizada."
            )
            return
        client = AsaasClient(config)
        results = Counter()
        try:
            for pk in ids:
                results[reconcile_charge(pk, client=client)] += 1
        except (AsaasError, DatabaseError):
            raise CommandError(
                "A conferência foi interrompida. Consulte os registros técnicos antes de repetir."
            ) from None
        self.stdout.write(
            f"Conferidas: {results['verified']}; revisão: {results['review']}; falhas: {results['error']}. Nenhum pedido aprovado ou acesso liberado."
        )
