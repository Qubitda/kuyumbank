"""F10-022 — özel üretim talep tipi + revizyon geçmişi."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.models import RFQ, RFQRevizyon
from siparis.services import rfq_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class RfqOzelF10022Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)

    def setUp(self):
        self.client = Client()

    def test_ozel_uretim_creates_revision_v1(self):
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="Özel yüzük",
            talep_tipi=RFQ.TalepTipi.OZEL_URETIM,
            line_specs=[
                {
                    "aciklama": "El işçiliği, 18 ayar",
                    "miktar": Decimal("2"),
                    "birim": "ADET",
                }
            ],
        )
        self.assertEqual(rfq.talep_tipi, RFQ.TalepTipi.OZEL_URETIM)
        rev = RFQRevizyon.objects.get(rfq=rfq)
        self.assertEqual(rev.sira, 1)
        self.assertIn("İlk", rev.ozet)

        rev2 = rfq_servisi.revizyon_ekle(
            actor=self.buyer, rfq=rfq, ozet="Taş rengi değiştirildi"
        )
        self.assertEqual(rev2.sira, 2)
        self.assertEqual(rfq.revizyonlar.count(), 2)

    def test_revision_blocked_for_katalog_disi(self):
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="Katalog dışı",
            talep_tipi=RFQ.TalepTipi.KATALOG_DISI,
            line_specs=[
                {"aciklama": "x", "miktar": Decimal("1"), "birim": "ADET"}
            ],
        )
        with self.assertRaises(ValidationError):
            rfq_servisi.revizyon_ekle(
                actor=self.buyer, rfq=rfq, ozet="olmamalı"
            )

    def test_buyer_ui_ozel_and_revision(self):
        self.client.force_login(self.buyer)
        res = self.client.post(
            reverse("buyer-rfq-create"),
            {
                "baslik": "Tasarım bilezik",
                "talep_tipi": "OZEL_URETIM",
                "aciklama": "CAD revizyonlu",
                "miktar": "1",
                "birim": "ADET",
            },
        )
        self.assertEqual(res.status_code, 302)
        rfq = RFQ.objects.get(alici_firma=self.buyer.firma, talep_tipi="OZEL_URETIM")
        det = self.client.get(reverse("buyer-rfq-detail", kwargs={"pk": rfq.pk}))
        self.assertEqual(det.status_code, 200)
        self.assertContains(det, "OZEL_URETIM")
        self.assertContains(det, "Revizyon geçmişi")
        self.assertNotContains(det, "tedarikci")

        rev = self.client.post(
            reverse("buyer-rfq-revision", kwargs={"pk": rfq.pk}),
            {"ozet": "Ölçü 16.5 olarak güncellendi"},
        )
        self.assertEqual(rev.status_code, 302)
        self.assertEqual(rfq.revizyonlar.count(), 2)
        det2 = self.client.get(reverse("buyer-rfq-detail", kwargs={"pk": rfq.pk}))
        self.assertContains(det2, "Ölçü 16.5")
