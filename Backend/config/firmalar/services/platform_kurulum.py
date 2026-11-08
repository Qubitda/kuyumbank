"""Platform firması ve break-glass kullanıcı bağlama (ADR-0003-02)."""

from django.db import transaction

from .. import roles
from ..models import Firma


@transaction.atomic
def ensure_platform_firma() -> Firma:
    """Tek platform firmasını getirir veya oluşturur."""
    existing = Firma.objects.filter(platform_mu=True).first()
    if existing:
        if not existing.firma_kodu:
            existing.firma_kodu = roles.PLATFORM_FIRMA_KODU
            existing.save(update_fields=["firma_kodu", "guncelleme_zamani"])
        return existing

    by_kod = Firma.objects.filter(firma_kodu=roles.PLATFORM_FIRMA_KODU).first()
    if by_kod:
        by_kod.platform_mu = True
        by_kod.aktif = True
        by_kod.onay_durumu = "onayli"
        by_kod.save()
        return by_kod

    return Firma.objects.create(
        ad="Kuyumbank Platform",
        unvan="Kuyumbank Platform",
        firma_kodu=roles.PLATFORM_FIRMA_KODU,
        platform_mu=True,
        aktif=True,
        onay_durumu="onayli",
    )
