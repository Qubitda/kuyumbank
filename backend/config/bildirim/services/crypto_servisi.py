"""SMTP parola sealed storage — SECRET_KEY türevi (ek bağımlılık yok)."""

from __future__ import annotations

from django.conf import settings
from django.core import signing

_SALT = "bildirim.smtp.password.v1"


def seal_password(plain: str) -> str:
    if plain is None:
        return ""
    plain = str(plain)
    if not plain:
        return ""
    return signing.dumps(plain, salt=_SALT, compress=True)


def unseal_password(sealed: str) -> str:
    if not sealed:
        return ""
    try:
        return str(signing.loads(sealed, salt=_SALT))
    except signing.BadSignature:
        return ""


def has_usable_secret() -> bool:
    return bool(getattr(settings, "SECRET_KEY", None))
