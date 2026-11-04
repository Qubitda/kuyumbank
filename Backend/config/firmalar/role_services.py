"""Kullanıcı iş rolü ile Django Group üyeliğini senkron tutan servisler."""

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction

from .kullanici import Kullanici

ROLE_GROUP_PREFIX = "rol:"


def role_group_name(role):
    return f"{ROLE_GROUP_PREFIX}{role}"


@transaction.atomic
def sync_user_role_groups(user):
    """Kullanıcının eski rol gruplarını kaldırıp yalnızca atanmış rol grubunu ekler.

    Firma/rol henüz tamamlanmamış eski kayıtlar için rol grupları temizlenir;
    böylece eksik tanımlı bir hesap eski grup yetkilerini taşımaz.
    """
    role_groups = Group.objects.filter(name__startswith=ROLE_GROUP_PREFIX)
    user.groups.remove(*role_groups)

    if not user.firma_id or not user.rol:
        return

    # Sinyal kayıt sonrasında çalışır: burada tam full_clean() çağırmak
    # username/email gibi alanların geçersizliği nedeniyle save() sonrasında
    # beklenmedik hata üretirdi. İş rolü-firma uyumunu kontrol edip fail-closed
    # davranıyoruz; dışarıdan atama yapan servis full_clean() çağırır.
    try:
        user.clean()
    except ValidationError:
        return

    group, _ = Group.objects.get_or_create(name=role_group_name(user.rol))
    user.groups.add(group)


@transaction.atomic
def assign_user_role(*, user, firma, rol):
    """Kullanıcının tek firma ve tek rol atamasını doğrulayarak uygular."""
    user.firma = firma
    user.rol = rol
    user.full_clean()
    user.save()  # post_save sinyali rol grubunu aynı transaction içinde eşitler.
    return user
