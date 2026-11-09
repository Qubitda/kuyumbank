"""Ödeme adaptörü seçimi — bilinmeyen sağlayıcı fail-closed (F5-020)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError

from finans.payments.fake import FakePaymentAdapter
from finans.payments.port import PaymentProviderPort


def get_payment_adapter(*, force_fail: bool | None = None) -> PaymentProviderPort:
    """settings.PAYMENT_PROVIDER; secret kodda yok (env only gelecekteki canlı adapter)."""
    name = (getattr(settings, "PAYMENT_PROVIDER", None) or "fake").strip().lower()
    if name == "fake":
        fail = bool(force_fail) if force_fail is not None else False
        # Test/ops: PAYMENT_FAKE_FORCE_FAIL=1
        if force_fail is None and getattr(settings, "PAYMENT_FAKE_FORCE_FAIL", False):
            fail = True
        return FakePaymentAdapter(force_fail=fail)
    raise ValidationError(
        f"Bilinmeyen ödeme sağlayıcı: {name!r} (fail-closed; F5-020)."
    )
