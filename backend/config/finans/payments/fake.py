"""Fake ödeme adaptörü — test / geliştirme (F5-020). Secret yok."""

from __future__ import annotations

from finans.payments.port import ChargeRequest, ChargeResult


class FakePaymentAdapter:
    """Varsayılan: başarılı. `force_fail=True` veya tutar<=0 → fail-closed."""

    def __init__(self, *, force_fail: bool = False):
        self.force_fail = force_fail

    def charge(self, request: ChargeRequest) -> ChargeResult:
        if self.force_fail:
            return ChargeResult(
                ok=False, provider_ref="", message="fake_forced_fail"
            )
        if request.amount is None or request.amount <= 0:
            return ChargeResult(
                ok=False, provider_ref="", message="fake_invalid_amount"
            )
        if not (request.currency or "").strip():
            return ChargeResult(
                ok=False, provider_ref="", message="fake_missing_currency"
            )
        ref = f"fake-{request.idempotency_key}"
        return ChargeResult(ok=True, provider_ref=ref, message="fake_ok")
