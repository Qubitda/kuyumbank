"""Ürün durum geçişleri: kurallar tek yerde durur (ADR-0003-03 K-004, Faz 1.1 P0).

Yetki/sahiplik kontrolleri atomic dışında yapılır. Reddedilen deneme audit'i
ayrı (durable) transaction'da yazılır; başarılı geçiş audit'i ürün yazımıyla
aynı atomic içindedir.
"""
import copy

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.utils import timezone

from firmalar.models import AuditOlay
from firmalar.role_permissions import P
from firmalar.services.audit_servisi import domain_atomic, record_audit, record_audit_durable
from firmalar.services.yetki_servisi import require_perm

from ..models import Urun

_KIMLIK_CAKISMA_MSG = "Kimlik anahtarı çakışması nedeniyle işlem yapılamaz."


def _kilitle(urun):
    return Urun.objects.select_for_update().get(pk=urun.pk)


def _gonderime_hazir_mi(urun):
    varyantlar = list(urun.varyantlar.filter(aktif=True))
    if not varyantlar:
        raise ValidationError("En az bir aktif varyant girilmeden onaya gönderilemez.")
    for v in varyantlar:
        try:
            v.full_clean()
        except ValidationError as e:
            raise ValidationError(f"Varyant {v.sku or v.pk}: " + "; ".join(e.messages))


def _taslak_kopya(urun, **degisiklikler):
    kopya = copy.copy(urun)
    kopya._state = copy.copy(urun._state)
    kopya._state.fields_cache = dict(urun._state.fields_cache)
    for alan, deger in degisiklikler.items():
        setattr(kopya, alan, deger)
    return kopya


def _deny(kullanici, *, action, urun, exc, reason, detail=None):
    record_audit_durable(
        actor=kullanici,
        action=action,
        entity_type="Urun",
        entity_id=getattr(urun, "pk", "") or "",
        success=False,
        reason=reason,
        detail=detail or {},
    )
    raise exc


def _assert_submit_ownership(urun, kullanici, *, action="urun.onaya_gonder"):
    """K-004: sahip firma + submit permission; IDOR engeli (atomic dışı)."""
    if not getattr(kullanici, "firma_id", None):
        _deny(
            kullanici,
            action=action,
            urun=urun,
            exc=ValidationError("Kullanıcının firması tanımlı olmalıdır."),
            reason="firma_yok",
        )
    # ADR-0005 K-004: onay öncesi yalnız oluşturan firma (taslak sahipliği)
    if urun.olusturan_firma_id != kullanici.firma_id:
        _deny(
            kullanici,
            action=action,
            urun=urun,
            exc=PermissionDenied("Başka firmaya ait ürüne işlem yapılamaz."),
            reason="sahiplik_uyusmazligi",
            detail={
                "urun_olusturan_firma_id": urun.olusturan_firma_id,
                "user_firma_id": kullanici.firma_id,
            },
        )
    try:
        require_perm(kullanici, P["submit_urun"], message="Ürün gönderim yetkiniz yok.")
    except PermissionDenied as exc:
        _deny(
            kullanici,
            action=action,
            urun=urun,
            exc=exc,
            reason="yetki_yok",
        )


def _require_platform_urun_perm(kullanici, perm, *, action, urun):
    try:
        require_perm(kullanici, perm)
    except PermissionDenied as exc:
        _deny(kullanici, action=action, urun=urun, exc=exc, reason="yetki_yok")
    if not (kullanici.firma_id and kullanici.firma.platform_mu):
        _deny(
            kullanici,
            action=action,
            urun=urun,
            exc=PermissionDenied("Bu işlem yalnızca platform firması kullanıcılarınındır."),
            reason="platform_firma_degil",
        )


def _aktif_kimlik_cakisiyor_mu(urun) -> bool:
    """A/B dolu anahtar: reddedildi hariç başka kayıt var mı? (ADR-0006 O2)."""
    if urun.kimlik_sinifi not in ("A", "B"):
        return False
    anahtar = (urun.kimlik_anahtari or "").strip()
    if not anahtar:
        return False
    return (
        Urun.objects.filter(
            kimlik_sinifi=urun.kimlik_sinifi,
            kimlik_anahtari=anahtar,
        )
        .exclude(onay_durumu="reddedildi")
        .exclude(pk=urun.pk)
        .exists()
    )


def onaya_gonder(urun, kullanici):
    _assert_submit_ownership(urun, kullanici)
    urun.refresh_from_db()
    if urun.onay_durumu not in ("taslak", "reddedildi"):
        _deny(
            kullanici,
            action="urun.onaya_gonder",
            urun=urun,
            exc=ValidationError("Yalnızca taslak veya reddedilmiş ürün onaya gönderilebilir."),
            reason="gecersiz_durum",
        )
    try:
        _gonderime_hazir_mi(urun)
    except ValidationError as exc:
        _deny(
            kullanici,
            action="urun.onaya_gonder",
            urun=urun,
            exc=exc,
            reason="hazir_degil",
        )

    # reddedildi→onay_bekliyor (ve taslak): aktif kayıtla anahtar çakışması
    if _aktif_kimlik_cakisiyor_mu(urun):
        _deny(
            kullanici,
            action="urun.onaya_gonder",
            urun=urun,
            exc=ValidationError(_KIMLIK_CAKISMA_MSG),
            reason="kimlik_cakisma",
        )

    try:
        with domain_atomic():
            urun = _kilitle(urun)
            if urun.onay_durumu not in ("taslak", "reddedildi"):
                raise ValidationError(
                    "Yalnızca taslak veya reddedilmiş ürün onaya gönderilebilir."
                )
            _gonderime_hazir_mi(urun)
            if _aktif_kimlik_cakisiyor_mu(urun):
                raise ValidationError(_KIMLIK_CAKISMA_MSG)

            aday = _taslak_kopya(urun, onay_durumu="onay_bekliyor", red_nedeni="")
            aday.full_clean()

            Urun.objects.filter(pk=urun.pk).update(
                onay_durumu="onay_bekliyor",
                red_nedeni="",
                guncelleme_zamani=timezone.now(),
            )
            urun.refresh_from_db()
            record_audit(
                actor=kullanici,
                action="urun.onaya_gonder",
                entity_type="Urun",
                entity_id=urun.pk,
                success=True,
            )
            return urun
    except ValidationError as exc:
        # full_clean / validate_constraints kimlik unique → genel mesaj (sızıntı yok)
        msgs = getattr(exc, "messages", [str(exc)])
        if any("urun_kimlik_ab_anahtar_uniq" in str(m) for m in msgs):
            _deny(
                kullanici,
                action="urun.onaya_gonder",
                urun=urun,
                exc=ValidationError(_KIMLIK_CAKISMA_MSG),
                reason="kimlik_cakisma_yaris",
            )
        record_audit_durable(
            actor=kullanici,
            action="urun.onaya_gonder",
            entity_type="Urun",
            entity_id=getattr(urun, "pk", ""),
            success=False,
            reason="atomic_sonrasi_red",
            detail={"messages": list(msgs)},
        )
        raise
    except IntegrityError:
        # Yarış: unique kısıt — genel mesaj, varlık sızdırma yok
        _deny(
            kullanici,
            action="urun.onaya_gonder",
            urun=urun,
            exc=ValidationError(_KIMLIK_CAKISMA_MSG),
            reason="kimlik_cakisma_yaris",
        )


def _son_gonderen_id(urun) -> int | None:
    """Son başarılı onaya_gonder aktörü; yoksa olusturan_kullanici."""
    row = (
        AuditOlay.objects.filter(
            action="urun.onaya_gonder",
            entity_type="Urun",
            entity_id=str(urun.pk),
            success=True,
        )
        .order_by("-created_at")
        .values_list("actor_id", flat=True)
        .first()
    )
    if row:
        return row
    return getattr(urun, "olusturan_kullanici_id", None)


def _assert_dort_goz(urun, kullanici, *, action: str):
    gonderen_id = _son_gonderen_id(urun)
    if gonderen_id and gonderen_id == getattr(kullanici, "pk", None):
        _deny(
            kullanici,
            action=action,
            urun=urun,
            exc=PermissionDenied("Dört göz: gönderen ile onaylayan/yayınlayan aynı olamaz."),
            reason="dort_goz",
        )


def onayla(urun, kullanici):
    _require_platform_urun_perm(
        kullanici, P["approve_urun"], action="urun.onayla", urun=urun
    )
    urun.refresh_from_db()
    if urun.onay_durumu != "onay_bekliyor":
        _deny(
            kullanici,
            action="urun.onayla",
            urun=urun,
            exc=ValidationError("Yalnızca onay bekleyen ürün onaylanabilir."),
            reason="gecersiz_durum",
        )
    _assert_dort_goz(urun, kullanici, action="urun.onayla")

    try:
        with domain_atomic():
            urun = _kilitle(urun)
            if urun.onay_durumu != "onay_bekliyor":
                raise ValidationError("Yalnızca onay bekleyen ürün onaylanabilir.")

            aday = _taslak_kopya(
                urun,
                onay_durumu="onayli",
                onaylayan_kullanici=kullanici,
                onay_zamani=timezone.now(),
                red_nedeni="",
            )
            aday.full_clean()

            Urun.objects.filter(pk=urun.pk).update(
                onay_durumu="onayli",
                onaylayan_kullanici=kullanici,
                onay_zamani=timezone.now(),
                red_nedeni="",
                guncelleme_zamani=timezone.now(),
            )
            urun.refresh_from_db()
            record_audit(
                actor=kullanici,
                action="urun.onayla",
                entity_type="Urun",
                entity_id=urun.pk,
                success=True,
            )
            return urun
    except ValidationError as exc:
        record_audit_durable(
            actor=kullanici,
            action="urun.onayla",
            entity_type="Urun",
            entity_id=getattr(urun, "pk", ""),
            success=False,
            reason="atomic_sonrasi_red",
            detail={"messages": getattr(exc, "messages", [str(exc)])},
        )
        raise


def reddet(urun, kullanici, neden):
    _require_platform_urun_perm(
        kullanici, P["approve_urun"], action="urun.reddet", urun=urun
    )
    if not (neden or "").strip():
        _deny(
            kullanici,
            action="urun.reddet",
            urun=urun,
            exc=ValidationError("Red nedeni yazılmalıdır."),
            reason="neden_yok",
        )
    urun.refresh_from_db()
    if urun.onay_durumu != "onay_bekliyor":
        _deny(
            kullanici,
            action="urun.reddet",
            urun=urun,
            exc=ValidationError("Yalnızca onay bekleyen ürün reddedilebilir."),
            reason="gecersiz_durum",
        )

    try:
        with domain_atomic():
            urun = _kilitle(urun)
            if urun.onay_durumu != "onay_bekliyor":
                raise ValidationError("Yalnızca onay bekleyen ürün reddedilebilir.")

            aday = _taslak_kopya(
                urun,
                onay_durumu="reddedildi",
                red_nedeni=neden.strip(),
                yayin_durumu="pasif",
                onaylayan_kullanici=None,
                onay_zamani=None,
            )
            aday.full_clean()

            Urun.objects.filter(pk=urun.pk).update(
                onay_durumu="reddedildi",
                red_nedeni=neden.strip(),
                yayin_durumu="pasif",
                onaylayan_kullanici=None,
                onay_zamani=None,
                guncelleme_zamani=timezone.now(),
            )
            urun.refresh_from_db()
            record_audit(
                actor=kullanici,
                action="urun.reddet",
                entity_type="Urun",
                entity_id=urun.pk,
                success=True,
                reason=neden.strip()[:255],
            )
            return urun
    except ValidationError as exc:
        record_audit_durable(
            actor=kullanici,
            action="urun.reddet",
            entity_type="Urun",
            entity_id=getattr(urun, "pk", ""),
            success=False,
            reason="atomic_sonrasi_red",
            detail={"messages": getattr(exc, "messages", [str(exc)])},
        )
        raise


def yayina_al(urun, kullanici, durum="aktif"):
    _require_platform_urun_perm(
        kullanici, P["publish_urun"], action="urun.yayina_al", urun=urun
    )
    if durum not in ("aktif", "yakinda"):
        _deny(
            kullanici,
            action="urun.yayina_al",
            urun=urun,
            exc=ValidationError("Yayın durumu 'aktif' veya 'yakinda' olmalıdır."),
            reason="gecersiz_durum",
        )
    urun.refresh_from_db()
    if urun.onay_durumu != "onayli":
        _deny(
            kullanici,
            action="urun.yayina_al",
            urun=urun,
            exc=ValidationError("Yalnızca onaylı ürün yayına alınabilir."),
            reason="gecersiz_durum",
        )
    _assert_dort_goz(urun, kullanici, action="urun.yayina_al")

    try:
        with domain_atomic():
            urun = _kilitle(urun)
            if urun.onay_durumu != "onayli":
                raise ValidationError("Yalnızca onaylı ürün yayına alınabilir.")
            if durum == "aktif" and not urun.kanallar.filter(aktif=True).exists():
                raise ValidationError(
                    "Aktif yayın için ürünün en az bir satış kanalı seçili olmalıdır."
                )

            aday = _taslak_kopya(urun, yayin_durumu=durum)
            aday.full_clean()

            Urun.objects.filter(pk=urun.pk).update(
                yayin_durumu=durum,
                guncelleme_zamani=timezone.now(),
            )
            urun.refresh_from_db()
            record_audit(
                actor=kullanici,
                action="urun.yayina_al",
                entity_type="Urun",
                entity_id=urun.pk,
                success=True,
                detail={"durum": durum},
            )
            return urun
    except ValidationError as exc:
        record_audit_durable(
            actor=kullanici,
            action="urun.yayina_al",
            entity_type="Urun",
            entity_id=getattr(urun, "pk", ""),
            success=False,
            reason="atomic_sonrasi_red",
            detail={"messages": getattr(exc, "messages", [str(exc)])},
        )
        raise


def pasife_al(urun, kullanici):
    _require_platform_urun_perm(
        kullanici, P["publish_urun"], action="urun.pasife_al", urun=urun
    )

    with domain_atomic():
        urun = _kilitle(urun)
        if urun.yayin_durumu == "pasif":
            return urun
        Urun.objects.filter(pk=urun.pk).update(
            yayin_durumu="pasif",
            guncelleme_zamani=timezone.now(),
        )
        urun.refresh_from_db()
        record_audit(
            actor=kullanici,
            action="urun.pasife_al",
            entity_type="Urun",
            entity_id=urun.pk,
            success=True,
        )
        return urun


# ADR-0006 O1 — kritik alanlar (onaylı ürün)
KRITIK_ALANLAR = (
    "kimlik_sinifi",
    "kimlik_anahtari",
    "ayar_id",
    "kategori_id",
    "fiyat_tipi",
    "ad",
)


def assert_onayli_kritik_kilit(urun):
    """Onaylı üründe kritik alan değişimini engeller; taslaga_al gerekir."""
    if getattr(urun, "onay_durumu", None) != "onayli" or not urun.pk:
        return
    eski = Urun.objects.filter(pk=urun.pk).values(*KRITIK_ALANLAR).first()
    if not eski:
        return
    for alan in KRITIK_ALANLAR:
        if eski.get(alan) != getattr(urun, alan):
            raise ValidationError(
                "Onaylı ürünün kritik alanı değiştirilemez; önce taslağa alın."
            )


def geri_cek(urun, kullanici):
    """Onay bekleyen ürünü taslağa çeker (tedarikçi sahiplik + submit_urun)."""
    _assert_submit_ownership(urun, kullanici, action="urun.geri_cek")
    urun.refresh_from_db()
    if urun.onay_durumu != "onay_bekliyor":
        _deny(
            kullanici,
            action="urun.geri_cek",
            urun=urun,
            exc=ValidationError("Yalnızca onay bekleyen ürün geri çekilebilir."),
            reason="gecersiz_durum",
        )
    try:
        with domain_atomic():
            urun = _kilitle(urun)
            if urun.onay_durumu != "onay_bekliyor":
                raise ValidationError("Yalnızca onay bekleyen ürün geri çekilebilir.")
            Urun.objects.filter(pk=urun.pk).update(
                onay_durumu="taslak",
                red_nedeni="",
                guncelleme_zamani=timezone.now(),
            )
            urun.refresh_from_db()
            record_audit(
                actor=kullanici,
                action="urun.geri_cek",
                entity_type="Urun",
                entity_id=urun.pk,
                success=True,
            )
            return urun
    except ValidationError as exc:
        record_audit_durable(
            actor=kullanici,
            action="urun.geri_cek",
            entity_type="Urun",
            entity_id=getattr(urun, "pk", ""),
            success=False,
            reason="atomic_sonrasi_red",
            detail={"messages": getattr(exc, "messages", [str(exc)])},
        )
        raise


def taslaga_al(urun, kullanici):
    """Onaylı ürünü taslağa alır (platform); yeniden onay gerekir."""
    _require_platform_urun_perm(
        kullanici, P["approve_urun"], action="urun.taslaga_al", urun=urun
    )
    urun.refresh_from_db()
    if urun.onay_durumu != "onayli":
        _deny(
            kullanici,
            action="urun.taslaga_al",
            urun=urun,
            exc=ValidationError("Yalnızca onaylı ürün taslağa alınabilir."),
            reason="gecersiz_durum",
        )
    try:
        with domain_atomic():
            urun = _kilitle(urun)
            if urun.onay_durumu != "onayli":
                raise ValidationError("Yalnızca onaylı ürün taslağa alınabilir.")
            Urun.objects.filter(pk=urun.pk).update(
                onay_durumu="taslak",
                yayin_durumu="pasif",
                onaylayan_kullanici=None,
                onay_zamani=None,
                red_nedeni="",
                guncelleme_zamani=timezone.now(),
            )
            urun.refresh_from_db()
            record_audit(
                actor=kullanici,
                action="urun.taslaga_al",
                entity_type="Urun",
                entity_id=urun.pk,
                success=True,
            )
            return urun
    except ValidationError as exc:
        record_audit_durable(
            actor=kullanici,
            action="urun.taslaga_al",
            entity_type="Urun",
            entity_id=getattr(urun, "pk", ""),
            success=False,
            reason="atomic_sonrasi_red",
            detail={"messages": getattr(exc, "messages", [str(exc)])},
        )
        raise
