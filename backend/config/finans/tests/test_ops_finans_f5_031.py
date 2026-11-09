"""F5-031 — platform finans ops API; view_all olmadan çapraz yok."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from firmalar.services.yetki_servisi import can_view_all_tenants
from finans.models import LedgerEntry
from finans.services import ledger_servisi, ops_finans_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class OpsFinanceApiTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def setUp(self):
        self.api = APIClient()

    def _seed_ledger(self):
        ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            karsi_firma=self.platform,
            tutar=Decimal("15.00"),
            para_birimi="TRY",
            yon=LedgerEntry.Yon.BORC,
            hareket_tipi=LedgerEntry.HareketTipi.SATIS,
            idempotency_key="ops-seed-1",
        )

    def test_ops_lists_cross_tenant(self):
        self.assertTrue(can_view_all_tenants(self.finance))
        self._seed_ledger()
        cari = ops_finans_servisi.liste_cari(actor=self.finance)
        led = ops_finans_servisi.liste_ledger(actor=self.finance)
        self.assertGreaterEqual(len(cari), 1)
        self.assertGreaterEqual(len(led), 1)
        ozet = ops_finans_servisi.ozet(actor=self.finance)
        self.assertTrue(ozet["ops"])
        self.assertGreaterEqual(ozet["ledger_count"], 1)

    def test_buyer_denied_service(self):
        with self.assertRaises(PermissionDenied):
            ops_finans_servisi.liste_ledger(actor=self.buyer)
        with self.assertRaises(PermissionDenied):
            ops_finans_servisi.ozet(actor=self.ted_user)

    def test_api_ops_ok_buyer_403(self):
        self._seed_ledger()
        self.api.force_authenticate(user=self.finance)
        res = self.api.get(
            reverse("api-ops-finance"), {"firma_id": 999999}
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ops"])

        cari = self.api.get(reverse("api-ops-finance-cari"))
        self.assertEqual(cari.status_code, 200)
        self.assertGreaterEqual(cari.json()["count"], 1)

        led = self.api.get(reverse("api-ops-finance-ledger"))
        self.assertEqual(led.status_code, 200)
        self.assertGreaterEqual(led.json()["count"], 1)

        self.api.force_authenticate(user=self.buyer)
        self.assertEqual(
            self.api.get(reverse("api-ops-finance")).status_code, 403
        )
        self.assertEqual(
            self.api.get(reverse("api-ops-finance-ledger")).status_code, 403
        )
        self.api.force_authenticate(user=self.ted_user)
        self.assertEqual(
            self.api.get(reverse("api-ops-finance-cari")).status_code, 403
        )
