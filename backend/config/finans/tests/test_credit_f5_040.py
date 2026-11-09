"""F5-040 — kredi özeti + limit aşımı; tenant sızıntısı yok."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import LedgerEntry
from finans.services import cari_servisi, credit_servisi, ledger_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class CreditVisibilityTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def setUp(self):
        self.api = APIClient()

    def _seed_cari(self, *, borc=Decimal("30.00"), limit=Decimal("100.00")):
        ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            karsi_firma=self.platform,
            tutar=borc,
            para_birimi="TRY",
            yon=LedgerEntry.Yon.BORC,
            hareket_tipi=LedgerEntry.HareketTipi.SATIS,
            idempotency_key=f"cr-seed-{borc}",
        )
        hesap = cari_servisi.get_or_create_locked(
            firma=self.alici, para_birimi="TRY", karsi_firma=self.platform
        )
        cari_servisi.set_kredi_limiti(
            actor=self.finance, hesap=hesap, limit=limit
        )
        return hesap

    def test_ozet_masked_and_usable(self):
        self._seed_cari()
        summary = credit_servisi.ozet_for_actor(actor=self.buyer, para_birimi="TRY")
        dto = credit_servisi.present_credit(summary)
        self.assertEqual(dto["bakiye"], "30.00")
        self.assertEqual(dto["kredi_limiti"], "100.00")
        self.assertEqual(dto["kullanilabilir"], "70.00")
        self.assertNotIn("karsi_firma", dto)
        self.assertNotIn("firma_id", dto)

    def test_assert_musait_over_limit(self):
        self._seed_cari(borc=Decimal("80.00"), limit=Decimal("100.00"))
        with self.assertRaises(ValidationError):
            credit_servisi.assert_musait(
                actor=self.buyer, tutar=Decimal("25.00"), para_birimi="TRY"
            )
        # sınırda OK
        credit_servisi.assert_musait(
            actor=self.buyer, tutar=Decimal("20.00"), para_birimi="TRY"
        )

    def test_supplier_denied(self):
        with self.assertRaises(PermissionDenied):
            credit_servisi.ozet_for_actor(actor=self.ted_user)

    def test_api_buyer_me_and_check(self):
        self._seed_cari()
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(
            reverse("api-credit-mine"), {"firma_id": 999999, "para_birimi": "TRY"}
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["kullanilabilir"], "70.00")
        self.assertNotIn("karsi_firma", body)

        ok = self.api.post(
            reverse("api-credit-check"),
            {"tutar": "50.00", "para_birimi": "TRY"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="credit-check-ok-1",
        )
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.json()["ok"])

        bad = self.api.post(
            reverse("api-credit-check"),
            {"tutar": "80.00", "para_birimi": "TRY"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="credit-check-bad-1",
        )
        self.assertEqual(bad.status_code, 400)

    def test_api_supplier_forbidden(self):
        self.api.force_authenticate(user=self.ted_user)
        self.assertEqual(
            self.api.get(reverse("api-credit-mine")).status_code, 403
        )
