from django.contrib.auth.views import LogoutView
from django.urls import path

from finans.views import BuyerFinanceView
from siparis.views import (
    BuyerCartView,
    BuyerCheckoutView,
    BuyerLoginView,
    BuyerOrderDetailView,
    BuyerOrderListView,
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
]
