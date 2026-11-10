"""API docs (Swagger/ReDoc/schema) erişim politikası.

- DEBUG veya API_DOCS_PUBLIC=True → AllowAny (yalnız geliştirme/staging şablonu)
- Prod: kimlikli + (staff | platform view_all)

Try it out gerçek `/api/v1/` uçlarına gider; permission atlanmaz.
"""

from __future__ import annotations

from django.conf import settings
from rest_framework.permissions import BasePermission, IsAuthenticated

from firmalar.services.yetki_servisi import can_view_all_tenants


class CanAccessApiDocs(BasePermission):
    message = "API dokümantasyonu bu ortamda kısıtlı."

    def has_permission(self, request, view) -> bool:
        if settings.DEBUG or getattr(settings, "API_DOCS_PUBLIC", False):
            return True
        user = request.user
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        if getattr(user, "is_staff", False):
            return True
        return can_view_all_tenants(user)


def docs_permission_classes() -> list:
    if settings.DEBUG or getattr(settings, "API_DOCS_PUBLIC", False):
        return [CanAccessApiDocs]
    return [IsAuthenticated, CanAccessApiDocs]
