from django.contrib.auth.views import LogoutView
from django.urls import path

from siparis.views.supplier_ui import (
    SupplierHomeView,
    SupplierLoginView,
    SupplierOfferListView,
    SupplierRfqListView,
    SupplierStockListView,
)

urlpatterns = [
    path("login/", SupplierLoginView.as_view(), name="supplier-login"),
    path(
        "logout/",
        LogoutView.as_view(next_page="supplier-login"),
        name="supplier-logout",
    ),
    path("", SupplierHomeView.as_view(), name="supplier-home"),
    path("offers/", SupplierOfferListView.as_view(), name="supplier-offers"),
    path("stock/", SupplierStockListView.as_view(), name="supplier-stock"),
    path("rfqs/", SupplierRfqListView.as_view(), name="supplier-rfqs"),
]
