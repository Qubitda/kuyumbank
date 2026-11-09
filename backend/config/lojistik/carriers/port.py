"""Kargo carrier portu (F6-021 / ADR-0013 F6-K11) — canlı carrier yok."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LabelRequest:
    shipment_id: int
    order_id: int
    idempotency_key: str


@dataclass(frozen=True)
class LabelResult:
    ok: bool
    tracking_no: str
    message: str


class CarrierPort(Protocol):
    """Carrier adaptör sözleşmesi. Başarısızlık → ok=False (fail-closed)."""

    def create_label(self, request: LabelRequest) -> LabelResult: ...
