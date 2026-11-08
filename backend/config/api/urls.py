from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.schemas import get_schema_view

from api.views import CartDetailView, HealthView, MeView, OrderDetailView

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
    path("carts/<int:pk>/", CartDetailView.as_view(), name="api-cart-detail"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="api-order-detail"),
    path("schema/", schema_view, name="api-schema"),
]
