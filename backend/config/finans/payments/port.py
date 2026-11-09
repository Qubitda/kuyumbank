"""Ödeme sağlayıcı portu (F5-020) — canlı banka yok."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class ChargeRequest:
    intent_id: int
    order_id: int
    amount: Decimal
    currency: str
    idempotency_key: str


@dataclass(frozen=True)
class ChargeResult:
    ok: bool
    provider_ref: str
    message: str


class PaymentProviderPort(Protocol):
    """Sağlayıcı adaptör sözleşmesi. Başarısızlık → ok=False (fail-closed)."""

    def charge(self, request: ChargeRequest) -> ChargeResult: ...
