"""Katalog eşleştirme servisleri (ADR-0005 K5, ADR-0006 B3/B4a).

Fail audit atomic dışı. Durum kontrolleri select_for_update sonrasında.
"""

from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import domain_atomic, record_audit, record_audit_durable
from firmalar.services.yetki_servisi import can_view_all_tenants, require_perm
from fiyatlama.models import TedarikciTeklif
from urunler.models import Urun
from urunler.selectors.katalog_tenant import scope_eslestirme_hedef_urun_queryset
from urunler.services.gram_bandi import teklif_gram_band_uygun_mu

_KANIT_IZINLI = frozenset(
    {"not", "aciklama", "referans", "kaynak", "red_nedeni", "ayirma_nedeni"}
)
_KANIT_MAX_LEN = 500
_GENEL_HEDEF_HATA = "Eşleştirme hedefi uygun değil."


def _deny(kullanici, *, action, entity_id, exc, reason, detail=None):
    record_audit_durable(
        actor=kullanici,
        action=action,
        entity_type="TedarikciTeklif",
        entity_id=str(entity_id or ""),
        success=False,
        reason=reason,
        detail=detail or {},
    )
    raise exc


def _require_own_teklif(teklif, kullanici):
    if teklif.tedarikci_id != getattr(kullanici, "firma_id", None):
        _deny(
            kullanici,
            action="teklif.eslestir_oner",
            entity_id=teklif.pk,
            exc=PermissionDenied("Başka firmanın teklifine işlem yapılamaz."),
            reason="sahiplik_uyusmazligi",
        )
    try:
        require_perm(kullanici, P["manage_own_teklif"])
    except PermissionDenied as exc:
        _deny(
            kullanici,
            action="teklif.eslestir_oner",
            entity_id=teklif.pk,
            exc=exc,
            reason="yetki_yok",
        )


def _require_platform_eslestirme(kullanici, *, action, entity_id):
    try:
        require_perm(kullanici, P["approve_eslestirme"])
    except PermissionDenied as exc:
        _deny(kullanici, action=action, entity_id=entity_id, exc=exc, reason="yetki_yok")
    if not (kullanici.firma_id and kullanici.firma.platform_mu):
        _deny(
            kullanici,
            action=action,
            entity_id=entity_id,
            exc=PermissionDenied("Eşleştirme onayı yalnız platform kullanıcılarınındır."),
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


def _guven_hesapla(urun, teklif) -> str:
    """kesin yalnız A/B ve tedarikci_kodu == urun.kimlik_anahtari (kanıt oracle yok)."""
    if urun.kimlik_sinifi not in ("A", "B"):
        return TedarikciTeklif.EslestirmeGuveni.MANUEL
    anahtar = (urun.kimlik_anahtari or "").strip()
    if not anahtar:
        return TedarikciTeklif.EslestirmeGuveni.MANUEL
    if (teklif.tedarikci_kodu or "").strip() == anahtar:
        return TedarikciTeklif.EslestirmeGuveni.KESIN
    return TedarikciTeklif.EslestirmeGuveni.MANUEL


def _hedef_uygun_mu(hedef: Urun, teklif, kullanici) -> bool:
    if not scope_eslestirme_hedef_urun_queryset(
        Urun.objects.filter(pk=hedef.pk), kullanici
    ).exists():
        return False
    if teklif.varyant.urun.ayar_id != hedef.ayar_id:
        return False
    return True


def _assert_gram_band(teklif, kullanici, *, action: str, hedef_urun=None):
    varyant = teklif.varyant
    if hedef_urun is not None:
        # Hedef ürünün aynı ayardaki varyant bandı — teklif varyantı üzerinden
        pass
    if not teklif_gram_band_uygun_mu(teklif, varyant):
        _deny(
            kullanici,
            action=action,
            entity_id=teklif.pk,
            exc=ValidationError("Teklif gramı uygun bandın dışında."),
            reason="gram_bandi_disi",
            detail={},
        )


def teklif_eslestir_oner(teklif, kullanici, *, hedef_urun=None, kanit=None):
    """Tedarikçi eşleştirme önerir; kesin yalnız sunucu kimliğiyle (K1/K5)."""
    _require_own_teklif(teklif, kullanici)
    try:
        kanit = _normalize_kanit(kanit)
    except ValidationError as exc:
        _deny(
            kullanici,
            action="teklif.eslestir_oner",
            entity_id=teklif.pk,
            exc=exc,
            reason="kanit_gecersiz",
        )

    urun = hedef_urun or teklif.varyant.urun
    if not _hedef_uygun_mu(urun, teklif, kullanici):
        _deny(
            kullanici,
            action="teklif.eslestir_oner",
            entity_id=teklif.pk,
            exc=ValidationError(_GENEL_HEDEF_HATA),
            reason="hedef_uygunsuz",
        )

    _assert_gram_band(teklif, kullanici, action="teklif.eslestir_oner", hedef_urun=urun)
    guven = _guven_hesapla(urun, teklif)
    # Audit detail'de güven yalnız platform aktöre (tedarikçiye sızmaz)
    audit_guven = guven if can_view_all_tenants(kullanici) else "gizli"

    try:
        with domain_atomic():
            teklif = TedarikciTeklif.objects.select_for_update().get(pk=teklif.pk)
            if teklif.eslestirme_durumu in (
                TedarikciTeklif.EslestirmeDurumu.ONAYLANDI,
                TedarikciTeklif.EslestirmeDurumu.AYRILDI,
            ):
                raise ValidationError("Bu eşleştirme durumunda yeni öneri yapılamaz.")

            teklif.eslestirme_durumu = TedarikciTeklif.EslestirmeDurumu.ONERILDI
            teklif.eslestirme_guveni = guven  # DB; tedarikçi admin formunda gizlenir (B1)
            teklif.eslestirme_kaniti = kanit
            teklif.esdegerlik_seviyesi = TedarikciTeklif.EsdegerlikSeviyesi.ESDEGER
            teklif.hedef_urun = urun
            teklif.save(
                update_fields=[
                    "eslestirme_durumu",
                    "eslestirme_guveni",
                    "eslestirme_kaniti",
                    "esdegerlik_seviyesi",
                    "hedef_urun",
                    "guncelleme_tarihi",
                ]
            )
            record_audit(
                actor=kullanici,
                action="teklif.eslestir_oner",
                entity_type="TedarikciTeklif",
                entity_id=teklif.pk,
                success=True,
                detail={"hedef_urun_id": urun.pk, "guven": audit_guven},
            )
            return teklif
    except ValidationError as exc:
        record_audit_durable(
            actor=kullanici,
            action="teklif.eslestir_oner",
            entity_type="TedarikciTeklif",
            entity_id=getattr(teklif, "pk", ""),
            success=False,
            reason="atomic_sonrasi_red",
            detail={"messages": getattr(exc, "messages", [str(exc)])},
        )
        raise


def eslestirmeyi_onayla(teklif, kullanici):
    _require_platform_eslestirme(
        kullanici, action="teklif.eslestirme_onayla", entity_id=teklif.pk
    )
    with domain_atomic():
        teklif = TedarikciTeklif.objects.select_for_update().get(pk=teklif.pk)
        if teklif.eslestirme_durumu != TedarikciTeklif.EslestirmeDurumu.ONERILDI:
            raise ValidationError("Yalnızca önerilmiş eşleştirme onaylanabilir.")
        hedef = teklif.hedef_urun
        if hedef is None:
            raise ValidationError("Eşleştirme hedefi uygun değil.")
        if teklif.varyant.urun.ayar_id != hedef.ayar_id:
            raise ValidationError("Eşleştirme hedefi uygun değil.")
        if not teklif_gram_band_uygun_mu(teklif, teklif.varyant):
            raise ValidationError("Teklif gramı uygun bandın dışında.")
        # Platform onayında güven yeniden hesaplanır
        teklif.eslestirme_guveni = _guven_hesapla(hedef, teklif)
        teklif.eslestirme_durumu = TedarikciTeklif.EslestirmeDurumu.ONAYLANDI
        teklif.eslestiren_kullanici = kullanici
        teklif.save(
            update_fields=[
                "eslestirme_durumu",
                "eslestirme_guveni",
                "eslestiren_kullanici",
                "guncelleme_tarihi",
            ]
        )
        record_audit(
            actor=kullanici,
            action="teklif.eslestirme_onayla",
            entity_type="TedarikciTeklif",
            entity_id=teklif.pk,
            success=True,
            detail={"guven": teklif.eslestirme_guveni, "hedef_urun_id": hedef.pk},
        )
        return teklif


def eslestirmeyi_reddet(teklif, kullanici, neden: str):
    _require_platform_eslestirme(
        kullanici, action="teklif.eslestirme_reddet", entity_id=teklif.pk
    )
    if not (neden or "").strip():
        _deny(
            kullanici,
            action="teklif.eslestirme_reddet",
            entity_id=teklif.pk,
            exc=ValidationError("Red nedeni zorunludur."),
            reason="neden_yok",
        )
    with domain_atomic():
        teklif = TedarikciTeklif.objects.select_for_update().get(pk=teklif.pk)
        if teklif.eslestirme_durumu != TedarikciTeklif.EslestirmeDurumu.ONERILDI:
            raise ValidationError("Yalnızca önerilmiş eşleştirme reddedilebilir.")
        teklif.eslestirme_durumu = TedarikciTeklif.EslestirmeDurumu.REDDEDILDI
        teklif.eslestiren_kullanici = kullanici
        kanit = dict(teklif.eslestirme_kaniti or {})
        kanit["red_nedeni"] = neden.strip()[:_KANIT_MAX_LEN]
        teklif.eslestirme_kaniti = kanit
        teklif.save(
            update_fields=[
                "eslestirme_durumu",
                "eslestiren_kullanici",
                "eslestirme_kaniti",
                "guncelleme_tarihi",
            ]
        )
        record_audit(
            actor=kullanici,
            action="teklif.eslestirme_reddet",
            entity_type="TedarikciTeklif",
            entity_id=teklif.pk,
            success=True,
            reason=neden.strip()[:255],
        )
        return teklif


def urunu_ayir(teklif, kullanici, neden: str):
    """Yanlış eşleştirmeyi geri al — yalnız ONAYLANDI durumundan (K5)."""
    _require_platform_eslestirme(kullanici, action="teklif.ayir", entity_id=teklif.pk)
    if not (neden or "").strip():
        _deny(
            kullanici,
            action="teklif.ayir",
            entity_id=teklif.pk,
            exc=ValidationError("Ayırma nedeni zorunludur."),
            reason="neden_yok",
        )
    with domain_atomic():
        teklif = TedarikciTeklif.objects.select_for_update().get(pk=teklif.pk)
        if teklif.eslestirme_durumu != TedarikciTeklif.EslestirmeDurumu.ONAYLANDI:
            raise ValidationError("Ayırma yalnız onaylanmış eşleştirmeden yapılabilir.")
        teklif.eslestirme_durumu = TedarikciTeklif.EslestirmeDurumu.AYRILDI
        kanit = dict(teklif.eslestirme_kaniti or {})
        kanit["ayirma_nedeni"] = neden.strip()[:_KANIT_MAX_LEN]
        teklif.eslestirme_kaniti = kanit
        teklif.save(
            update_fields=["eslestirme_durumu", "eslestirme_kaniti", "guncelleme_tarihi"]
        )
        record_audit(
            actor=kullanici,
            action="teklif.ayir",
            entity_type="TedarikciTeklif",
            entity_id=teklif.pk,
            success=True,
            reason=neden.strip()[:255],
        )
        return teklif
