"""Merkezi döviz dönüşümü (K-012 / ADR-0008 Dilim 3.4).

Kur semantiği (DOĞRULANDI — `DovizKuru.kur` verbose: "Kur (TL)"):
  gözlem.kur = 1 birim yabancı para için TRY tutarı.

  USD → TRY: tutar_usd × kur
  TRY → USD: tutar_try / kur
  USD → EUR: (tutar_usd × kur_usd) / kur_eur   (TRY pivot)

Aynı PB: kimlik dönüşümü (kur=1, gözlem yok).
Gözlem verilirse o kayıt kullanılır; sessizce daha yeni gözleme düşülmez.
Gözlem yoksa `kur_servisi.resolve_doviz_kuru` (aktif sağlayıcı + taraf tipi + stale kontrol).

TRY dışı yuvarlama: ADR §6 açık (muhasebe doğrulaması). Geçici politika:
tüm ISO para birimleri için 0.01 HALF_UP (TRY ile aynı); finans kararı gelince konfig.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError

from tanimlar.models import DovizKuru, KurTaraf
from tanimlar.services import kur_servisi

TRY = "TRY"
DESTEKLENEN_PB = frozenset({"TRY", "USD", "EUR", "GBP"})
HASSASIYET = Decimal("0.01")
ROUNDING = ROUND_HALF_UP


class CurrencyConversionError(ValidationError):
    """Dönüşüm reddi (eksik/stale/geçersiz kur veya PB)."""


@dataclass(frozen=True)
class ConversionResult:
    tutar: Decimal
    tutar_yuvarlanmis: Decimal
    kaynak_pb: str
    hedef_pb: str
    efektif_carpan: Decimal
    gozlem_idler: tuple[int, ...]
    taraf: str


def _d(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def _q(d: Decimal) -> Decimal:
    return d.quantize(HASSASIYET, rounding=ROUNDING)


def _normalize_pb(pb: str) -> str:
    code = (pb or "").strip().upper()
    if code not in DESTEKLENEN_PB:
        raise CurrencyConversionError({"para_birimi": f"Desteklenmeyen para birimi: {pb!r}"})
    return code


def _assert_taraf(taraf: str) -> str:
    if taraf not in (KurTaraf.ALICI, KurTaraf.TEDARIKCI):
        raise CurrencyConversionError({"taraf": f"Geçersiz kur tarafı: {taraf!r}"})
    return taraf


def _assert_gozlem(gozlem: DovizKuru, *, para_birimi: str, now=None) -> None:
    if gozlem.para_birimi != para_birimi:
        raise CurrencyConversionError(
            f"Gözlem para birimi uyuşmuyor: beklenen {para_birimi}, gelen {gozlem.para_birimi}."
        )
    if gozlem.kur is None or gozlem.kur <= 0:
        raise CurrencyConversionError("Kur gözlemi geçersiz (kur ≤ 0).")
    if kur_servisi.gozlem_stale_mi(gozlem, now=now):
        raise kur_servisi.KurStaleError(
            f"Döviz kuru stale (id={gozlem.pk}); dönüşüm reddedildi."
        )


def _try_per_unit(
    para_birimi: str,
    *,
    taraf: str,
    gozlem: DovizKuru | None,
    now=None,
) -> tuple[Decimal, int]:
    """1 birim yabancı para = kaç TRY. Döner (kur, gozlem_id)."""
    if gozlem is not None:
        _assert_gozlem(gozlem, para_birimi=para_birimi, now=now)
        return _d(gozlem.kur), int(gozlem.pk)
    obs = kur_servisi.resolve_doviz_kuru(para_birimi, taraf=taraf, now=now)
    return _d(obs.kur), int(obs.pk)


def convert(
    amount,
    *,
    kaynak_pb: str,
    hedef_pb: str,
    taraf: str,
    gozlem: DovizKuru | None = None,
    gozlem_hedef: DovizKuru | None = None,
    now=None,
) -> ConversionResult:
    """
    Tutarı kaynak_pb → hedef_pb dönüştür.

    `gozlem`: kaynak yabancı PB için sabit gözlem (TRY↔FX).
    `gozlem_hedef`: FX→FX’te hedef yabancı PB gözlemi; verilmezse resolve edilir
    (kaynak gözlemi hedefe sessizce uygulanmaz).
    """
    tutar = _d(amount)
    if tutar < 0:
        raise CurrencyConversionError("Dönüştürülecek tutar negatif olamaz.")

    kaynak = _normalize_pb(kaynak_pb)
    hedef = _normalize_pb(hedef_pb)
    taraf = _assert_taraf(taraf)

    if kaynak == hedef:
        return ConversionResult(
            tutar=tutar,
            tutar_yuvarlanmis=_q(tutar),
            kaynak_pb=kaynak,
            hedef_pb=hedef,
            efektif_carpan=Decimal("1"),
            gozlem_idler=(),
            taraf=taraf,
        )

    ids: list[int] = []

    # FX → TRY
    if hedef == TRY and kaynak != TRY:
        kur, gid = _try_per_unit(kaynak, taraf=taraf, gozlem=gozlem, now=now)
        ids.append(gid)
        out = tutar * kur
        return ConversionResult(
            tutar=out,
            tutar_yuvarlanmis=_q(out),
            kaynak_pb=kaynak,
            hedef_pb=hedef,
            efektif_carpan=kur,
            gozlem_idler=tuple(ids),
            taraf=taraf,
        )

    # TRY → FX
    if kaynak == TRY and hedef != TRY:
        # gozlem burada hedef PB’ye aittir
        kur, gid = _try_per_unit(hedef, taraf=taraf, gozlem=gozlem or gozlem_hedef, now=now)
        ids.append(gid)
        out = tutar / kur
        return ConversionResult(
            tutar=out,
            tutar_yuvarlanmis=_q(out),
            kaynak_pb=kaynak,
            hedef_pb=hedef,
            efektif_carpan=(Decimal("1") / kur),
            gozlem_idler=tuple(ids),
            taraf=taraf,
        )

    # FX → FX (TRY pivot)
    kur_k, gid_k = _try_per_unit(kaynak, taraf=taraf, gozlem=gozlem, now=now)
    kur_h, gid_h = _try_per_unit(hedef, taraf=taraf, gozlem=gozlem_hedef, now=now)
    ids.extend([gid_k, gid_h])
    try_tutar = tutar * kur_k
    out = try_tutar / kur_h
    return ConversionResult(
        tutar=out,
        tutar_yuvarlanmis=_q(out),
        kaynak_pb=kaynak,
        hedef_pb=hedef,
        efektif_carpan=(kur_k / kur_h),
        gozlem_idler=tuple(ids),
        taraf=taraf,
    )


def to_try(amount, *, kaynak_pb: str, taraf: str, gozlem: DovizKuru | None = None, now=None) -> ConversionResult:
    return convert(
        amount,
        kaynak_pb=kaynak_pb,
        hedef_pb=TRY,
        taraf=taraf,
        gozlem=gozlem,
        now=now,
    )
