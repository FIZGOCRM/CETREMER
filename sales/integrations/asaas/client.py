"""Read-only Asaas client with fixed destinations and no automatic redirects/retries."""

import json
from decimal import Decimal
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .config import AsaasConfig
from .dto import PaymentPage, PaymentSnapshot, resource_id
from .errors import AsaasError

MAX_RESPONSE_BYTES = 512 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class AsaasClient:
    def __init__(self, config=None, *, transport=None):
        self.config = config or AsaasConfig.from_settings()
        self.transport = transport or build_opener(NoRedirect()).open

    def _get(self, path, params=None):
        self.config.validate_api()
        url = self.config.base_url + path
        if params:
            url += "?" + urlencode(params)
        request = Request(
            url,
            method="GET",
            headers={
                "access_token": self.config.api_key,
                "User-Agent": "CETREMER/1.0",
                "Accept": "application/json",
            },
        )
        try:
            with self.transport(
                request, timeout=float(self.config.timeout)
            ) as response:
                status = response.status
                body = response.read(MAX_RESPONSE_BYTES + 1)
                if not 200 <= status < 300:
                    raise self._http_error(status)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise AsaasError("invalid_response")
                payload = json.loads(body, parse_float=Decimal)
        except HTTPError as exc:
            status = exc.code
            exc.close()
            raise self._http_error(status) from None
        except (URLError, OSError, TimeoutError, HTTPException):
            raise AsaasError("network_error") from None
        except (ValueError, UnicodeError, RecursionError):
            raise AsaasError("invalid_response") from None
        if not isinstance(payload, dict):
            raise AsaasError("invalid_response")
        return payload

    @staticmethod
    def _http_error(status):
        if status in (401, 403):
            code = "authentication_failed"
        elif status == 404:
            code = "not_found"
        elif status == 429:
            code = "rate_limited"
        elif 300 <= status < 400:
            code = "redirect_blocked"
        elif status >= 500:
            code = "provider_unavailable"
        else:
            code = "request_rejected"
        return AsaasError(code, http_status=status)

    def get_payment(self, payment_id):
        resource_id(payment_id, "pay_")
        snapshot = PaymentSnapshot.from_payload(self._get("/payments/" + payment_id))
        if snapshot.gateway_id != payment_id:
            raise AsaasError("payment_identity_mismatch")
        return snapshot

    def find_payments(self, external_reference, *, limit=2):
        if (
            not isinstance(external_reference, str)
            or not external_reference
            or len(external_reference) > 200
            or type(limit) is not int
            or not 1 <= limit <= 100
        ):
            raise AsaasError("invalid_request")
        payload = self._get(
            "/payments",
            {"externalReference": external_reference, "limit": limit, "offset": 0},
        )
        data, has_more = payload.get("data"), payload.get("hasMore")
        if (
            not isinstance(data, list)
            or len(data) > limit
            or not isinstance(has_more, bool)
        ):
            raise AsaasError("invalid_response")
        return PaymentPage(
            tuple(PaymentSnapshot.from_payload(item) for item in data), has_more
        )

    def create_payment(self, **kwargs):
        raise AsaasError("billing_not_enabled")

    def create_subscription(self, **kwargs):
        raise AsaasError("billing_not_enabled")
