"""API-B3 — finans / sevkiyat / iade HTTP (maske, yetki, allowed_actions)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import PaymentIntent
from finans.models import LedgerEntry
from finans.services import ledger_servisi, payment_servisi
from kalite.services import inspection_servisi, olcum_servisi
from lojistik.models import ReturnRequest
from lojistik.services import pod_servisi, shipment_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class B3FixtureMixin(CheckoutFixtureMixin):
    @classmethod
    def _build_b3_world(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.qc = User(
            username="b3_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)
        cls.log = User(
            username="b3_log",
            firma=cls.platform,
            rol=roles.PLATFORM_LOGISTICS,
            is_staff=True,
        )
        cls.log.set_password("x")
        cls.log.save()
        sync_user_role_groups(cls.log)
        sync_user_role_groups(cls.finance)

    def _delivered(self, key):
        self._quote_and_cart(miktar=Decimal("2.500"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        insp = inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        line = order.lines.get()
        olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=line.miktar,
        )
        inspection_servisi.pass_et(actor=self.qc, inspection=insp)
        ship = shipment_servisi.olustur(actor=self.log, order=order)
        ship = shipment_servisi.hazirla(actor=self.log, shipment=ship)
        ship = shipment_servisi.sevk_et(
            actor=self.log, shipment=ship, takip_no="B3-TRK"
        )
        ship = shipment_servisi.teslim_et(actor=self.log, shipment=ship)
        return order, ship


class ApiB3FinanceOpsTests(B3FixtureMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_b3_world()

    def setUp(self):
        self.api = APIClient()

    def _idem(self, key):
        return {"HTTP_IDEMPOTENCY_KEY": key}

    def test_finance_me_allowed_actions_masked(self):
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-finance-mine"))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("allowed_actions", body)
        self.assertIn("create_payment_intent", body["allowed_actions"])
        self.assertNotIn("karsi_firma", body)
        self.assertNotIn("tedarikci", str(body).lower())

    def test_buyer_cari_ledger_tenant(self):
        ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            karsi_firma=self.platform,
            tutar=Decimal("25.00"),
            para_birimi="TRY",
            yon=LedgerEntry.Yon.BORC,
            hareket_tipi=LedgerEntry.HareketTipi.SATIS,
            idempotency_key="b3-led-1",
        )
        self.api.force_authenticate(user=self.buyer)
        cari = self.api.get(reverse("api-finance-cari"))
        self.assertEqual(cari.status_code, 200)
        self.assertGreaterEqual(cari.json()["count"], 1)
        row = cari.json()["results"][0]
        self.assertNotIn("karsi_firma_id", row)
        self.assertIn("bakiye", row)

        led = self.api.get(reverse("api-finance-ledger"))
        self.assertEqual(led.status_code, 200)
        self.assertGreaterEqual(led.json()["count"], 1)
        lrow = led.json()["results"][0]
        self.assertNotIn("karsi_firma_id", lrow)
        self.assertNotIn("firma_id", lrow)

        self.api.force_authenticate(user=self.ted_user)
        denied = self.api.get(reverse("api-finance-cari"))
        self.assertEqual(denied.status_code, 403)

    def test_ops_finance_payments_view_all(self):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="b3-co-pay"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        payment_servisi.olustur_intent(
            actor=self.buyer, order=order, idempotency_key="b3-pi-ops"
        )
        self.api.force_authenticate(user=self.finance)
        res = self.api.get(reverse("api-ops-finance-payments"))
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(res.json()["count"], 1)
        self.api.force_authenticate(user=self.buyer)
        deny = self.api.get(reverse("api-ops-finance-payments"))
        self.assertEqual(deny.status_code, 403)

    def test_payment_intent_create(self):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="b3-co-pi"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        self.api.force_authenticate(user=self.buyer)
        res = self.api.post(
            reverse("api-payment-intent-create"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b3-pi-create"),
        )
        self.assertEqual(res.status_code, 201, res.content)
        body = res.json()
        self.assertEqual(body["order_id"], order.pk)
        self.assertEqual(body["durum"], PaymentIntent.Durum.BEKLEMEDE)
        self.assertIsInstance(body["tutar"], str)
        again = self.api.post(
            reverse("api-payment-intent-create"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b3-pi-create"),
        )
        self.assertEqual(again.status_code, 201)
        self.assertEqual(again.json()["id"], body["id"])

    def test_shipment_allowed_actions(self):
        order, ship = self._delivered("b3-ship-aa")
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-shipment-detail", kwargs={"pk": ship.pk}))
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("request_return", body["allowed_actions"])
        self.assertEqual(body["order_id"], order.pk)

    def test_return_ops_create_buyer_read(self):
        order, ship = self._delivered("b3-ret-1")
        line = order.lines.get()
        self.api.force_authenticate(user=self.buyer)
        deny = self.api.post(
            reverse("api-return-list"),
            {
                "order_id": order.pk,
                "shipment_id": ship.pk,
                "sebep": "Hasarlı ürün iadesi",
                "lines": [{"order_line_id": line.pk, "miktar": "1.000"}],
            },
            format="json",
            **self._idem("b3-ret-buyer-deny"),
        )
        self.assertEqual(deny.status_code, 403)

        self.api.force_authenticate(user=self.log)
        create = self.api.post(
            reverse("api-return-list"),
            {
                "order_id": order.pk,
                "shipment_id": ship.pk,
                "sebep": "Hasarlı ürün iadesi",
                "lines": [{"order_line_id": line.pk, "miktar": "1.000"}],
            },
            format="json",
            **self._idem("b3-ret-create"),
        )
        self.assertEqual(create.status_code, 201, create.content)
        rid = create.json()["id"]
        self.assertEqual(create.json()["durum"], ReturnRequest.Durum.TASLAK)
        self.assertIn("submit_review", create.json()["allowed_actions"])
        self.assertIn("stok_iade_yapildi", create.json())

        self.api.force_authenticate(user=self.buyer)
        detail = self.api.get(reverse("api-return-detail", kwargs={"pk": rid}))
        self.assertEqual(detail.status_code, 200)
        self.assertNotIn("stok_iade_yapildi", detail.json())
        self.assertEqual(detail.json()["allowed_actions"], [])

        lst = self.api.get(reverse("api-return-list"), {"order_id": order.pk})
        self.assertEqual(lst.status_code, 200)
        self.assertEqual(lst.json()["count"], 1)

    def test_return_transitions(self):
        order, ship = self._delivered("b3-ret-tr")
        line = order.lines.get()
        self.api.force_authenticate(user=self.log)
        create = self.api.post(
            reverse("api-return-list"),
            {
                "order_id": order.pk,
                "shipment_id": ship.pk,
                "sebep": "Eksik ürün şikayeti",
                "lines": [{"order_line_id": line.pk, "miktar": "0.500"}],
            },
            format="json",
            **self._idem("b3-ret-tr-c"),
        )
        rid = create.json()["id"]
        sub = self.api.post(
            reverse("api-return-submit", kwargs={"pk": rid}),
            {},
            format="json",
            **self._idem("b3-ret-tr-s"),
        )
        self.assertEqual(sub.status_code, 200)
        self.assertEqual(sub.json()["durum"], ReturnRequest.Durum.INCELENIYOR)
        appr = self.api.post(
            reverse("api-return-approve", kwargs={"pk": rid}),
            {},
            format="json",
            **self._idem("b3-ret-tr-a"),
        )
        self.assertEqual(appr.status_code, 200)
        self.assertEqual(appr.json()["durum"], ReturnRequest.Durum.ONAYLANDI)
        self.assertTrue(appr.json()["stok_iade_yapildi"])


class ApiB3ConcurrencyTests(B3FixtureMixin, TransactionTestCase):
    def setUp(self):
        self._build_b3_world()

    def _parallel_post(self, user_pk, url, data, key, n=4):
        def worker(payload):
            connection.close()
            user = User.objects.get(pk=user_pk)
            api = APIClient()
            api.force_authenticate(user=user)
            return api.post(
                url, payload, format="json", HTTP_IDEMPOTENCY_KEY=key
            )

        results = []
        with ThreadPoolExecutor(max_workers=n) as pool:
            futs = [pool.submit(worker, data) for _ in range(n)]
            for f in as_completed(futs):
                results.append(f.result())
        return results

    def test_concurrent_payment_intent_one(self):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="b3c-co-pi"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        url = reverse("api-payment-intent-create")
        results = self._parallel_post(
            self.buyer.pk, url, {"order_id": order.pk}, "b3c-pi-1", n=4
        )
        self.assertTrue(all(r.status_code == 201 for r in results), [r.status_code for r in results])
        ids = {r.json()["id"] for r in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(
            PaymentIntent.objects.filter(order=order).count(), 1
        )

    def test_concurrent_return_create_one(self):
        order, ship = self._delivered("b3c-ret")
        line = order.lines.get()
        url = reverse("api-return-list")
        payload = {
            "order_id": order.pk,
            "shipment_id": ship.pk,
            "sebep": "Hasarlı ürün iadesi",
            "lines": [{"order_line_id": line.pk, "miktar": "1.000"}],
        }
        results = self._parallel_post(
            self.log.pk, url, payload, "b3c-ret-1", n=4
        )
        self.assertTrue(all(r.status_code == 201 for r in results), [r.content for r in results])
        ids = {r.json()["id"] for r in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(ReturnRequest.objects.filter(order=order).count(), 1)

    def test_concurrent_return_approve_once(self):
        order, ship = self._delivered("b3c-ret-ap")
        line = order.lines.get()
        from lojistik.services import return_servisi

        req = return_servisi.olustur(
            actor=self.log,
            order=order,
            shipment=ship,
            sebep="Hasarlı ürün iadesi",
            line_specs=[{"order_line": line, "miktar": Decimal("1.000")}],
        )
        req = return_servisi.incelemeye_al(actor=self.log, return_request=req)
        url = reverse("api-return-approve", kwargs={"pk": req.pk})
        results = self._parallel_post(self.log.pk, url, {}, "b3c-ret-ap-1", n=4)
        self.assertTrue(all(r.status_code == 200 for r in results), [r.status_code for r in results])
        req.refresh_from_db()
        self.assertEqual(req.durum, ReturnRequest.Durum.ONAYLANDI)
