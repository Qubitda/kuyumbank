"""Fiyat sözleşmesi yaşam döngüsü (ADR-0007 §2.3, dilim 3.2 / K-008).

AKTIF immutability + yayın çakışma kontrolü. Yetki: manage_sozlesme.
"""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import domain_atomic, record_audit, record_audit_durable
from firmalar.services.yetki_servisi import require_perm

from fiyatlama.models import FiyatSozlesmesi, FiyatSozlesmesiKalemi

_CAKISMA_MSG = (
    "Aynı firma/kontrat tipi/kanal için AKTIF sözleşme tarih aralığı çakışıyor."
)


def _deny(kullanici, *, action, sozlesme, exc, reason, detail=None):
    record_audit_durable(
        actor=kullanici,
        action=action,
        entity_type="FiyatSozlesmesi",
        entity_id=getattr(sozlesme, "pk", "") or "",
        success=False,
        reason=reason,
        detail=detail or {},
    )
    raise exc


def _require_manage(kullanici, *, action, sozlesme):
    try:
        require_perm(
            kullanici,
            P["manage_sozlesme"],
            message="Sözleşme yönetim yetkiniz yok.",
        )
    except PermissionDenied as exc:
        _deny(kullanici, action=action, sozlesme=sozlesme, exc=exc, reason="yetki_yok")


def _kilitle(sozlesme_id: int) -> FiyatSozlesmesi:
    return FiyatSozlesmesi.objects.select_for_update().get(pk=sozlesme_id)


def assert_sozlesme_mutable(sozlesme: FiyatSozlesmesi) -> None:
    if sozlesme.durum == FiyatSozlesmesi.Durum.AKTIF:
        raise ValidationError(
            "AKTIF sözleşme değiştirilemez; yeni versiyon açın (ADR-0007 §2.3)."
        )


def _kanal_anahtari(sozlesme) -> int:
    return sozlesme.satis_kanali_id or 0


def _overlap_qs(sozlesme, *, exclude_pk=None):
    """Servis kilidi (exclusion ile aynı semantik; friendly hata)."""
    qs = FiyatSozlesmesi.objects.filter(
        firma_id=sozlesme.firma_id,
        kontrat_tipi=sozlesme.kontrat_tipi,
        durum=FiyatSozlesmesi.Durum.AKTIF,
        gecerlilik_baslangic__lte=sozlesme.gecerlilik_bitis,
        gecerlilik_bitis__gte=sozlesme.gecerlilik_baslangic,
    )
    if sozlesme.satis_kanali_id:
        qs = qs.filter(satis_kanali_id=sozlesme.satis_kanali_id)
    else:
        qs = qs.filter(satis_kanali__isnull=True)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs


def _assert_no_aktif_cakisma(sozlesme, *, exclude_pk=None):
    if _overlap_qs(sozlesme, exclude_pk=exclude_pk).exists():
        raise ValidationError(_CAKISMA_MSG)


def aktif_yap(sozlesme: FiyatSozlesmesi, kullanici) -> FiyatSozlesmesi:
    """TASLAK/PASIF → AKTIF; çakışma yoksa. Versiyon zincirinde eski AKTIF → PASIF."""
    action = "sozlesme.aktif_yap"
    sozlesme.refresh_from_db()
    _require_manage(kullanici, action=action, sozlesme=sozlesme)

    if sozlesme.durum == FiyatSozlesmesi.Durum.AKTIF:
        _deny(
            kullanici,
            action=action,
            sozlesme=sozlesme,
            exc=ValidationError("Sözleşme zaten AKTIF."),
            reason="gecersiz_durum",
        )
    if sozlesme.durum not in (
        FiyatSozlesmesi.Durum.TASLAK,
        FiyatSozlesmesi.Durum.PASIF,
    ):
        _deny(
            kullanici,
            action=action,
            sozlesme=sozlesme,
            exc=ValidationError("Yalnızca taslak veya pasif sözleşme aktifleştirilebilir."),
            reason="gecersiz_durum",
        )

    try:
        with domain_atomic():
            s = _kilitle(sozlesme.pk)
            if s.durum == FiyatSozlesmesi.Durum.AKTIF:
                raise ValidationError("Sözleşme zaten AKTIF.")

            eski = None
            if s.onceki_versiyon_id:
                eski = _kilitle(s.onceki_versiyon_id)
                if eski.durum == FiyatSozlesmesi.Durum.AKTIF:
                    eski.durum = FiyatSozlesmesi.Durum.PASIF
                    eski.save(update_fields=["durum", "guncelleme_tarihi"])

            _assert_no_aktif_cakisma(s, exclude_pk=eski.pk if eski else None)

            s.durum = FiyatSozlesmesi.Durum.AKTIF
            s.onaylayan_kullanici = kullanici
            try:
                s.full_clean()
                s.save(
                    update_fields=[
                        "durum",
                        "onaylayan_kullanici",
                        "guncelleme_tarihi",
                    ]
                )
            except IntegrityError as exc:
                raise ValidationError(_CAKISMA_MSG) from exc

            record_audit(
                actor=kullanici,
                action=action,
                entity_type="FiyatSozlesmesi",
                entity_id=str(s.pk),
                success=True,
                detail={
                    "durum": s.durum,
                    "eski_pasif_id": eski.pk if eski else None,
                    "kanal_anahtari": _kanal_anahtari(s),
                },
            )
            return s
    except ValidationError as exc:
        _deny(kullanici, action=action, sozlesme=sozlesme, exc=exc, reason="dogrulama")


def pasifle(sozlesme: FiyatSozlesmesi, kullanici) -> FiyatSozlesmesi:
    action = "sozlesme.pasifle"
    sozlesme.refresh_from_db()
    _require_manage(kullanici, action=action, sozlesme=sozlesme)
    if sozlesme.durum != FiyatSozlesmesi.Durum.AKTIF:
        _deny(
            kullanici,
            action=action,
            sozlesme=sozlesme,
            exc=ValidationError("Yalnızca AKTIF sözleşme pasifleştirilebilir."),
            reason="gecersiz_durum",
        )
    try:
        with domain_atomic():
            s = _kilitle(sozlesme.pk)
            if s.durum != FiyatSozlesmesi.Durum.AKTIF:
                raise ValidationError("Yalnızca AKTIF sözleşme pasifleştirilebilir.")
            s.durum = FiyatSozlesmesi.Durum.PASIF
            s.save(update_fields=["durum", "guncelleme_tarihi"])
            record_audit(
                actor=kullanici,
                action=action,
                entity_type="FiyatSozlesmesi",
                entity_id=str(s.pk),
                success=True,
                detail={"durum": s.durum},
            )
            return s
    except ValidationError as exc:
        _deny(kullanici, action=action, sozlesme=sozlesme, exc=exc, reason="dogrulama")


def yeni_versiyon_olustur(sozlesme: FiyatSozlesmesi, kullanici) -> FiyatSozlesmesi:
    """AKTIF (veya PASIF) sözleşmeden TASLAK kopya; kalemler dahil."""
    action = "sozlesme.yeni_versiyon"
    sozlesme.refresh_from_db()
    _require_manage(kullanici, action=action, sozlesme=sozlesme)
    if sozlesme.durum not in (
        FiyatSozlesmesi.Durum.AKTIF,
        FiyatSozlesmesi.Durum.PASIF,
    ):
        _deny(
            kullanici,
            action=action,
            sozlesme=sozlesme,
            exc=ValidationError("Yalnızca aktif/pasif sözleşmeden yeni versiyon açılır."),
            reason="gecersiz_durum",
        )

    try:
        with domain_atomic():
            eski = _kilitle(sozlesme.pk)
            yeni = FiyatSozlesmesi(
                firma_id=eski.firma_id,
                kontrat_tipi=eski.kontrat_tipi,
                satis_kanali_id=eski.satis_kanali_id,
                gecerlilik_baslangic=eski.gecerlilik_baslangic,
                gecerlilik_bitis=eski.gecerlilik_bitis,
                durum=FiyatSozlesmesi.Durum.TASLAK,
                olusturan_kullanici=kullanici,
                versiyon=eski.versiyon + 1,
                onceki_versiyon=eski,
                notlar=eski.notlar,
            )
            # TASLAK: exclusion uygulanmaz; full_clean version unique kontrol eder
            yeni.full_clean()
            yeni.save()
            for kalem in eski.kalemler.all():
                FiyatSozlesmesiKalemi.objects.create(
                    sozlesme=yeni,
                    metal_id=kalem.metal_id,
                    ayar_id=kalem.ayar_id,
                    marj_tipi=kalem.marj_tipi,
                    marj_degeri=kalem.marj_degeri,
                    iscilik=kalem.iscilik,
                    islcilik_dahil_mi=kalem.islcilik_dahil_mi,
                    sira=kalem.sira,
                )
            record_audit(
                actor=kullanici,
                action=action,
                entity_type="FiyatSozlesmesi",
                entity_id=str(yeni.pk),
                success=True,
                detail={"onceki_id": eski.pk, "versiyon": yeni.versiyon},
            )
            return yeni
    except ValidationError as exc:
        _deny(kullanici, action=action, sozlesme=sozlesme, exc=exc, reason="dogrulama")
