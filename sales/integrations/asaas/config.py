"""One authoritative configuration, supplied by server settings, not legacy DB fields."""

import math
from dataclasses import dataclass, field

from django.conf import settings

from .errors import AsaasError

HOSTS = {
    "sandbox": "https://api-sandbox.asaas.com/v3",
    "production": "https://api.asaas.com/v3",
}


@dataclass(frozen=True)
class AsaasConfig:
    environment: str = "sandbox"
    api_enabled: bool = False
    webhook_enabled: bool = False
    api_key: str = field(default="", repr=False)
    webhook_token: str = field(default="", repr=False)
    timeout: float = 10

    @classmethod
    def from_settings(cls):
        return cls(
            environment=getattr(settings, "ASAAS_ENVIRONMENT", "sandbox"),
            api_enabled=getattr(settings, "ASAAS_API_ENABLED", False),
            webhook_enabled=getattr(settings, "ASAAS_WEBHOOK_ENABLED", False),
            api_key=getattr(settings, "ASAAS_API_KEY", ""),
            webhook_token=getattr(settings, "ASAAS_WEBHOOK_TOKEN", ""),
            timeout=getattr(settings, "ASAAS_TIMEOUT", 10),
        )

    @property
    def base_url(self):
        if self.environment not in HOSTS:
            raise AsaasError("invalid_configuration")
        return HOSTS[self.environment]

    def validate_api(self):
        if self.api_enabled is not True:
            raise AsaasError("integration_disabled")
        self.base_url
        if (
            not isinstance(self.api_key, str)
            or not self.api_key
            or len(self.api_key) > 8192
            or any(not 33 <= ord(c) <= 126 for c in self.api_key)
        ):
            raise AsaasError("invalid_configuration")
        if (
            self.api_key.startswith("$aact_prod_") and self.environment != "production"
        ) or (self.api_key.startswith("$aact_hmlg_") and self.environment != "sandbox"):
            raise AsaasError("invalid_configuration")
        try:
            timeout = float(self.timeout)
        except (TypeError, ValueError):
            raise AsaasError("invalid_configuration") from None
        if not math.isfinite(timeout) or not 1 <= timeout <= 30:
            raise AsaasError("invalid_configuration")

    def validate_webhook(self):
        if self.webhook_enabled is not True:
            raise AsaasError("integration_disabled")
        self.base_url
        token = self.webhook_token
        if (
            not isinstance(token, str)
            or not 32 <= len(token) <= 255
            or any(not 33 <= ord(c) <= 126 for c in token)
            or token.startswith("$aact_")
            or token == self.api_key
        ):
            raise AsaasError("invalid_configuration")

    def public_status(self):
        result = {
            "environment": {"sandbox": "Sandbox", "production": "Produção"}.get(
                self.environment, "Configuração pendente"
            ),
            "api_ready": False,
            "webhook_ready": False,
        }
        try:
            self.validate_api()
            result["api_ready"] = True
        except AsaasError:
            pass
        try:
            self.validate_webhook()
            result["webhook_ready"] = True
        except AsaasError:
            pass
        return result
