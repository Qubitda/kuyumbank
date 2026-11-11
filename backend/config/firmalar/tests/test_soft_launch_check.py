"""soft_launch_check — odaklı; secret basılmaz."""

from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings


class SoftLaunchCheckTests(TestCase):
    @override_settings(
        DEBUG=True,
        MFA_ENFORCE_PLATFORM=False,
        PAYMENT_PROVIDER="fake",
        CARRIER_PROVIDER="fake",
        ALLOW_FAKE_PROVIDERS=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        PASSWORD_RESET_BASE_URL="https://example.test",
    )
    def test_debug_sandbox_passes(self):
        out = StringIO()
        call_command("soft_launch_check", "--allow-fake", stdout=out)
        self.assertIn("errors=0", out.getvalue())

    @override_settings(
        DEBUG=False,
        ALLOWED_HOSTS=["app.example.test"],
        MFA_ENFORCE_PLATFORM=False,
        PAYMENT_PROVIDER="fake",
        CARRIER_PROVIDER="fake",
        ALLOW_FAKE_PROVIDERS=False,
        ALLOW_LOCMEM_CACHE=False,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "test-soft-launch",
            }
        },
    )
    def test_prod_locmem_without_allow_fails(self):
        with self.assertRaises(CommandError):
            call_command("soft_launch_check", stdout=StringIO())

    @override_settings(DEBUG=True, MFA_ENFORCE_PLATFORM=False)
    def test_require_mfa_fails_when_off(self):
        with self.assertRaises(CommandError):
            call_command(
                "soft_launch_check",
                "--allow-fake",
                "--require-mfa",
                stdout=StringIO(),
            )
