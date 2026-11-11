from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from bildirim.models import SmtpSettings
from bildirim.services import smtp_servisi
from bildirim.services.smtp_servisi import MASK


class SmtpSettingsForm(forms.ModelForm):
    password = forms.CharField(
        label="SMTP parola",
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={"placeholder": MASK}),
        help_text="Boş bırakırsanız mevcut parola korunur.",
    )

    class Meta:
        model = SmtpSettings
        fields = (
            "enabled",
            "host",
            "port",
            "encryption",
            "username",
            "password",
            "from_name",
            "from_email",
            "reply_to",
            "max_attempts",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and smtp_servisi.password_is_set(self.instance):
            self.fields["password"].help_text = (
                f"Parola kayıtlı ({MASK}). Değiştirmek için yeni değer yazın."
            )

    def save(self, commit=True):
        obj = super().save(commit=False)
        smtp_servisi.set_password(obj, self.cleaned_data.get("password"))
        if commit:
            obj.save()
        return obj


@admin.register(SmtpSettings)
class SmtpSettingsAdmin(admin.ModelAdmin):
    form = SmtpSettingsForm
    list_display = ("host", "port", "encryption", "from_email", "enabled")
    actions = ("action_test_email",)

    def has_add_permission(self, request):
        if SmtpSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return request.user.has_perm("bildirim.manage_smtp") or request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    @admin.action(description="Test e-posta gönder (kendi e-postanıza)")
    def action_test_email(self, request, queryset):
        to = (getattr(request.user, "email", None) or "").strip()
        if not to:
            self.message_user(request, "Kullanıcı e-postası yok.", level=messages.ERROR)
            return
        try:
            smtp_servisi.test_connection(to_email=to)
            self.message_user(request, f"Test gönderildi: {to}", level=messages.SUCCESS)
        except ValidationError as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
