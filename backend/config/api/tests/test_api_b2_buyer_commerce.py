"""API-B2 — buyer quote/lock/cart/order HTTP + maske + allowed_actions."""

from decimal import Decimal

from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient

from api.masking import assert_masked
from fiyatlama.models import PriceLock
from fiyatlama.services import pricing_service
from siparis.models import Order
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class BuyerCommerceApiTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(user=self.buyer)

    def _headers(self, key: str) -> dict:
        return {"HTTP_IDEMPOTENCY_KEY": key}

    def test_quote_create_and_get_masked(self):
        res = self.api.post(
            reverse("api-quote-create"),
            {
                "varyant_id": self.varyant.pk,
                "satis_kanali_id": self.kanal.pk,
                "para_birimi": "TRY",
            },
            format="json",
            **self._headers("b2-q-1"),
        )
        self.assertEqual(res.status_code, 201, res.content)
        body = res.json()
        assert_masked(body)
        self.assertIn("expires_at", body)
        self.assertIn("server_now", body)
        self.assertIn("lock", body["allowed_actions"])
        self.assertIsInstance(body["toplam_vergisiz"], str)
        self.assertNotIn("teklif_id", body)
        self.assertNotIn("tedarikci", body)

        det = self.api.get(reverse("api-quote-detail", kwargs={"pk": body["id"]}))
        self.assertEqual(det.status_code, 200)
        assert_masked(det.json())

    def test_lock_cart_checkout_order_cancel_reorder(self):
        quote = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        lock_res = self.api.post(
            reverse("api-price-lock-create"),
            {"quote_id": quote.pk},
            format="json",
            **self._headers("b2-lock-1"),
        )
        self.assertEqual(lock_res.status_code, 201, lock_res.content)
        lock_body = lock_res.json()
        self.assertIn("expires_at", lock_body)
        self.assertTrue(lock_body["gecerli"])
        self.assertTrue(PriceLock.objects.filter(pk=lock_body["id"]).exists())

        # Fresh quote for cart (lock does not block cart which uses quote)
        quote2 = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        add = self.api.post(
            reverse("api-cart-line-create"),
            {"quote_id": quote2.pk, "miktar": "1"},
            format="json",
            **self._headers("b2-cart-1"),
        )
        self.assertEqual(add.status_code, 201, add.content)
        assert_masked(add.json())
        line_id = add.json()["line"]["id"]

        patch = self.api.patch(
            reverse("api-cart-line-detail", kwargs={"line_id": line_id}),
            {"miktar": "2"},
            format="json",
            **self._headers("b2-cart-upd-1"),
        )
        self.assertEqual(patch.status_code, 200, patch.content)
        self.assertEqual(patch.json()["line"]["miktar"], "2")

        co = self.api.post(
            reverse("api-checkout-create"),
            {},
            format="json",
            **self._headers("b2-co-1"),
        )
        self.assertEqual(co.status_code, 201, co.content)
        self.assertIn("create_order", co.json().get("allowed_actions", []))

        ord_res = self.api.post(
            reverse("api-order-from-checkout"),
            {"checkout_id": co.json()["id"]},
            format="json",
            **self._headers("b2-ord-1"),
        )
        self.assertEqual(ord_res.status_code, 201, ord_res.content)
        order_body = ord_res.json()
        assert_masked(order_body)
        self.assertIn("cancel", order_body["allowed_actions"])
        oid = order_body["id"]

        cancel = self.api.post(
            reverse("api-order-cancel", kwargs={"pk": oid}),
            {},
            format="json",
            **self._headers("b2-cancel-1"),
        )
        self.assertEqual(cancel.status_code, 200, cancel.content)
        self.assertEqual(cancel.json()["durum"], Order.Durum.IPTAL)
        self.assertNotIn("cancel", cancel.json()["allowed_actions"])

        # New order for reorder
        self._quote_and_cart(miktar=Decimal("1"))
        co2 = checkout_servisi.checkout(actor=self.buyer, idempotency_key="b2-co-svc")
        order2 = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co2.attempt
        )
        re = self.api.post(
            reverse("api-order-reorder", kwargs={"pk": order2.pk}),
            {"replace_cart": True},
            format="json",
            **self._headers("b2-re-1"),
        )
        self.assertEqual(re.status_code, 200, re.content)
        assert_masked(re.json())
        self.assertIn("cart", re.json())

    def test_supplier_cannot_quote(self):
        self.api.force_authenticate(user=self.ted_user)
        res = self.api.post(
            reverse("api-quote-create"),
            {
                "varyant_id": self.varyant.pk,
                "satis_kanali_id": self.kanal.pk,
            },
            format="json",
            **self._headers("b2-sup-q"),
        )
        self.assertEqual(res.status_code, 403)

    def test_catalog_detail(self):
        lst = self.api.get(reverse("api-buyer-catalog"))
        self.assertEqual(lst.status_code, 200)
        # may be empty if fixture product not yayinli — use varyant.urun
        urun = self.varyant.urun
        urun.yayin_durumu = "aktif"
        urun.onay_durumu = "onayli"
        urun.save(update_fields=["yayin_durumu", "onay_durumu"])
        det = self.api.get(
            reverse("api-buyer-catalog-detail", kwargs={"pk": urun.pk})
        )
        self.assertEqual(det.status_code, 200)
        body = det.json()
        assert_masked(body)
        self.assertIn("quote", body["allowed_actions"])
        self.assertIn("varyantlar", body)
        self.assertTrue(any(v["id"] == self.varyant.pk for v in body["varyantlar"]))

    def test_catalog_search_q(self):
        urun = self.varyant.urun
        urun.yayin_durumu = "aktif"
        urun.onay_durumu = "onayli"
        urun.save(update_fields=["yayin_durumu", "onay_durumu"])
        hit = self.api.get(reverse("api-buyer-catalog"), {"q": urun.ad[:4]})
        self.assertEqual(hit.status_code, 200)
        ids = [r["id"] for r in hit.json()["results"]]
        self.assertIn(urun.pk, ids)
        self.assertIn("kategori", hit.json()["results"][0])
        miss = self.api.get(
            reverse("api-buyer-catalog"), {"q": "zzz-no-match-xxx"}
        )
        self.assertEqual(miss.status_code, 200)
        self.assertEqual(miss.json()["count"], 0)
