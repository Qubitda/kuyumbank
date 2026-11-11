"""Şifre sıfırlama + oturum içi şifre değişimi."""

from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from firmalar.services.audit_servisi import record_audit_durable

logger = logging.getLogger(__name__)
User = get_user_model()
_token_gen = PasswordResetTokenGenerator()

# Enumeration önleme: her zaman aynı genel mesaj
RESET_REQUEST_MSG = (
    "Eğer hesap varsa şifre sıfırlama bağlantısı e-posta ile gönderildi."
)


def _public_base_url() -> str:
    base = (getattr(settings, "PASSWORD_RESET_BASE_URL", None) or "").strip()
    if base:
        return base.rstrip("/")
    # Host header'a güvenme; boşsa relative path API istemcisine bırakılır
    return ""


def request_password_reset(*, email: str, request=None) -> str:
    """E-posta varsa token maili atar; yoksa da aynı mesajı döner (enumeration yok)."""
    email = (email or "").strip().lower()
    if not email:
        raise ValidationError({"email": "E-posta zorunlu."})

    users = list(
        User.objects.filter(email__iexact=email, is_active=True).select_related(
            "firma"
        )[:5]
    )
    base = _public_base_url()
    for user in users:
        if not user.email:
            continue
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = _token_gen.make_token(user)
        if base:
            link = f"{base}/reset-password?uid={uid}&token={token}"
        else:
            link = f"/api/v1/auth/password-reset/confirm/ (uid={uid} token={token})"
        try:
            send_mail(
                subject="Kuyumbank şifre sıfırlama",
                message=(
                    "Şifre sıfırlama talebi aldık.\n\n"
                    f"Bağlantı / bilgiler:\n{link}\n\n"
                    "Talep sizden değilse bu e-postayı yok sayın."
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None)
                or "webmaster@localhost",
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("password reset mail failed user_id=%s", user.pk)
            # Enumeration sızdırma: yine genel mesaj
    return RESET_REQUEST_MSG


def confirm_password_reset(
    *, uidb64: str, token: str, new_password: str, new_password_confirm: str
) -> User:
    if (new_password or "") != (new_password_confirm or ""):
        raise ValidationError({"new_password_confirm": "Şifreler eşleşmiyor."})
    if not (new_password or "").strip():
        raise ValidationError({"new_password": "Yeni şifre zorunlu."})

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
        raise ValidationError("Geçersiz veya süresi dolmuş bağlantı.") from exc

    if not user.is_active:
        raise ValidationError("Geçersiz veya süresi dolmuş bağlantı.")
    if not _token_gen.check_token(user, token):
        raise ValidationError("Geçersiz veya süresi dolmuş bağlantı.")

    validate_password(new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    record_audit_durable(
        actor=user,
        action="user.password_reset",
        entity_type="Kullanici",
        entity_id=str(user.pk),
        success=True,
        reason="reset_confirm",
    )
    return user


def change_password(
    *, actor, current_password: str, new_password: str, new_password_confirm: str
) -> User:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise ValidationError("Kimlik gerekli.")
    if not actor.check_password(current_password or ""):
        record_audit_durable(
            actor=actor,
            action="user.password_change",
            entity_type="Kullanici",
            entity_id=str(actor.pk),
            success=False,
            reason="current_password_wrong",
        )
        raise ValidationError({"current_password": "Mevcut şifre hatalı."})
    if (new_password or "") != (new_password_confirm or ""):
        raise ValidationError({"new_password_confirm": "Şifreler eşleşmiyor."})
    validate_password(new_password, user=actor)
    actor.set_password(new_password)
    actor.save(update_fields=["password"])
    record_audit_durable(
        actor=actor,
        action="user.password_change",
        entity_type="Kullanici",
        entity_id=str(actor.pk),
        success=True,
        reason="changed",
    )
    return actor
