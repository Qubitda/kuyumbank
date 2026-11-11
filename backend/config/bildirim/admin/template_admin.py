from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from bildirim.models import EmailTemplate
from bildirim.services import manual_servisi, template_servisi


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "aktif", "sistem_mi", "guncelleme_tarihi")
    list_filter = ("aktif", "sistem_mi")
    search_fields = ("kod", "ad", "subject")
    readonly_fields = ("sistem_mi",)
    actions = ("action_test_send",)

    def has_module_permission(self, request):
        return (
            request.user.has_perm("bildirim.manage_email_template")
            or request.user.is_superuser
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.sistem_mi:
            return False
        return self.has_module_permission(request)

    @admin.action(description="Önizleme context ile test kuyruğa al (kendi e-posta)")
    def action_test_send(self, request, queryset):
        to = (getattr(request.user, "email", None) or "").strip()
        if not to:
            self.message_user(request, "Kullanıcı e-postası yok.", level=messages.ERROR)
            return
        ctx = {
            "order_id": "0",
            "firma_adi": "Test Firma",
            "firma_kodu": "TEST",
            "user_email": to,
            "user_name": request.user.get_username(),
            "amount": "0",
            "currency": "TRY",
            "shipment_id": "0",
            "takip_no": "",
            "inspection_id": "0",
            "return_id": "0",
            "event_type": "manual",
            "reason": "admin-test",
            "line_count": "0",
            "document_notes": "",
            "platform_name": "Kuyumbank",
        }
        ok = 0
        for tpl in queryset:
            try:
                template_servisi.render_template(tpl, ctx)
                manual_servisi.enqueue_manual(
                    actor=request.user,
                    to_emails=[to],
                    template=tpl,
                    context=ctx,
                )
                ok += 1
            except (ValidationError, PermissionError) as exc:
                self.message_user(request, f"{tpl.kod}: {exc}", level=messages.ERROR)
        if ok:
            self.message_user(
                request,
                f"{ok} şablon kuyruğa alındı → process_email_queue.",
                level=messages.SUCCESS,
            )
