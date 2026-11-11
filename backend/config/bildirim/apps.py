from django.apps import AppConfig


class BildirimConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bildirim"
    verbose_name = "Bildirim"

    def ready(self) -> None:
        from bildirim.admin import patch_admin_urls
        from bildirim.services import dispatch_servisi

        dispatch_servisi.register_outbox_handlers()
        patch_admin_urls()
