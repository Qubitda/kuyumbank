"""API yetki yardımcıları — tenant client `firma_id` güvenilmez (ADR-0003)."""

from rest_framework.permissions import BasePermission


class IsAuthenticatedWithFirma(BasePermission):
    """Oturum + tek firma bağlamı zorunlu."""

    message = "Kimlik ve firma bağlamı gerekli."

    def has_permission(self, request, view):
        user = request.user
        if user is None or not user.is_authenticated:
            return False
        return bool(getattr(user, "firma_id", None))
