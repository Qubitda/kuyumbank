"""ADR-0028 — davet + e-posta doğrulama (odaklı)."""

from __future__ import annotations

from datetime import timedelta
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient

from firmalar import roles
from firmalar.models import Firma, FirmaInvite, Kullanici
from firmalar.role_permissions import seed_role_permissions
from firmalar.services import email_verify_servisi, invite_servisi
from firmalar.services.email_verify_servisi import EmailVerifyTokenGenerator
from firmalar.services.rol_servisi import sync_user_role_groups


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    INVITE_TTL_HOURS=72,
    EMAIL_VERIFY_REQUIRED_FOR_WRITE=False,
    PASSWORD_RESET_BASE_URL="https://app.test",
)
class InviteServiceTests(TestCase):
    def setUp(self):
        seed_role_permissions()
        self.firma = Firma.objects.create(
            ad="Alıcı Inv",
            firma_kodu="INVAL1",
            vergi_no="4444444444",
            alici_mi=True,
            onay_durumu="onayli",
            aktif=True,
        )
        self.admin = Kullanici(
            username="inv_admin",
            email="inv_admin@example.com",
            firma=self.firma,
            rol=roles.ALICI_YONETICI,
        )
        self.admin.set_password("SecurePass12!")
        self.admin.save()
        sync_user_role_groups(self.admin)

    def test_create_and_accept_marks_email_verified(self):
        inv = invite_servisi.create_invite(
            actor=self.admin,
            email="newuser@example.com",
            rol=roles.ALICI_SATINALMACI,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(inv.token)
        user = invite_servisi.accept_invite(
            token=inv.token,
            username="new_buyer",
            password="SecurePass12!",
            password_confirm="SecurePass12!",
        )
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.firma_id, self.firma.pk)
        self.assertEqual(user.rol, roles.ALICI_SATINALMACI)
        self.assertIsNotNone(user.email_verified_at)
        inv.refresh_from_db()
        self.assertIsNotNone(inv.kabul_edildi_at)

    def test_expired_invite_rejected(self):
        inv = invite_servisi.create_invite(
            actor=self.admin,
            email="late@example.com",
            rol=roles.ALICI_SATINALMACI,
        )
        FirmaInvite.objects.filter(pk=inv.pk).update(
            expires_at=timezone.now() - timedelta(hours=1)
        )
        with self.assertRaises(Exception):
            invite_servisi.accept_invite(
                token=inv.token,
                username="late_user",
                password="SecurePass12!",
                password_confirm="SecurePass12!",
            )

    def test_buyer_cannot_invite_platform_rol(self):
        with self.assertRaises(Exception):
            invite_servisi.create_invite(
                actor=self.admin,
                email="plat@example.com",
                rol=roles.PLATFORM_SUPER,
            )


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_VERIFY_REQUIRED_FOR_WRITE=False,
)
class EmailVerifyServiceTests(TestCase):
    def setUp(self):
        self.firma = Firma.objects.create(
            ad="Alıcı Ev",
            firma_kodu="EVAL1",
            vergi_no="5555555555",
            alici_mi=True,
            onay_durumu="onayli",
            aktif=True,
        )
        self.user = Kullanici(
            username="ev_user",
            email="ev_user@example.com",
            firma=self.firma,
            rol=roles.ALICI_SATINALMACI,
        )
        self.user.set_password("SecurePass12!")
        self.user.save()
        sync_user_role_groups(self.user)

    def test_request_and_confirm(self):
        msg = email_verify_servisi.request_verification(user=self.user)
        self.assertIn("doğrulama", msg.lower())
        self.assertEqual(len(mail.outbox), 1)
        gen = EmailVerifyTokenGenerator()
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = gen.make_token(self.user)
        confirmed = email_verify_servisi.confirm_verification(
            uidb64=uid, token=token
        )
        self.assertTrue(email_verify_servisi.is_email_verified(confirmed))

    def test_enumeration_safe_unknown_email(self):
        msg = email_verify_servisi.request_verification(
            email="nobody@example.com"
        )
        self.assertEqual(msg, email_verify_servisi.VERIFY_REQUEST_MSG)
        self.assertEqual(len(mail.outbox), 0)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_VERIFY_REQUIRED_FOR_WRITE=False,
    PASSWORD_RESET_BASE_URL="https://app.test",
)
class InviteEmailVerifyApiTests(TestCase):
    def setUp(self):
        seed_role_permissions()
        self.api = APIClient(enforce_csrf_checks=False)
        self.firma = Firma.objects.create(
            ad="Alıcı Api",
            firma_kodu="APINV1",
            vergi_no="6666666666",
            alici_mi=True,
            onay_durumu="onayli",
            aktif=True,
        )
        self.admin = Kullanici(
            username="api_inv_admin",
            email="api_inv_admin@example.com",
            firma=self.firma,
            rol=roles.ALICI_YONETICI,
            email_verified_at=timezone.now(),
        )
        self.admin.set_password("SecurePass12!")
        self.admin.save()
        sync_user_role_groups(self.admin)

    def test_api_create_accept_me_flag(self):
        self.api.force_authenticate(user=self.admin)
        res = self.api.post(
            reverse("api-auth-invite-create"),
            {
                "email": "api_new@example.com",
                "rol": roles.ALICI_SATINALMACI,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        token = FirmaInvite.objects.get(pk=res.data["id"]).token

        self.api.force_authenticate(user=None)
        accept = self.api.post(
            reverse("api-auth-invite-accept"),
            {
                "token": token,
                "username": "api_new_buyer",
                "password": "SecurePass12!",
                "password_confirm": "SecurePass12!",
            },
            format="json",
        )
        self.assertEqual(accept.status_code, 201, accept.data)

        user = Kullanici.objects.get(username="api_new_buyer")
        self.api.force_authenticate(user=user)
        me = self.api.get(reverse("api-me"))
        self.assertEqual(me.status_code, 200)
        self.assertTrue(me.data["email_verified"])
        self.assertIn("can_manage_users", me.data["capabilities"])


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_VERIFY_REQUIRED_FOR_WRITE=True,
)
class EmailVerifyWriteGateTests(TestCase):
    def setUp(self):
        from api.permissions import IsBuyerCommerceWrite
        from rest_framework.test import APIRequestFactory

        self.factory = APIRequestFactory()
        self.perm = IsBuyerCommerceWrite()
        self.firma = Firma.objects.create(
            ad="Alıcı Gate",
            firma_kodu="GATE1",
            vergi_no="7777777777",
            alici_mi=True,
            onay_durumu="onayli",
            aktif=True,
        )
        self.user = Kullanici(
            username="gate_buyer",
            email="gate@example.com",
            firma=self.firma,
            rol=roles.ALICI_SATINALMACI,
        )
        self.user.set_password("SecurePass12!")
        self.user.save()
        sync_user_role_groups(self.user)

    def test_write_denied_when_unverified(self):
        req = self.factory.post("/api/v1/carts/me/lines/")
        req.user = self.user
        self.assertFalse(self.perm.has_permission(req, None))

    def test_write_allowed_when_verified(self):
        email_verify_servisi.mark_verified(self.user)
        req = self.factory.post("/api/v1/carts/me/lines/")
        req.user = self.user
        self.assertTrue(self.perm.has_permission(req, None))
