from django.contrib.auth.views import LogoutView
from django.urls import path

from finans.views import BuyerFinanceView
from firmalar.views import BuyerApprovalActionView, BuyerApprovalListView
from siparis.views import (
    BuyerCartView,
    BuyerCheckoutView,
    BuyerLoginView,
    BuyerOrderDetailView,
    BuyerOrderListView,
    BuyerRfqCreateView,
    BuyerRfqDetailView,
    BuyerRfqListView,
    BuyerRfqMessageView,
    BuyerRfqRevisionView,
    BuyerRfqSendView,
)

urlpatterns = [
    path("login/", BuyerLoginView.as_view(), name="buyer-login"),
    path(
        "logout/",
        LogoutView.as_view(next_page="buyer-login"),
        name="buyer-logout",
    ),
    path("", BuyerCartView.as_view(), name="buyer-cart"),
    path("checkout/", BuyerCheckoutView.as_view(), name="buyer-checkout"),
    path("orders/", BuyerOrderListView.as_view(), name="buyer-order-list"),
    path(
        "orders/<int:pk>/",
        BuyerOrderDetailView.as_view(),
        name="buyer-order-detail",
    ),
    path("finance/", BuyerFinanceView.as_view(), name="buyer-finance"),
    # F10-014
    path("approvals/", BuyerApprovalListView.as_view(), name="buyer-approval-list"),
    path(
        "approvals/<int:pk>/action/",
        BuyerApprovalActionView.as_view(),
        name="buyer-approval-action",
    ),
    # F10-023 (+ F10-021 create)
    path("rfq/", BuyerRfqListView.as_view(), name="buyer-rfq-list"),
    path("rfq/new/", BuyerRfqCreateView.as_view(), name="buyer-rfq-create"),
    path("rfq/<int:pk>/", BuyerRfqDetailView.as_view(), name="buyer-rfq-detail"),
    path("rfq/<int:pk>/send/", BuyerRfqSendView.as_view(), name="buyer-rfq-send"),
    path(
        "rfq/<int:pk>/message/",
        BuyerRfqMessageView.as_view(),
        name="buyer-rfq-message",
    ),
    path(
        "rfq/<int:pk>/revision/",
        BuyerRfqRevisionView.as_view(),
        name="buyer-rfq-revision",
    ),
]
