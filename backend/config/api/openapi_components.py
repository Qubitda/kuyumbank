"""OpenAPI bileşen şemaları — presenter alanlarıyla hizalı (stub yasak).

Kaynak: `api.presenters.*` + `capabilities_servisi` + pagination zarfı.
`scripts/export_openapi.py` / drf-spectacular postprocess bu modülü kullanır.
"""

from __future__ import annotations

from typing import Any


def _str(**extra: Any) -> dict:
    return {"type": "string", **extra}


def _int(**extra: Any) -> dict:
    return {"type": "integer", **extra}


def _bool(**extra: Any) -> dict:
    return {"type": "boolean", **extra}


def _null_str() -> dict:
    return {"oneOf": [{"type": "string"}, {"type": "null"}]}


def _null_int() -> dict:
    return {"oneOf": [{"type": "integer"}, {"type": "null"}]}


def _actions() -> dict:
    return {"type": "array", "items": {"type": "string"}}


def _obj(properties: dict, required: list[str] | None = None) -> dict:
    out: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        out["required"] = required
    return out


PROBLEM_DETAIL = _obj(
    {
        "type": _str(),
        "title": _str(),
        "status": _int(),
        "detail": _str(),
        "code": _str(),
        "request_id": _str(),
        "errors": {"type": "object", "additionalProperties": True},
    },
    ["status"],
)

FIRMA_MASKED = _obj(
    {
        "id": _int(),
        "ad": _str(),
        "alici_mi": _bool(),
        "tedarikci_mi": _bool(),
        "platform_mu": _bool(),
        "aktif": _bool(),
    },
    ["id", "ad", "alici_mi", "tedarikci_mi", "platform_mu", "aktif"],
)

CAPABILITIES = {
    "type": "object",
    "additionalProperties": {"type": "boolean"},
    "properties": {
        k: _bool()
        for k in (
            "can_checkout",
            "can_view_catalog",
            "can_view_cart",
            "can_view_orders",
            "can_view_finance",
            "can_view_credit",
            "can_view_shipments",
            "can_approve",
            "can_manage_rfq",
            "can_manage_org",
            "can_lock_quote",
            "can_manage_offers",
            "can_view_supplier_stock",
            "can_view_ops",
            "can_view_ops_finance",
            "can_manage_qc",
            "can_manage_shipment",
            "can_manage_return",
            "can_manage_users",
            "can_manage_addresses",
            "can_act_as",
        )
    },
}

ACT_AS_STATE = _obj(
    {
        "active": _bool(),
        "actor_id": _null_int(),
        "actor_username": _null_str(),
        "target_id": _null_int(),
        "target_username": _null_str(),
    },
    ["active"],
)

ME_RESPONSE = _obj(
    {
        "id": _int(),
        "username": _str(),
        "rol": _str(),
        "email_verified": _bool(),
        "firma": {"oneOf": [FIRMA_MASKED, {"type": "null"}]},
        "firma_id": _null_int(),
        "capabilities": CAPABILITIES,
        "act_as": ACT_AS_STATE,
    },
    [
        "id",
        "username",
        "rol",
        "email_verified",
        "firma",
        "firma_id",
        "capabilities",
        "act_as",
    ],
)

HEALTH = _obj(
    {"status": _str(), "service": _str(), "api": _str()},
    ["status"],
)
READY = _obj(
    {
        "status": _str(),
        "service": _str(),
        "api": _str(),
        "checks": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
    },
    ["status", "checks"],
)
CSRF = _obj({"csrf_token": _str()}, ["csrf_token"])
LOGOUT_OK = _obj({"ok": _bool()}, ["ok"])

INVITE_ITEM = _obj(
    {
        "id": _int(),
        "email": _str(),
        "rol": _str(),
        "firma_id": _int(),
        "expires_at": _str(),
        "expired": _bool(),
    }
)
INVITE_LIST = _obj({"results": {"type": "array", "items": INVITE_ITEM}}, ["results"])
INVITE_CREATED = _obj(
    {
        "id": _int(),
        "email": _str(),
        "rol": _str(),
        "firma_id": _int(),
        "expires_at": _str(),
    },
    ["id", "email", "rol", "firma_id", "expires_at"],
)
INVITE_ACCEPTED = _obj(
    {"detail": _str(), "username": _str()},
    ["detail", "username"],
)
EMAIL_VERIFY_REQUEST_OK = _obj({"detail": _str()}, ["detail"])
EMAIL_VERIFY_CONFIRM_OK = _obj(
    {"detail": _str(), "username": _str(), "email_verified": _bool()},
    ["detail", "username", "email_verified"],
)
DETAIL_OK = _obj({"detail": _str()}, ["detail"])
MFA_VERIFY_OK = _obj(
    {
        "mfa_ok": _bool(),
        "detail": _str(description="MFA gerekli değilken"),
    },
    ["mfa_ok"],
)
ME_PROFILE = _obj(
    {
        "id": _int(),
        "username": _str(),
        "email": _str(),
        "first_name": _str(),
        "last_name": _str(),
        "rol": _str(),
        "email_verified": _bool(),
        "firma": {"oneOf": [FIRMA_MASKED, {"type": "null"}]},
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "username", "email", "first_name", "last_name", "rol", "email_verified"],
)
FIRMA_ADRESI = _obj(
    {
        "id": _int(),
        "tip": _str(),
        "il": _str(),
        "ilce": _str(),
        "adres": _str(),
        "varsayilan": _bool(),
        "firma_id": _int(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "tip", "il", "adres", "varsayilan", "firma_id"],
)
ME_DASHBOARD = _obj(
    {
        "username": _str(),
        "rol": _str(),
        "firma_id": _null_int(),
        "firma_ad": _str(),
        "firma_kodu": _str(),
        "cart_id": _int(),
        "cart_line_count": _int(),
        "order_count": _int(),
        "rfq_count": _int(),
        "rfq_ozel_count": _int(),
    }
)
ACT_AS_START_OK = _obj(
    {
        "act_as": _bool(),
        "target_id": _int(),
        "target_username": _str(),
        "redirect_url": _str(),
    },
    ["act_as", "target_id", "target_username", "redirect_url"],
)
ACT_AS_STOP_OK = _obj(
    {
        "act_as": _bool(),
        "actor_id": _null_int(),
        "redirect_url": _str(),
    },
    ["act_as", "redirect_url"],
)

OPS_PRODUCT_VARIANT = _obj(
    {
        "id": _int(),
        "sku": _str(),
        "gram": _null_str(),
        "renk_id": _null_int(),
        "beden_id": _null_int(),
        "ek_bedel": _str(),
        "aktif": _bool(),
    },
    ["id", "sku", "aktif"],
)
OPS_PRODUCT = _obj(
    {
        "id": _int(),
        "ad": _str(),
        "platform_kodu": _str(),
        "aciklama": _str(),
        "kategori_id": _int(),
        "kategori": _str(),
        "ayar_id": _int(),
        "ayar": _str(),
        "fiyat_tipi": _str(),
        "onay_durumu": _str(),
        "yayin_durumu": _str(),
        "red_nedeni": _str(),
        "olusturan_firma_id": _int(),
        "varyant_count": _int(),
        "varyantlar": {"type": "array", "items": OPS_PRODUCT_VARIANT},
        "allowed_actions": _actions(),
    },
    [
        "id",
        "ad",
        "platform_kodu",
        "kategori_id",
        "ayar_id",
        "onay_durumu",
        "yayin_durumu",
        "olusturan_firma_id",
        "varyant_count",
    ],
)

BUYER_CATALOG_VARIANT = _obj(
    {
        "id": _int(),
        "sku": _str(),
        "gram": _null_str(),
        "renk": _str(),
        "beden": _str(),
    }
)
BUYER_CATALOG_ITEM = _obj(
    {
        "id": _int(),
        "ad": _str(),
        "platform_kodu": _str(),
        "kategori": _str(),
        "ayar": _str(),
        "fiyat_tipi": _str(),
        "yayin_durumu": _str(),
        "varyant_count": _int(),
        "allowed_actions": _actions(),
    },
    ["id", "ad", "allowed_actions"],
)
BUYER_CATALOG_DETAIL = _obj(
    {
        "id": _int(),
        "ad": _str(),
        "platform_kodu": _str(),
        "aciklama": _str(),
        "kategori": _str(),
        "ayar": _str(),
        "fiyat_tipi": _str(),
        "varyantlar": {"type": "array", "items": BUYER_CATALOG_VARIANT},
        "allowed_actions": _actions(),
    },
    ["id", "ad", "varyantlar", "allowed_actions"],
)

BUYER_QUOTE_NET_OZET = _obj(
    {
        "toplam_vergisiz": _null_str(),
        "gram": _null_str(),
        "gram_basi_vergisiz": _null_str(),
        "iscilik_vergisiz": _null_str(),
        "has_gram": _null_str(),
    }
)
PIYASA_PANO_SATIR = _obj(
    {
        "kod": _str(),
        "ad": _str(),
        "fiyat": _str(),
        "para_birimi": _str(),
        "olcek": _str(),
        "kaynak": _str(),
        "guncelleme": _null_str(),
        "banner": _null_str(),
    },
    ["kod", "fiyat", "para_birimi", "kaynak"],
)
PIYASA_PANO = _obj(
    {
        "server_now": _str(),
        "olcek": _null_str(),
        "satirlar": {"type": "array", "items": PIYASA_PANO_SATIR},
    },
    ["server_now", "satirlar"],
)
BUYER_QUOTE = _obj(
    {
        "id": _int(),
        "belge_turu": _str(),
        "durum": _str(),
        "urun": _str(),
        "varyant_id": _int(),
        "varyant_sku": _str(),
        "satis_kanali_kod": _str(),
        "toplam_vergisiz": _str(),
        "para_birimi": _str(),
        "gram": _str(),
        "gram_basi_vergisiz": _str(),
        "iscilik_vergisiz": _null_str(),
        "has_gram": _null_str(),
        "net_ozet": BUYER_QUOTE_NET_OZET,
        "expires_at": _null_str(),
        "hesap_zamani": _null_str(),
        "server_now": _str(),
        "allowed_actions": _actions(),
        "satirlar": {"oneOf": [{"type": "array"}, {"type": "null"}]},
    },
    ["id", "toplam_vergisiz", "para_birimi", "server_now"],
)
BUYER_PRICE_LOCK = _obj(
    {
        "id": _int(),
        "quote_id": _int(),
        "durum": _str(),
        "toplam_vergisiz": _str(),
        "para_birimi": _str(),
        "kilit_zamani": _null_str(),
        "expires_at": _null_str(),
        "server_now": _str(),
        "gecerli": _bool(),
        "allowed_actions": _actions(),
    },
    ["id", "quote_id", "gecerli", "server_now"],
)
BUYER_CART_LINE = _obj(
    {
        "id": _int(),
        "quote_id": _int(),
        "varyant_id": _int(),
        "miktar": _str(),
        "birim": _str(),
        "para_birimi": _str(),
        "birim_fiyat_vergisiz": _str(),
        "gecerlilik_sonu": _null_str(),
    }
)
BUYER_CART = _obj(
    {
        "id": _int(),
        "alici_firma_id": _int(),
        "sube_id": _null_int(),
        "line_count": _int(),
        "server_now": _str(),
        "allowed_actions": _actions(),
        "lines": {"type": "array", "items": BUYER_CART_LINE},
    },
    ["id", "server_now"],
)
BUYER_ORDER_LINE = _obj(
    {
        "id": _int(),
        "varyant_id": _int(),
        "miktar": _str(),
        "birim": _str(),
        "snapshot_birim_fiyat_vergisiz": _str(),
        "snapshot_satir_tutari_vergisiz": _str(),
        "para_birimi": _str(),
    }
)
BUYER_ORDER = _obj(
    {
        "id": _int(),
        "durum": _str(),
        "alici_firma_id": _int(),
        "sube_id": _null_int(),
        "idempotency_key": _null_str(),
        "olusturma_tarihi": _null_str(),
        "line_count": _int(),
        "lines": {"type": "array", "items": BUYER_ORDER_LINE},
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "durum", "allowed_actions"],
)

BUYER_SHIPMENT = _obj(
    {
        "id": _int(),
        "durum": _str(),
        "order_id": _int(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "durum"],
)
BUYER_RETURN = _obj(
    {
        "id": _int(),
        "durum": _str(),
        "order_id": _int(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "durum"],
)
BUYER_FINANCE_SUMMARY = _obj(
    {
        "para_birimi": _str(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["server_now"],
)
OPS_FINANCE_SUMMARY = _obj(
    {
        "ops": _bool(),
        "cari_count": _int(),
        "ledger_count": _int(),
        "payment_intent_count": _int(),
        "recent_ledger": {"type": "array"},
        "recent_payments": {"type": "array"},
    },
    ["ops", "cari_count", "ledger_count", "payment_intent_count"],
)
BUYER_CARI = _obj(
    {
        "id": _int(),
        "para_birimi": _str(),
        "bakiye": _str(),
        "kredi_limiti": _str(),
        "guncelleme_tarihi": _null_str(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "para_birimi", "bakiye"],
)
BUYER_LEDGER = _obj(
    {
        "id": _int(),
        "yon": _str(),
        "tutar": _str(),
        "para_birimi": _str(),
        "hareket_tipi": _str(),
        "referans_tip": _str(),
        "referans_id": _null_int(),
        "olusturma_tarihi": _null_str(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "tutar", "para_birimi"],
)
BUYER_CREDIT = _obj(
    {
        "para_birimi": _str(),
        "bakiye": _str(),
        "kredi_limiti": _str(),
        "kullanilabilir": _null_str(),
        "limit_aktif": _bool(),
    },
    ["para_birimi", "bakiye", "kredi_limiti", "limit_aktif"],
)
BUYER_PAYMENT_INTENT = _obj(
    {
        "id": _int(),
        "durum": _str(),
        "tutar": _str(),
        "para_birimi": _str(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "durum"],
)
WEBHOOK_ACK = _obj({"ok": _bool(), "duplicate": _bool()}, ["ok"])

ORG_UNIT = _obj(
    {
        "id": _int(),
        "kod": _str(),
        "ad": _str(),
        "aktif": _bool(),
        "parent_id": _null_int(),
        "firma_id": _int(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "kod", "ad"],
)
ORG_MEMBER = _obj(
    {
        "id": _int(),
        "org_birimi_id": _int(),
        "kullanici_id": _int(),
        "olusturma_tarihi": _null_str(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "org_birimi_id", "kullanici_id"],
)
APPROVAL = _obj(
    {
        "id": _int(),
        "durum": _str(),
        "tutar": _str(),
        "para_birimi": _str(),
        "gerekce": _str(),
        "org_birimi_id": _null_int(),
        "order_id": _null_int(),
        "olusturma_tarihi": _null_str(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "durum", "tutar"],
)
RFQ = _obj(
    {
        "id": _int(),
        "durum": _str(),
        "talep_tipi": _str(),
        "lines": {"type": "array", "items": {"type": "object"}},
        "messages": {"type": "array", "items": {"type": "object"}},
        "revizyonlar": {"type": "array", "items": {"type": "object"}},
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "durum"],
)
SUPPLIER_OFFER = _obj(
    {
        "id": _int(),
        "varyant_id": _int(),
        "tedarikci_kodu": _str(),
        "versiyon": _int(),
        "durum": _str(),
        "fiyat_modeli": _str(),
        "gram": _null_str(),
        "birim_fiyat": _null_str(),
        "para_birimi": _str(),
        "gecerlilik_baslangic": _null_str(),
        "gecerlilik_bitis": _null_str(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "varyant_id", "durum"],
)
RFQ_MATCH = _obj(
    {
        "id": _int(),
        "rfq_line_id": _int(),
        "varyant_id": _int(),
        "durum": _str(),
        "skor": _int(),
        "kanit": {"type": "object"},
        "allowed_actions": _actions(),
    },
    ["id", "rfq_line_id", "varyant_id", "durum"],
)
RFQ_MATCH_CANDIDATES = _obj(
    {
        "rfq_line_id": _int(),
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "varyant_id": _int(),
                    "sku": _str(),
                    "urun_ad": _str(),
                    "platform_kodu": _str(),
                    "skor": _int(),
                },
            },
        },
    },
    ["rfq_line_id", "results"],
)
RFQ_MATCH_LIST = _obj(
    {
        "rfq_line_id": _int(),
        "results": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/RfqMatch"},
        },
    },
    ["rfq_line_id", "results"],
)
SUPPLIER_STOCK = _obj(
    {
        "warehouse_id": _int(),
        "teklif_id": _int(),
        "varyant_id": _int(),
        "birim": _str(),
        "on_hand": _str(),
        "reserved": _str(),
        "blocked": _str(),
        "available": _str(),
    },
    ["varyant_id", "birim", "available"],
)
TICARI_SIPARIS_OZET = _obj(
    {
        "scope": _str(),
        "alici_firma_id": _null_int(),
        "siparis_adet": _int(),
        "siparis_olusturuldu": _int(),
        "siparis_iptal": _int(),
        "satir_adet": _int(),
        "ciro_vergisiz": _str(),
        "read_model": _str(),
    },
    ["scope", "siparis_adet", "ciro_vergisiz", "read_model"],
)
ALICI_DAVRANIS_OZET = _obj(
    {
        "scope": _str(),
        "alici_firma_id": _int(),
        "siparis_adet": _int(),
        "satir_adet": _int(),
        "ciro_vergisiz": _str(),
        "quote_adet": _int(),
        "quote_toplam_sum": _str(),
        "read_model": _str(),
    },
    ["scope", "alici_firma_id", "read_model"],
)
CIRO_ANOMALI = _obj(
    {
        "scope": _str(),
        "esik_ciro": _str(),
        "uyari_adet": _int(),
        "uyarilar": {"type": "array", "items": {"type": "object"}},
        "read_model": _str(),
    },
    ["scope", "esik_ciro", "uyari_adet", "uyarilar", "read_model"],
)
SUPPLIER_MOVEMENT = _obj(
    {
        "id": _int(),
        "warehouse_id": _int(),
        "teklif_id": _int(),
        "varyant_id": _int(),
        "birim": _str(),
        "miktar": _str(),
        "tip": _str(),
        "neden": _str(),
    },
    ["id", "tip", "miktar"],
)
OPS_INSPECTION = _obj(
    {
        "id": _int(),
        "durum": _str(),
        "order_id": _int(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "durum"],
)
OPS_SHIPMENT = _obj(
    {
        "id": _int(),
        "durum": _str(),
        "order_id": _int(),
        "allowed_actions": _actions(),
        "server_now": _str(),
    },
    ["id", "durum"],
)
OPS_SUMMARY = _obj(
    {
        "counts": {"type": "object", "additionalProperties": True},
        "server_now": _str(),
    }
)
BULK_ORDER_RESULT = _obj(
    {
        "order_id": _null_int(),
        "created": _bool(),
        "errors": {"type": "array", "items": {"type": "object"}},
        "server_now": _str(),
    }
)
CHECKOUT_RESULT = _obj(
    {
        "checkout_id": _int(),
        "order_id": _null_int(),
        "durum": _str(),
        "server_now": _str(),
    },
    ["checkout_id"],
)

PAGE_PROPS = {
    "count": _int(),
    "next": _null_str(),
    "previous": _null_str(),
    "page": _int(),
    "page_size": _int(),
}


def paginated(item_name: str) -> dict:
    return _obj(
        {
            **PAGE_PROPS,
            "results": {
                "type": "array",
                "items": {"$ref": f"#/components/schemas/{item_name}"},
            },
        },
        ["count", "page", "page_size", "results"],
    )


COMPONENT_SCHEMAS: dict[str, dict] = {
    "ProblemDetail": PROBLEM_DETAIL,
    "FirmaMasked": FIRMA_MASKED,
    "Capabilities": CAPABILITIES,
    "MeResponse": ME_RESPONSE,
    "MeProfile": ME_PROFILE,
    "FirmaAdresi": FIRMA_ADRESI,
    "FirmaAdresiPage": paginated("FirmaAdresi"),
    "Health": HEALTH,
    "Ready": READY,
    "CsrfResponse": CSRF,
    "LogoutOk": LOGOUT_OK,
    "InviteList": INVITE_LIST,
    "InviteCreated": INVITE_CREATED,
    "InviteAccepted": INVITE_ACCEPTED,
    "EmailVerifyRequestOk": EMAIL_VERIFY_REQUEST_OK,
    "EmailVerifyConfirmOk": EMAIL_VERIFY_CONFIRM_OK,
    "DetailOk": DETAIL_OK,
    "MfaVerifyOk": MFA_VERIFY_OK,
    "MeDashboard": ME_DASHBOARD,
    "ActAsStartOk": ACT_AS_START_OK,
    "ActAsStopOk": ACT_AS_STOP_OK,
    "OpsProduct": OPS_PRODUCT,
    "OpsProductPage": paginated("OpsProduct"),
    "OpsProductVariant": OPS_PRODUCT_VARIANT,
    "BuyerCatalogItem": BUYER_CATALOG_ITEM,
    "BuyerCatalogDetail": BUYER_CATALOG_DETAIL,
    "BuyerCatalogPage": paginated("BuyerCatalogItem"),
    "BuyerQuote": BUYER_QUOTE,
    "PiyasaPano": PIYASA_PANO,
    "PiyasaPanoSatir": PIYASA_PANO_SATIR,
    "BuyerPriceLock": BUYER_PRICE_LOCK,
    "BuyerCart": BUYER_CART,
    "BuyerCartLine": BUYER_CART_LINE,
    "BuyerOrder": BUYER_ORDER,
    "BuyerOrderPage": paginated("BuyerOrder"),
    "BuyerShipment": BUYER_SHIPMENT,
    "BuyerShipmentPage": paginated("BuyerShipment"),
    "BuyerReturn": BUYER_RETURN,
    "BuyerReturnPage": paginated("BuyerReturn"),
    "BuyerFinanceSummary": BUYER_FINANCE_SUMMARY,
    "OpsFinanceSummary": OPS_FINANCE_SUMMARY,
    "BuyerCari": BUYER_CARI,
    "BuyerCariPage": paginated("BuyerCari"),
    "BuyerLedger": BUYER_LEDGER,
    "BuyerLedgerPage": paginated("BuyerLedger"),
    "BuyerCredit": BUYER_CREDIT,
    "BuyerPaymentIntent": BUYER_PAYMENT_INTENT,
    "TicariSiparisOzet": TICARI_SIPARIS_OZET,
    "AliciDavranisOzet": ALICI_DAVRANIS_OZET,
    "CiroAnomali": CIRO_ANOMALI,
    "WebhookAck": WEBHOOK_ACK,
    "OrgUnit": ORG_UNIT,
    "OrgUnitPage": paginated("OrgUnit"),
    "OrgMember": ORG_MEMBER,
    "OrgMemberPage": paginated("OrgMember"),
    "Approval": APPROVAL,
    "ApprovalPage": paginated("Approval"),
    "Rfq": RFQ,
    "RfqPage": paginated("Rfq"),
    "SupplierOffer": SUPPLIER_OFFER,
    "SupplierOfferPage": paginated("SupplierOffer"),
    "RfqMatch": RFQ_MATCH,
    "RfqMatchCandidates": RFQ_MATCH_CANDIDATES,
    "RfqMatchList": RFQ_MATCH_LIST,
    "SupplierStock": SUPPLIER_STOCK,
    "SupplierStockPage": paginated("SupplierStock"),
    "SupplierMovement": SUPPLIER_MOVEMENT,
    "OpsInspection": OPS_INSPECTION,
    "OpsInspectionPage": paginated("OpsInspection"),
    "OpsShipment": OPS_SHIPMENT,
    "OpsShipmentPage": paginated("OpsShipment"),
    "OpsSummary": OPS_SUMMARY,
    "BulkOrderResult": BULK_ORDER_RESULT,
    "CheckoutResult": CHECKOUT_RESULT,
}

# (status_code, schema_name)
_R = dict[str, tuple[str, str]]

RESPONSE_BINDINGS: dict[str, _R] = {
    "/api/v1/health/": {"get": ("200", "Health")},
    "/api/v1/ready/": {"get": ("200", "Ready")},
    "/api/v1/auth/csrf/": {"get": ("200", "CsrfResponse")},
    "/api/v1/auth/login/": {"post": ("200", "MeResponse")},
    "/api/v1/auth/logout/": {"post": ("200", "LogoutOk")},
    "/api/v1/auth/password-reset/": {"post": ("200", "DetailOk")},
    "/api/v1/auth/password-reset/confirm/": {"post": ("200", "DetailOk")},
    "/api/v1/auth/password-change/": {"post": ("200", "DetailOk")},
    "/api/v1/auth/mfa/verify/": {"post": ("200", "MfaVerifyOk")},
    "/api/v1/auth/mfa/resend/": {"post": ("200", "DetailOk")},
    "/api/v1/auth/invites/": {"get": ("200", "InviteList")},
    "/api/v1/auth/invites/create/": {"post": ("201", "InviteCreated")},
    "/api/v1/auth/invites/accept/": {"post": ("201", "InviteAccepted")},
    "/api/v1/auth/email-verify/": {"post": ("200", "EmailVerifyRequestOk")},
    "/api/v1/auth/email-verify/confirm/": {"post": ("200", "EmailVerifyConfirmOk")},
    "/api/v1/me/": {"get": ("200", "MeResponse")},
    "/api/v1/me/dashboard/": {"get": ("200", "MeDashboard")},
    "/api/v1/me/profile/": {
        "get": ("200", "MeProfile"),
        "patch": ("200", "MeProfile"),
    },
    "/api/v1/me/addresses/": {
        "get": ("200", "FirmaAdresiPage"),
        "post": ("201", "FirmaAdresi"),
    },
    "/api/v1/me/addresses/{id}/": {
        "get": ("200", "FirmaAdresi"),
        "patch": ("200", "FirmaAdresi"),
        "delete": ("200", "DetailOk"),
    },
    "/api/v1/act-as/start/": {"post": ("200", "ActAsStartOk")},
    "/api/v1/act-as/stop/": {"post": ("200", "ActAsStopOk")},
    "/api/v1/catalog/": {"get": ("200", "BuyerCatalogPage")},
    "/api/v1/catalog/{id}/": {"get": ("200", "BuyerCatalogDetail")},
    "/api/v1/quotes/": {"post": ("201", "BuyerQuote")},
    "/api/v1/quotes/{id}/": {"get": ("200", "BuyerQuote")},
    "/api/v1/piyasa/pano/": {"get": ("200", "PiyasaPano")},
    "/api/v1/price-locks/": {"post": ("201", "BuyerPriceLock")},
    "/api/v1/price-locks/{id}/": {"get": ("200", "BuyerPriceLock")},
    "/api/v1/carts/me/": {"get": ("200", "BuyerCart")},
    "/api/v1/carts/me/lines/": {"post": ("201", "BuyerCart")},
    "/api/v1/carts/me/lines/{line_id}/": {
        "patch": ("200", "BuyerCart"),
        "delete": ("200", "BuyerCart"),
    },
    "/api/v1/carts/{id}/": {"get": ("200", "BuyerCart")},
    "/api/v1/checkouts/": {"post": ("201", "CheckoutResult")},
    "/api/v1/bulk-orders/": {"post": ("201", "BulkOrderResult")},
    "/api/v1/orders/": {"get": ("200", "BuyerOrderPage")},
    "/api/v1/orders/from-checkout/": {"post": ("201", "BuyerOrder")},
    "/api/v1/orders/{id}/": {"get": ("200", "BuyerOrder")},
    "/api/v1/orders/{id}/cancel/": {"post": ("200", "BuyerOrder")},
    "/api/v1/orders/{id}/reorder/": {"post": ("201", "BuyerCart")},
    "/api/v1/shipments/": {"get": ("200", "BuyerShipmentPage")},
    "/api/v1/shipments/{id}/": {"get": ("200", "BuyerShipment")},
    "/api/v1/returns/": {"get": ("200", "BuyerReturnPage"), "post": ("201", "BuyerReturn")},
    "/api/v1/returns/{id}/": {"get": ("200", "BuyerReturn")},
    "/api/v1/returns/{id}/submit/": {"post": ("200", "BuyerReturn")},
    "/api/v1/returns/{id}/approve/": {"post": ("200", "BuyerReturn")},
    "/api/v1/returns/{id}/reject/": {"post": ("200", "BuyerReturn")},
    "/api/v1/returns/{id}/cancel/": {"post": ("200", "BuyerReturn")},
    "/api/v1/returns/{id}/mahsup/": {"post": ("200", "BuyerReturn")},
    "/api/v1/credit/me/": {"get": ("200", "BuyerCredit")},
    "/api/v1/credit/check/": {"post": ("200", "BuyerCredit")},
    "/api/v1/finance/me/": {"get": ("200", "BuyerFinanceSummary")},
    "/api/v1/finance/cari/": {"get": ("200", "BuyerCariPage")},
    "/api/v1/finance/cari/{id}/": {"get": ("200", "BuyerCari")},
    "/api/v1/finance/ledger/": {"get": ("200", "BuyerLedgerPage")},
    "/api/v1/payments/intents/": {"post": ("201", "BuyerPaymentIntent")},
    "/api/v1/payments/webhook/": {"post": ("200", "WebhookAck")},
    "/api/v1/ops/finance/": {"get": ("200", "OpsFinanceSummary")},
    "/api/v1/ops/finance/cari/": {"get": ("200", "BuyerCariPage")},
    "/api/v1/ops/finance/ledger/": {"get": ("200", "BuyerLedgerPage")},
    "/api/v1/ops/finance/payments/": {"get": ("200", "BuyerOrderPage")},
    "/api/v1/reports/orders/": {"get": ("200", "TicariSiparisOzet")},
    "/api/v1/reports/buyer-behavior/": {"get": ("200", "AliciDavranisOzet")},
    "/api/v1/ops/anomalies/ciro/": {"get": ("200", "CiroAnomali")},
    "/api/v1/ops/orders/summary/": {"get": ("200", "OpsSummary")},
    "/api/v1/ops/inspections/": {
        "get": ("200", "OpsInspectionPage"),
        "post": ("201", "OpsInspection"),
    },
    "/api/v1/ops/inspections/{id}/": {"get": ("200", "OpsInspection")},
    "/api/v1/ops/inspections/{id}/start/": {"post": ("200", "OpsInspection")},
    "/api/v1/ops/inspections/{id}/pass/": {"post": ("200", "OpsInspection")},
    "/api/v1/ops/inspections/{id}/fail/": {"post": ("200", "OpsInspection")},
    "/api/v1/ops/inspections/{id}/cancel/": {"post": ("200", "OpsInspection")},
    "/api/v1/ops/inspections/{id}/measurements/": {"post": ("201", "OpsInspection")},
    "/api/v1/ops/shipments/": {
        "get": ("200", "OpsShipmentPage"),
        "post": ("201", "OpsShipment"),
    },
    "/api/v1/ops/shipments/{id}/": {"get": ("200", "OpsShipment")},
    "/api/v1/ops/shipments/{id}/prepare/": {"post": ("200", "OpsShipment")},
    "/api/v1/ops/shipments/{id}/dispatch/": {"post": ("200", "OpsShipment")},
    "/api/v1/ops/shipments/{id}/deliver/": {"post": ("200", "OpsShipment")},
    "/api/v1/ops/shipments/{id}/cancel/": {"post": ("200", "OpsShipment")},
    "/api/v1/ops/shipments/{id}/pod/": {"post": ("200", "OpsShipment")},
    "/api/v1/org-units/": {"get": ("200", "OrgUnitPage"), "post": ("201", "OrgUnit")},
    "/api/v1/org-units/{id}/": {"get": ("200", "OrgUnit")},
    "/api/v1/org-units/{id}/members/": {
        "get": ("200", "OrgMemberPage"),
        "post": ("201", "OrgMember"),
    },
    "/api/v1/approvals/": {
        "get": ("200", "ApprovalPage"),
        "post": ("201", "Approval"),
    },
    "/api/v1/approvals/{id}/": {"get": ("200", "Approval")},
    "/api/v1/approvals/{id}/submit/": {"post": ("200", "Approval")},
    "/api/v1/approvals/{id}/approve/": {"post": ("200", "Approval")},
    "/api/v1/approvals/{id}/reject/": {"post": ("200", "Approval")},
    "/api/v1/rfqs/": {"get": ("200", "RfqPage"), "post": ("201", "Rfq")},
    "/api/v1/rfqs/{id}/": {"get": ("200", "Rfq")},
    "/api/v1/rfqs/{id}/send/": {"post": ("200", "Rfq")},
    "/api/v1/rfqs/{id}/messages/": {"post": ("201", "Rfq")},
    "/api/v1/rfqs/{id}/revisions/": {"post": ("201", "Rfq")},
    "/api/v1/supplier/offers/": {
        "get": ("200", "SupplierOfferPage"),
        "post": ("201", "SupplierOffer"),
    },
    "/api/v1/supplier/offers/{id}/": {"get": ("200", "SupplierOffer")},
    "/api/v1/supplier/offers/{id}/submit/": {"post": ("200", "SupplierOffer")},
    "/api/v1/supplier/offers/{id}/deactivate/": {"post": ("200", "SupplierOffer")},
    "/api/v1/supplier/offers/{id}/versions/": {"post": ("201", "SupplierOffer")},
    "/api/v1/ops/rfq-lines/{line_id}/match-candidates/": {
        "get": ("200", "RfqMatchCandidates")
    },
    "/api/v1/ops/rfq-lines/{line_id}/matches/": {
        "get": ("200", "RfqMatchList"),
        "post": ("201", "RfqMatch"),
    },
    "/api/v1/ops/rfq-matches/{id}/approve/": {"post": ("200", "RfqMatch")},
    "/api/v1/ops/rfq-matches/{id}/reject/": {"post": ("200", "RfqMatch")},
    "/api/v1/ops/products/": {
        "get": ("200", "OpsProductPage"),
        "post": ("201", "OpsProduct"),
    },
    "/api/v1/ops/products/{id}/": {"get": ("200", "OpsProduct")},
    "/api/v1/ops/products/{id}/variants/": {"post": ("201", "OpsProductVariant")},
    "/api/v1/ops/products/{id}/submit/": {"post": ("200", "OpsProduct")},
    "/api/v1/ops/products/{id}/approve/": {"post": ("200", "OpsProduct")},
    "/api/v1/ops/products/{id}/reject/": {"post": ("200", "OpsProduct")},
    "/api/v1/ops/products/{id}/publish/": {"post": ("200", "OpsProduct")},
    "/api/v1/ops/products/{id}/unpublish/": {"post": ("200", "OpsProduct")},
    "/api/v1/supplier/stock/": {"get": ("200", "SupplierStockPage")},
    "/api/v1/supplier/stock/adjustments/": {"post": ("201", "SupplierMovement")},
    "/api/v1/supplier/rfqs/": {"get": ("200", "RfqPage")},
    "/api/v1/supplier/rfqs/{id}/": {"get": ("200", "Rfq")},
    "/api/v1/supplier/rfqs/{id}/messages/": {"post": ("201", "Rfq")},
    "/api/v1/supplier/rfqs/{id}/revisions/": {"post": ("201", "Rfq")},
}

TAG_BY_PREFIX = (
    ("/api/v1/auth/", "auth"),
    ("/api/v1/me/", "me"),
    ("/api/v1/health/", "health"),
    ("/api/v1/ready/", "health"),
    ("/api/v1/catalog/", "catalog"),
    ("/api/v1/quotes/", "pricing"),
    ("/api/v1/price-locks/", "pricing"),
    ("/api/v1/piyasa/", "piyasa"),
    ("/api/v1/carts/", "cart"),
    ("/api/v1/checkouts/", "checkout"),
    ("/api/v1/bulk-orders/", "orders"),
    ("/api/v1/orders/", "orders"),
    ("/api/v1/shipments/", "shipments"),
    ("/api/v1/returns/", "returns"),
    ("/api/v1/credit/", "finance"),
    ("/api/v1/finance/", "finance"),
    ("/api/v1/payments/", "finance"),
    ("/api/v1/ops/", "ops"),
    ("/api/v1/reports/", "reports"),
    ("/api/v1/org-units/", "org"),
    ("/api/v1/approvals/", "approvals"),
    ("/api/v1/rfqs/", "rfq"),
    ("/api/v1/supplier/", "supplier"),
)


def _binding_for(path: str) -> _R | None:
    if path in RESPONSE_BINDINGS:
        return RESPONSE_BINDINGS[path]
    alt = path.replace("{pk}", "{id}").replace("{line_id}", "{line_id}")
    if alt in RESPONSE_BINDINGS:
        return RESPONSE_BINDINGS[alt]
    return RESPONSE_BINDINGS.get(path.replace("{id}", "{pk}"))


def _tag_for(path: str) -> str:
    for prefix, tag in TAG_BY_PREFIX:
        if path.startswith(prefix):
            return tag
    return "api"


def enrich_openapi_schema(schema: dict) -> dict:
    """DRF şemasına response/request DTO, tag, security ve Problem+JSON ekler."""
    from api.openapi_requests import REQUEST_SCHEMAS, _binding_for as _req_binding

    schema["openapi"] = schema.get("openapi") or "3.1.0"
    if schema["openapi"].startswith("3.0"):
        # Hedef 3.1; spectacular varsayılanı 3.0.3 olabilir
        schema["openapi"] = "3.1.0"

    info = schema.setdefault("info", {})
    info.setdefault("title", "Kuyumbank API")
    info.setdefault("version", "1.0.0")
    info["description"] = (
        "Kuyumbank `/api/v1/` — ADR-0017. "
        "Auth: session+CSRF (tarayıcı) veya Token (S2S). "
        "Hata: application/problem+json. "
        "Tenant: client firma_id yok sayılır. "
        "Rapor HTTP: ADR-0026. Mahsup HTTP: ADR-0023."
    )

    components = schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas.update(COMPONENT_SCHEMAS)
    schemas.update(REQUEST_SCHEMAS)
    components["securitySchemes"] = {
        "cookieAuth": {"type": "apiKey", "in": "cookie", "name": "sessionid"},
        "csrfHeader": {"type": "apiKey", "in": "header", "name": "X-CSRFToken"},
        "tokenAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "Token"},
    }
    schema["security"] = [{"cookieAuth": []}, {"tokenAuth": []}]

    paths = schema.get("paths") or {}
    seen_ids: dict[str, str] = {}
    for path, methods in paths.items():
        bindings = _binding_for(path)
        tag = _tag_for(path)
        for method, op in list(methods.items()):
            if method.startswith("x-") or not isinstance(op, dict):
                continue
            op.setdefault("tags", [tag])
            if not op.get("summary"):
                op["summary"] = f"{method.upper()} {path}"
            if not op.get("description"):
                op["description"] = (
                    f"`{method.upper()} {path}` — yetki ve tenant view/serviste "
                    f"yeniden doğrulanır; UI gizleme güvenlik değildir."
                )
            oid = op.get("operationId") or f"{method}_{path}"
            oid = (
                str(oid)
                .replace("/", "_")
                .replace("{", "")
                .replace("}", "")
                .replace("-", "_")
            )
            if oid in seen_ids and seen_ids[oid] != f"{method} {path}":
                oid = f"{oid}_{abs(hash(path + method)) % 10000}"
            seen_ids[oid] = f"{method} {path}"
            op["operationId"] = oid

            # Request body (POST/PUT/PATCH/DELETE body kullananlar)
            req_binds = _req_binding(path)
            if req_binds and method in req_binds:
                rname = req_binds[method]
                op["requestBody"] = {
                    "required": rname != "EmptyRequest",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": f"#/components/schemas/{rname}"
                            }
                        }
                    },
                }

            responses = op.setdefault("responses", {})
            if bindings and method in bindings:
                code, name = bindings[method]
                responses[code] = {
                    "description": name,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{name}"}
                        }
                    },
                }
                # AutoSchema boş 201 stub bırakabiliyor — bağlanan 2xx dışındakileri temizle
                for other in list(responses.keys()):
                    if other == code or not str(other).startswith("2"):
                        continue
                    other_resp = responses.get(other) or {}
                    content = (other_resp.get("content") or {}).get(
                        "application/json"
                    ) or {}
                    sch = content.get("schema")
                    if not sch or sch == {} or (
                        isinstance(sch, dict)
                        and sch.get("type") == "array"
                        and sch.get("items") == {}
                    ):
                        del responses[other]
            for err in ("400", "401", "403", "404", "409", "429"):
                responses.setdefault(
                    err,
                    {
                        "description": "Problem+JSON",
                        "content": {
                            "application/problem+json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ProblemDetail"
                                }
                            }
                        },
                    },
                )
    return schema
