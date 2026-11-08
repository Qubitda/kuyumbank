"""Session auth: AnonymousUser'ı 'başarılı auth' sayma → korumalı rota 401."""

from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication


class SessionAuthentication(DRFSessionAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, auth = result
        if not getattr(user, "is_authenticated", False):
            return None
        return (user, auth)
