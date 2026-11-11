"""Platform katalog yazma — ADR-0030 (HTTP ince; kurallar burada)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import record_audit, record_audit_durable
from firmalar.services.yetki_servisi import require_perm
from tanimlar.models import AyarMilyem, SatisKanali
from urunler.models import Kategori, Renk, Urun, UrunKanal, Varyant


def _deny(actor, *, action, urun, exc, reason, detail=None):
    record_audit_durable(
        actor=actor,
        action=action,
        entity_type="Urun",
        entity_id=getattr(urun, "pk", "") or "",
        success=False,
        reason=reason,
        detail=detail or {},
    )
    raise exc


def _require_platform_submit(actor, *, action, urun=None):
    try:
        require_perm(actor, P["submit_urun"], message="Ürün yazma yetkiniz yok.")
    except PermissionDenied as exc:
        _deny(actor, action=action, urun=urun, exc=exc, reason="yetki_yok")
    firma = getattr(actor, "firma", None)
    if not (getattr(actor, "firma_id", None) and firma and firma.platform_mu):
        _deny(
            actor,
            action=action,
            urun=urun,
            exc=PermissionDenied("Bu işlem yalnızca platform firması kullanıcılarınındır."),
            reason="platform_firma_degil",
        )


def taslak_urun_olustur(
    *,
    actor,
    ad: str,
    kategori_id: int,
    ayar_id: int,
    aciklama: str = "",
    fiyat_tipi: str = "gram",
    satis_kanali_id: int | None = None,
) -> Urun:
    """Platform taslak ürün — onay/yayın yalnız onay_servisi."""
    _require_platform_submit(actor, action="urun.taslak_olustur")
    ad = (ad or "").strip()
    if not ad:
        raise ValidationError({"ad": "Zorunlu."})
    if fiyat_tipi not in dict(Urun.FIYAT_TIPI):
        raise ValidationError({"fiyat_tipi": "Geçersiz."})
    kategori = Kategori.objects.filter(pk=kategori_id, aktif=True).first()
    if kategori is None:
        raise ValidationError({"kategori_id": "Aktif kategori bulunamadı."})
    ayar = AyarMilyem.objects.filter(pk=ayar_id).first()
    if ayar is None:
        raise ValidationError({"ayar_id": "Ayar bulunamadı."})
    kanal = None
    if satis_kanali_id not in (None, ""):
        kanal = SatisKanali.objects.filter(pk=int(satis_kanali_id), aktif=True).first()
        if kanal is None:
            raise ValidationError({"satis_kanali_id": "Aktif satış kanalı bulunamadı."})

    try:
        with transaction.atomic():
            urun = Urun(
                olusturan_firma=actor.firma,
                olusturan_kullanici=actor,
                ad=ad,
                aciklama=(aciklama or "").strip(),
                kategori=kategori,
                ayar=ayar,
                fiyat_tipi=fiyat_tipi,
            )
            urun.full_clean()
            urun.save()
            if kanal is not None:
                UrunKanal.objects.create(urun=urun, kanal=kanal, aktif=True)
            record_audit(
                actor=actor,
                action="urun.taslak_olustur",
                entity_type="Urun",
                entity_id=urun.pk,
                success=True,
            )
            return urun
    except ValidationError as exc:
        record_audit_durable(
            actor=actor,
            action="urun.taslak_olustur",
            entity_type="Urun",
            entity_id="",
            success=False,
            reason="validation",
            detail={"messages": getattr(exc, "messages", [str(exc)])},
        )
        raise


def varyant_ekle(
    *,
    actor,
    urun: Urun,
    gram: Decimal | str | None = None,
    renk_id: int | None = None,
    ek_bedel: Decimal | str | None = None,
) -> Varyant:
    """Taslak/reddedildi ürüne aktif varyant ekle (onaya_gonder önkoşulu)."""
    _require_platform_submit(actor, action="urun.varyant_ekle", urun=urun)
    urun.refresh_from_db()
    if urun.olusturan_firma_id != actor.firma_id:
        _deny(
            actor,
            action="urun.varyant_ekle",
            urun=urun,
            exc=PermissionDenied("Başka firmaya ait ürüne varyant eklenemez."),
            reason="sahiplik_uyusmazligi",
        )
    if urun.onay_durumu not in ("taslak", "reddedildi"):
        _deny(
            actor,
            action="urun.varyant_ekle",
            urun=urun,
            exc=ValidationError("Yalnızca taslak/reddedildi ürüne varyant eklenir."),
            reason="gecersiz_durum",
        )

    gram_v = None
    if gram not in (None, ""):
        try:
            gram_v = Decimal(str(gram))
        except (InvalidOperation, TypeError) as exc:
            raise ValidationError({"gram": "Geçersiz."}) from exc
        if gram_v <= 0:
            raise ValidationError({"gram": "Pozitif olmalı."})

    ek = Decimal("0")
    if ek_bedel not in (None, ""):
        try:
            ek = Decimal(str(ek_bedel))
        except (InvalidOperation, TypeError) as exc:
            raise ValidationError({"ek_bedel": "Geçersiz."}) from exc

    renk = None
    if renk_id not in (None, ""):
        renk = Renk.objects.filter(pk=int(renk_id)).first()
        if renk is None:
            raise ValidationError({"renk_id": "Renk bulunamadı."})

    try:
        with transaction.atomic():
            v = Varyant(
                urun=urun,
                gram=gram_v,
                renk=renk,
                ek_bedel=ek,
                aktif=True,
            )
            v.full_clean()
            v.save()
            record_audit(
                actor=actor,
                action="urun.varyant_ekle",
                entity_type="Varyant",
                entity_id=v.pk,
                success=True,
                detail={"urun_id": urun.pk},
            )
            return v
    except ValidationError as exc:
        record_audit_durable(
            actor=actor,
            action="urun.varyant_ekle",
            entity_type="Urun",
            entity_id=str(urun.pk),
            success=False,
            reason="validation",
            detail={"messages": getattr(exc, "messages", [str(exc)])},
        )
        raise
