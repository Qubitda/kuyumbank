"""API-B5 — ops QC / sevkiyat HTTP (view_all dışı manage_qc / manage_shipment)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from api.masking import assert_masked
from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from kalite.models import QualityInspection
from lojistik.models import Shipment
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class B5FixtureMixin(CheckoutFixtureMixin):
    @classmethod
    def _build_b5_world(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)
        cls.qc = User(
            username="b5_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)
        cls.log = User(
            username="b5_log",
            firma=cls.platform,
            rol=roles.PLATFORM_LOGISTICS,
            is_staff=True,
        )
        cls.log.set_password("x")
        cls.log.save()
        sync_user_role_groups(cls.log)

    def _order(self, key: str):
        self._quote_and_cart(miktar=Decimal("2.500"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def _idem(self, key):
        return {"HTTP_IDEMPOTENCY_KEY": key}


class ApiB5OpsTests(B5FixtureMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_b5_world()

    def setUp(self):
        self.api = APIClient()

    def test_qc_flow_masked_idempotency(self):
        order = self._order("b5-qc-ord")
        self.api.force_authenticate(user=self.qc)
        create = self.api.post(
            reverse("api-ops-inspection-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b5-qi-1"),
        )
        self.assertEqual(create.status_code, 201, create.content)
        body = create.json()
        self.assertEqual(body["durum"], QualityInspection.Durum.TASLAK)
        self.assertIn("start", body["allowed_actions"])
        self.assertNotIn("olusturan", body)
        assert_masked(body)
        qid = body["id"]

        again = self.api.post(
            reverse("api-ops-inspection-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b5-qi-1"),
        )
        self.assertEqual(again.status_code, 201)
        self.assertEqual(again.json()["id"], qid)

        conflict = self.api.post(
            reverse("api-ops-inspection-list"),
            {"order_id": order.pk, "notlar": "farkli"},
            format="json",
            **self._idem("b5-qi-1"),
        )
        self.assertEqual(conflict.status_code, 409)

        start = self.api.post(
            reverse("api-ops-inspection-start", kwargs={"pk": qid}),
            {},
            format="json",
            **self._idem("b5-qi-s"),
        )
        self.assertEqual(start.status_code, 200)
        self.assertEqual(start.json()["durum"], QualityInspection.Durum.OLCUMDE)

        line = order.lines.get()
        meas = self.api.post(
            reverse("api-ops-inspection-measurement", kwargs={"pk": qid}),
            {"order_line_id": line.pk, "olculen": str(line.miktar)},
            format="json",
            **self._idem("b5-qi-m"),
        )
        self.assertEqual(meas.status_code, 201, meas.content)
        self.assertEqual(meas.json()["sonuc"], "UYGUN")
        self.assertIsInstance(meas.json()["olculen"], str)

        passed = self.api.post(
            reverse("api-ops-inspection-pass", kwargs={"pk": qid}),
            {},
            format="json",
            **self._idem("b5-qi-p"),
        )
        self.assertEqual(passed.status_code, 200)
        self.assertEqual(passed.json()["durum"], QualityInspection.Durum.PASS)
        self.assertFalse(passed.json()["shipment_blok"])

        # Alıcı / tedarikçi → 403
        self.api.force_authenticate(user=self.buyer)
        deny_b = self.api.get(reverse("api-ops-inspection-list"))
        self.assertEqual(deny_b.status_code, 403)
        self.api.force_authenticate(user=self.ted_user)
        deny_t = self.api.get(
            reverse("api-ops-inspection-detail", kwargs={"pk": qid})
        )
        self.assertEqual(deny_t.status_code, 403)

    def test_qc_missing_order_404_and_list_filter(self):
        order = self._order("b5-qc-list")
        self.api.force_authenticate(user=self.qc)
        miss = self.api.post(
            reverse("api-ops-inspection-list"),
            {"order_id": 99999999},
            format="json",
            **self._idem("b5-qi-miss"),
        )
        self.assertEqual(miss.status_code, 404)

        create = self.api.post(
            reverse("api-ops-inspection-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b5-qi-list"),
        )
        self.assertEqual(create.status_code, 201)
        page = self.api.get(
            reverse("api-ops-inspection-list"),
            {"page": 1, "page_size": 2, "durum": "TASLAK"},
        )
        self.assertEqual(page.status_code, 200)
        self.assertLessEqual(page.json()["page_size"], 100)
        self.assertGreaterEqual(page.json()["count"], 1)

        # Logistics view_qc okuma; manage_qc yok → yazma 403
        self.api.force_authenticate(user=self.log)
        lst = self.api.get(reverse("api-ops-inspection-list"))
        self.assertEqual(lst.status_code, 200)
        deny = self.api.post(
            reverse("api-ops-inspection-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b5-qi-log-deny"),
        )
        self.assertEqual(deny.status_code, 403)

    def test_qc_fail_path(self):
        order = self._order("b5-qc-fail")
        self.api.force_authenticate(user=self.qc)
        create = self.api.post(
            reverse("api-ops-inspection-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b5-qi-f0"),
        )
        qid = create.json()["id"]
        self.api.post(
            reverse("api-ops-inspection-start", kwargs={"pk": qid}),
            {},
            format="json",
            **self._idem("b5-qi-f1"),
        )
        fail = self.api.post(
            reverse("api-ops-inspection-fail", kwargs={"pk": qid}),
            {"reason": "gram sapma"},
            format="json",
            **self._idem("b5-qi-f2"),
        )
        self.assertEqual(fail.status_code, 200)
        self.assertEqual(fail.json()["durum"], QualityInspection.Durum.FAIL)
        self.assertTrue(fail.json()["shipment_blok"])

    def _pass_qc(self, order, key_prefix: str):
        self.api.force_authenticate(user=self.qc)
        create = self.api.post(
            reverse("api-ops-inspection-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem(f"{key_prefix}-c"),
        )
        qid = create.json()["id"]
        self.api.post(
            reverse("api-ops-inspection-start", kwargs={"pk": qid}),
            {},
            format="json",
            **self._idem(f"{key_prefix}-s"),
        )
        line = order.lines.get()
        self.api.post(
            reverse("api-ops-inspection-measurement", kwargs={"pk": qid}),
            {"order_line_id": line.pk, "olculen": str(line.miktar)},
            format="json",
            **self._idem(f"{key_prefix}-m"),
        )
        self.api.post(
            reverse("api-ops-inspection-pass", kwargs={"pk": qid}),
            {},
            format="json",
            **self._idem(f"{key_prefix}-p"),
        )

    def test_ops_shipment_flow_pod_rbac(self):
        order = self._order("b5-ship-ord")
        self._pass_qc(order, "b5-ship-qc")

        self.api.force_authenticate(user=self.log)
        create = self.api.post(
            reverse("api-ops-shipment-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b5-sh-1"),
        )
        self.assertEqual(create.status_code, 201, create.content)
        body = create.json()
        self.assertEqual(body["durum"], Shipment.Durum.TASLAK)
        self.assertIn("prepare", body["allowed_actions"])
        assert_masked(body)
        sid = body["id"]

        prep = self.api.post(
            reverse("api-ops-shipment-prepare", kwargs={"pk": sid}),
            {},
            format="json",
            **self._idem("b5-sh-p"),
        )
        self.assertEqual(prep.status_code, 200)
        self.assertEqual(prep.json()["durum"], Shipment.Durum.HAZIR)

        disp = self.api.post(
            reverse("api-ops-shipment-dispatch", kwargs={"pk": sid}),
            {},
            format="json",
            **self._idem("b5-sh-d"),
        )
        self.assertEqual(disp.status_code, 200)
        self.assertEqual(disp.json()["durum"], Shipment.Durum.YOLDA)
        self.assertTrue(disp.json().get("takip_no"))

        pod = self.api.post(
            reverse("api-ops-shipment-pod", kwargs={"pk": sid}),
            {"teslim_alan": "Ahmet Y."},
            format="json",
            **self._idem("b5-sh-pod"),
        )
        self.assertEqual(pod.status_code, 200, pod.content)
        self.assertIsNotNone(pod.json().get("pod"))

        deliv = self.api.post(
            reverse("api-ops-shipment-deliver", kwargs={"pk": sid}),
            {},
            format="json",
            **self._idem("b5-sh-del"),
        )
        self.assertEqual(deliv.status_code, 200)
        self.assertEqual(deliv.json()["durum"], Shipment.Durum.TESLIM)

        # Buyer ops path 403; buyer public shipments hâlâ ayrı
        self.api.force_authenticate(user=self.buyer)
        deny = self.api.get(reverse("api-ops-shipment-list"))
        self.assertEqual(deny.status_code, 403)

        # QC manage_shipment yok → yazma 403; view_all yok → liste 403
        self.api.force_authenticate(user=self.qc)
        deny_qc = self.api.post(
            reverse("api-ops-shipment-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b5-sh-qc-deny"),
        )
        self.assertEqual(deny_qc.status_code, 403)

    def test_ops_shipment_qc_gate_and_idempotency(self):
        order = self._order("b5-gate")
        self.api.force_authenticate(user=self.log)
        blocked = self.api.post(
            reverse("api-ops-shipment-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b5-sh-gate"),
        )
        self.assertEqual(blocked.status_code, 400)

        self._pass_qc(order, "b5-gate-qc")
        self.api.force_authenticate(user=self.log)
        a = self.api.post(
            reverse("api-ops-shipment-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b5-sh-idem"),
        )
        self.assertEqual(a.status_code, 201)
        b = self.api.post(
            reverse("api-ops-shipment-list"),
            {"order_id": order.pk},
            format="json",
            **self._idem("b5-sh-idem"),
        )
        self.assertEqual(b.status_code, 201)
        self.assertEqual(a.json()["id"], b.json()["id"])
        self.assertEqual(
            Shipment.objects.filter(order=order).count(), 1
        )


class ApiB5ConcurrencyTests(B5FixtureMixin, TransactionTestCase):
    def setUp(self):
        self._build_b5_world()

    def _order(self, key: str):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def _pass_qc_service(self, order):
        from kalite.services import inspection_servisi, olcum_servisi

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

    def test_concurrent_inspection_create_one(self):
        order = self._order("b5c-qi")
        url = reverse("api-ops-inspection-list")
        results = self._parallel_post(
            self.qc.pk,
            url,
            {"order_id": order.pk},
            "b5c-qi-1",
            n=4,
        )
        self.assertTrue(
            all(r.status_code == 201 for r in results),
            [r.status_code for r in results],
        )
        ids = {r.json()["id"] for r in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(
            QualityInspection.objects.filter(order=order).count(), 1
        )

    def test_concurrent_shipment_create_one(self):
        order = self._order("b5c-sh")
        self._pass_qc_service(order)
        url = reverse("api-ops-shipment-list")
        results = self._parallel_post(
            self.log.pk,
            url,
            {"order_id": order.pk},
            "b5c-sh-1",
            n=4,
        )
        self.assertTrue(
            all(r.status_code == 201 for r in results),
            [r.content for r in results],
        )
        ids = {r.json()["id"] for r in results}
        self.assertEqual(len(ids), 1)
        self.assertEqual(Shipment.objects.filter(order=order).count(), 1)
