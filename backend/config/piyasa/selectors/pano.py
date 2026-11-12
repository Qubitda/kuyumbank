"""Alıcı/portal piyasa panosu DTO (GAP-F3-01).

Marj / maliyet / saf kur gözlemi / detay kırılımı sızdırılmaz.
`fiyat` = pano satış (SATIS) nihai tutar — board görüntü fiyatı.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.utils import timezone

from piyasa.models import PiyasaUrun
from piyasa.services import piyasa_fiyat_servisi
from tanimlar.fiyat_kaynagi import FeedHealth

_OLCEK_FILTRE = frozenset(
    {
        PiyasaUrun.Olcek.ONS,
        PiyasaUrun.Olcek.KG,
        PiyasaUrun.Olcek.GRAM,
    }
)

_KAYNAK_MAP = {
    FeedHealth.FEED_OK: "CANLI",
    FeedHealth.FEED_STALE_LKG: "LKG",
    FeedHealth.FEED_LOCKED_MANUEL: "MANUEL",
    FeedHealth.FEED_FAIL: "FAIL",
}


def _dec(value) -> str | None:
    if value is None:
        return None
    return str(Decimal(str(value)))


def _dt(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _kaynak(feed_health: str | None) -> str:
    if not feed_health:
        return "LKG"
    return _KAYNAK_MAP.get(str(feed_health), "LKG")


def present_buyer_pano(
    *,
    olcek: str | None = None,
    now=None,
) -> dict[str, Any]:
    """
    GET /api/v1/piyasa/pano/ gövdesi.

    Query `olcek`: ONS | KG | GRAM (opsiyonel). Geçersiz → ValidationError.
    """
    now = now or timezone.now()
    olcek_norm = (olcek or "").strip().upper() or None
    if olcek_norm is not None and olcek_norm not in _OLCEK_FILTRE:
        raise ValidationError(
            {"olcek": f"Geçersiz olcek: {olcek!r} (ONS|KG|GRAM)."}
        )

    rows = piyasa_fiyat_servisi.pano_ozeti(only_aktif=True, now=now)
    satirlar: list[dict[str, Any]] = []
    for row in rows:
        if olcek_norm is not None and row.get("olcek") != olcek_norm:
            continue
        if not row.get("ok"):
            continue
        fiyat = row.get("satis")
        if fiyat is None:
            continue
        satirlar.append(
            {
                "kod": row["kod"],
                "ad": row.get("ad") or row["kod"],
                "fiyat": _dec(fiyat),
                "para_birimi": row.get("cikti_pb") or "TRY",
                "olcek": row.get("olcek") or PiyasaUrun.Olcek.GRAM,
                "kaynak": _kaynak(row.get("feed_health")),
                "guncelleme": _dt(row.get("guncelleme") or now),
                "banner": (row.get("banner") or None) or None,
            }
        )

    return {
        "server_now": now.isoformat(),
        "olcek": olcek_norm,
        "satirlar": satirlar,
    }
