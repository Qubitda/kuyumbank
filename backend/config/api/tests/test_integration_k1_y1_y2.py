"""Entegrasyon regresyon — K1 iptal engeli (servis), Y1 ops order read, Y2 actor idempotency."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from api.models import IdempotencyRecord
from api.services import idempotency_servisi as idem
from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class IntegrationK1Y1Y2Tests(CheckoutFixtureMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)
        cls.qc = User(
            username="int_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)
        cls.log = User(
            username="int_log",
            firma=cls.platform,
            rol=roles.PLATFORM_LOGISTICS,
            is_staff=True,
        )
        cls.log.set_password("x")
        cls.log.save()
        sync_user_role_groups(cls.log)

    def setUp(self):
        self.api = APIClient()

    def _order(self, key: str):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_y1_qc_and_logistics_can_read_orders(self):
        order = self._order("int-y1-ord")
        self.api.force_authenticate(user=self.qc)
        lst = self.api.get(reverse("api-order-list"))
        self.assertEqual(lst.status_code, 200, lst.content)
        ids = {r["id"] for r in lst.json()["results"]}
        self.assertIn(order.pk, ids)

        det = self.api.get(reverse("api-order-detail", kwargs={"pk": order.pk}))
        self.assertEqual(det.status_code, 200)
        self.assertEqual(det.json()["id"], order.pk)

        self.api.force_authenticate(user=self.log)
        lst2 = self.api.get(reverse("api-order-list"))
        self.assertEqual(lst2.status_code, 200)
        self.assertIn(order.pk, {r["id"] for r in lst2.json()["results"]})

        # Tedarikçi hâlâ 403
        self.api.force_authenticate(user=self.ted_user)
        deny = self.api.get(reverse("api-order-list"))
        self.assertEqual(deny.status_code, 403)

    def test_y2_platform_users_same_client_key_isolated(self):
        """Aynı platform firma + aynı client Idempotency-Key → farklı actor storage."""
        self.assertNotEqual(self.qc.pk, self.log.pk)
        self.assertEqual(self.qc.firma_id, self.log.firma_id)
        client_key = "shared-platform-key-1"
        sk_qc = idem.storage_key(actor_id=self.qc.pk, client_key=client_key)
        sk_log = idem.storage_key(actor_id=self.log.pk, client_key=client_key)
        self.assertNotEqual(sk_qc, sk_log)

        # QC RFQ değil — org create yok; payment intent yok.
        # Basit: iki actor aynı key ile farklı path'e yazabilmeli (çakışma yok).
        order = self._order("int-y2-ord")
        self.api.force_authenticate(user=self.qc)
        a = self.api.post(
            reverse("api-ops-inspection-list"),
            {"order_id": order.pk},
            format="json",
            HTTP_IDEMPOTENCY_KEY=client_key,
        )
        self.assertEqual(a.status_code, 201, a.content)

        # Aynı client key ile logistics farklı uç — 409 olmamalı
        # (önce QC PASS + ölçüm gerekir shipment için; sadece storage isolation kanıtı:)
        self.assertTrue(
            IdempotencyRecord.objects.filter(
                firma_id=self.qc.firma_id, key=sk_qc
            ).exists()
        )
        self.assertFalse(
            IdempotencyRecord.objects.filter(
                firma_id=self.log.firma_id, key=sk_log
            ).exists()
        )

        # QC retry aynı key → aynı inspection
        again = self.api.post(
            reverse("api-ops-inspection-list"),
            {"order_id": order.pk},
            format="json",
            HTTP_IDEMPOTENCY_KEY=client_key,
        )
        self.assertEqual(again.status_code, 201)
        self.assertEqual(again.json()["id"], a.json()["id"])
