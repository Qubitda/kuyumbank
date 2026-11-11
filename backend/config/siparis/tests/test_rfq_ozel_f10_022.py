"""F10-022 — özel üretim talep tipi + revizyon geçmişi."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

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

    def test_ozel_uretim_revision_has_no_supplier_leak_in_fields(self):
        """HTML buyer RFQ UI kaldırıldı (ADR-0029); HTTP kanıtı api.tests.test_api_b4_enterprise."""
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="Tasarım bilezik",
            talep_tipi=RFQ.TalepTipi.OZEL_URETIM,
            line_specs=[
                {
                    "aciklama": "CAD revizyonlu",
                    "miktar": Decimal("1"),
                    "birim": "ADET",
                }
            ],
        )
        rfq_servisi.revizyon_ekle(
            actor=self.buyer, rfq=rfq, ozet="Ölçü 16.5 olarak güncellendi"
        )
        self.assertEqual(rfq.revizyonlar.count(), 2)
        for rev in rfq.revizyonlar.all():
            self.assertFalse(hasattr(rev, "tedarikci"))
