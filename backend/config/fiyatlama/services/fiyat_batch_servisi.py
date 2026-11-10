"""ADR-0018 CP-5…CP-13 — batch dry-run + atomik publish (senkron / freeze)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.yetki_servisi import require_perm
from fiyatlama.models import FiyatBatchIslek, FiyatBatchSatir
from fiyatlama.services.guardrail_servisi import assert_marj_guardrail
from tanimlar.fiyat_kaynagi import FiyatKaynagi, TRY_QUANT
from tanimlar.services.kur_servisi import get_or_create_politikasi
from urunler.models import Urun, Varyant

P_MANAGE_KUR = "tanimlar.manage_kur"
_Q = Decimal(TRY_QUANT)


def _require(actor, *, action: str, entity_id: str = ""):
    try:
        require_perm(actor, P_MANAGE_KUR, message="Kur/batch yetkiniz yok.")
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action=action,
            entity_type="FiyatBatchIslek",
            entity_id=entity_id,
            success=False,
            reason="yetki_yok",
        )
        raise


def _filtre_varyant_qs(filtre: dict):
    qs = Varyant.objects.filter(aktif=True).select_related(
        "urun", "urun__ayar", "urun__kategori", "urun__koleksiyon"
    )
    if not filtre:
        return qs
    ids = filtre.get("varyant_ids") or filtre.get("id_list")
    if ids:
        qs = qs.filter(pk__in=list(ids))
    ayar_id = filtre.get("ayar_id")
    if ayar_id:
        qs = qs.filter(urun__ayar_id=ayar_id)
    koleksiyon_id = filtre.get("koleksiyon_id")
    if koleksiyon_id:
        qs = qs.filter(urun__koleksiyon_id=koleksiyon_id)
    kategori_id = filtre.get("kategori_id")
    if kategori_id:
        # Alt ağaç: kategori + path içeren çocuklar (basit: aynı parent veya self)
        from urunler.models import Kategori

        try:
            kat = Kategori.objects.get(pk=int(kategori_id))
        except (Kategori.DoesNotExist, TypeError, ValueError) as exc:
            raise ValidationError({"kategori_id": "Geçersiz kategori."}) from exc
        # Kategori ağacı alanları projede değişebilir — id + parent_id soft
        child_ids = list(
            Kategori.objects.filter(Q(pk=kat.pk) | Q(ust_id=kat.pk)).values_list(
                "pk", flat=True
            )
        )
        if not child_ids:
            child_ids = [kat.pk]
        qs = qs.filter(urun__kategori_id__in=child_ids)
    return qs


def _etkin_fiyat_try(varyant: Varyant) -> Decimal | None:
    if varyant.sabit_fiyat is not None:
        return Decimal(str(varyant.sabit_fiyat))
    return None


def dry_run_canli_senkron(
    *,
    actor,
    filtre: dict | None = None,
    hedef_fiyatlar: dict[int, Decimal] | None = None,
) -> FiyatBatchIslek:
    """CP-6/8/9: yazmadan önce staging; politika alanları dokunulmaz."""
    _require(actor, action="fiyat.batch.dry_run")
    pol = get_or_create_politikasi()
    filtre = filtre or {}
    hedef_fiyatlar = hedef_fiyatlar or {}
    qs = list(_filtre_varyant_qs(filtre)[: pol.max_batch_satir + 1])
    if len(qs) > pol.max_batch_satir:
        raise ValidationError(
            f"Batch {pol.max_batch_satir} satırı aşıyor; küçültün (CP-13)."
        )
    sok = Decimal(str(pol.sok_esigi_yuzde))
    with domain_atomic():
        islek = FiyatBatchIslek(
            tip=FiyatBatchIslek.Tip.CANLI_SENKRON,
            durum=FiyatBatchIslek.Durum.DRY_RUN,
            filtre=filtre,
            olusturan=actor if getattr(actor, "pk", None) else None,
        )
        islek.save()
        aday = sok_n = bloke = 0
        delta_sum = Decimal("0")
        for v in qs:
            onceki = _etkin_fiyat_try(v)
            yeni = hedef_fiyatlar.get(v.pk)
            if yeni is None:
                FiyatBatchSatir(
                    islek=islek,
                    varyant=v,
                    onceki_sabit_fiyat=onceki,
                    sonuc=FiyatBatchSatir.Sonuc.ATLANDI,
                    neden="Hedef fiyat yok.",
                ).save()
                continue
            yeni_q = Decimal(str(yeni)).quantize(_Q, rounding=ROUND_HALF_UP)
            if yeni_q <= 0:
                FiyatBatchSatir(
                    islek=islek,
                    varyant=v,
                    onceki_sabit_fiyat=onceki,
                    yeni_sabit_fiyat=yeni_q,
                    sonuc=FiyatBatchSatir.Sonuc.BLOKE,
                    neden="0 fiyat yasak.",
                ).save()
                bloke += 1
                continue
            delta = None
            sonuc = FiyatBatchSatir.Sonuc.ADAY
            neden = ""
            if onceki and onceki > 0:
                delta = (
                    (yeni_q - onceki) / onceki * Decimal("100")
                ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                delta_sum += abs(delta)
                if abs(delta) > sok:
                    sonuc = FiyatBatchSatir.Sonuc.SOK
                    neden = f"Şok |Δ|%{delta} > %{sok}"
                    sok_n += 1
                else:
                    aday += 1
            else:
                aday += 1
            # Guardrail: maliyet yoksa yalnız 0 kontrolü; varsa min marj
            maliyet = None
            gr = assert_marj_guardrail(
                toplam_vergisiz=yeni_q, maliyet_referans=maliyet
            )
            if not gr.ok:
                sonuc = FiyatBatchSatir.Sonuc.BLOKE
                neden = gr.neden
                bloke += 1
                aday = max(0, aday - 1)
            FiyatBatchSatir(
                islek=islek,
                varyant=v,
                onceki_sabit_fiyat=onceki,
                yeni_sabit_fiyat=yeni_q,
                delta_yuzde=delta,
                sonuc=sonuc,
                neden=neden,
            ).save()
        n = max(1, aday + sok_n)
        islek.ozet = {
            "n": len(qs),
            "aday": aday,
            "sok": sok_n,
            "bloke": bloke,
            "ortalama_abs_delta_yuzde": str(
                (delta_sum / Decimal(n)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            ),
        }
        islek._allow_transition = True
        try:
            islek.save(update_fields=["ozet"])
        finally:
            islek._allow_transition = False
        record_audit(
            actor=actor,
            action="fiyat.batch.dry_run",
            entity_type="FiyatBatchIslek",
            entity_id=str(islek.pk),
            success=True,
            detail=islek.ozet,
        )
        return islek


def dry_run_manuel_freeze(
    *,
    actor,
    filtre: dict | None = None,
    hedef_fiyatlar: dict[int, Decimal] | None = None,
) -> FiyatBatchIslek:
    """CP-7: etkin fiyat → sabit mühür adayları (henüz yazılmaz)."""
    _require(actor, action="fiyat.batch.freeze_dry")
    # Aynı staging yolu; tip farklı
    islek = dry_run_canli_senkron(
        actor=actor, filtre=filtre, hedef_fiyatlar=hedef_fiyatlar
    )
    islek.tip = FiyatBatchIslek.Tip.MANUEL_FREEZE
    islek._allow_transition = True
    try:
        islek.save(update_fields=["tip"])
    finally:
        islek._allow_transition = False
    return islek


def publish(*, actor, islek: FiyatBatchIslek) -> FiyatBatchIslek:
    """CP-13: tek atomic; BLOKE/SOK publish'e girmez; partial success yok."""
    _require(actor, action="fiyat.batch.publish", entity_id=str(islek.pk))
    if islek.durum != FiyatBatchIslek.Durum.DRY_RUN:
        raise ValidationError("Yalnız DRY_RUN yayınlanır.")
    with domain_atomic():
        locked = FiyatBatchIslek.objects.select_for_update().get(pk=islek.pk)
        if locked.durum != FiyatBatchIslek.Durum.DRY_RUN:
            raise ValidationError("Yalnız DRY_RUN yayınlanır.")
        satirlar = list(
            FiyatBatchSatir.objects.select_for_update()
            .select_related("varyant", "varyant__urun")
            .filter(islek=locked)
        )
        uygula = [
            s
            for s in satirlar
            if s.sonuc == FiyatBatchSatir.Sonuc.ADAY and s.yeni_sabit_fiyat
        ]
        for s in uygula:
            v = Varyant.objects.select_for_update().select_related("urun").get(
                pk=s.varyant_id
            )
            u = Urun.objects.select_for_update().get(pk=v.urun_id)
            yeni = Decimal(str(s.yeni_sabit_fiyat)).quantize(
                _Q, rounding=ROUND_HALF_UP
            )
            v.sabit_fiyat = yeni
            v.save(update_fields=["sabit_fiyat"])
            # Freeze / senkron mühür
            if u.fiyat_tipi != "sabit":
                # Urun immutability — update() ile alan (servis dışı save koruması)
                Urun.objects.filter(pk=u.pk).update(
                    fiyat_tipi="sabit",
                    fiyat_kaynagi=FiyatKaynagi.MANUEL_GIRIS
                    if locked.tip == FiyatBatchIslek.Tip.MANUEL_FREEZE
                    else FiyatKaynagi.CANLI_PIYASA,
                )
            else:
                Urun.objects.filter(pk=u.pk).update(
                    fiyat_kaynagi=FiyatKaynagi.MANUEL_GIRIS
                    if locked.tip == FiyatBatchIslek.Tip.MANUEL_FREEZE
                    else u.fiyat_kaynagi,
                )
            s.sonuc = FiyatBatchSatir.Sonuc.UYGULANDI
            s._allow_update = True
            try:
                s.save(update_fields=["sonuc"])
            finally:
                s._allow_update = False
        locked.durum = FiyatBatchIslek.Durum.YAYINLANDI
        locked.yayin_tarihi = timezone.now()
        locked._allow_transition = True
        try:
            locked.save(update_fields=["durum", "yayin_tarihi"])
        finally:
            locked._allow_transition = False
        record_audit(
            actor=actor,
            action="fiyat.batch.publish",
            entity_type="FiyatBatchIslek",
            entity_id=str(locked.pk),
            success=True,
            detail={"uygulanan": len(uygula), "tip": locked.tip},
        )
        return locked
