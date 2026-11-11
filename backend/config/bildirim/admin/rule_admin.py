from django.contrib import admin

from bildirim.models import NotificationRule


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    list_display = (
        "event_type",
        "template",
        "recipient_mode",
        "enabled",
        "guncelleme_tarihi",
    )
    list_filter = ("enabled", "recipient_mode", "event_type")
    search_fields = ("event_type", "aciklama", "template__kod")
    autocomplete_fields = ("template",)
    list_select_related = ("template",)

    def has_module_permission(self, request):
        return (
            request.user.has_perm("bildirim.manage_notification_rule")
            or request.user.is_superuser
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)
