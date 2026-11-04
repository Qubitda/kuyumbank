from django.db.models.signals import post_save
from django.dispatch import receiver

from .kullanici import Kullanici
from .role_services import sync_user_role_groups


@receiver(post_save, sender=Kullanici)
def keep_role_group_in_sync(sender, instance, **kwargs):
    sync_user_role_groups(instance)
