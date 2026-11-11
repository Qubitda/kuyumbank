"""Act-as (impersonation) — ADR-0021.

Session anahtarları middleware tarafından okunur; login oturumu aktörde kalır.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

from firmalar.role_permissions import P
from firmalar.services.audit_servisi import record_audit, record_audit_durable
from firmalar.services.yetki_servisi import has_perm, require_perm

User = get_user_model()

SESSION_ACTOR = "act_as_actor_id"
SESSION_TARGET = "act_as_target_id"
P_ACT_AS = P["act_as_user"]


def act_as_aktif_mi(session) -> bool:
    return bool(session.get(SESSION_ACTOR) and session.get(SESSION_TARGET))


def baslat(*, actor, target, session) -> User:
    """Act-as başlat. `session` = request.session."""
    try:
        require_perm(actor, P_ACT_AS, message="Act-as yetkisi yok.")
    except PermissionDenied as exc:
        record_audit_durable(
            actor=actor,
            action="user.act_as_start",
            entity_type="Kullanici",
            entity_id=str(getattr(target, "pk", "") or ""),
            success=False,
            reason="yetki_yok",
        )
        raise exc

    if act_as_aktif_mi(session):
        record_audit_durable(
            actor=actor,
            action="user.act_as_start",
            entity_type="Kullanici",
            entity_id=str(getattr(target, "pk", "") or ""),
            success=False,
            reason="zaten_aktif",
        )
        raise ValidationError("Önce mevcut act-as oturumunu sonlandırın.")

    if target is None or not getattr(target, "pk", None):
        raise ValidationError("Hedef kullanıcı gerekli.")
    if target.pk == actor.pk:
        raise ValidationError("Kendiniz olarak act-as yapılamaz.")
    if not target.is_active:
        raise ValidationError("Pasif kullanıcı için act-as yok.")

    from firmalar.services import mfa_servisi

    mfa_servisi.assert_mfa_for_act_as(actor=actor, session=session)

    session[SESSION_ACTOR] = actor.pk
    session[SESSION_TARGET] = target.pk
    session.modified = True
    record_audit(
        actor=actor,
        action="user.act_as_start",
        entity_type="Kullanici",
        entity_id=str(target.pk),
        success=True,
        detail={
            "target_username": target.username,
            "target_firma_id": target.firma_id,
            "target_rol": target.rol,
        },
    )
    return target


def durdur(*, session, actor_fallback=None) -> User | None:
    """Act-as bitir; aktör Kullanici döner (varsa)."""
    actor_id = session.get(SESSION_ACTOR)
    target_id = session.get(SESSION_TARGET)
    actor = None
    if actor_id:
        actor = User.objects.filter(pk=actor_id).first() or actor_fallback
    session.pop(SESSION_ACTOR, None)
    session.pop(SESSION_TARGET, None)
    session.modified = True
    if actor is not None:
        record_audit(
            actor=actor,
            action="user.act_as_stop",
            entity_type="Kullanici",
            entity_id=str(target_id or ""),
            success=True,
        )
    return actor


def portal_hedef_url(user) -> str:
    """Act-as sonrası yönlendirme — FE base veya Admin (ADR-0029; HTML portal yok)."""
    from django.conf import settings

    base = (getattr(settings, "FRONTEND_PORTAL_BASE_URL", "") or "").strip().rstrip(
        "/"
    )
    if base:
        return f"{base}/"
    # FE yoksa operatör Admin'de kalır (hedef staff değilse yine Admin; API kullanır)
    return "/admin/"
