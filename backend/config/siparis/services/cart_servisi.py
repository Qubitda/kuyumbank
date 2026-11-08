"""Cart yazım servisi — F4-030/031. Stok düşürmez; PriceLock yok (checkout)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from firmalar.services.audit_servisi import domain_atomic, record_audit
from firmalar.services.yetki_servisi import can_view_all_tenants, is_platform_firm_user
from fiyatlama.models import PriceQuote
from siparis.models import Cart, CartLine
from siparis.selectors.tenant import CartNotFound, get_cart_for_actor
from stok.services.birim import birim_from_teklif


def _assert_buyer_actor(actor, alici_firma) -> None:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Sepet için kimlik gerekli.")
    firma = getattr(actor, "firma", None)
    firma_id = getattr(actor, "firma_id", None)
    if firma is None or not firma_id:
        raise PermissionDenied("Sepet için firma bağlamı gerekli.")
    if not getattr(firma, "alici_mi", False):
        raise PermissionDenied("Sepet yalnız alıcı firma kullanıcıları içindir.")
    if firma_id != getattr(alici_firma, "pk", None):
        raise PermissionDenied("Sepet firması aktör firması ile eşleşmeli.")
    if not getattr(firma, "aktif", True):
        raise PermissionDenied("Pasif firma sepet kullanamaz.")


def _get_or_create_cart_locked(*, actor, alici_firma) -> tuple[Cart, bool]:
    cart, created = Cart.objects.select_for_update().get_or_create(
        alici_firma=alici_firma,
        defaults={"olusturan": actor},
    )
    return cart, created


def al_veya_olustur_sepet(*, actor, alici_firma=None) -> Cart:
    """Alıcı firmasının tek sepetini getirir veya oluşturur."""
    if alici_firma is None:
        alici_firma = getattr(actor, "firma", None)
    _assert_buyer_actor(actor, alici_firma)

    with domain_atomic():
        cart, created = _get_or_create_cart_locked(
            actor=actor, alici_firma=alici_firma
        )
        if created:
            record_audit(
                actor=actor,
                action="cart.create",
                entity_type="Cart",
                entity_id=str(cart.pk),
                success=True,
                detail={"alici_firma_id": alici_firma.pk},
            )
        return cart


def _require_own_cart(actor, cart: Cart) -> Cart:
    if can_view_all_tenants(actor) and is_platform_firm_user(actor):
        return cart
    try:
        return get_cart_for_actor(actor, cart_id=cart.pk)
    except CartNotFound as exc:
        raise CartNotFound("Sepet bulunamadı.") from exc


def _assert_quote_usable(quote: PriceQuote, *, alici_firma, now) -> None:
    if quote.alici_firma_id != alici_firma.pk:
        raise ValidationError("Quote bu alıcı firmaya ait değil.")
    if now >= quote.gecerlilik_sonu:
        raise ValidationError("PriceQuote süresi dolmuş; sepete eklenemez.")
    varyant = quote.varyant
    if not varyant.aktif:
        raise ValidationError("Varyant pasif; sepete eklenemez.")
    urun = varyant.urun
    if urun.onay_durumu != "onayli" or urun.yayin_durumu != "aktif":
        raise ValidationError("Ürün yayınlı/onaylı değil; sepete eklenemez.")


def satir_ekle(
    *, actor, price_quote: PriceQuote, miktar: Decimal, now=None
) -> CartLine:
    """Sepete satır ekler veya aynı varyant satırını günceller. Stok dokunulmaz."""
    miktar = Decimal(miktar)
    if miktar <= 0:
        raise ValidationError("Miktar pozitif olmalı.")

    alici_firma = getattr(actor, "firma", None)
    _assert_buyer_actor(actor, alici_firma)
    now = now or timezone.now()
    _assert_quote_usable(price_quote, alici_firma=alici_firma, now=now)

    birim = birim_from_teklif(price_quote.teklif)

    with domain_atomic():
        cart, created = _get_or_create_cart_locked(
            actor=actor, alici_firma=alici_firma
        )
        if created:
            record_audit(
                actor=actor,
                action="cart.create",
                entity_type="Cart",
                entity_id=str(cart.pk),
                success=True,
                detail={"alici_firma_id": alici_firma.pk},
            )

        existing = (
            CartLine.objects.select_for_update()
            .filter(cart=cart, varyant_id=price_quote.varyant_id)
            .first()
        )
        if existing is not None:
            existing.price_quote = price_quote
            existing.miktar = miktar
            existing.birim = birim
            existing.save()
            line = existing
            action = "cart.line.update"
        else:
            line = CartLine(
                cart=cart,
                price_quote=price_quote,
                varyant_id=price_quote.varyant_id,
                miktar=miktar,
                birim=birim,
            )
            line.save()
            action = "cart.line.add"

        cart.save(update_fields=["guncelleme_tarihi"])
        record_audit(
            actor=actor,
            action=action,
            entity_type="CartLine",
            entity_id=str(line.pk),
            success=True,
            detail={
                "cart_id": cart.pk,
                "quote_id": price_quote.pk,
                "varyant_id": price_quote.varyant_id,
                "miktar": str(miktar),
                "birim": birim,
            },
        )
        return line


def satir_guncelle_miktar(*, actor, line: CartLine, miktar: Decimal) -> CartLine:
    miktar = Decimal(miktar)
    if miktar <= 0:
        raise ValidationError("Miktar pozitif olmalı.")
    _require_own_cart(actor, line.cart)
    now = timezone.now()
    _assert_quote_usable(
        line.price_quote, alici_firma=line.cart.alici_firma, now=now
    )

    with domain_atomic():
        locked = CartLine.objects.select_for_update().get(pk=line.pk)
        locked.miktar = miktar
        locked.save(update_fields=["miktar", "guncelleme_tarihi"])
        locked.cart.save(update_fields=["guncelleme_tarihi"])
        record_audit(
            actor=actor,
            action="cart.line.update",
            entity_type="CartLine",
            entity_id=str(locked.pk),
            success=True,
            detail={"miktar": str(miktar)},
        )
        return locked


def satir_sil(*, actor, line: CartLine) -> None:
    _require_own_cart(actor, line.cart)
    with domain_atomic():
        pk = line.pk
        cart = line.cart
        CartLine.objects.filter(pk=pk).delete()
        cart.save(update_fields=["guncelleme_tarihi"])
        record_audit(
            actor=actor,
            action="cart.line.remove",
            entity_type="CartLine",
            entity_id=str(pk),
            success=True,
            detail={"cart_id": cart.pk},
        )


def present_cart_line(line: CartLine) -> dict:
    """Alıcı yüzeyi — tedarikçi/maliyet/teklif yok (B-02)."""
    q = line.price_quote
    return {
        "id": line.pk,
        "quote_id": q.pk,
        "varyant_id": line.varyant_id,
        "miktar": line.miktar,
        "birim": line.birim,
        "para_birimi": q.para_birimi,
        "birim_fiyat_vergisiz": q.toplam_vergisiz,
        "gecerlilik_sonu": q.gecerlilik_sonu,
    }
