"""Kullanıcı iş rolü atama — tek yazma noktası (ADR-0003, ADR-0006 B2)."""

from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .. import roles
from ..role_permissions import P
from .audit_servisi import record_audit, record_audit_durable
from .yetki_servisi import can_manage_all_users, require_perm


def role_group_name(role):
    return roles.role_group_name(role)


@transaction.atomic
def sync_user_role_groups(user):
    """Kullanıcının rol gruplarını `rol` alanıyla eşitler."""
    role_groups = Group.objects.filter(name__startswith=roles.ROLE_GROUP_PREFIX)
    user.groups.remove(*role_groups)

    if not user.firma_id or not user.rol:
        return

    group, _ = Group.objects.get_or_create(name=role_group_name(user.rol))
    user.groups.add(group)


def _deny_assign(actor, *, user, exc, reason, detail=None):
    record_audit_durable(
        actor=actor,
        action="user.assign_role",
        entity_type="Kullanici",
        entity_id=getattr(user, "pk", "") or "",
        success=False,
        reason=reason,
        detail=detail or {},
    )
    raise exc


def assign_user_role(*, actor, user, firma, rol):
    """Tek firma + tek rol; actor=değiştiren; perm + tenant (ADR-0006 B2)."""
    if actor is None:
        _deny_assign(
            actor,
            user=user,
            exc=ValidationError("Rol ataması için aktör zorunludur."),
            reason="aktor_yok",
        )

    if can_manage_all_users(actor):
        pass
    else:
        try:
            require_perm(actor, P["manage_users"])
        except PermissionDenied as exc:
            _deny_assign(actor, user=user, exc=exc, reason="yetki_yok")

        if firma is None or firma.pk != getattr(actor, "firma_id", None):
            _deny_assign(
                actor,
                user=user,
                exc=PermissionDenied("Yalnız kendi firmanızdaki kullanıcılara rol atayabilirsiniz."),
                reason="tenant_firma",
            )
        if user.pk and user.firma_id and user.firma_id != actor.firma_id:
            _deny_assign(
                actor,
                user=user,
                exc=PermissionDenied("Başka firma kullanıcısına işlem yapılamaz."),
                reason="tenant_hedef",
            )
        # Firma değişikliği yalnız platform
        if user.pk and user.firma_id and firma.pk != user.firma_id:
            _deny_assign(
                actor,
                user=user,
                exc=PermissionDenied("Firma değişikliği yalnız platform yetkilisinindir."),
                reason="firma_degisikligi_yasak",
            )
        if rol in roles.PLATFORM_ROLLERI:
            _deny_assign(
                actor,
                user=user,
                exc=PermissionDenied("Platform rolü atanamaz."),
                reason="platform_rol_yasak",
            )

    if not firma:
        _deny_assign(
            actor,
            user=user,
            exc=ValidationError("Firma zorunludur."),
            reason="firma_yok",
        )
    if rol not in roles.ALL_ROLES:
        _deny_assign(
            actor,
            user=user,
            exc=ValidationError("Geçersiz rol."),
            reason="gecersiz_rol",
        )

    eski = {"firma_id": user.firma_id, "rol": user.rol}
    with transaction.atomic():
        user.firma = firma
        user.rol = rol
        user.save()
        sync_user_role_groups(user)
        record_audit(
            actor=actor,
            action="user.assign_role",
            entity_type="Kullanici",
            entity_id=user.pk,
            success=True,
            detail={
                "eski": eski,
                "yeni": {"firma_id": firma.pk, "rol": rol},
                "hedef_user_id": user.pk,
                "hedef_username": user.username,
            },
        )
    return user
