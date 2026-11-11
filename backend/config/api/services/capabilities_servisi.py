"""ADR-0017 NX-5 — /me capabilities (UI keşif; güvenlik değil)."""

from __future__ import annotations

from firmalar.role_permissions import P
from firmalar.services.email_verify_servisi import is_email_verified
from firmalar.services.yetki_servisi import (
    can_manage_all_users,
    can_view_all_tenants,
    has_perm,
)


def present_firma_masked(firma) -> dict | None:
    if firma is None:
        return None
    return {
        "id": firma.pk,
        "ad": firma.ad,
        "alici_mi": bool(getattr(firma, "alici_mi", False)),
        "tedarikci_mi": bool(getattr(firma, "tedarikci_mi", False)),
        "platform_mu": bool(getattr(firma, "platform_mu", False)),
        "aktif": bool(getattr(firma, "aktif", True)),
    }


def capabilities_for(user) -> dict[str, bool]:
    """Menü/buton görünürlüğü için yetenek bayrakları; her uç yine RBAC yapar."""
    firma = getattr(user, "firma", None)
    buyer = bool(firma and getattr(firma, "alici_mi", False))
    supplier = bool(firma and getattr(firma, "tedarikci_mi", False))
    ops = can_view_all_tenants(user)

    return {
        "can_checkout": buyer or ops,
        "can_view_catalog": buyer or ops,
        "can_view_cart": buyer or ops,
        "can_view_orders": buyer or ops,
        "can_view_finance": buyer or ops,
        "can_view_credit": buyer or ops,
        "can_view_shipments": buyer or ops,
        "can_approve": has_perm(user, P["manage_approval"]),
        "can_manage_rfq": has_perm(user, P["manage_rfq"]) or buyer or ops,
        "can_manage_org": has_perm(user, P["manage_org"]),
        "can_lock_quote": has_perm(user, P["lock_quote"]) or buyer or ops,
        "can_manage_offers": supplier or has_perm(user, P["manage_own_teklif"]),
        "can_view_supplier_stock": supplier or ops,
        "can_view_ops": ops,
        "can_view_ops_finance": ops,
        "can_manage_qc": has_perm(user, P["manage_qc"]),
        "can_manage_shipment": has_perm(user, P["manage_shipment"]),
        "can_manage_return": has_perm(user, P["manage_return"]),
        "can_manage_users": can_manage_all_users(user)
        or has_perm(user, P["manage_users"]),
        "can_manage_addresses": can_manage_all_users(user)
        or has_perm(user, P["manage_users"]),
        "can_act_as": has_perm(user, P["act_as_user"]),
    }


def present_me(user, *, request=None) -> dict:
    firma = getattr(user, "firma", None)
    caps_user = user
    act_as_payload = {"active": False}
    if request is not None and getattr(request, "act_as_active", False):
        actor = getattr(request, "act_as_actor", None)
        caps_user = actor or user
        act_as_payload = {
            "active": True,
            "actor_id": getattr(actor, "pk", None),
            "actor_username": actor.get_username() if actor is not None else None,
            "target_id": user.pk,
            "target_username": user.get_username(),
        }
    return {
        "id": user.pk,
        "username": user.get_username(),
        "rol": getattr(user, "rol", "") or "",
        "email_verified": is_email_verified(user),
        "firma": present_firma_masked(firma),
        # Geriye uyum (B0 me alanı); yeni istemciler `firma` kullanır
        "firma_id": getattr(user, "firma_id", None),
        "capabilities": capabilities_for(caps_user),
        "act_as": act_as_payload,
    }
