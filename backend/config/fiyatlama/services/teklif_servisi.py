"""Tedarikçi teklifi yaşam döngüsü (ADR-0007 §2.1, dilim 3.1).

Durum geçişleri yalnız bu serviste. Yetki/sahiplik atomic dışında;
fail audit durable; başarı audit'i domain_atomic içinde.
"""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.utils import timezone

from firmalar.models import AuditOlay
from firmalar.role_permissions import P
from firmalar.services.audit_servisi import domain_atomic, record_audit, record_audit_durable
from firmalar.services.yetki_servisi import require_perm

from fiyatlama.models import TedarikciTeklif
from fiyatlama.selectors.tenant import teklif_eslestirme_uygun_mu

_CAKISMA_MSG = "Aynı tedarikçi/varyant/kod için yayında teklif zaten var."


def _deny(kullanici, *, action, teklif, exc, reason, detail=None):
    record_audit_durable(
        actor=kullanici,
        action=action,
        entity_type="TedarikciTeklif",
        entity_id=getattr(teklif, "pk", "") or "",
        success=False,
        reason=reason,
        detail=detail or {},
    )
    raise exc


def _kilitle(teklif_id: int) -> TedarikciTeklif:
    return TedarikciTeklif.objects.select_for_update().get(pk=teklif_id)


def _assert_supplier_owner(teklif, kullanici, *, action: str):
    firma = getattr(kullanici, "firma", None)
    if not getattr(kullanici, "firma_id", None) or firma is None:
        _deny(
            kullanici,
            action=action,
            teklif=teklif,
            exc=ValidationError("Kullanıcının firması tanımlı olmalıdır."),
            reason="firma_yok",
        )
    if not firma.tedarikci_mi:
        _deny(
            kullanici,
            action=action,
            teklif=teklif,
            exc=PermissionDenied("Teklif yalnız tedarikçi firması tarafından yönetilir."),
            reason="tedarikci_degil",
        )
    if teklif.tedarikci_id != kullanici.firma_id:
        _deny(
            kullanici,
            action=action,
            teklif=teklif,
            exc=PermissionDenied("Başka tedarikçinin teklifine işlem yapılamaz."),
            reason="sahiplik_uyusmazligi",
            detail={
                "teklif_tedarikci_id": teklif.tedarikci_id,
                "user_firma_id": kullanici.firma_id,
            },
        )
    try:
        require_perm(
            kullanici,
            P["manage_own_teklif"],
            message="Teklif yönetim yetkiniz yok.",
        )
    except PermissionDenied as exc:
        _deny(kullanici, action=action, teklif=teklif, exc=exc, reason="yetki_yok")


def _assert_platform_approve(kullanici, *, action: str, teklif):
    try:
        require_perm(kullanici, P["approve_teklif"])
    except PermissionDenied as exc:
        _deny(kullanici, action=action, teklif=teklif, exc=exc, reason="yetki_yok")
    firma = getattr(kullanici, "firma", None)
    if not (kullanici.firma_id and firma and firma.platform_mu):
        _deny(
            kullanici,
            action=action,
            teklif=teklif,
            exc=PermissionDenied("Bu işlem yalnızca platform firması kullanıcılarınındır."),
            reason="platform_firma_degil",
        )


def _son_gonderen_id(teklif) -> int | None:
    """VARSAYIM: dört göz için AuditOlay (ürün deseni); ayrı gonderen alanı yok."""
    return (
        AuditOlay.objects.filter(
            action="teklif.onaya_gonder",
            entity_type="TedarikciTeklif",
            entity_id=str(teklif.pk),
            success=True,
        )
        .order_by("-created_at")
        .values_list("actor_id", flat=True)
        .first()
    )


def _assert_dort_goz(teklif, kullanici, *, action: str):
    gonderen_id = _son_gonderen_id(teklif)
    if gonderen_id and gonderen_id == getattr(kullanici, "pk", None):
        _deny(
            kullanici,
            action=action,
            teklif=teklif,
            exc=PermissionDenied("Dört göz: gönderen ile onaylayan aynı olamaz."),
            reason="dort_goz",
        )


def _require_yayin_gecerlilik(teklif):
    if teklif.gecerlilik_baslangic is None or teklif.gecerlilik_bitis is None:
        raise ValidationError(
            "YAYINDA teklifte geçerlilik başlangıç ve bitiş zorunludur."
        )
    if teklif.gecerlilik_bitis < teklif.gecerlilik_baslangic:
        raise ValidationError({"gecerlilik_bitis": "Bitiş, başlangıçtan önce olamaz."})


def _assert_no_yayinda_cakisma(teklif, *, exclude_pk=None):
    qs = TedarikciTeklif.objects.filter(
        tedarikci_id=teklif.tedarikci_id,
        varyant_id=teklif.varyant_id,
        durum=TedarikciTeklif.Durum.YAYINDA,
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    kod = teklif.tedarikci_kodu or ""
    if kod:
        qs = qs.filter(tedarikci_kodu=kod)
    else:
        qs = qs.filter(tedarikci_kodu="")
    if qs.exists():
        raise ValidationError(_CAKISMA_MSG)


def onaya_gonder(teklif: TedarikciTeklif, kullanici) -> TedarikciTeklif:
    action = "teklif.onaya_gonder"
    teklif.refresh_from_db()
    _assert_supplier_owner(teklif, kullanici, action=action)
    if teklif.durum != TedarikciTeklif.Durum.TASLAK:
        _deny(
            kullanici,
            action=action,
            teklif=teklif,
            exc=ValidationError("Yalnızca taslak teklif onaya gönderilebilir."),
            reason="gecersiz_durum",
        )
    try:
        with domain_atomic():
            t = _kilitle(teklif.pk)
            if t.durum != TedarikciTeklif.Durum.TASLAK:
                raise ValidationError("Yalnızca taslak teklif onaya gönderilebilir.")
            t.durum = TedarikciTeklif.Durum.ONAY_BEKLIYOR
            t.full_clean()
            t.save(update_fields=["durum", "guncelleme_tarihi"])
            record_audit(
                actor=kullanici,
                action=action,
                entity_type="TedarikciTeklif",
                entity_id=str(t.pk),
                success=True,
                detail={"durum": t.durum},
            )
            return t
    except ValidationError as exc:
        _deny(kullanici, action=action, teklif=teklif, exc=exc, reason="dogrulama")


def yayina_al(teklif: TedarikciTeklif, kullanici) -> TedarikciTeklif:
    """ONAY_BEKLIYOR → YAYINDA; versiyon ise önce eski PASIF (ADR netleştirme)."""
    action = "teklif.yayina_al"
    teklif.refresh_from_db()
    _assert_platform_approve(kullanici, action=action, teklif=teklif)
    if teklif.durum != TedarikciTeklif.Durum.ONAY_BEKLIYOR:
        _deny(
            kullanici,
            action=action,
            teklif=teklif,
            exc=ValidationError("Yalnızca onay bekleyen teklif yayına alınabilir."),
            reason="gecersiz_durum",
        )
    _assert_dort_goz(teklif, kullanici, action=action)

    try:
        with domain_atomic():
            t = _kilitle(teklif.pk)
            if t.durum != TedarikciTeklif.Durum.ONAY_BEKLIYOR:
                raise ValidationError("Yalnızca onay bekleyen teklif yayına alınabilir.")
            _require_yayin_gecerlilik(t)

            eski = None
            if t.onceki_teklif_id:
                eski = _kilitle(t.onceki_teklif_id)
                if eski.durum == TedarikciTeklif.Durum.YAYINDA:
                    # Sıra: önce eski PASIF, sonra yeni YAYINDA
                    eski.durum = TedarikciTeklif.Durum.PASIF
                    eski.save(update_fields=["durum", "guncelleme_tarihi"])

            _assert_no_yayinda_cakisma(t, exclude_pk=eski.pk if eski else None)

            t.durum = TedarikciTeklif.Durum.YAYINDA
            t.onaylayan = kullanici
            t.onay_zamani = timezone.now()
            t.full_clean()
            try:
                t.save(
                    update_fields=[
                        "durum",
                        "onaylayan",
                        "onay_zamani",
                        "guncelleme_tarihi",
                    ]
                )
            except IntegrityError as exc:
                raise ValidationError(_CAKISMA_MSG) from exc

            record_audit(
                actor=kullanici,
                action=action,
                entity_type="TedarikciTeklif",
                entity_id=str(t.pk),
                success=True,
                detail={
                    "durum": t.durum,
                    "eski_pasif_id": eski.pk if eski else None,
                },
            )
            return t
    except ValidationError as exc:
        _deny(kullanici, action=action, teklif=teklif, exc=exc, reason="dogrulama")


def pasifle(teklif: TedarikciTeklif, kullanici) -> TedarikciTeklif:
    action = "teklif.pasifle"
    teklif.refresh_from_db()
    # Platform veya sahip tedarikçi (manage)
    firma = getattr(kullanici, "firma", None)
    if firma and firma.platform_mu:
        _assert_platform_approve(kullanici, action=action, teklif=teklif)
    else:
        _assert_supplier_owner(teklif, kullanici, action=action)

    if teklif.durum != TedarikciTeklif.Durum.YAYINDA:
        _deny(
            kullanici,
            action=action,
            teklif=teklif,
            exc=ValidationError("Yalnızca yayındaki teklif pasifleştirilebilir."),
            reason="gecersiz_durum",
        )
    try:
        with domain_atomic():
            t = _kilitle(teklif.pk)
            if t.durum != TedarikciTeklif.Durum.YAYINDA:
                raise ValidationError("Yalnızca yayındaki teklif pasifleştirilebilir.")
            t.durum = TedarikciTeklif.Durum.PASIF
            t.save(update_fields=["durum", "guncelleme_tarihi"])
            record_audit(
                actor=kullanici,
                action=action,
                entity_type="TedarikciTeklif",
                entity_id=str(t.pk),
                success=True,
                detail={"durum": t.durum},
            )
            return t
    except ValidationError as exc:
        _deny(kullanici, action=action, teklif=teklif, exc=exc, reason="dogrulama")


def yeniden_yayinla(teklif: TedarikciTeklif, kullanici) -> TedarikciTeklif:
    action = "teklif.yeniden_yayinla"
    teklif.refresh_from_db()
    _assert_platform_approve(kullanici, action=action, teklif=teklif)
    if teklif.durum != TedarikciTeklif.Durum.PASIF:
        _deny(
            kullanici,
            action=action,
            teklif=teklif,
            exc=ValidationError("Yalnızca pasif teklif yeniden yayınlanabilir."),
            reason="gecersiz_durum",
        )
    try:
        with domain_atomic():
            t = _kilitle(teklif.pk)
            if t.durum != TedarikciTeklif.Durum.PASIF:
                raise ValidationError("Yalnızca pasif teklif yeniden yayınlanabilir.")
            _require_yayin_gecerlilik(t)
            _assert_no_yayinda_cakisma(t)
            t.durum = TedarikciTeklif.Durum.YAYINDA
            t.full_clean()
            try:
                t.save(update_fields=["durum", "guncelleme_tarihi"])
            except IntegrityError as exc:
                raise ValidationError(_CAKISMA_MSG) from exc
            record_audit(
                actor=kullanici,
                action=action,
                entity_type="TedarikciTeklif",
                entity_id=str(t.pk),
                success=True,
                detail={"durum": t.durum},
            )
            return t
    except ValidationError as exc:
        _deny(kullanici, action=action, teklif=teklif, exc=exc, reason="dogrulama")


def yeni_versiyon_olustur(
    teklif: TedarikciTeklif,
    kullanici,
    *,
    gram=None,
    birim_fiyat=None,
    fiyat_modeli=None,
    iscilik_override=None,
    gecerlilik_baslangic=None,
    gecerlilik_bitis=None,
) -> TedarikciTeklif:
    """YAYINDA tekliften yeni ONAY_BEKLIYOR satırı; eski YAYINDA kalır."""
    action = "teklif.yeni_versiyon"
    teklif.refresh_from_db()
    _assert_supplier_owner(teklif, kullanici, action=action)
    if teklif.durum != TedarikciTeklif.Durum.YAYINDA:
        _deny(
            kullanici,
            action=action,
            teklif=teklif,
            exc=ValidationError("Yalnızca yayındaki tekliften yeni versiyon açılır."),
            reason="gecersiz_durum",
        )

    try:
        with domain_atomic():
            eski = _kilitle(teklif.pk)
            if eski.durum != TedarikciTeklif.Durum.YAYINDA:
                raise ValidationError(
                    "Yalnızca yayındaki tekliften yeni versiyon açılır."
                )
            yeni = TedarikciTeklif(
                varyant_id=eski.varyant_id,
                tedarikci_id=eski.tedarikci_id,
                tedarikci_kodu=eski.tedarikci_kodu,
                versiyon=eski.versiyon + 1,
                onceki_teklif=eski,
                gecerlilik_baslangic=(
                    gecerlilik_baslangic
                    if gecerlilik_baslangic is not None
                    else eski.gecerlilik_baslangic
                ),
                gecerlilik_bitis=(
                    gecerlilik_bitis
                    if gecerlilik_bitis is not None
                    else eski.gecerlilik_bitis
                ),
                fiyat_modeli=fiyat_modeli or eski.fiyat_modeli,
                gram=eski.gram if gram is None else gram,
                gram_tolerans=eski.gram_tolerans,
                birim_fiyat=eski.birim_fiyat if birim_fiyat is None else birim_fiyat,
                para_birimi=eski.para_birimi,
                iscilik_override=(
                    eski.iscilik_override
                    if iscilik_override is None
                    else iscilik_override
                ),
                temin_tipi=eski.temin_tipi,
                stok_adet=eski.stok_adet,
                uretim_suresi_gun=eski.uretim_suresi_gun,
                oncelik=eski.oncelik,
                durum=TedarikciTeklif.Durum.ONAY_BEKLIYOR,
                # ADR-0009 H5(a): eşleştirme kopyalanmaz — otomatik onay yok
                eslestirme_durumu="",
                eslestirme_guveni="",
                eslestirme_kaniti={},
                esdegerlik_seviyesi="",
                hedef_urun=None,
                eslestiren_kullanici=None,
            )
            yeni.full_clean()
            yeni.save()
            record_audit(
                actor=kullanici,
                action=action,
                entity_type="TedarikciTeklif",
                entity_id=str(yeni.pk),
                success=True,
                detail={
                    "onceki_teklif_id": eski.pk,
                    "versiyon": yeni.versiyon,
                    "eski_durum": eski.durum,
                },
            )
            # Yeni satır için onaya_gonder audit'i yok; dört göz: yeni_versiyon
            # aktörü gönderen sayılır (VARSAYIM — aşağıdaki not).
            record_audit(
                actor=kullanici,
                action="teklif.onaya_gonder",
                entity_type="TedarikciTeklif",
                entity_id=str(yeni.pk),
                success=True,
                detail={"kaynak": "yeni_versiyon"},
            )
            return yeni
    except ValidationError as exc:
        _deny(kullanici, action=action, teklif=teklif, exc=exc, reason="dogrulama")


# Predicate re-export for callers that import from services
eslestirme_uygun_mu = teklif_eslestirme_uygun_mu
