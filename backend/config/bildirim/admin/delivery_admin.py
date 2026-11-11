from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from bildirim.models import EmailDelivery
from bildirim.services.queue_servisi import retry_delivery


@admin.register(EmailDelivery)
class EmailDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "event_type",
        "subject",
        "attempts",
        "order_id",
        "created_at",
        "sent_at",
    )
    list_filter = ("status", "event_type")
    search_fields = ("subject", "idempotency_key", "error", "to_emails")
    readonly_fields = (
        "to_emails",
        "cc_emails",
        "bcc_emails",
        "subject",
        "body_html",
        "status",
        "error",
        "attempts",
        "template",
        "rule",
        "event_type",
        "idempotency_key",
        "order_id",
        "related_refs",
        "attachment_notes",
        "sent_at",
        "created_at",
        "updated_at",
    )
    actions = ("action_retry",)

    def has_add_permission(self, request):
        return False

    def has_module_permission(self, request):
        return (
            request.user.has_perm("bildirim.view_email_log")
            or request.user.is_superuser
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        # Retry action için change gerekir
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="FAILED/PENDING yeniden dene (PENDING yap)")
    def action_retry(self, request, queryset):
        n = 0
        for row in queryset:
            try:
                retry_delivery(row)
                n += 1
            except ValidationError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
        self.message_user(request, f"{n} kayıt PENDING.", level=messages.SUCCESS)
