"""F5-032 — Finans UI RBAC (buyer maskeli + ops view_all)."""

from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import LedgerEntry
from finans.services import ledger_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class FinanceUiF5032Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def setUp(self):
        self.client = Client()

    def test_buyer_finance_ok_masked(self):
        self.client.force_login(self.buyer)
        res = self.client.get(reverse("buyer-finance"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Finans özeti")
        self.assertContains(res, "Kredi")
        self.assertNotContains(res, "komisyon")
        self.assertNotContains(res, "tedarikci")
        self.assertNotContains(res, "ledger_entry")

    def test_supplier_buyer_finance_forbidden(self):
        self.client.force_login(self.ted_user)
        res = self.client.get(reverse("buyer-finance"))
        self.assertEqual(res.status_code, 403)

    def test_ops_finance_ok(self):
        ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            karsi_firma=self.platform,
            tutar=Decimal("12.50"),
            para_birimi="TRY",
            yon=LedgerEntry.Yon.BORC,
            hareket_tipi=LedgerEntry.HareketTipi.SATIS,
            idempotency_key="ui-ops-seed-1",
        )
        self.client.force_login(self.finance)
        res = self.client.get(reverse("ops-finance"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Finans özeti")
        self.assertContains(res, "Ledger")

    def test_buyer_ops_finance_forbidden(self):
        self.client.force_login(self.buyer)
        res = self.client.get(reverse("ops-finance"))
        self.assertEqual(res.status_code, 403)
