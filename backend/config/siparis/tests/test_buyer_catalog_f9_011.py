"""F9-011 — Katalog browse UI (kör; maliyet/tedarikçi yok)."""

from django.test import Client, TestCase
from django.urls import reverse

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from urunler.models import Urun


class BuyerCatalogF9011Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)
        # fixture ürünü zaten onaylı+aktif (quote world)
        cls.urun = Urun.objects.get(pk=cls.varyant.urun_id)

    def setUp(self):
        self.client = Client()

    def test_login_required(self):
        res = self.client.get(reverse("buyer-catalog"))
        self.assertEqual(res.status_code, 302)
        self.assertIn("/buyer/login/", res.url)

    def test_supplier_forbidden(self):
        self.client.force_login(self.ted_user)
        res = self.client.get(reverse("buyer-catalog"))
        self.assertEqual(res.status_code, 403)

    def test_buyer_list_and_detail_masked(self):
        self.client.force_login(self.buyer)
        res = self.client.get(reverse("buyer-catalog"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.urun.ad)
        self.assertNotContains(res, "tedarikci_sku")
        self.assertNotContains(res, "olusturan_firma")
        self.assertNotContains(res, self.ted.ad)

        det = self.client.get(
            reverse("buyer-catalog-detail", kwargs={"pk": self.urun.pk})
        )
        self.assertEqual(det.status_code, 200)
        self.assertContains(det, self.urun.ad)
        self.assertContains(det, self.varyant.sku)
        self.assertNotContains(det, "tedarikci_sku")
        self.assertNotContains(det, "tedarikci")
        self.assertNotContains(det, self.ted.ad)

    def test_search_filters(self):
        self.client.force_login(self.buyer)
        res = self.client.get(reverse("buyer-catalog"), {"q": self.urun.ad[:4]})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.urun.ad)
        miss = self.client.get(reverse("buyer-catalog"), {"q": "zzz-no-match-xxx"})
        self.assertEqual(miss.status_code, 200)
        self.assertContains(miss, "Sonuç yok")

    def test_unpublished_404(self):
        self.urun.yayin_durumu = "pasif"
        # yayın yalnız servisten; test için force flag yoksa update
        Urun.objects.filter(pk=self.urun.pk).update(yayin_durumu="pasif")
        self.client.force_login(self.buyer)
        res = self.client.get(
            reverse("buyer-catalog-detail", kwargs={"pk": self.urun.pk})
        )
        self.assertEqual(res.status_code, 404)
