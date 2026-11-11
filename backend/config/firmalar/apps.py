from django.apps import AppConfig


class FirmalarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "firmalar"
    verbose_name = "Firmalar"

    def ready(self) -> None:
        from django.contrib import admin

        from firmalar.admin.auth_forms import AdminAuthenticationForm
        from firmalar.services import outbox_servisi

        # F7 EDI punchout: inbound kabul edildi; dış tüketici yok → ack-only.
        outbox_servisi.register_ack_handler("edi.punchout.inbound")
        admin.site.login_form = AdminAuthenticationForm
