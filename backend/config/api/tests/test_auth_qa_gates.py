"""QA kapıları: login firma/aktif, şifre reset/change, MFA OTP."""

from __future__ import annotations

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from firmalar import roles
from firmalar.models import Firma, Kullanici
from firmalar.services import mfa_servisi, sifre_servisi
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    MFA_ENFORCE_PLATFORM=False,
    PASSWORD_RESET_TIMEOUT=3600,
)
class AuthGateLoginTests(TestCase):
    def setUp(self):
        self.api = APIClient(enforce_csrf_checks=False)
        self.firma = Firma.objects.create(
            ad="Alıcı QA",
            firma_kodu="QAAL1",
            vergi_no="3333333333",
            alici_mi=True,
            onay_durumu="onayli",
            aktif=True,
        )
        self.user = Kullanici(
            username="qa_buyer",
            email="qa_buyer@example.com",
            firma=self.firma,
            rol=roles.ALICI_SATINALMACI,
        )
        self.user.set_password("SecurePass12!")
        self.user.save()
        sync_user_role_groups(self.user)

    def _login(self, username="qa_buyer", password="SecurePass12!"):
        return self.api.post(
            reverse("api-auth-login"),
            {"username": username, "password": password},
            format="json",
        )

    def test_login_ok(self):
        res = self._login()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["username"], "qa_buyer")

    def test_inactive_user_denied(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        res = self._login()
        self.assertEqual(res.status_code, 401)

    def test_unapproved_firma_denied(self):
        self.firma.onay_durumu = "bekliyor"
        self.firma.save(update_fields=["onay_durumu"])
        res = self._login()
        self.assertEqual(res.status_code, 403)

    def test_inactive_firma_denied(self):
        self.firma.aktif = False
        self.firma.save(update_fields=["aktif"])
        res = self._login()
        self.assertEqual(res.status_code, 403)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    MFA_ENFORCE_PLATFORM=False,
)
class PasswordResetChangeTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        # Full-suite: login-scope LocMem throttle kovası diğer testlerden dolabilir → 429
        cache.clear()
        self.api = APIClient(enforce_csrf_checks=False)
        self.firma = Firma.objects.create(
            ad="Alıcı QA2",
            firma_kodu="QAAL2",
            vergi_no="4444444444",
            alici_mi=True,
            onay_durumu="onayli",
            aktif=True,
        )
        self.user = Kullanici(
            username="qa_pwd",
            email="qa_pwd@example.com",
            firma=self.firma,
            rol=roles.ALICI_SATINALMACI,
        )
        self.user.set_password("SecurePass12!")
        self.user.save()
        sync_user_role_groups(self.user)

    def test_reset_request_same_message_unknown_email(self):
        r1 = self.api.post(
            reverse("api-auth-password-reset"),
            {"email": "qa_pwd@example.com"},
            format="json",
        )
        r2 = self.api.post(
            reverse("api-auth-password-reset"),
            {"email": "nobody@example.com"},
            format="json",
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r1.data["detail"], r2.data["detail"])
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_confirm_and_reuse_fails(self):
        sifre_servisi.request_password_reset(email="qa_pwd@example.com")
        self.assertEqual(len(mail.outbox), 1)
        # Token üret (servis içi generator)
        from django.contrib.auth.tokens import PasswordResetTokenGenerator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = PasswordResetTokenGenerator().make_token(self.user)
        res = self.api.post(
            reverse("api-auth-password-reset-confirm"),
            {
                "uid": uid,
                "token": token,
                "new_password": "NewerPass12!x",
                "new_password_confirm": "NewerPass12!x",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewerPass12!x"))
        # reuse
        res2 = self.api.post(
            reverse("api-auth-password-reset-confirm"),
            {
                "uid": uid,
                "token": token,
                "new_password": "AnotherPass12!",
                "new_password_confirm": "AnotherPass12!",
            },
            format="json",
        )
        self.assertEqual(res2.status_code, 400)

    def test_change_requires_current_password(self):
        self.api.force_authenticate(user=self.user)
        bad = self.api.post(
            reverse("api-auth-password-change"),
            {
                "current_password": "wrong",
                "new_password": "NewerPass12!x",
                "new_password_confirm": "NewerPass12!x",
            },
            format="json",
        )
        self.assertEqual(bad.status_code, 400)
        ok = self.api.post(
            reverse("api-auth-password-change"),
            {
                "current_password": "SecurePass12!",
                "new_password": "NewerPass12!x",
                "new_password_confirm": "NewerPass12!x",
            },
            format="json",
        )
        self.assertEqual(ok.status_code, 200)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    MFA_ENFORCE_PLATFORM=True,
)
class MfaPlatformTests(TestCase):
    def setUp(self):
        self.api = APIClient(enforce_csrf_checks=False)
        plat = ensure_platform_firma()
        self.admin = Kullanici(
            username="qa_plat",
            email="qa_plat@example.com",
            firma=plat,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        self.admin.set_password("SecurePass12!")
        self.admin.save()
        sync_user_role_groups(self.admin)

    def test_login_requires_mfa_then_verify(self):
        res = self.api.post(
            reverse("api-auth-login"),
            {"username": "qa_plat", "password": "SecurePass12!"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data.get("mfa_required"))
        self.assertEqual(len(mail.outbox), 1)
        import re

        m = re.search(r"kodunuz:\s*(\d{6})", mail.outbox[0].body)
        self.assertIsNotNone(m)
        code = m.group(1)
        # me blocked until MFA (problem+json)
        me = self.api.get(reverse("api-me"))
        self.assertEqual(me.status_code, 403)
        self.assertIn("application/problem+json", me.get("Content-Type", ""))
        self.assertEqual(me.json().get("code"), "mfa_required")
        ver = self.api.post(
            reverse("api-auth-mfa-verify"),
            {"code": code},
            format="json",
        )
        self.assertEqual(ver.status_code, 200)
        self.assertTrue(ver.data.get("mfa_ok"))
        me2 = self.api.get(reverse("api-me"))
        self.assertEqual(me2.status_code, 200)
