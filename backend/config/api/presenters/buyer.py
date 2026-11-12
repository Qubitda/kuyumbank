"""Buyer* sunum — kör havuz; Decimal string; allowed_actions; server_now."""

from __future__ import annotations

from django.utils import timezone

from api.masking import assert_masked
from fiyatlama.models import PriceLock, PriceQuote
from fiyatlama.selectors.buyer_quote import present_buyer_quote
from siparis.models import Order
from siparis.services.cart_servisi import present_cart_line as _raw_cart_line
from siparis.services.presenters import present_order as _raw_order


def _dt(value) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _dec(value) -> str | None:
    if value is None:
        return None
    return str(value)


def BuyerCartLinePresenter(line) -> dict:
    raw = _raw_cart_line(line)
    data = {
        "id": raw["id"],
        "quote_id": raw["quote_id"],
        "varyant_id": raw["varyant_id"],
        "miktar": _dec(raw["miktar"]),
        "birim": raw["birim"],
        "para_birimi": raw["para_birimi"],
        "birim_fiyat_vergisiz": _dec(raw["birim_fiyat_vergisiz"]),
        "gecerlilik_sonu": _dt(raw["gecerlilik_sonu"]),
    }
    assert_masked(data)
    return data


def BuyerCartPresenter(cart, *, include_lines: bool = True) -> dict:
    now = timezone.now()
    data = {
        "id": cart.pk,
        "alici_firma_id": cart.alici_firma_id,
        "sube_id": getattr(cart, "sube_id", None),
        "line_count": cart.lines.count(),
        "server_now": now.isoformat(),
        "allowed_actions": ["add_line", "update_line", "remove_line", "checkout"],
    }
    if include_lines:
        data["lines"] = [
            BuyerCartLinePresenter(ln)
            for ln in cart.lines.select_related("price_quote").order_by("pk")
        ]
    assert_masked(data)
    return data


def BuyerQuotePresenter(quote: PriceQuote, *, now=None) -> dict:
    now = now or timezone.now()
    raw = present_buyer_quote(quote, now=now)
    gecerli = raw["durum"] == "gecerli"
    net_raw = raw.get("net_ozet") or {}
    net_ozet = {
        "toplam_vergisiz": _dec(net_raw.get("toplam_vergisiz")),
        "gram": _dec(net_raw.get("gram")),
        "gram_basi_vergisiz": _dec(net_raw.get("gram_basi_vergisiz")),
        "iscilik_vergisiz": _dec(net_raw.get("iscilik_vergisiz")),
        "has_gram": _dec(net_raw.get("has_gram")),
    }
    data = {
        "id": raw["id"],
        "belge_turu": raw["belge_turu"],
        "durum": raw["durum"],
        "urun": raw["urun"],
        "varyant_id": quote.varyant_id,
        "varyant_sku": raw["varyant_sku"],
        "satis_kanali_kod": raw["satis_kanali_kod"],
        "toplam_vergisiz": _dec(raw["toplam_vergisiz"]),
        "para_birimi": raw["para_birimi"],
        "gram": _dec(raw["gram"]),
        "gram_basi_vergisiz": _dec(raw["gram_basi_vergisiz"]),
        "iscilik_vergisiz": _dec(raw.get("iscilik_vergisiz")),
        "has_gram": _dec(raw.get("has_gram")),
        "net_ozet": net_ozet,
        "expires_at": _dt(raw["gecerlilik_sonu"]),
        "hesap_zamani": _dt(raw["hesap_zamani"]),
        "server_now": now.isoformat(),
        "allowed_actions": (["lock", "add_to_cart"] if gecerli else []),
        "satirlar": None,
    }
    assert_masked(data)
    return data


def BuyerPriceLockPresenter(lock: PriceLock, *, now=None) -> dict:
    now = now or timezone.now()
    from fiyatlama.services.pricing_service import is_lock_gecerli

    gecerli = is_lock_gecerli(lock, now=now)
    lock.refresh_from_db()
    data = {
        "id": lock.pk,
        "quote_id": lock.quote_id,
        "durum": lock.durum,
        "toplam_vergisiz": _dec(lock.toplam_vergisiz),
        "para_birimi": lock.para_birimi,
        "kilit_zamani": _dt(lock.kilit_zamani),
        "expires_at": _dt(lock.gecerlilik_sonu),
        "server_now": now.isoformat(),
        "gecerli": gecerli,
        "allowed_actions": (["checkout"] if gecerli else []),
    }
    assert_masked(data)
    return data


def BuyerOrderPresenter(order: Order, *, include_lines: bool = True) -> dict:
    data = _raw_order(order, include_lines=include_lines)
    actions: list[str] = ["reorder"]
    if order.durum == Order.Durum.OLUSTURULDU:
        actions.insert(0, "cancel")
    data["allowed_actions"] = actions
    data["server_now"] = timezone.now().isoformat()
    assert_masked(data)
    return data


def BuyerCatalogItemPresenter(urun) -> dict:
    """Liste satırı — `buyer_katalog_servisi.liste` alanlarıyla hizalı (+ allowed_actions)."""
    varyant_count = getattr(urun, "varyant_count", None)
    if varyant_count is None:
        varyant_count = urun.varyantlar.filter(aktif=True).count()
    data = {
        "id": urun.pk,
        "ad": urun.ad,
        "platform_kodu": urun.platform_kodu or "",
        "kategori": getattr(getattr(urun, "kategori", None), "ad", "") or "",
        "ayar": getattr(getattr(urun, "ayar", None), "ayar_kodu", "") or "",
        "fiyat_tipi": urun.fiyat_tipi,
        "yayin_durumu": urun.yayin_durumu,
        "varyant_count": int(varyant_count),
        "allowed_actions": ["quote"],
    }
    assert_masked(data)
    return data


def BuyerCatalogDetailPresenter(urun_id: int) -> dict:
    """Detay — domain `buyer_katalog_servisi.detay` (varyantlar; kör)."""
    from urunler.services.buyer_katalog_servisi import (
        BuyerCatalogNotFound,
        detay,
    )

    try:
        data = detay(urun_id=urun_id)
    except BuyerCatalogNotFound as exc:
        raise LookupError("Ürün bulunamadı.") from exc
    data["allowed_actions"] = ["quote"]
    assert_masked(data)
    return data
