"""Admin login — aynı firma/aktif kapısı (auth_gate_servisi)."""

from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from firmalar.services.auth_gate_servisi import assert_user_may_login


class AdminAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        try:
            assert_user_may_login(user)
        except ValidationError as exc:
            raise ValidationError(exc.messages if hasattr(exc, "messages") else [str(exc)])
