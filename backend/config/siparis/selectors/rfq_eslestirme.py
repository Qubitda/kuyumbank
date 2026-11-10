"""F10-021 — Katalog aday arama + eşleştirme tenant scope."""

from __future__ import annotations

import re
from decimal import Decimal

from django.db.models import Q, QuerySet

from firmalar.services.yetki_servisi import can_view_all_tenants
from siparis.models import RFQEslestirme
from urunler.models import Varyant

_TOKEN_RE = re.compile(r"[^\wçğıöşüÇĞİÖŞÜ]+", re.UNICODE)


def tokenize_aciklama(text: str) -> list[str]:
    raw = (text or "").strip().lower()
    if not raw:
        return []
    parts = _TOKEN_RE.split(raw)
    return [p for p in parts if len(p) >= 2]


def scope_rfq_eslestirme_queryset(qs: QuerySet, user) -> QuerySet:
    """Platform tümü; alıcı yalnız kendi RFQ satırları; diğerleri boş."""
    if can_view_all_tenants(user):
        return qs
    firma_id = getattr(user, "firma_id", None)
    if not firma_id:
        return qs.none()
    return qs.filter(rfq_line__rfq__alici_firma_id=firma_id)


def catalog_aday_queryset(*, aciklama: str, limit: int = 20) -> list[tuple[Varyant, int]]:
    """Kural tabanlı katalog adayları (platform SKU/ad/kod; tedarikçi SKU skorlanmaz).

    Döner: [(varyant, skor), ...] skor azalan.
    """
    tokens = tokenize_aciklama(aciklama)
    qs = (
        Varyant.objects.filter(
            aktif=True,
            urun__onay_durumu="onayli",
            urun__yayin_durumu="aktif",
        )
        .select_related("urun")
        .order_by("pk")
    )

    # Daralt: token yoksa boş; aksi halde OR filtre
    if not tokens:
        return []

    q = Q()
    for tok in tokens[:12]:
        q |= Q(sku__icontains=tok)
        q |= Q(urun__ad__icontains=tok)
        q |= Q(urun__platform_kodu__icontains=tok)
        q |= Q(urun__kimlik_anahtari__icontains=tok)
        q |= Q(urun__aciklama__icontains=tok)
    candidates = list(qs.filter(q)[: max(limit * 5, 50)])

    scored: list[tuple[Varyant, int]] = []
    aciklama_l = (aciklama or "").strip().lower()
    for v in candidates:
        skor = _score_varyant(v, tokens=tokens, aciklama_l=aciklama_l)
        if skor > 0:
            scored.append((v, skor))
    scored.sort(key=lambda x: (-x[1], x[0].pk))
    return scored[:limit]


def _score_varyant(v: Varyant, *, tokens: list[str], aciklama_l: str) -> int:
    skor = 0
    sku = (v.sku or "").strip().lower()
    kod = (v.urun.platform_kodu or "").strip().lower()
    kimlik = (v.urun.kimlik_anahtari or "").strip().lower()
    ad = (v.urun.ad or "").strip().lower()
    uacik = (v.urun.aciklama or "").strip().lower()

    if sku and sku == aciklama_l:
        skor += 100
    if kod and kod == aciklama_l:
        skor += 90
    if kimlik and kimlik == aciklama_l:
        skor += 85

    for tok in tokens:
        if sku and tok == sku:
            skor += 40
        elif sku and tok in sku:
            skor += 20
        if kod and tok == kod:
            skor += 35
        elif kod and tok in kod:
            skor += 15
        if kimlik and tok == kimlik:
            skor += 30
        if tok in ad:
            skor += 10
        if tok in uacik:
            skor += 5

    # Gram ipucu: "14.5g" / "14,5 gram" — soft boost
    gram = v.gram
    if gram is not None and isinstance(gram, Decimal):
        g_s = format(gram.normalize(), "f")
        if g_s in aciklama_l or g_s.replace(".", ",") in aciklama_l:
            skor += 8

    return skor
