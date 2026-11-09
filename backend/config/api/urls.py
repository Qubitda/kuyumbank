from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.schemas import get_schema_view

from api.views import (
    BulkOrderCreateView,
    BuyerCatalogListView,
    BuyerFinanceSummaryView,
    CartDetailView,
    CartMineView,
    CheckoutCreateView,
    CreditCheckView,
    CreditMineView,
    HealthView,
    MeView,
    OpsFinanceCariListView,
    OpsFinanceLedgerListView,
    OpsFinanceSummaryView,
    OpsOrderSummaryView,
    OrderDetailView,
    OrderListView,
    PaymentWebhookView,
    ShipmentDetailView,
    ShipmentListView,
    SupplierOfferListView,
    SupplierStockSummaryView,
)

schema_view = get_schema_view(
    title="Kuyumbank API",
    description="İnce PRE yüzeyi (U-012). Tam Prosperer API değildir.",
    version="1.0.0",
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="api-health"),
    path("me/", MeView.as_view(), name="api-me"),
    path("catalog/", BuyerCatalogListView.as_view(), name="api-buyer-catalog"),
    path("carts/me/", CartMineView.as_view(), name="api-cart-mine"),
    path("carts/<int:pk>/", CartDetailView.as_view(), name="api-cart-detail"),
    path("checkouts/", CheckoutCreateView.as_view(), name="api-checkout-create"),
    path("bulk-orders/", BulkOrderCreateView.as_view(), name="api-bulk-order-create"),
    path("orders/", OrderListView.as_view(), name="api-order-list"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="api-order-detail"),
    path("shipments/", ShipmentListView.as_view(), name="api-shipment-list"),
    path(
        "shipments/<int:pk>/",
        ShipmentDetailView.as_view(),
        name="api-shipment-detail",
    ),
    path(
        "supplier/offers/",
        SupplierOfferListView.as_view(),
        name="api-supplier-offers",
    ),
    path(
        "supplier/stock/",
        SupplierStockSummaryView.as_view(),
        name="api-supplier-stock",
    ),
    path("credit/me/", CreditMineView.as_view(), name="api-credit-mine"),
    path("credit/check/", CreditCheckView.as_view(), name="api-credit-check"),
    path("finance/me/", BuyerFinanceSummaryView.as_view(), name="api-finance-mine"),
    path("ops/finance/", OpsFinanceSummaryView.as_view(), name="api-ops-finance"),
    path(
        "ops/finance/cari/",
        OpsFinanceCariListView.as_view(),
        name="api-ops-finance-cari",
    ),
    path(
        "ops/finance/ledger/",
        OpsFinanceLedgerListView.as_view(),
        name="api-ops-finance-ledger",
    ),
    path(
        "ops/orders/summary/",
        OpsOrderSummaryView.as_view(),
        name="api-ops-orders-summary",
    ),
    path(
        "payments/webhook/",
        PaymentWebhookView.as_view(),
        name="api-payment-webhook",
    ),
    path("schema/", schema_view, name="api-schema"),
]
