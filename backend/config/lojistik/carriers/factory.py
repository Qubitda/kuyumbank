"""Carrier adaptör seçimi — bilinmeyen sağlayıcı fail-closed (F6-021)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError

from lojistik.carriers.fake import FakeCarrierAdapter
from lojistik.carriers.port import CarrierPort


def get_carrier_adapter(*, force_fail: bool | None = None) -> CarrierPort:
    """settings.CARRIER_PROVIDER; secret kodda yok."""
    name = (getattr(settings, "CARRIER_PROVIDER", None) or "fake").strip().lower()
    if name == "fake":
        fail = bool(force_fail) if force_fail is not None else False
        if force_fail is None and getattr(settings, "CARRIER_FAKE_FORCE_FAIL", False):
            fail = True
        return FakeCarrierAdapter(force_fail=fail)
    raise ValidationError(
        f"Bilinmeyen kargo sağlayıcı: {name!r} (fail-closed; F6-021)."
    )
