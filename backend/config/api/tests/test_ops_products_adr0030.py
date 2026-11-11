"""ADR-0030 — ops products HTTP create → submit → approve → publish."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from urunler.models import Urun

User = get_user_model()


class OpsProductsAdr0030Tests(PriceQuoteFixtureMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.submitter = User(
            username="ops_prod_submit",
            firma=cls.platform,
            rol=roles.PLATFORM_CATALOG,
            is_staff=True,
        )
        cls.submitter.set_password("x")
        cls.submitter.save()
        sync_user_role_groups(cls.submitter)

        cls.approver = User(
            username="ops_prod_approve",
            firma=cls.platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.approver.set_password("x")
        cls.approver.save()
        sync_user_role_groups(cls.approver)

        cls.buyer_u = User(
            username="ops_prod_buyer",
            firma=cls.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.buyer_u.set_password("x")
        cls.buyer_u.save()
        sync_user_role_groups(cls.buyer_u)

    def setUp(self):
        self.api = APIClient()

    def _idem(self, key):
        return {"HTTP_IDEMPOTENCY_KEY": key}

    def test_lifecycle_and_tenant_deny(self):
        self.api.force_authenticate(user=self.submitter)
        create = self.api.post(
            reverse("api-ops-products"),
            {
                "ad": "Ops HTTP Ürün",
                "kategori_id": self.urun.kategori_id,
                "ayar_id": self.ayar.pk,
                "aciklama": "ADR-0030",
                "satis_kanali_id": self.kanal.pk,
            },
            format="json",
            **self._idem("ops-p-create-1"),
        )
        self.assertEqual(create.status_code, 201, create.content)
        body = create.json()
        self.assertEqual(body["onay_durumu"], "taslak")
        self.assertEqual(body["yayin_durumu"], "pasif")
        self.assertEqual(body["olusturan_firma_id"], self.platform.pk)
        self.assertNotIn("tedarikci_sku", str(body))
        pid = body["id"]

        var = self.api.post(
            reverse("api-ops-product-variants", kwargs={"pk": pid}),
            {"gram": "2.500", "ek_bedel": "5.00"},
            format="json",
            **self._idem("ops-p-var-1"),
        )
        self.assertEqual(var.status_code, 201, var.content)
        self.assertEqual(Decimal(var.json()["gram"]), Decimal("2.500"))

        sub = self.api.post(
            reverse("api-ops-product-submit", kwargs={"pk": pid}),
            {},
            format="json",
            **self._idem("ops-p-sub-1"),
        )
        self.assertEqual(sub.status_code, 200, sub.content)
        self.assertEqual(sub.json()["onay_durumu"], "onay_bekliyor")

        # dört göz: submitter cannot approve
        bad = self.api.post(
            reverse("api-ops-product-approve", kwargs={"pk": pid}),
            {},
            format="json",
            **self._idem("ops-p-appr-self"),
        )
        self.assertIn(bad.status_code, (400, 403), bad.content)

        self.api.force_authenticate(user=self.approver)
        appr = self.api.post(
            reverse("api-ops-product-approve", kwargs={"pk": pid}),
            {},
            format="json",
            **self._idem("ops-p-appr-1"),
        )
        self.assertEqual(appr.status_code, 200, appr.content)
        self.assertEqual(appr.json()["onay_durumu"], "onayli")

        pub = self.api.post(
            reverse("api-ops-product-publish", kwargs={"pk": pid}),
            {"durum": "aktif"},
            format="json",
            **self._idem("ops-p-pub-1"),
        )
        self.assertEqual(pub.status_code, 200, pub.content)
        self.assertEqual(pub.json()["yayin_durumu"], "aktif")

        urun = Urun.objects.get(pk=pid)
        self.assertEqual(urun.onay_durumu, "onayli")
        self.assertEqual(urun.yayin_durumu, "aktif")

        self.api.force_authenticate(user=self.buyer_u)
        deny = self.api.get(reverse("api-ops-products"))
        self.assertIn(deny.status_code, (403, 401), deny.content)

    def test_list_filters(self):
        self.api.force_authenticate(user=self.submitter)
        res = self.api.get(reverse("api-ops-products"), {"onay_durumu": "onayli"})
        self.assertEqual(res.status_code, 200, res.content)
        self.assertIn("results", res.json())
