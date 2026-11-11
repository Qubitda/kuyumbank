"""E-posta OTP MFA — platform kullanıcıları / act-as (MFA_ENFORCE_PLATFORM).

Harici TOTP kütüphanesi yok; 6 haneli OTP cache'te hash'lenir.
"""

from __future__ import annotations

import hashlib
import logging
import secrets

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail

from firmalar import roles
from firmalar.services.audit_servisi import record_audit_durable

logger = logging.getLogger(__name__)

SESSION_MFA_OK = "mfa_ok"
_OTP_PREFIX = "mfa_otp:"
_OTP_TTL = 600  # 10 dk


def mfa_enforce_enabled() -> bool:
    return bool(getattr(settings, "MFA_ENFORCE_PLATFORM", False))


def user_requires_mfa(user) -> bool:
    if not mfa_enforce_enabled():
        return False
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    rol = getattr(user, "rol", "") or ""
    return rol in roles.PLATFORM_ROLLERI


def session_mfa_ok(session) -> bool:
    return bool(session.get(SESSION_MFA_OK))


def mark_mfa_ok(session) -> None:
    session[SESSION_MFA_OK] = True
    session.modified = True


def clear_mfa(session) -> None:
    session.pop(SESSION_MFA_OK, None)
    session.modified = True


def _otp_cache_key(user_id: int) -> str:
    return f"{_OTP_PREFIX}{user_id}"


def _hash_otp(code: str) -> str:
    secret = getattr(settings, "SECRET_KEY", "") or ""
    raw = f"{secret}:{code}".encode()
    return hashlib.sha256(raw).hexdigest()


def issue_email_otp(*, user) -> None:
    """OTP üretir, cache'e yazar, e-posta gönderir. Kod loglanmaz."""
    email = (getattr(user, "email", None) or "").strip()
    if not email:
        raise ValidationError("MFA için kullanıcı e-postası zorunlu.")
    code = f"{secrets.randbelow(1_000_000):06d}"
    cache.set(_otp_cache_key(user.pk), _hash_otp(code), _OTP_TTL)
    try:
        send_mail(
            subject="Kuyumbank doğrulama kodu",
            message=(
                f"Doğrulama kodunuz: {code}\n"
                "Kod on dakika icinde gecersiz olur."
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None)
            or "webmaster@localhost",
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("mfa otp mail failed user_id=%s", user.pk)
        raise ValidationError("Doğrulama kodu gönderilemedi.")


def verify_email_otp(*, user, code: str, session) -> None:
    code = (code or "").strip()
    if len(code) != 6 or not code.isdigit():
        raise ValidationError({"code": "6 haneli kod gerekli."})
    stored = cache.get(_otp_cache_key(user.pk))
    if not stored or stored != _hash_otp(code):
        record_audit_durable(
            actor=user,
            action="user.mfa_verify",
            entity_type="Kullanici",
            entity_id=str(user.pk),
            success=False,
            reason="bad_otp",
        )
        raise ValidationError({"code": "Kod geçersiz veya süresi dolmuş."})
    cache.delete(_otp_cache_key(user.pk))
    mark_mfa_ok(session)
    record_audit_durable(
        actor=user,
        action="user.mfa_verify",
        entity_type="Kullanici",
        entity_id=str(user.pk),
        success=True,
        reason="ok",
    )


def assert_mfa_for_act_as(*, actor, session) -> None:
    if not user_requires_mfa(actor):
        return
    if not session_mfa_ok(session):
        raise ValidationError(
            "Act-as için MFA doğrulaması gerekli (e-posta OTP)."
        )
