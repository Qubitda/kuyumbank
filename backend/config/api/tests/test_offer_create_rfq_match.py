"""P0 — supplier teklif create HTTP + RFQ eşleştirme HTTP."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import TedarikciTeklif
from siparis.models import RFQ, RFQLine
from siparis.services import rfq_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class OfferCreateAndRfqMatchApiTests(CheckoutFixtureMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.ted_user)
        sync_user_role_groups(cls.buyer)
        cls.catalog = User(
            username="match_catalog",
            firma=cls.platform,
            rol=roles.PLATFORM_CATALOG,
            is_staff=True,
        )
        cls.catalog.set_password("x")
        cls.catalog.save()
        sync_user_role_groups(cls.catalog)

    def setUp(self):
        self.api = APIClient()

    def _idem(self, key):
        return {"HTTP_IDEMPOTENCY_KEY": key}

    def test_supplier_offer_create_json(self):
        self.api.force_authenticate(user=self.ted_user)
        bas = date.today()
        res = self.api.post(
            reverse("api-supplier-offers"),
            {
                "varyant_id": self.varyant.pk,
                "fiyat_modeli": TedarikciTeklif.FiyatModeli.METAL_BAZLI,
                "gram": "1.500",
                "tedarikci_kodu": "CREATE1",
                "gecerlilik_baslangic": bas.isoformat(),
                "gecerlilik_bitis": (bas + timedelta(days=30)).isoformat(),
                "tedarikci_id": 999999,  # ignored
            },
            format="json",
            **self._idem("offer-c1"),
        )
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res["Content-Type"].split(";")[0], "application/json")
        body = res.json()
        self.assertEqual(body["durum"], TedarikciTeklif.Durum.TASLAK)
        self.assertEqual(body["varyant_id"], self.varyant.pk)
        t = TedarikciTeklif.objects.get(pk=body["id"])
        self.assertEqual(t.tedarikci_id, self.ted.pk)

        buyer = self.api.post(
            reverse("api-supplier-offers"),
            {
                "varyant_id": self.varyant.pk,
                "fiyat_modeli": TedarikciTeklif.FiyatModeli.METAL_BAZLI,
                "gram": "1",
            },
            format="json",
            **self._idem("offer-buyer"),
        )
        self.api.force_authenticate(user=self.buyer)
        buyer = self.api.post(
            reverse("api-supplier-offers"),
            {
                "varyant_id": self.varyant.pk,
                "fiyat_modeli": TedarikciTeklif.FiyatModeli.METAL_BAZLI,
                "gram": "1",
            },
            format="json",
            **self._idem("offer-buyer2"),
        )
        self.assertIn(buyer.status_code, (403, 401), buyer.content)

        bad = self.api
        self.api.force_authenticate(user=self.ted_user)
        bad = self.api.post(
            reverse("api-supplier-offers"),
            {"varyant_id": "x", "fiyat_modeli": "METAL_BAZLI"},
            format="json",
            **self._idem("offer-bad"),
        )
        self.assertEqual(bad.status_code, 400, bad.content)

    def test_rfq_match_flow_json(self):
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="Match HTTP",
            talep_tipi=RFQ.TalepTipi.KATALOG_DISI,
            line_specs=[
                {
                    "aciklama": self.varyant.sku or "katalog disi",
                    "miktar": Decimal("1"),
                    "birim": "ADET",
                }
            ],
        )
        line = rfq.lines.get()
        self.assertIsNone(line.varyant_id)

        self.api.force_authenticate(user=self.buyer)
        denied = self.api.get(
            reverse("api-ops-rfq-match-candidates", kwargs={"line_id": line.pk})
        )
        self.assertEqual(denied.status_code, 403, denied.content)

        self.api.force_authenticate(user=self.catalog)
        cand = self.api.get(
            reverse("api-ops-rfq-match-candidates", kwargs={"line_id": line.pk})
        )
        self.assertEqual(cand.status_code, 200, cand.content)
        self.assertEqual(cand["Content-Type"].split(";")[0], "application/json")

        create = self.api.post(
            reverse("api-ops-rfq-matches", kwargs={"line_id": line.pk}),
            {"varyant_id": self.varyant.pk, "kanit": {"not": "sku"}},
            format="json",
            **self._idem("match-1"),
        )
        self.assertEqual(create.status_code, 201, create.content)
        mid = create.json()["id"]

        appr = self.api.post(
            reverse("api-ops-rfq-match-approve", kwargs={"pk": mid}),
            {},
            format="json",
            **self._idem("match-appr"),
        )
        self.assertEqual(appr.status_code, 200, appr.content)
        line.refresh_from_db()
        self.assertEqual(line.varyant_id, self.varyant.pk)
