"""Katalog (Urun) tenant scope — tek selector (ADR-0004, ADR-0005).

Platform çapraz görünürlük yalnız `firmalar.view_all_tenants` ile;
`is_superuser` kısa yolu yok.

Faz 2: taslak kapsamı `olusturan_firma_id` (eski `tedarikci_id` kaldırıldı).
"""

from firmalar.services.yetki_servisi import can_view_all_tenants


def user_may_see_tedarikci_identity(user) -> bool:
    """Alıcı/tedarikçi yüzeylerinde oluşturan firma / tedarikçi kimliği gizlenir."""
    return can_view_all_tenants(user)


def scope_urun_queryset(qs, user):
    """Urun queryset — platform tümü; tedarikçi yalnız kendi oluşturduğu taslak/red.

    Onaylı katalog ürünleri tedarikçi changelist'inde görünmez (K6: ürün işlemi yok).
    Teklif ekleme için ayrı teklif/varyant selector kullanılacak.
    """
    if can_view_all_tenants(user):
        return qs
    firma_id = getattr(user, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(
        olusturan_firma_id=firma_id,
        onay_durumu__in=("taslak", "reddedildi", "onay_bekliyor"),
    )


def scope_urun_related_queryset(qs, user, *, urun_field: str = "urun"):
    """Varyant / UrunKanal / UrunTasi gibi Urun FK'li queryset."""
    if can_view_all_tenants(user):
        return qs
    firma_id = getattr(user, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(
        **{
            f"{urun_field}__olusturan_firma_id": firma_id,
            f"{urun_field}__onay_durumu__in": ("taslak", "reddedildi", "onay_bekliyor"),
        }
    )


def scope_eslestirme_hedef_urun_queryset(qs, user):
    """Eşleştirme hedef ürün — onaylı katalog + kendi onay-öncesi taslakları."""
    from django.db.models import Q

    if can_view_all_tenants(user):
        return qs
    firma_id = getattr(user, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(
        Q(onay_durumu="onayli")
        | Q(
            olusturan_firma_id=firma_id,
            onay_durumu__in=("taslak", "reddedildi", "onay_bekliyor"),
        )
    )
