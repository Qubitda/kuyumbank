"""API yetki — ADR-0003 tenant + ADR-0019 object-level (OL-1…11 Kabul).

Client firma_id güvenilmez. Çapraz tenant → selector 404. Yeni perm kodu yok (OL-10).
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS

from firmalar import roles
from firmalar.services.email_verify_servisi import (
    email_verify_required_for_write,
    is_email_verified,
)
from firmalar.services.yetki_servisi import can_view_all_tenants
from fiyatlama.selectors.buyer_quote import BuyerQuoteNotFound, get_quote_for_actor
from siparis.selectors.tenant import (
    CartNotFound,
    OrderNotFound,
    can_ops_read_orders,
    get_cart_for_actor,
    get_order_for_actor,
)

# OL-3/OL-4 matrisi: commerce W yalnız yönetici + satınalmacı
BUYER_COMMERCE_WRITE_ROLES = frozenset(
    {
        roles.ALICI_YONETICI,
        roles.ALICI_SATINALMACI,
    }
)

# GET serbest (alıcı firma); W yasak — onay / denetçi / alıcı finans
BUYER_COMMERCE_WRITE_DENIED_ROLES = frozenset(
    {
        roles.ALICI_ONAYLAYICI,
        roles.ALICI_DENETCI,
        roles.ALICI_FINANS,
    }
)


def _rol(user) -> str:
    return (getattr(user, "rol", None) or "").strip()


def is_platform_support(user) -> bool:
    return _rol(user) == roles.PLATFORM_SUPPORT


def is_buyer_firma(user) -> bool:
    firma = getattr(user, "firma", None)
    return bool(firma is not None and getattr(firma, "alici_mi", False))


def can_buyer_commerce_read(user) -> bool:
    """Order/cart/quote GET — alıcı firma veya ops okuma; SUPPORT yok (OL-5)."""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if is_platform_support(user):
        return False
    if can_ops_read_orders(user) or can_view_all_tenants(user):
        return True
    return is_buyer_firma(user)


def can_buyer_commerce_write(user) -> bool:
    """Quote/lock/cart/checkout/order yazma — SoD (OL-3/OL-4); ops yazamaz."""
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if can_view_all_tenants(user):
        return False
    if not is_buyer_firma(user):
        return False
    rol = _rol(user)
    if rol in BUYER_COMMERCE_WRITE_DENIED_ROLES:
        return False
    return rol in BUYER_COMMERCE_WRITE_ROLES


class IsAuthenticatedWithFirma(BasePermission):
    """Oturum + tek firma bağlamı zorunlu."""

    message = "Kimlik ve firma bağlamı gerekli."

    def has_permission(self, request, view):
        user = request.user
        if user is None or not user.is_authenticated:
            return False
        return bool(getattr(user, "firma_id", None))


class IsBuyerCommerceRead(BasePermission):
    """Buyer commerce GET yüzeyi (liste/detay gate)."""

    message = "Okuma yalnız alıcı veya QC/lojistik/platform ops."

    def has_permission(self, request, view):
        if not IsAuthenticatedWithFirma().has_permission(request, view):
            return False
        return can_buyer_commerce_read(request.user)


class IsBuyerCommerceWrite(BasePermission):
    """Buyer commerce yazma — satınalmacı/yönetici; denetçi/onaycı/finans ve ops yok."""

    message = "Yazma yalnız alıcı satınalmacı/yönetici."

    def has_permission(self, request, view):
        if not IsAuthenticatedWithFirma().has_permission(request, view):
            return False
        if request.method in SAFE_METHODS:
            return can_buyer_commerce_read(request.user)
        if not can_buyer_commerce_write(request.user):
            return False
        # ADR-0028 IE-3: varsayılan kapalı; açılınca yazma için e-posta doğrulama
        if email_verify_required_for_write() and not is_email_verified(request.user):
            self.message = "E-posta doğrulaması gerekli."
            return False
        return True


class HasOrderObjectAccess(BasePermission):
    """Nesne: get_order_for_actor; kapsam dışı → has_object False (view 404)."""

    message = "Sipariş erişimi yok."

    def has_permission(self, request, view):
        return IsBuyerCommerceRead().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        try:
            get_order_for_actor(request.user, order_id=obj.pk)
            return True
        except OrderNotFound:
            return False


class HasCartObjectAccess(BasePermission):
    message = "Sepet erişimi yok."

    def has_permission(self, request, view):
        return IsBuyerCommerceRead().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        try:
            get_cart_for_actor(request.user, cart_id=obj.pk)
            return True
        except CartNotFound:
            return False


class HasQuoteObjectAccess(BasePermission):
    message = "Quote erişimi yok."

    def has_permission(self, request, view):
        return IsBuyerCommerceRead().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        try:
            get_quote_for_actor(request.user, quote_id=obj.pk)
            return True
        except BuyerQuoteNotFound:
            return False
