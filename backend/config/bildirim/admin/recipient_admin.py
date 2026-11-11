from django.contrib import admin

from bildirim.models import RecipientSettings


@admin.register(RecipientSettings)
class RecipientSettingsAdmin(admin.ModelAdmin):
    list_display = ("__str__", "guncelleme_tarihi")
    fields = ("admin_notify_emails", "default_bcc")

    def has_add_permission(self, request):
        if RecipientSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return (
            request.user.has_perm("bildirim.manage_smtp")
            or request.user.has_perm("bildirim.manage_notification_rule")
            or request.user.is_superuser
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)
