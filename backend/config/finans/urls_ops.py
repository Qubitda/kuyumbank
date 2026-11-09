from django.urls import path

from finans.views import OpsFinanceView

urlpatterns = [
    path("finance/", OpsFinanceView.as_view(), name="ops-finance"),
]
