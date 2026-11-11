from bildirim.admin import (  # noqa: F401 — register side effects
    delivery_admin,
    recipient_admin,
    rule_admin,
    smtp_admin,
    template_admin,
)
from bildirim.admin.manual_views import get_manual_urls, manual_send_view

__all__ = ["manual_send_view", "get_manual_urls"]


def patch_admin_urls() -> None:
    """Idempotent AdminSite URL patch (apps.ready)."""
    from django.contrib import admin

    if getattr(admin.site, "_bildirim_urls_patched", False):
        return
    original = admin.site.get_urls

    def _bildirim_get_urls():
        return get_manual_urls() + original()

    admin.site.get_urls = _bildirim_get_urls
    admin.site._bildirim_urls_patched = True
