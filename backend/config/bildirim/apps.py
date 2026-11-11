from django.apps import AppConfig


class BildirimConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bildirim"
    verbose_name = "Bildirim"

    def ready(self) -> None:
        from bildirim.services import dispatch_servisi

        dispatch_servisi.register_outbox_handlers()
