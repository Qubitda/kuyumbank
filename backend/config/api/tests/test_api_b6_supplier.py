"""API-B6 — tedarikçi teklif/stok yazma + ters kör RFQ."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from api.masking import assert_masked
from fiyatlama.models import TedarikciTeklif
from siparis.models import RFQ
from siparis.services import rfq_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.models import StockBalance


class ApiB6SupplierTests(CheckoutFixtureMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def setUp(self):
        self.api = APIClient()

    def _idem(self, key):
        return {"HTTP_IDEMPOTENCY_KEY": key}

    def _taslak_teklif(self):
        bas = date.today()
        bit = bas + timedelta(days=30)
        return TedarikciTeklif.objects.create(
            varyant=self.varyant,
            tedarikci=self.ted,
            tedarikci_kodu="B6T",
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("1.250"),
            durum=TedarikciTeklif.Durum.TASLAK,
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
        )

    def test_offer_submit_version_stock_adjust(self):
        taslak = self._taslak_teklif()
        self.api.force_authenticate(user=self.ted_user)

        detail = self.api.get(
            reverse("api-supplier-offer-detail", kwargs={"pk": taslak.pk})
        )
        self.assertEqual(detail.status_code, 200, detail.content)
        body = detail.json()
        self.assertIn("submit", body["allowed_actions"])
        self.assertNotIn("alici", str(body).lower())
        assert_masked(body)

        submit = self.api.post(
            reverse("api-supplier-offer-submit", kwargs={"pk": taslak.pk}),
            {},
            format="json",
            **self._idem("b6-sub-1"),
        )
        self.assertEqual(submit.status_code, 200, submit.content)
        self.assertEqual(
            submit.json()["durum"], TedarikciTeklif.Durum.ONAY_BEKLIYOR
        )
        again = self.api.post(
            reverse("api-supplier-offer-submit", kwargs={"pk": taslak.pk}),
            {},
            format="json",
            **self._idem("b6-sub-1"),
        )
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json()["id"], submit.json()["id"])

        ver = self.api.post(
            reverse(
                "api-supplier-offer-versions", kwargs={"pk": self.teklif.pk}
            ),
            {"gram": "2.600"},
            format="json",
            **self._idem("b6-ver-1"),
        )
        self.assertEqual(ver.status_code, 201, ver.content)
        self.assertEqual(ver.json()["durum"], TedarikciTeklif.Durum.ONAY_BEKLIYOR)
        self.assertEqual(ver.json()["versiyon"], self.teklif.versiyon + 1)

        before = StockBalance.objects.get(
            warehouse=self.wh, teklif=self.teklif
        ).on_hand
        adj = self.api.post(
            reverse("api-supplier-stock-adjust"),
            {
                "warehouse_id": self.wh.pk,
                "teklif_id": self.teklif.pk,
                "miktar": "5",
                "neden": "B6 stok duzeltme",
            },
            format="json",
            **self._idem("b6-adj-1"),
        )
        self.assertEqual(adj.status_code, 201, adj.content)
        assert_masked(adj.json())
        after = StockBalance.objects.get(
            warehouse=self.wh, teklif=self.teklif
        ).on_hand
        self.assertEqual(after, before + Decimal("5"))

        stock = self.api.get(reverse("api-supplier-stock"))
        self.assertEqual(stock.status_code, 200)
        row = stock.json()["results"][0]
        self.assertIn("teklif_id", row)
        assert_masked(row)

    def test_supplier_rfq_reverse_blind_message(self):
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="B6 RFQ",
            line_specs=[
                {
                    "aciklama": "14k yuzuk",
                    "miktar": Decimal("3"),
                    "birim": "ADET",
                    "varyant": self.varyant,
                }
            ],
            talep_tipi=RFQ.TalepTipi.OZEL_URETIM,
        )
        rfq = rfq_servisi.gonder(actor=self.buyer, rfq=rfq)

        self.api.force_authenticate(user=self.ted_user)
        listing = self.api.get(reverse("api-supplier-rfq-list"))
        self.assertEqual(listing.status_code, 200, listing.content)
        ids = [r["id"] for r in listing.json()["results"]]
        self.assertIn(rfq.pk, ids)

        det = self.api.get(
            reverse("api-supplier-rfq-detail", kwargs={"pk": rfq.pk})
        )
        self.assertEqual(det.status_code, 200, det.content)
        body = det.json()
        self.assertNotIn("alici_firma_id", body)
        self.assertNotIn("sube_id", body)
        self.assertNotIn("buyer_name", body)
        self.assertNotIn("alici_ad", body)
        assert_masked(body)
        self.assertIn("add_message", body["allowed_actions"])

        msg = self.api.post(
            reverse("api-supplier-rfq-message", kwargs={"pk": rfq.pk}),
            {"govde": "Uretim suresi 10 gun"},
            format="json",
            **self._idem("b6-rfq-m1"),
        )
        self.assertEqual(msg.status_code, 200, msg.content)
        assert_masked(msg.json())
        self.assertTrue(
            any("Uretim" in m["govde"] for m in msg.json()["messages"])
        )

        rev = self.api.post(
            reverse("api-supplier-rfq-revision", kwargs={"pk": rfq.pk}),
            {"ozet": "Tasarim revizyon onerisi"},
            format="json",
            **self._idem("b6-rfq-r1"),
        )
        self.assertEqual(rev.status_code, 200, rev.content)
        self.assertGreaterEqual(len(rev.json()["revizyonlar"]), 2)

    def test_buyer_forbidden_supplier_draft_hidden(self):
        draft = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="Gizli taslak",
            line_specs=[
                {
                    "aciklama": "x",
                    "miktar": Decimal("1"),
                    "birim": "ADET",
                }
            ],
        )
        self.api.force_authenticate(user=self.ted_user)
        hidden = self.api.get(
            reverse("api-supplier-rfq-detail", kwargs={"pk": draft.pk})
        )
        self.assertEqual(hidden.status_code, 404)

        self.api.force_authenticate(user=self.buyer)
        forb = self.api.get(reverse("api-supplier-offers"))
        self.assertEqual(forb.status_code, 403)
        forb2 = self.api.get(reverse("api-supplier-rfq-list"))
        self.assertEqual(forb2.status_code, 403)
        forb3 = self.api.post(
            reverse("api-supplier-stock-adjust"),
            {
                "warehouse_id": self.wh.pk,
                "teklif_id": self.teklif.pk,
                "miktar": "1",
                "neden": "buyer deneme",
            },
            format="json",
            **self._idem("b6-buyer-adj"),
        )
        self.assertEqual(forb3.status_code, 403)
