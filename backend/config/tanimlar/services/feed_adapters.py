"""ADR-0018 CP-2 — Binance anlık + TCMB EOD adaptörleri (Decimal; float yasak).

HTTP enjekte edilebilir; testlerde fake fetcher.
"""

from __future__ import annotations

import json
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable
from urllib.request import urlopen

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from tanimlar.fiyat_kaynagi import ARA_QUANT, TROY_OZ_GRAM
from tanimlar.models import KurTaraf, KurTipi, MetalKuru
from tanimlar.services import kur_servisi
from tanimlar.services.capraz_sanity import capraz_makas_kontrol

_Q = Decimal(ARA_QUANT)
_TROY = Decimal(TROY_OZ_GRAM)

Fetcher = Callable[[str], dict]


def _http_json(url: str) -> dict:
    with urlopen(url, timeout=15) as resp:  # noqa: S310 — kontrollü URL
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValidationError("Feed JSON nesne değil.")
    return data


def troy_oz_to_gram_try(*, oz_try: Decimal) -> Decimal:
    """1 troy oz TRY → 1 gram TRY (ara 1e-6); metal DB alanı 4 hane için ayrıca quantize."""
    oz = Decimal(str(oz_try))
    if oz <= 0:
        raise ValidationError("0 fiyat yok.")
    return (oz / _TROY).quantize(_Q, rounding=ROUND_HALF_UP)


def gram_try_metal_quantize(gram_try: Decimal) -> Decimal:
    """MetalKuru.saf_birim_fiyat decimal_places=4."""
    return Decimal(str(gram_try)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def parse_binance_xauusdt(payload: dict) -> Decimal:
    price = payload.get("price") or payload.get("lastPrice")
    if price is None:
        raise ValidationError("Binance payload'da price yok.")
    return Decimal(str(price))


def sync_binance_metal(
    *,
    metal,
    actor,
    xauusdt: Decimal | None = None,
    usdttry: Decimal | None = None,
    tcmb_usdtry: Decimal | None = None,
    fetcher: Fetcher | None = None,
    skip_capraz: bool = False,
) -> MetalKuru:
    """Canlı metal kuru yazar. Çapraz aşımda yazmaz (LKG korunur)."""
    kur_servisi._require_manage(
        actor, action="kur.feed.binance", entity_type="MetalKuru"
    )
    fetch = fetcher or _http_json
    if xauusdt is None:
        # XAUUSDT spot'ta yok; Binance USD-M futures (GoldXT ile aynı)
        payload = fetch(
            "https://fapi.binance.com/fapi/v1/ticker/price?symbol=XAUUSDT"
        )
        xauusdt = parse_binance_xauusdt(payload)
    if usdttry is None:
        # Basit: USDTTRY ticker (yoksa test inject)
        try:
            up = fetch("https://api.binance.com/api/v3/ticker/price?symbol=USDTTRY")
            usdttry = parse_binance_xauusdt(up)
        except Exception as exc:  # noqa: BLE001
            raise ValidationError(f"USDTTRY alınamadı: {exc}") from exc

    if not skip_capraz and tcmb_usdtry is not None:
        sanity = capraz_makas_kontrol(
            xauusdt=xauusdt, usdttry=usdttry, tcmb_usdtry=tcmb_usdtry
        )
        if not sanity.ok:
            raise ValidationError(sanity.neden or "Çapraz kur sanity red.")

    # XAUUSDT * USDTTRY = TRY / troy oz → gram
    oz_try = (Decimal(str(xauusdt)) * Decimal(str(usdttry))).quantize(
        _Q, rounding=ROUND_HALF_UP
    )
    gram_try = gram_try_metal_quantize(troy_oz_to_gram_try(oz_try=oz_try))
    saglayici = kur_servisi.aktif_saglayici()
    now = timezone.now()
    # Alış + satış gözlemleri
    last = None
    for kt in (KurTipi.SATIS, KurTipi.ALIS):
        last = kur_servisi.feed_metal_kuru_kaydet(
            saglayici=saglayici,
            metal=metal,
            saf_birim_fiyat=gram_try,
            kur_tipi=kt,
            zaman=now,
            alinma_zamani=now,
            kaynak="api",
        )
    kur_servisi.set_feed_health(health="FEED_OK", banner="")
    # CAP-ALERT: taze feed sonrası eşik tara (checkout’a bağlanmaz)
    from tanimlar.services import kur_alert_servisi

    kur_alert_servisi.degerlendir(metal=metal)
    return last


def sync_tcmb_doviz(
    *,
    actor,
    para_birimi: str = "USD",
    kur: Decimal | None = None,
    zaman=None,
) -> object:
    """TCMB EOD döviz gözlemi (`kaynak=tcmb`)."""
    from tanimlar.models import DovizKuru

    kur_servisi._require_manage(
        actor, action="kur.feed.tcmb", entity_type="DovizKuru"
    )
    if kur is None or Decimal(str(kur)) <= 0:
        raise ValidationError("TCMB kur pozitif zorunlu (0 yok).")
    saglayici = kur_servisi.aktif_saglayici()
    now = timezone.now()
    zaman = zaman or now
    if isinstance(zaman, str):
        zaman = parse_datetime(zaman) or now
    tip = kur_servisi.tarafa_kur_tipi(KurTaraf.ALICI)
    obj = DovizKuru(
        para_birimi=para_birimi,
        saglayici=saglayici,
        kur_tipi=tip,
        zaman=zaman,
        alinma_zamani=now,
        kur=Decimal(str(kur)),
        kaynak="tcmb",
    )
    obj.full_clean()
    obj.save()
    return obj
