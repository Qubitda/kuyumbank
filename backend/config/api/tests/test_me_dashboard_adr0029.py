"""ADR-0029 — GET /me/dashboard/."""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from firmalar import roles
from firmalar.models import Firma, Kullanici
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups


class MeDashboardApiTests(TestCase):
    def setUp(self):
        seed_role_permissions()
        self.api = APIClient(enforce_csrf_checks=False)
        self.firma = Firma.objects.create(
            ad="Dash Alıcı",
            firma_kodu="DASH1",
            vergi_no="8888888888",
            alici_mi=True,
            onay_durumu="onayli",
            aktif=True,
        )
        self.user = Kullanici(
            username="dash_buyer",
            email="dash@example.com",
            firma=self.firma,
            rol=roles.ALICI_SATINALMACI,
        )
        self.user.set_password("SecurePass12!")
        self.user.save()
        sync_user_role_groups(self.user)

    def test_dashboard_ok(self):
        self.api.force_authenticate(user=self.user)
        res = self.api.get(reverse("api-me-dashboard"))
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["username"], "dash_buyer")
        self.assertIn("cart_id", res.data)
        self.assertIn("order_count", res.data)
