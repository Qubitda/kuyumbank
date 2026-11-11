"""Firma kullanıcı daveti — ADR-0028."""

from __future__ import annotations

import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from firmalar import roles
from firmalar.models import Firma, FirmaInvite
from firmalar.role_permissions import P
from firmalar.services.audit_servisi import (
    domain_atomic,
    record_audit,
    record_audit_durable,
)
from firmalar.services.email_verify_servisi import mark_verified
from firmalar.services.rol_servisi import sync_user_role_groups
from firmalar.services.yetki_servisi import can_manage_all_users, has_perm

logger = logging.getLogger(__name__)
User = get_user_model()


def _invite_ttl_hours() -> int:
    return int(getattr(settings, "INVITE_TTL_HOURS", 72) or 72)


def _assert_rol_for_firma(firma: Firma, rol: str) -> None:
    if rol not in roles.ALL_ROLES:
        raise ValidationError({"rol": "Geçersiz rol."})
    if rol in roles.PLATFORM_ROLLERI and not firma.platform_mu:
        raise ValidationError({"rol": "Platform rolü yalnız platform firmasına."})
    if rol in roles.ALICI_ROLLERI and not firma.alici_mi:
        raise ValidationError({"rol": "Alıcı rolü yalnız alıcı firmaya."})
    if rol in roles.TEDARIKCI_ROLLERI and not firma.tedarikci_mi:
        raise ValidationError({"rol": "Tedarikçi rolü yalnız tedarikçi firmaya."})


def create_invite(
    *,
    actor,
    email: str,
    rol: str,
    firma: Firma | None = None,
) -> FirmaInvite:
    if actor is None or not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Kimlik gerekli.")

    email = (email or "").strip().lower()
    if not email:
        raise ValidationError({"email": "E-posta zorunlu."})
    rol = (rol or "").strip()

    target_firma = firma
    if can_manage_all_users(actor):
        if target_firma is None:
            raise ValidationError({"firma": "Platform davetinde firma zorunlu."})
    else:
        if not has_perm(actor, P["manage_users"]):
            record_audit_durable(
                actor=actor,
                action="firmalar.invite.denied",
                entity_type="FirmaInvite",
                entity_id="",
                success=False,
                reason="manage_users yok",
            )
            raise PermissionDenied("Davet için manage_users gerekir.")
        target_firma = actor.firma
        if target_firma is None:
            raise ValidationError("Aktör firması yok.")
        if firma is not None and firma.pk != target_firma.pk:
            raise PermissionDenied("Yalnız kendi firmanıza davet.")

    if rol in roles.PLATFORM_ROLLERI and not can_manage_all_users(actor):
        raise PermissionDenied("Platform rolü daveti yalnız manage_all_users.")

    _assert_rol_for_firma(target_firma, rol)

    if User.objects.filter(email__iexact=email, firma_id=target_firma.pk).exists():
        raise ValidationError({"email": "Bu e-posta zaten bu firmada kayıtlı."})

    # Bekleyen eski daveti iptal et (unique pending)
    FirmaInvite.objects.filter(
        firma=target_firma, email__iexact=email, kabul_edildi_at__isnull=True
    ).delete()

    token = secrets.token_urlsafe(32)[:64]
    expires = timezone.now() + timedelta(hours=_invite_ttl_hours())

    with domain_atomic():
        inv = FirmaInvite.objects.create(
            firma=target_firma,
            email=email,
            rol=rol,
            token=token,
            expires_at=expires,
            olusturan=actor,
        )
        record_audit(
            actor=actor,
            action="firmalar.invite.created",
            entity_type="FirmaInvite",
            entity_id=str(inv.pk),
            success=True,
            detail={"firma_id": target_firma.pk, "rol": rol},
        )

    base = (getattr(settings, "PASSWORD_RESET_BASE_URL", "") or "").strip().rstrip(
        "/"
    )
    if base:
        link = f"{base}/accept-invite?token={token}"
    else:
        link = f"/api/v1/auth/invites/accept/ token={token}"
    try:
        send_mail(
            subject="Kuyumbank firma daveti",
            message=(
                f"{target_firma.ad} firmasına davet edildiniz (rol: {rol}).\n"
                f"Kabul: {link}\n"
                f"Geçerlilik: {_invite_ttl_hours()} saat.\n"
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None)
            or "webmaster@localhost",
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("invite mail failed invite_id=%s", inv.pk)

    return inv


def accept_invite(
    *,
    token: str,
    username: str,
    password: str,
    password_confirm: str,
) -> User:
    token = (token or "").strip()
    username = (username or "").strip()
    if not token:
        raise ValidationError({"token": "Token zorunlu."})
    if not username:
        raise ValidationError({"username": "Kullanıcı adı zorunlu."})
    if password != password_confirm:
        raise ValidationError({"password_confirm": "Şifreler eşleşmiyor."})

    inv = (
        FirmaInvite.objects.select_related("firma")
        .filter(token=token, kabul_edildi_at__isnull=True)
        .first()
    )
    if inv is None:
        raise ValidationError("Geçersiz veya kullanılmış davet.")
    if inv.is_expired:
        raise ValidationError("Davetin süresi dolmuş.")

    if User.objects.filter(username__iexact=username).exists():
        raise ValidationError({"username": "Kullanıcı adı kullanımda."})

    validate_password(password)

    with transaction.atomic():
        locked = FirmaInvite.objects.select_for_update().get(pk=inv.pk)
        if locked.kabul_edildi_at is not None:
            raise ValidationError("Davet zaten kabul edilmiş.")
        if locked.is_expired:
            raise ValidationError("Davetin süresi dolmuş.")

        user = User(
            username=username,
            email=locked.email,
            firma=locked.firma,
            rol=locked.rol,
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        user.set_password(password)
        # assign_user_role actor olarak kendini kullanamayız; bootstrap:
        user.save()
        sync_user_role_groups(user)
        mark_verified(user)

        locked.kabul_edildi_at = timezone.now()
        locked.kabul_eden = user
        locked.save(update_fields=["kabul_edildi_at", "kabul_eden"])

        record_audit_durable(
            actor=user,
            action="firmalar.invite.accepted",
            entity_type="FirmaInvite",
            entity_id=str(locked.pk),
            success=True,
            reason="accepted",
            detail={"firma_id": locked.firma_id, "user_id": user.pk},
        )
    return user
