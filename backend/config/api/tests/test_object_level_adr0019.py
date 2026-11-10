"""ADR-0019 OL-11 — Permission + IDOR; SoD (denetçi/onaycı W yok); yeni uç yok."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from django.test import TestCase

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.services import cart_servisi, checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class ObjectLevelAdr0019Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)
        sync_user_role_groups(cls.ted_user)

        cls.denetci = User(
            username="ol_denetci",
            firma=cls.alici,
            rol=roles.ALICI_DENETCI,
            is_staff=True,
        )
        cls.denetci.set_password("x")
        cls.denetci.save()
        sync_user_role_groups(cls.denetci)

        cls.onayci = User(
            username="ol_onay",
            firma=cls.alici,
            rol=roles.ALICI_ONAYLAYICI,
            is_staff=True,
        )
        cls.onayci.set_password("x")
        cls.onayci.save()
        sync_user_role_groups(cls.onayci)

        cls.support = User(
            username="ol_support",
            firma=cls.platform,
            rol=roles.PLATFORM_SUPPORT,
            is_staff=True,
        )
        cls.support.set_password("x")
        cls.support.save()
        sync_user_role_groups(cls.support)

    def setUp(self):
        self.api = APIClient()

    def _order(self, key: str):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_cross_tenant_order_404(self):
        order = self._order("ol-idor-1")
        other_firma = Firma.objects.create(
            ad="OL2", firma_kodu="OL2", alici_mi=True
        )
        other = User(
            username="ol_other",
            firma=other_firma,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        other.set_password("x")
        other.save()
        sync_user_role_groups(other)
        self.api.force_authenticate(user=other)
        res = self.api.get(reverse("api-order-detail", kwargs={"pk": order.pk}))
        self.assertEqual(res.status_code, 404)

    def test_denetci_order_get_ok_checkout_forbidden(self):
        order = self._order("ol-den-1")
        cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        self.api.force_authenticate(user=self.denetci)
        self.assertEqual(
            self.api.get(reverse("api-order-detail", kwargs={"pk": order.pk})).status_code,
            200,
        )
        self.api.credentials(HTTP_IDEMPOTENCY_KEY="ol-den-co")
        res = self.api.post(reverse("api-checkout-create"), {}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_onayci_commerce_write_forbidden_order_get_ok(self):
        order = self._order("ol-onay-1")
        self.api.force_authenticate(user=self.onayci)
        self.assertEqual(
            self.api.get(reverse("api-order-detail", kwargs={"pk": order.pk})).status_code,
            200,
        )
        self.api.credentials(HTTP_IDEMPOTENCY_KEY="ol-onay-co")
        self.assertEqual(
            self.api.post(reverse("api-checkout-create"), {}, format="json").status_code,
            403,
        )
        self.api.credentials(HTTP_IDEMPOTENCY_KEY="ol-onay-cancel")
        self.assertEqual(
            self.api.post(
                reverse("api-order-cancel", kwargs={"pk": order.pk}), {}, format="json"
            ).status_code,
            403,
        )

    def test_support_order_list_forbidden(self):
        self.api.force_authenticate(user=self.support)
        self.assertEqual(self.api.get(reverse("api-order-list")).status_code, 403)

    def test_supplier_order_forbidden(self):
        order = self._order("ol-ted-1")
        self.api.force_authenticate(user=self.ted_user)
        self.assertEqual(self.api.get(reverse("api-order-list")).status_code, 403)
        self.assertEqual(
            self.api.get(reverse("api-order-detail", kwargs={"pk": order.pk})).status_code,
            403,
        )

    def test_quote_cross_tenant_404(self):
        from fiyatlama.services import pricing_service

        quote = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        other_firma = Firma.objects.create(
            ad="OLQ", firma_kodu="OLQ", alici_mi=True
        )
        other = User(
            username="ol_q_other",
            firma=other_firma,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        other.set_password("x")
        other.save()
        sync_user_role_groups(other)
        self.api.force_authenticate(user=other)
        res = self.api.get(reverse("api-quote-detail", kwargs={"pk": quote.pk}))
        self.assertEqual(res.status_code, 404)
