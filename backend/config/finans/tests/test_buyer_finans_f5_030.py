"""F5-030 — buyer finans özeti API; kör alan / komisyon yok."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import LedgerEntry
from finans.services import buyer_finans_servisi, cari_servisi, ledger_servisi, payment_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class BuyerFinanceSummaryTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def setUp(self):
        self.api = APIClient()

    def _seed(self):
        ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            karsi_firma=self.platform,
            tutar=Decimal("40.00"),
            para_birimi="TRY",
            yon=LedgerEntry.Yon.BORC,
            hareket_tipi=LedgerEntry.HareketTipi.SATIS,
            idempotency_key="bf-seed",
        )
        hesap = cari_servisi.get_or_create_locked(
            firma=self.alici, para_birimi="TRY", karsi_firma=self.platform
        )
        cari_servisi.set_kredi_limiti(
            actor=self.finance, hesap=hesap, limit=Decimal("200.00")
        )
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="bf-co"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        payment_servisi.olustur_intent(
            actor=self.buyer, order=order, idempotency_key="bf-pi"
        )

    def test_ozet_masked(self):
        self._seed()
        data = buyer_finans_servisi.ozet_for_actor(actor=self.buyer)
        self.assertIn("credit", data)
        self.assertEqual(data["credit"]["bakiye"], "40.00")
        self.assertGreaterEqual(len(data["payment_intents"]), 1)
        pi = data["payment_intents"][0]
        self.assertIn("tutar", pi)
        self.assertNotIn("ledger_entry_id", pi)
        buyer_finans_servisi.assert_masked(data)

    def test_forbidden_key_detected(self):
        with self.assertRaises(PermissionDenied):
            buyer_finans_servisi.assert_masked({"komisyon": "1"})

    def test_supplier_denied(self):
        with self.assertRaises(PermissionDenied):
            buyer_finans_servisi.ozet_for_actor(actor=self.ted_user)

    def test_api_buyer_ok_supplier_403(self):
        self._seed()
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(
            reverse("api-finance-mine"), {"firma_id": 999999, "para_birimi": "TRY"}
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("credit", body)
        self.assertIn("payment_intents", body)
        blob = str(body).lower()
        self.assertNotIn("komisyon", blob)
        self.assertNotIn("marj", blob)
        self.assertNotIn("tedarikci", blob)

        self.api.force_authenticate(user=self.ted_user)
        self.assertEqual(
            self.api.get(reverse("api-finance-mine")).status_code, 403
        )
