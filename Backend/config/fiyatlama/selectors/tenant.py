"""Fiyatlama tenant scope (ADR-0003-05, Faz 2.0 / 2.1)."""

from django.db.models import Q

from firmalar.services.yetki_servisi import can_view_all_tenants


def user_may_see_fiyat_maliyet(user) -> bool:
    """Maliyet / price log: alıcı ve tedarikçi yüzeylerinde gizli; platform+view_all."""
    return can_view_all_tenants(user)


def scope_teklif_queryset(qs, user):
    if can_view_all_tenants(user):
        return qs
    firma_id = getattr(user, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(tedarikci_id=firma_id)


def scope_teklif_varyant_queryset(qs, user):
    """Teklif formu varyant FK — tek selector (ADR-0006 B1).

    Platform: tümü. Tedarikçi: kendi oluşturduğu (onay öncesi) veya onaylı katalog.
    """
    if can_view_all_tenants(user):
        return qs
    firma_id = getattr(user, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(
        Q(urun__onay_durumu="onayli")
        | Q(
            urun__olusturan_firma_id=firma_id,
            urun__onay_durumu__in=("taslak", "reddedildi", "onay_bekliyor"),
        )
    )


def scope_teklif_uruntasi_queryset(qs, user):
    if can_view_all_tenants(user):
        return qs
    firma_id = getattr(user, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(teklif__tedarikci_id=firma_id)


def scope_fiyat_sozlesmesi_queryset(qs, user):
    if can_view_all_tenants(user):
        return qs
    firma_id = getattr(user, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(firma_id=firma_id)


def scope_fiyat_sozlesmesi_kalemi_queryset(qs, user):
    if can_view_all_tenants(user):
        return qs
    firma_id = getattr(user, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(sozlesme__firma_id=firma_id)


def scope_price_log_queryset(qs, user):
    """PriceCalculationLog — alıcı/tedarikçi görmez; yalnız maliyet yetkisi."""
    if not user_may_see_fiyat_maliyet(user):
        return qs.none()
    return qs
