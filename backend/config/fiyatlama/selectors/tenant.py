"""Fiyatlama tenant scope (ADR-0003-05, Faz 2.0 / 2.1)."""

from django.db.models import Q

from firmalar.services.yetki_servisi import can_view_all_tenants


def user_may_see_fiyat_maliyet(user) -> bool:
    """Platform maliyet / price log / sözleşme marjı (ADR-0009 H3).

    Alıcı ve tedarikçi bu yüzeyde maliyet görmez; teklif kendi maliyeti için
    `user_may_see_teklif_maliyet` kullanın.
    """
    return can_view_all_tenants(user)


def user_may_see_teklif_maliyet(user) -> bool:
    """Teklif birim_fiyat / iscilik_override: platform veya tedarikçi (kendi qs)."""
    if can_view_all_tenants(user):
        return True
    firma = getattr(user, "firma", None)
    return bool(firma is not None and getattr(firma, "tedarikci_mi", False))


def scope_teklif_queryset(qs, user):
    if can_view_all_tenants(user):
        return qs
    firma_id = getattr(user, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(tedarikci_id=firma_id)


def teklif_eslestirme_uygun_mu(teklif) -> bool:
    """ADR-0007 §2.1 kapı predicate — quote çağrısı yok (3a).

    True yalnız eslestirme_durumu=onaylandi ve hedef_urun dolu + tutarlı.
    """
    if getattr(teklif, "eslestirme_durumu", "") != "onaylandi":
        return False
    hedef_id = getattr(teklif, "hedef_urun_id", None)
    if not hedef_id:
        return False
    varyant = getattr(teklif, "varyant", None)
    if varyant is None:
        return False
    urun_id = getattr(varyant, "urun_id", None)
    return urun_id == hedef_id


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


def scope_teklif_tas_maliyeti_queryset(qs, user):
    """TeklifTasMaliyeti (K-011) — platform tümü; tedarikçi yalnız kendi teklifi."""
    if can_view_all_tenants(user):
        return qs
    firma = getattr(user, "firma", None)
    firma_id = getattr(user, "firma_id", None)
    if not firma_id or firma is None:
        return qs.none()
    # Alıcı teklif taş maliyetini görmez (kör havuz)
    if getattr(firma, "alici_mi", False) and not getattr(firma, "tedarikci_mi", False):
        return qs.none()
    return qs.filter(teklif__tedarikci_id=firma_id)


# Geriye dönük alias (admin / eski testler)
scope_teklif_uruntasi_queryset = scope_teklif_tas_maliyeti_queryset


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


def scope_price_quote_queryset(qs, user):
    """PriceQuote — platform tümü; alıcı yalnız kendi firması; tedarikçi görmez."""
    if can_view_all_tenants(user):
        return qs
    firma = getattr(user, "firma", None)
    firma_id = getattr(user, "firma_id", None)
    if not firma_id or firma is None:
        return qs.none()
    if getattr(firma, "alici_mi", False):
        return qs.filter(alici_firma_id=firma_id)
    return qs.none()


def scope_price_quote_line_queryset(qs, user):
    """Satır kırılımı: platform maliyet yetkisi; alıcı B-02 yüzeyi 3.6 (şimdilik kapalı)."""
    if can_view_all_tenants(user) and user_may_see_fiyat_maliyet(user):
        return qs
    # Alıcı varsayılan kırılım görmez (B-02); yalnız başlık selector'da
    return qs.none()


def scope_price_lock_queryset(qs, user):
    """PriceLock — platform tümü; alıcı yalnız kendi firması; tedarikçi görmez."""
    if can_view_all_tenants(user):
        return qs
    firma = getattr(user, "firma", None)
    firma_id = getattr(user, "firma_id", None)
    if not firma_id or firma is None:
        return qs.none()
    if getattr(firma, "alici_mi", False):
        return qs.filter(alici_firma_id=firma_id)
    return qs.none()
