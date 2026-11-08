from django.apps import AppConfig


class FiyatlamaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fiyatlama"
    verbose_name = "Fiyatlama"

    def ready(self):
        import fiyatlama.admin  # noqa: F401 — admin kayıtlarını yükle
