"""E-posta doğrulama token — ADR-0028."""

from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from firmalar.services.audit_servisi import record_audit_durable

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailVerifyTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "firmalar.email_verify.v1"

    def _make_hash_value(self, user, timestamp):
        email = getattr(user, "email", "") or ""
        verified = "" if user.email_verified_at is None else str(user.email_verified_at)
        return f"{user.pk}{user.password}{email}{verified}{timestamp}"


_token_gen = EmailVerifyTokenGenerator()

VERIFY_REQUEST_MSG = (
    "Eğer hesap varsa doğrulama bağlantısı e-posta ile gönderildi."
)


def is_email_verified(user) -> bool:
    return bool(getattr(user, "email_verified_at", None))


def email_verify_required_for_write() -> bool:
    return bool(getattr(settings, "EMAIL_VERIFY_REQUIRED_FOR_WRITE", False))


def assert_email_verified_for_write(user) -> None:
    if not email_verify_required_for_write():
        return
    if is_email_verified(user):
        return
    raise ValidationError("E-posta doğrulaması gerekli.")


def mark_verified(user) -> None:
    if user.email_verified_at is not None:
        return
    user.email_verified_at = timezone.now()
    user.save(update_fields=["email_verified_at"])


def request_verification(*, email: str = "", user=None) -> str:
    """Enumeration-safe: her zaman aynı mesaj."""
    targets = []
    if user is not None and getattr(user, "pk", None):
        targets = [user]
    else:
        email = (email or "").strip().lower()
        if not email:
            raise ValidationError({"email": "E-posta zorunlu."})
        targets = list(
            User.objects.filter(email__iexact=email, is_active=True)[:5]
        )

    base = (getattr(settings, "PASSWORD_RESET_BASE_URL", "") or "").strip().rstrip(
        "/"
    )
    for u in targets:
        if not (u.email or "").strip():
            continue
        if is_email_verified(u):
            continue
        uid = urlsafe_base64_encode(force_bytes(u.pk))
        token = _token_gen.make_token(u)
        if base:
            link = f"{base}/verify-email?uid={uid}&token={token}"
        else:
            link = f"/api/v1/auth/email-verify/confirm/ uid={uid} token={token}"
        try:
            send_mail(
                subject="Kuyumbank e-posta doğrulama",
                message=f"E-postanızı doğrulamak için:\n{link}\n",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None)
                or "webmaster@localhost",
                recipient_list=[u.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("email verify mail failed user_id=%s", u.pk)
    return VERIFY_REQUEST_MSG


def confirm_verification(*, uidb64: str, token: str) -> User:
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
        raise ValidationError("Geçersiz veya süresi dolmuş bağlantı.") from exc
    if not user.is_active:
        raise ValidationError("Geçersiz veya süresi dolmuş bağlantı.")
    if not _token_gen.check_token(user, token):
        raise ValidationError("Geçersiz veya süresi dolmuş bağlantı.")
    mark_verified(user)
    record_audit_durable(
        actor=user,
        action="user.email_verified",
        entity_type="Kullanici",
        entity_id=str(user.pk),
        success=True,
        reason="confirm",
    )
    return user
