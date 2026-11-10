"""OpenAPI request body şemaları — view `request.data` alanlarıyla hizalı.

A grubu: gerçek payload. B grubu: EmptyRequest veya ReasonRequest / opsiyonel alanlar.
"""

from __future__ import annotations

from typing import Any


def _str(**extra: Any) -> dict:
    return {"type": "string", **extra}


def _int(**extra: Any) -> dict:
    return {"type": "integer", **extra}


def _bool(**extra: Any) -> dict:
    return {"type": "boolean", **extra}


def _num_str(**extra: Any) -> dict:
    """Decimal alanlar API’de string veya number olabilir; dokümanda string."""
    return {"type": "string", **extra}


def _obj(properties: dict, required: list[str] | None = None) -> dict:
    out: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        out["required"] = required
    return out


# --- B: boş / gerekçe ---
EMPTY_REQUEST = _obj({})
REASON_REQUEST = _obj({"reason": _str(description="Red/fail gerekçesi")})
TAKIP_NO_REQUEST = _obj({"takip_no": _str()})
REORDER_REQUEST = _obj(
    {"replace_cart": _bool(description="Varsayılan true")},
)

# --- A: auth / commerce ---
LOGIN_REQUEST = _obj(
    {"username": _str(), "password": _str(format="password")},
    ["username", "password"],
)
CART_LINE_CREATE = _obj(
    {"quote_id": _int(), "miktar": _num_str()},
    ["quote_id", "miktar"],
)
CART_LINE_PATCH = _obj({"miktar": _num_str()}, ["miktar"])
QUOTE_CREATE = _obj(
    {
        "varyant_id": _int(),
        "satis_kanali_id": _int(),
        "para_birimi": _str(default="TRY"),
    },
    ["varyant_id", "satis_kanali_id"],
)
PRICE_LOCK_CREATE = _obj({"quote_id": _int()}, ["quote_id"])
ORDER_FROM_CHECKOUT = _obj({"checkout_id": _int()}, ["checkout_id"])
BULK_ROW = _obj(
    {
        "sku": _str(),
        "miktar": _num_str(),
        "birim": _str(description="Opsiyonel; yoksa teklif birimi"),
    },
    ["sku", "miktar"],
)
BULK_ORDER_CREATE = _obj(
    {
        "satis_kanali_id": _int(),
        "csv": _str(description="CSV metin; rows yoksa"),
        "rows": {"type": "array", "items": BULK_ROW},
    },
    ["satis_kanali_id"],
)

CREDIT_CHECK = _obj(
    {"tutar": _num_str(), "para_birimi": _str(default="TRY")},
    ["tutar"],
)
PAYMENT_INTENT_CREATE = _obj({"order_id": _int()}, ["order_id"])
PAYMENT_WEBHOOK = _obj(
    {
        "event_id": _str(),
        "event_type": _str(),
        "provider": _str(default="fake"),
        "payload": {
            "type": "object",
            "additionalProperties": True,
            "description": "Provider payload; payment.succeeded için intent_id",
        },
        "intent_id": _str(description="Düz alan da kabul (iskelet)"),
    },
    ["event_id", "event_type"],
)

RETURN_LINE = _obj(
    {"order_line_id": _int(), "miktar": _num_str()},
    ["order_line_id", "miktar"],
)
RETURN_CREATE = _obj(
    {
        "order_id": _int(),
        "shipment_id": _int(),
        "sebep": _str(),
        "notlar": _str(),
        "lines": {"type": "array", "items": RETURN_LINE, "minItems": 1},
    },
    ["order_id", "shipment_id", "lines"],
)

APPROVAL_CREATE = _obj(
    {
        "tutar": _num_str(),
        "para_birimi": _str(default="TRY"),
        "gerekce": _str(),
        "org_birimi_id": _int(),
        "order_id": _int(),
    },
    ["tutar"],
)

ORG_UNIT_CREATE = _obj(
    {
        "kod": _str(),
        "ad": _str(),
        "parent_id": _int(),
    },
    ["kod"],
)
ORG_MEMBER_CREATE = _obj({"kullanici_id": _int()}, ["kullanici_id"])

RFQ_LINE = _obj(
    {
        "aciklama": _str(),
        "miktar": _num_str(),
        "birim": _str(default="ADET"),
        "varyant_id": _int(description="Opsiyonel; katalog satırı"),
    },
    ["miktar"],
)
RFQ_CREATE = _obj(
    {
        "baslik": _str(),
        "talep_tipi": _str(description="STANDART | OZEL_URETIM vb."),
        "sube_id": _int(),
        "lines": {"type": "array", "items": RFQ_LINE, "minItems": 1},
    },
    ["lines"],
)
RFQ_MESSAGE = _obj({"govde": _str()}, ["govde"])
RFQ_REVISION = _obj({"ozet": _str()}, ["ozet"])

SUPPLIER_OFFER_VERSION = _obj(
    {
        "gram": _num_str(),
        "birim_fiyat": _num_str(),
        "fiyat_modeli": _str(),
    }
)
SUPPLIER_STOCK_ADJUST = _obj(
    {
        "warehouse_id": _int(),
        "teklif_id": _int(),
        "miktar": _num_str(),
        "neden": _str(),
    },
    ["warehouse_id", "teklif_id", "miktar"],
)

OPS_INSPECTION_CREATE = _obj(
    {
        "order_id": _int(),
        "order_line_id": _int(),
        "notlar": _str(),
    },
    ["order_id"],
)
OPS_MEASUREMENT = _obj(
    {
        "order_line_id": _int(),
        "olculen": _num_str(),
        "override_gerekce": _str(),
    },
    ["order_line_id", "olculen"],
)
OPS_SHIPMENT_CREATE = _obj(
    {
        "order_id": _int(),
        "notlar": _str(),
        "takip_no": _str(),
    },
    ["order_id"],
)
OPS_POD = _obj(
    {
        "teslim_alan": _str(),
        "notlar": _str(),
        "belgeler_ref": _str(),
    }
)

REQUEST_SCHEMAS: dict[str, dict] = {
    "EmptyRequest": EMPTY_REQUEST,
    "ReasonRequest": REASON_REQUEST,
    "TakipNoRequest": TAKIP_NO_REQUEST,
    "ReorderRequest": REORDER_REQUEST,
    "LoginRequest": LOGIN_REQUEST,
    "CartLineCreateRequest": CART_LINE_CREATE,
    "CartLinePatchRequest": CART_LINE_PATCH,
    "QuoteCreateRequest": QUOTE_CREATE,
    "PriceLockCreateRequest": PRICE_LOCK_CREATE,
    "OrderFromCheckoutRequest": ORDER_FROM_CHECKOUT,
    "BulkOrderCreateRequest": BULK_ORDER_CREATE,
    "CreditCheckRequest": CREDIT_CHECK,
    "PaymentIntentCreateRequest": PAYMENT_INTENT_CREATE,
    "PaymentWebhookRequest": PAYMENT_WEBHOOK,
    "ReturnCreateRequest": RETURN_CREATE,
    "ReturnApproveRequest": _obj(
        {"mahsup": _bool(description="ONAYLANDI ile birlikte F5-023 mahsup (post_ledger)")}
    ),
    "ApprovalCreateRequest": APPROVAL_CREATE,
    "OrgUnitCreateRequest": ORG_UNIT_CREATE,
    "OrgMemberCreateRequest": ORG_MEMBER_CREATE,
    "RfqCreateRequest": RFQ_CREATE,
    "RfqMessageRequest": RFQ_MESSAGE,
    "RfqRevisionRequest": RFQ_REVISION,
    "SupplierOfferVersionRequest": SUPPLIER_OFFER_VERSION,
    "SupplierStockAdjustRequest": SUPPLIER_STOCK_ADJUST,
    "OpsInspectionCreateRequest": OPS_INSPECTION_CREATE,
    "OpsMeasurementRequest": OPS_MEASUREMENT,
    "OpsShipmentCreateRequest": OPS_SHIPMENT_CREATE,
    "OpsPodRequest": OPS_POD,
}

# path → method → schema component name
REQUEST_BINDINGS: dict[str, dict[str, str]] = {
    # A — payload
    "/api/v1/auth/login/": {"post": "LoginRequest"},
    "/api/v1/carts/me/lines/": {"post": "CartLineCreateRequest"},
    "/api/v1/carts/me/lines/{line_id}/": {
        "patch": "CartLinePatchRequest",
        "delete": "EmptyRequest",
    },
    "/api/v1/checkouts/": {"post": "EmptyRequest"},
    "/api/v1/orders/from-checkout/": {"post": "OrderFromCheckoutRequest"},
    "/api/v1/bulk-orders/": {"post": "BulkOrderCreateRequest"},
    "/api/v1/quotes/": {"post": "QuoteCreateRequest"},
    "/api/v1/price-locks/": {"post": "PriceLockCreateRequest"},
    "/api/v1/credit/check/": {"post": "CreditCheckRequest"},
    "/api/v1/payments/intents/": {"post": "PaymentIntentCreateRequest"},
    "/api/v1/payments/webhook/": {"post": "PaymentWebhookRequest"},
    "/api/v1/returns/": {"post": "ReturnCreateRequest"},
    "/api/v1/approvals/": {"post": "ApprovalCreateRequest"},
    "/api/v1/org-units/": {"post": "OrgUnitCreateRequest"},
    "/api/v1/org-units/{id}/members/": {"post": "OrgMemberCreateRequest"},
    "/api/v1/rfqs/": {"post": "RfqCreateRequest"},
    "/api/v1/rfqs/{id}/messages/": {"post": "RfqMessageRequest"},
    "/api/v1/rfqs/{id}/revisions/": {"post": "RfqRevisionRequest"},
    "/api/v1/supplier/offers/{id}/versions/": {"post": "SupplierOfferVersionRequest"},
    "/api/v1/supplier/rfqs/{id}/messages/": {"post": "RfqMessageRequest"},
    "/api/v1/supplier/rfqs/{id}/revisions/": {"post": "RfqRevisionRequest"},
    "/api/v1/supplier/stock/adjustments/": {"post": "SupplierStockAdjustRequest"},
    "/api/v1/ops/inspections/": {"post": "OpsInspectionCreateRequest"},
    "/api/v1/ops/inspections/{id}/measurements/": {"post": "OpsMeasurementRequest"},
    "/api/v1/ops/shipments/": {"post": "OpsShipmentCreateRequest"},
    "/api/v1/ops/shipments/{id}/pod/": {"post": "OpsPodRequest"},
    # B — action (empty / reason / optional)
    "/api/v1/auth/logout/": {"post": "EmptyRequest"},
    "/api/v1/orders/{id}/cancel/": {"post": "EmptyRequest"},
    "/api/v1/orders/{id}/reorder/": {"post": "ReorderRequest"},
    "/api/v1/approvals/{id}/submit/": {"post": "EmptyRequest"},
    "/api/v1/approvals/{id}/approve/": {"post": "EmptyRequest"},
    "/api/v1/approvals/{id}/reject/": {"post": "ReasonRequest"},
    "/api/v1/returns/{id}/submit/": {"post": "EmptyRequest"},
    "/api/v1/returns/{id}/approve/": {"post": "ReturnApproveRequest"},
    "/api/v1/returns/{id}/reject/": {"post": "ReasonRequest"},
    "/api/v1/returns/{id}/cancel/": {"post": "EmptyRequest"},
    "/api/v1/returns/{id}/mahsup/": {"post": "EmptyRequest"},
    "/api/v1/ops/inspections/{id}/start/": {"post": "EmptyRequest"},
    "/api/v1/ops/inspections/{id}/pass/": {"post": "EmptyRequest"},
    "/api/v1/ops/inspections/{id}/fail/": {"post": "ReasonRequest"},
    "/api/v1/ops/inspections/{id}/cancel/": {"post": "EmptyRequest"},
    "/api/v1/ops/shipments/{id}/prepare/": {"post": "EmptyRequest"},
    "/api/v1/ops/shipments/{id}/dispatch/": {"post": "TakipNoRequest"},
    "/api/v1/ops/shipments/{id}/deliver/": {"post": "EmptyRequest"},
    "/api/v1/ops/shipments/{id}/cancel/": {"post": "EmptyRequest"},
    "/api/v1/rfqs/{id}/send/": {"post": "EmptyRequest"},
    "/api/v1/supplier/offers/{id}/submit/": {"post": "EmptyRequest"},
    "/api/v1/supplier/offers/{id}/deactivate/": {"post": "EmptyRequest"},
}


def _binding_for(path: str) -> dict[str, str] | None:
    if path in REQUEST_BINDINGS:
        return REQUEST_BINDINGS[path]
    alt = path.replace("{pk}", "{id}")
    if alt in REQUEST_BINDINGS:
        return REQUEST_BINDINGS[alt]
    return REQUEST_BINDINGS.get(path.replace("{id}", "{pk}"))
