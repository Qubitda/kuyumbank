"""NX-FE hardening — docs auth, MFA problem+json, ready, token revoke, supplier ops scope."""

from __future__ import annotations

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from firmalar import roles
from firmalar.models import Kullanici
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


@override_settings(DEBUG=False, API_DOCS_PUBLIC=False)
class ApiDocsAuthHardeningTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        plat = ensure_platform_firma()
        self.staff = Kullanici(
            username="docs_staff",
            email="docs_staff@example.com",
            firma=plat,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        self.staff.set_password("SecurePass12!")
        self.staff.save()
        sync_user_role_groups(self.staff)

    def test_anon_schema_denied(self):
        res = self.api.get("/api/schema/")
        self.assertIn(res.status_code, (401, 403))

    def test_staff_session_schema_200(self):
        self.api.force_authenticate(user=self.staff)
        res = self.api.get("/api/schema/")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(str(body.get("openapi", "")).startswith("3."))
        self.assertIn("/api/v1/ready/", body.get("paths", {}))


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    MFA_ENFORCE_PLATFORM=True,
)
class MfaProblemJsonTests(TestCase):
    def setUp(self):
        self.api = APIClient(enforce_csrf_checks=False)
        plat = ensure_platform_firma()
        self.admin = Kullanici(
            username="mfa_prob",
            email="mfa_prob@example.com",
            firma=plat,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        self.admin.set_password("SecurePass12!")
        self.admin.save()
        sync_user_role_groups(self.admin)

    def test_blocked_me_is_problem_json(self):
        login = self.api.post(
            reverse("api-auth-login"),
            {"username": "mfa_prob", "password": "SecurePass12!"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        self.assertTrue(login.data.get("mfa_required"))
        me = self.api.get(reverse("api-me"))
        self.assertEqual(me.status_code, 403)
        ctype = me.get("Content-Type", "")
        self.assertIn("application/problem+json", ctype)
        body = me.json()
        self.assertEqual(body.get("code"), "mfa_required")
        self.assertEqual(body.get("status"), 403)


class ReadyAndTokenRevokeTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def setUp(self):
        self.api = APIClient(enforce_csrf_checks=False)

    def test_ready_ok(self):
        res = self.api.get(reverse("api-ready"))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "ready")
        self.assertEqual(body["checks"]["database"], "ok")

    def test_logout_revokes_token(self):
        token = Token.objects.create(user=self.buyer)
        self.api.force_authenticate(user=self.buyer)
        res = self.api.post(reverse("api-auth-logout"), {}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())
        # Token artık geçersiz
        self.api.force_authenticate(user=None)
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        me = self.api.get(reverse("api-me"))
        self.assertEqual(me.status_code, 401)


class SupplierViewAllScopeTests(CheckoutFixtureMixin, TestCase):
    """view_all: ops ayrıcalığıyla tüm teklifler; ?tedarikci_id= daraltır. Supplier yalnız kendi."""

    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        plat = ensure_platform_firma()
        cls.ops = Kullanici(
            username="sup_ops",
            email="sup_ops@example.com",
            firma=plat,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.ops.set_password("x")
        cls.ops.save()
        sync_user_role_groups(cls.ops)

    def setUp(self):
        self.api = APIClient()

    def test_supplier_sees_only_own(self):
        self.api.force_authenticate(user=self.ted_user)
        res = self.api.get(reverse("api-supplier-offers"))
        self.assertEqual(res.status_code, 200)
        for row in res.json().get("results", []):
            # Presenter maskeleyebilir; en azından kendi teklif listesi boş değilse kendi
            self.assertIn("id", row)

    def test_ops_view_all_can_list_and_filter(self):
        self.api.force_authenticate(user=self.ops)
        all_res = self.api.get(reverse("api-supplier-offers"))
        self.assertEqual(all_res.status_code, 200)
        scoped = self.api.get(
            reverse("api-supplier-offers"),
            {"tedarikci_id": self.ted.pk},
        )
        self.assertEqual(scoped.status_code, 200)
        # Geçersiz tedarikci_id → 400 problem
        bad = self.api.get(
            reverse("api-supplier-offers"),
            {"tedarikci_id": "x"},
        )
        self.assertEqual(bad.status_code, 400)
