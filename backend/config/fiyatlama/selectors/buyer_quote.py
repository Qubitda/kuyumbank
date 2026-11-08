"""Alıcıya dönük PriceQuote sunum katmanı (ADR-0008 B-02 / Dilim 3.6).

Varsayılan: yalnız toplam_vergisiz (+ isteğe bağlı gram başı), PB, geçerlilik, durum.
Kırılım / tedarikçi kimliği / maliyet / teklif id → asla.
Object-level erişim: kapsam dışı → DoesNotExist (404 semantiği; varlık sızdırılmaz).
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.utils import timezone

from firmalar.services.yetki_servisi import can_view_all_tenants
from fiyatlama.models import PriceQuote
from fiyatlama.selectors.tenant import (
    scope_price_quote_queryset,
    user_may_see_fiyat_maliyet,
)

_HASSASIYET = Decimal("0.01")


class BuyerQuoteNotFound(ObjectDoesNotExist):
    """Alıcıya 404 eşdeğeri — quote yok veya kapsam dışı."""


def _is_buyer_firma(user) -> bool:
    firma = getattr(user, "firma", None)
    return bool(firma is not None and getattr(firma, "alici_mi", False))


def get_quote_for_actor(user, quote_id: int) -> PriceQuote:
    """
    Tenant + rol süzgeçli quote getir.

    - Platform (view_all): tüm quote'lar
    - Alıcı: yalnız kendi firmasının quote'ları
    - Tedarikçi / diğer: DoesNotExist (kör havuz — varlık sızdırılmaz)
    """
    if user is None or not getattr(user, "is_authenticated", False):
        raise BuyerQuoteNotFound("Quote bulunamadı.")

    qs = scope_price_quote_queryset(
        PriceQuote.objects.select_related(
            "varyant",
            "varyant__urun",
            "satis_kanali",
            "alici_firma",
        ),
        user,
    )
    try:
        return qs.get(pk=quote_id)
    except PriceQuote.DoesNotExist as exc:
        raise BuyerQuoteNotFound("Quote bulunamadı.") from exc


def present_buyer_quote(quote: PriceQuote, *, now=None) -> dict:
    """
    B-02 A: alıcı yüzeyi DTO. Satır kırılımı yok.
    Tedarikçi / teklif / maliyet / kur gözlem / hesap_girdisi yok.
    """
    now = now or timezone.now()
    gecerli = quote.gecerlilik_sonu >= now
    gram = quote.gram
    gram_basi = None
    if gram is not None and gram > 0:
        gram_basi = (quote.toplam_vergisiz / gram).quantize(
            _HASSASIYET, rounding=ROUND_HALF_UP
        )

    urun = quote.varyant.urun
    return {
        "id": quote.pk,
        "belge_turu": quote.belge_turu,
        "durum": "gecerli" if gecerli else "suresi_dolmus",
        "urun": {
            "platform_kodu": urun.platform_kodu,
            "ad": urun.ad,
        },
        "varyant_sku": quote.varyant.sku,
        "satis_kanali_kod": quote.satis_kanali.kod,
        "toplam_vergisiz": quote.toplam_vergisiz,
        "para_birimi": quote.para_birimi,
        "gram": gram,
        "gram_basi_vergisiz": gram_basi,
        "gecerlilik_sonu": quote.gecerlilik_sonu,
        "hesap_zamani": quote.hesap_zamani,
        # Bilinçli yok: teklif, tedarikçi, satırlar, maliyet, kur, hesap_girdisi
        "satirlar": None,
    }


def get_buyer_quote_view(user, quote_id: int, *, now=None) -> dict:
    """Alıcı (veya platform denetim) için güvenli quote görünümü."""
    quote = get_quote_for_actor(user, quote_id)

    # Tedarikçi zaten qs.none(); ekstra savunma
    firma = getattr(user, "firma", None)
    if firma is not None and getattr(firma, "tedarikci_mi", False):
        if not can_view_all_tenants(user):
            raise BuyerQuoteNotFound("Quote bulunamadı.")

    # Alıcı kendi firması dışında (platform değilse) — selector zaten keser
    if _is_buyer_firma(user) and not can_view_all_tenants(user):
        if quote.alici_firma_id != user.firma_id:
            raise BuyerQuoteNotFound("Quote bulunamadı.")

    return present_buyer_quote(quote, now=now)


def assert_buyer_cannot_see_internal(payload: dict) -> None:
    """Test yardımcısı — yasaklı anahtarlar."""
    yasak = {
        "teklif",
        "teklif_id",
        "tedarikci",
        "tedarikci_id",
        "birim_fiyat",
        "iscilik",
        "kanal_marj",
        "hesap_girdisi",
        "metal_kuru",
        "alici_kalem",
        "tedarikci_kalem",
        "platform_servis",
        "vergi",
    }
    flat = set(payload.keys())
    leak = flat & yasak
    if leak:
        raise AssertionError(f"Alıcı payload sızıntı: {leak}")


def require_platform_maliyet_for_lines(user) -> None:
    """Satır kırılımı yalnız platform maliyet yetkisi (B-02 hukuk öncesi kapalı)."""
    if not (can_view_all_tenants(user) and user_may_see_fiyat_maliyet(user)):
        raise PermissionDenied("Quote satır kırılımı bu rol için kapalı.")
