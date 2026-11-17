"""Stable error categories; never include provider bodies, URLs or credentials."""


class AsaasError(Exception):
    def __init__(self, code, *, http_status=None):
        self.code = code
        self.http_status = http_status
        self.retryable = code in {
            "network_error",
            "rate_limited",
            "provider_unavailable",
        }
        super().__init__("Falha na integração Asaas: " + code)
