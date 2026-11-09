"""API-B2 concurrency — Idempotency-Key eşzamanlılık (PostgreSQL; TransactionTestCase)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient

from fiyatlama.models import PriceLock, PriceQuote
from fiyatlama.services import pricing_service
from siparis.models import CheckoutAttempt, Order
from siparis.services import cart_servisi, checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.models import StockMovement
from stok.services import ledger_servisi


class BuyerIdempotencyConcurrencyTests(CheckoutFixtureMixin, TransactionTestCase):
    def setUp(self):
        # TransactionTestCase: setUpTestData yok; her testte dünya kur
        self._build_checkout_world()
        # Extra stock for repeated checkouts in threads
        ledger_servisi.kaydet_hareket(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=self.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("50"),
        )

    def _client(self) -> APIClient:
        api = APIClient()
        api.force_authenticate(user=self.buyer)
        return api

    def _parallel_post(self, url, data, key, n=4):
        buyer_id = self.buyer.pk

        def worker(payload):
            connection.close()
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.get(pk=buyer_id)
            api = APIClient()
            api.force_authenticate(user=user)
            return api.post(
                url,
                payload,
                format="json",
                HTTP_IDEMPOTENCY_KEY=key,
            )

        results = []
        with ThreadPoolExecutor(max_workers=n) as pool:
            futs = [pool.submit(worker, data) for _ in range(n)]
            for f in as_completed(futs):
                results.append(f.result())
        return results

    def test_concurrent_checkout_same_key_one_attempt(self):
        self._quote_and_cart(miktar=Decimal("1"))
        url = reverse("api-checkout-create")
        results = self._parallel_post(url, {}, "conc-co-1", n=4)
        codes = [r.status_code for r in results]
        self.assertTrue(all(c == 201 for c in codes), codes)
        ids = {r.json()["id"] for r in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(
            CheckoutAttempt.objects.filter(
                alici_firma=self.alici, idempotency_key="conc-co-1"
            ).count(),
            1,
        )

    def test_same_key_different_body_conflict(self):
        self._quote_and_cart(miktar=Decimal("1"))
        api = self._client()
        url = reverse("api-checkout-create")
        first = api.post(url, {}, format="json", HTTP_IDEMPOTENCY_KEY="conc-cf-1")
        self.assertEqual(first.status_code, 201, first.content)
        conflict = api.post(
            url,
            {"note": "diff"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="conc-cf-1",
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json().get("code"), "idempotency_conflict")

    def test_concurrent_from_checkout_one_order(self):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="conc-co-ord"
        )
        url = reverse("api-order-from-checkout")
        payload = {"checkout_id": co.attempt.pk}
        results = self._parallel_post(url, payload, "conc-ord-1", n=4)
        self.assertTrue(all(r.status_code == 201 for r in results), [r.status_code for r in results])
        ids = {r.json()["id"] for r in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(Order.objects.filter(checkout_attempt=co.attempt).count(), 1)

    def test_concurrent_cancel_single_state(self):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="conc-co-can"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        url = reverse("api-order-cancel", kwargs={"pk": order.pk})
        results = self._parallel_post(url, {}, "conc-can-1", n=4)
        self.assertTrue(all(r.status_code == 200 for r in results))
        order.refresh_from_db()
        self.assertEqual(order.durum, Order.Durum.IPTAL)

    def test_concurrent_quote_create_one_record(self):
        url = reverse("api-quote-create")
        payload = {
            "varyant_id": self.varyant.pk,
            "satis_kanali_id": self.kanal.pk,
            "para_birimi": "TRY",
        }
        before = PriceQuote.objects.filter(alici_firma=self.alici).count()
        results = self._parallel_post(url, payload, "conc-q-1", n=4)
        self.assertTrue(all(r.status_code == 201 for r in results), [r.content for r in results])
        ids = {r.json()["id"] for r in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(
            PriceQuote.objects.filter(alici_firma=self.alici).count(),
            before + 1,
        )

    def test_concurrent_lock_one_record(self):
        quote = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        url = reverse("api-price-lock-create")
        payload = {"quote_id": quote.pk}
        results = self._parallel_post(url, payload, "conc-lock-1", n=4)
        self.assertTrue(all(r.status_code == 201 for r in results))
        ids = {r.json()["id"] for r in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(PriceLock.objects.filter(quote=quote).count(), 1)

    def test_concurrent_reorder_safe(self):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="conc-co-re"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        url = reverse("api-order-reorder", kwargs={"pk": order.pk})
        results = self._parallel_post(
            url, {"replace_cart": True}, "conc-re-1", n=4
        )
        self.assertTrue(all(r.status_code == 200 for r in results), [r.status_code for r in results])
        cart_ids = {r.json()["cart"]["id"] for r in results}
        self.assertEqual(len(cart_ids), 1)
