"""Login / oturum kapıları — pasif kullanıcı, pasif/onaysız firma."""

from __future__ import annotations

from django.core.exceptions import ValidationError


def assert_user_may_login(user) -> None:
    """Kimlik doğrulandıktan sonra oturum açmadan önce çağrılır.

    - is_active
    - firma zorunlu
    - firma.aktif
    - platform dışı: onay_durumu == onayli
    """
    if user is None:
        raise ValidationError("Kimlik doğrulanamadı.")
    if not getattr(user, "is_active", False):
        raise ValidationError("Hesap pasif.")
    firma = getattr(user, "firma", None)
    if firma is None or not getattr(user, "firma_id", None):
        raise ValidationError("Firma bağlamı gerekli.")
    if not getattr(firma, "aktif", False):
        raise ValidationError("Firma pasif; giriş yok.")
    if getattr(firma, "platform_mu", False):
        return
    if getattr(firma, "onay_durumu", None) != "onayli":
        raise ValidationError("Firma henüz onaylı değil; giriş yok.")
