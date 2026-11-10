"""F10-021 — Katalog dışı RFQ eşleştirme motoru (platform aracılı; kör).

Otomatik onay yok; AI yok. Kural tabanlı aday + insan onayı.
"""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm
from siparis.models import RFQ, RFQEslestirme, RFQLine
from siparis.selectors.rfq_eslestirme import catalog_aday_queryset
from urunler.models import Varyant

_KANIT_IZINLI = frozenset({"not", "aciklama", "referans", "kaynak", "red_nedeni"})
_KANIT_MAX_LEN = 500
_MAX_ADAY = 20


def _deny(actor, *, action: str, entity_id, exc, reason: str, detail=None):
    record_audit_durable(
        actor=actor,
        action=action,
        entity_type="RFQEslestirme",
        entity_id=str(entity_id or ""),
        success=False,
        reason=reason,
        detail=detail or {},
    )
    raise exc


def _require_platform_eslestirme(actor, *, action: str, entity_id=""):
    try:
        require_perm(actor, P["approve_eslestirme"])
    except PermissionDenied as exc:
        _deny(
            actor,
            action=action,
            entity_id=entity_id,
            exc=exc,
            reason="yetki_yok",
        )
    firma = getattr(actor, "firma", None)
    if not (firma and getattr(firma, "platform_mu", False)):
        _deny(
            actor,
            action=action,
            entity_id=entity_id,
            exc=PermissionDenied(
                "RFQ katalog eşleştirme yalnız platform kullanıcılarınındır."
            ),
            reason="platform_firma_degil",
        )


def _normalize_kanit(kanit) -> dict:
    if kanit is None:
        return {}
    if not isinstance(kanit, dict):
        raise ValidationError("Eşleştirme kanıtı geçersiz.")
    out = {}
    for key, val in kanit.items():
        if key not in _KANIT_IZINLI:
            raise ValidationError("Eşleştirme kanıtı geçersiz.")
        if not isinstance(val, str):
            raise ValidationError("Eşleştirme kanıtı geçersiz.")
        if len(val) > _KANIT_MAX_LEN:
            raise ValidationError("Eşleştirme kanıtı geçersiz.")
        out[key] = val
    return out


def _assert_line_eslestirilebilir(line: RFQLine) -> None:
    if line.varyant_id is not None:
        raise ValidationError("Satır zaten katalog varyantına bağlı.")
    rfq = line.rfq
    if rfq.durum in {RFQ.Durum.KAPANDI, RFQ.Durum.IPTAL}:
        raise ValidationError("Kapalı/iptal RFQ satırı eşleştirilemez.")


def _assert_varyant_katalog(varyant: Varyant) -> None:
    if not varyant.aktif:
        raise ValidationError("Pasif varyant eşleştirilemez.")
    urun = varyant.urun
    if urun.onay_durumu != "onayli" or urun.yayin_durumu != "aktif":
        raise ValidationError("Yalnız onaylı ve yayında katalog ürünleri.")


def adaylari_bul(*, actor, rfq_line: RFQLine, limit: int = 10) -> list[dict]:
    """Salt okuma aday listesi (yazmaz). Platform SKU/ad; tedarikçi SKU yok."""
    _require_platform_eslestirme(
        actor, action="siparis.rfq.eslestirme.aday_denied", entity_id=str(rfq_line.pk)
    )
    _assert_line_eslestirilebilir(rfq_line)
    lim = max(1, min(int(limit or 10), _MAX_ADAY))
    pairs = catalog_aday_queryset(aciklama=rfq_line.aciklama, limit=lim)
    return [
        {
            "varyant_id": v.pk,
            "sku": v.sku,
            "urun_ad": v.urun.ad,
            "platform_kodu": v.urun.platform_kodu,
            "skor": skor,
        }
        for v, skor in pairs
    ]


def oner(
    *,
    actor,
    rfq_line: RFQLine,
    varyant: Varyant,
    kanit=None,
    skor: int | None = None,
) -> RFQEslestirme:
    """Platform katalog varyantı önerir (ONERILDI). Otomatik bağlama yok."""
    _require_platform_eslestirme(
        actor, action="siparis.rfq.eslestirme.oner_denied", entity_id=str(rfq_line.pk)
    )
    try:
        kanit_n = _normalize_kanit(kanit)
    except ValidationError as exc:
        _deny(
            actor,
            action="siparis.rfq.eslestirme.oner_denied",
            entity_id=str(rfq_line.pk),
            exc=exc,
            reason="kanit_gecersiz",
        )

    try:
        _assert_line_eslestirilebilir(rfq_line)
        _assert_varyant_katalog(varyant)
    except ValidationError as exc:
        _deny(
            actor,
            action="siparis.rfq.eslestirme.oner_denied",
            entity_id=str(rfq_line.pk),
            exc=exc,
            reason="hedef_uygunsuz",
        )

    if skor is None:
        from siparis.selectors.rfq_eslestirme import catalog_aday_queryset as _aday

        found = {
            v.pk: s for v, s in _aday(aciklama=rfq_line.aciklama, limit=_MAX_ADAY)
        }
        skor_v = int(found.get(varyant.pk, 1))
    else:
        skor_v = max(0, min(int(skor), 255))

    try:
        with domain_atomic():
            line = RFQLine.objects.select_for_update().select_related("rfq").get(
                pk=rfq_line.pk
            )
            _assert_line_eslestirilebilir(line)
            if RFQEslestirme.objects.filter(
                rfq_line=line,
                onerilen_varyant=varyant,
                durum=RFQEslestirme.Durum.ONERILDI,
            ).exists():
                raise ValidationError("Bu varyant zaten önerilmiş.")
            if RFQEslestirme.objects.filter(
                rfq_line=line, durum=RFQEslestirme.Durum.ONAYLANDI
            ).exists():
                raise ValidationError("Satır zaten onaylı eşleştirmeye sahip.")

            row = RFQEslestirme(
                rfq_line=line,
                onerilen_varyant=varyant,
                durum=RFQEslestirme.Durum.ONERILDI,
                skor=skor_v,
                kanit=kanit_n,
                olusturan=actor if getattr(actor, "pk", None) else None,
            )
            row.save()
            record_audit(
                actor=actor,
                action="siparis.rfq.eslestirme.onerildi",
                entity_type="RFQEslestirme",
                entity_id=str(row.pk),
                success=True,
                detail={
                    "rfq_line_id": line.pk,
                    "varyant_id": varyant.pk,
                    "skor": skor_v,
                },
            )
            return row
    except ValidationError as exc:
        record_audit_durable(
            actor=actor,
            action="siparis.rfq.eslestirme.oner_denied",
            entity_type="RFQEslestirme",
            entity_id=str(getattr(rfq_line, "pk", "")),
            success=False,
            reason="atomic_sonrasi_red",
            detail={"messages": getattr(exc, "messages", [str(exc)])},
        )
        raise


def onayla(*, actor, eslestirme: RFQEslestirme) -> RFQEslestirme:
    """Öneriyi onayla → RFQLine.varyant bağla; diğer ONERILDI → REDDEDILDI."""
    _require_platform_eslestirme(
        actor,
        action="siparis.rfq.eslestirme.onay_denied",
        entity_id=str(eslestirme.pk),
    )
    try:
        with domain_atomic():
            locked = (
                RFQEslestirme.objects.select_for_update()
                .select_related("rfq_line", "rfq_line__rfq", "onerilen_varyant__urun")
                .get(pk=eslestirme.pk)
            )
            if locked.durum != RFQEslestirme.Durum.ONERILDI:
                raise ValidationError("Yalnız önerilmiş eşleştirme onaylanabilir.")
            line = RFQLine.objects.select_for_update().select_related("rfq").get(
                pk=locked.rfq_line_id
            )
            _assert_line_eslestirilebilir(line)
            _assert_varyant_katalog(locked.onerilen_varyant)

            locked.durum = RFQEslestirme.Durum.ONAYLANDI
            locked._allow_status_transition = True
            try:
                locked.save(update_fields=["durum", "guncelleme_tarihi"])
            finally:
                locked._allow_status_transition = False

            line.varyant = locked.onerilen_varyant
            line._allow_katalog_eslestirme = True
            try:
                line.save(update_fields=["varyant"])
            finally:
                line._allow_katalog_eslestirme = False

            siblings = (
                RFQEslestirme.objects.select_for_update()
                .filter(
                    rfq_line=line,
                    durum=RFQEslestirme.Durum.ONERILDI,
                )
                .exclude(pk=locked.pk)
            )
            for sib in siblings:
                sib.durum = RFQEslestirme.Durum.REDDEDILDI
                kanit = dict(sib.kanit or {})
                kanit["red_nedeni"] = "Başka eşleştirme onaylandı."
                sib.kanit = kanit
                sib._allow_status_transition = True
                try:
                    sib.save(update_fields=["durum", "kanit", "guncelleme_tarihi"])
                finally:
                    sib._allow_status_transition = False

            record_audit(
                actor=actor,
                action="siparis.rfq.eslestirme.onaylandi",
                entity_type="RFQEslestirme",
                entity_id=str(locked.pk),
                success=True,
                detail={
                    "rfq_line_id": line.pk,
                    "varyant_id": locked.onerilen_varyant_id,
                },
            )
            return locked
    except ValidationError as exc:
        record_audit_durable(
            actor=actor,
            action="siparis.rfq.eslestirme.onay_denied",
            entity_type="RFQEslestirme",
            entity_id=str(getattr(eslestirme, "pk", "")),
            success=False,
            reason="atomic_sonrasi_red",
            detail={"messages": getattr(exc, "messages", [str(exc)])},
        )
        raise


def reddet(*, actor, eslestirme: RFQEslestirme, neden: str) -> RFQEslestirme:
    _require_platform_eslestirme(
        actor,
        action="siparis.rfq.eslestirme.red_denied",
        entity_id=str(eslestirme.pk),
    )
    text = (neden or "").strip()
    if not text:
        _deny(
            actor,
            action="siparis.rfq.eslestirme.red_denied",
            entity_id=str(eslestirme.pk),
            exc=ValidationError("Red nedeni zorunludur."),
            reason="neden_yok",
        )
    with domain_atomic():
        locked = RFQEslestirme.objects.select_for_update().get(pk=eslestirme.pk)
        if locked.durum != RFQEslestirme.Durum.ONERILDI:
            raise ValidationError("Yalnız önerilmiş eşleştirme reddedilebilir.")
        locked.durum = RFQEslestirme.Durum.REDDEDILDI
        kanit = dict(locked.kanit or {})
        kanit["red_nedeni"] = text[:_KANIT_MAX_LEN]
        locked.kanit = kanit
        locked._allow_status_transition = True
        try:
            locked.save(update_fields=["durum", "kanit", "guncelleme_tarihi"])
        finally:
            locked._allow_status_transition = False
        record_audit(
            actor=actor,
            action="siparis.rfq.eslestirme.reddedildi",
            entity_type="RFQEslestirme",
            entity_id=str(locked.pk),
            success=True,
            reason=text[:255],
        )
        return locked
