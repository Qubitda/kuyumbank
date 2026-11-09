"""Session auth: anonim → None (401); CSRF yalnız kimlikli oturumda."""

from rest_framework.authentication import SessionAuthentication as DRFSessionAuthentication


class SessionAuthentication(DRFSessionAuthentication):
    """Anonim kullanıcıda CSRF/auth deneme yok — NotAuthenticated (401).

    DRF, ilk authenticator `authenticate_header` döndürmezse 401'i 403'e zorlar.
    Session birincil olduğu için buradan sabit bir challenge döneriz (NX-1: 401/403 ayrımı).
    """

    def authenticate(self, request):
        django_user = getattr(request._request, "user", None)
        if django_user is None or not getattr(django_user, "is_authenticated", False):
            return None
        return super().authenticate(request)

    def authenticate_header(self, request):
        return "Session"


def enforce_csrf(request) -> None:
    """DRF APIView csrf_exempt olduğu için yazma uçlarında açık CSRF kontrolü."""
    SessionAuthentication().enforce_csrf(request)
