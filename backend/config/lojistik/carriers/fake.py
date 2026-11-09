"""Fake carrier adaptörü — test / geliştirme (F6-021). Secret yok."""

from __future__ import annotations

from lojistik.carriers.port import LabelRequest, LabelResult


class FakeCarrierAdapter:
    """Varsayılan: başarılı. `force_fail=True` → fail-closed."""

    def __init__(self, *, force_fail: bool = False):
        self.force_fail = force_fail

    def create_label(self, request: LabelRequest) -> LabelResult:
        if self.force_fail:
            return LabelResult(
                ok=False, tracking_no="", message="fake_forced_fail"
            )
        if not request.shipment_id or not request.order_id:
            return LabelResult(
                ok=False, tracking_no="", message="fake_missing_ids"
            )
        key = (request.idempotency_key or "").strip()
        if not key:
            return LabelResult(
                ok=False, tracking_no="", message="fake_missing_idempotency"
            )
        return LabelResult(
            ok=True,
            tracking_no=f"FAKE-{key}"[:64],
            message="fake_ok",
        )
