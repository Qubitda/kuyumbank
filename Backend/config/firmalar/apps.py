from django.apps import AppConfig


class FirmalarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "firmalar"

    def ready(self):
        from . import signals  # noqa: F401
