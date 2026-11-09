"""F8-007 — tenant/IDOR güvenlik smoke (checklist yüzeyi)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from firmalar import roles
from firmalar.models import Firma, OnayTalebi
from firmalar.role_permissions import seed_role_permissions
from firmalar.services import onay_servisi
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.models import RFQ
from siparis.services import cart_servisi, checkout_servisi, order_servisi, rfq_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class SecurityIdorF8007Tests(CheckoutFixtureMixin, TestCase):
    """Çapraz tenant → 404/403; supplier buyer yüzeyine giremez; client firma_id yok sayılır."""

    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)

        cls.other_alici = Firma.objects.create(
            ad="SEC2", firma_kodu="SEC2", alici_mi=True
        )
        cls.other_buyer = User(
            username="sec_other_buyer",
            firma=cls.other_alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.other_buyer.set_password("x")
        cls.other_buyer.save()
        sync_user_role_groups(cls.other_buyer)

        cls.approver = User(
            username="sec_appr",
            firma=cls.alici,
            rol=roles.ALICI_ONAYLAYICI,
            is_staff=True,
        )
        cls.approver.set_password("x")
        cls.approver.save()
        sync_user_role_groups(cls.approver)

    def setUp(self):
        self.api = APIClient()
        self.browser = Client()

    def _order(self, key="sec-ord-1"):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_api_order_cross_tenant_404(self):
        order = self._order()
        self.api.force_authenticate(user=self.other_buyer)
        res = self.api.get(reverse("api-order-detail", kwargs={"pk": order.pk}))
        self.assertEqual(res.status_code, 404)

    def test_api_cart_ignores_client_firma_id(self):
        cart = cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get(reverse("api-cart-mine"), {"firma_id": self.other_alici.pk})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], cart.pk)

    def test_supplier_buyer_surfaces_forbidden(self):
        order = self._order(key="sec-sup-1")
        self.api.force_authenticate(user=self.ted_user)
        self.assertEqual(self.api.get(reverse("api-order-list")).status_code, 403)
        self.assertEqual(
            self.api.get(
                reverse("api-order-detail", kwargs={"pk": order.pk})
            ).status_code,
            403,
        )
        self.browser.force_login(self.ted_user)
        self.assertEqual(self.browser.get(reverse("buyer-cart")).status_code, 403)
        self.assertEqual(
            self.browser.get(reverse("buyer-rfq-list")).status_code, 403
        )

    def test_buyer_ui_approval_cross_tenant_404(self):
        ot = onay_servisi.olustur(
            actor=self.approver,
            firma=self.alici,
            tutar=Decimal("33.00"),
        )
        ot = onay_servisi.beklemede_al(actor=self.approver, onay=ot)
        other_appr = User(
            username="sec_appr2",
            firma=self.other_alici,
            rol=roles.ALICI_ONAYLAYICI,
            is_staff=True,
        )
        other_appr.set_password("x")
        other_appr.save()
        sync_user_role_groups(other_appr)
        self.browser.force_login(other_appr)
        res = self.browser.post(
            reverse("buyer-approval-action", kwargs={"pk": ot.pk}),
            {"action": "onayla"},
        )
        self.assertEqual(res.status_code, 404)
        ot.refresh_from_db()
        self.assertEqual(ot.durum, OnayTalebi.Durum.BEKLEMEDE)

    def test_rfq_detail_cross_actor_denied(self):
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="SEC RFQ",
            line_specs=[
                {"aciklama": "x", "miktar": Decimal("1"), "birim": "ADET"}
            ],
        )
        self.assertEqual(RFQ.objects.filter(pk=rfq.pk).count(), 1)
        self.browser.force_login(self.other_buyer)
        res = self.browser.get(reverse("buyer-rfq-detail", kwargs={"pk": rfq.pk}))
        self.assertEqual(res.status_code, 404)
