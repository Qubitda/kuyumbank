from django.apps import AppConfig


class TanimlarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tanimlar"
    verbose_name = "Tanımlar"

    def ready(self) -> None:
        from firmalar.services import outbox_servisi

        # CAP-ALERT: outbox kaydı bilinçli; canlı push henüz yok → ack-only.
        outbox_servisi.register_ack_handler("kur.alert")
