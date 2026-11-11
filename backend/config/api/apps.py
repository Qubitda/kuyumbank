from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    verbose_name = "API (PRE ince yüzeyi)"

    def ready(self):
        # System checks (cache/throttle prod uyarısı)
        from config import checks  # noqa: F401
