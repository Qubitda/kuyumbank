"""ADR-0014 KS-6 — hedef_toplam → PriceQuote (banka/GV yok)."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import PriceQuoteLine
from fiyatlama.services import fiyat_hesaplama, pricing_service
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class Ks6HedefToplamQuoteTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def test_pure_math_hedef_toplam(self):
        s = fiyat_hesaplama.hesapla_hedef_toplam(
            hedef_toplam=Decimal("120000"),
            gram=Decimal("10"),
        )
        self.assertEqual(s["fiyat_modeli"], "HEDEF_TOPLAM")
        self.assertEqual(s["toplam_vergisiz"], Decimal("120000.00"))
        self.assertEqual(s["kalemler_yuvarlanmis"]["hedef_toplam"], Decimal("120000.00"))

    def test_quote_hedef_toplam_platform(self):
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
            hedef_toplam=Decimal("9999.50"),
        )
        self.assertEqual(pq.fiyat_modeli, "HEDEF_TOPLAM")
        self.assertEqual(pq.toplam_vergisiz, Decimal("9999.50"))
        self.assertEqual(pq.hesap_girdisi.get("hedef_toplam"), "9999.50")
        self.assertIsNone(pq.hesap_girdisi.get("banka_gv_isletme"))
        line = pq.satirlar.get(kalem_tipi=PriceQuoteLine.KalemTipi.HEDEF_TOPLAM)
        self.assertEqual(line.tutar, Decimal("9999.50"))
        # Tek satır tipi — klasik metal/marj satırı yok
        self.assertEqual(pq.satirlar.count(), 1)

    def test_buyer_cannot_force_hedef(self):
        with self.assertRaises(PermissionDenied):
            pricing_service.quote(
                alici_firma=self.alici,
                satis_kanali=self.kanal,
                varyant=self.varyant,
                kullanici=self.buyer,
                hedef_toplam=Decimal("1000"),
            )

    def test_hedef_must_be_positive(self):
        with self.assertRaises(ValidationError):
            pricing_service.quote(
                alici_firma=self.alici,
                satis_kanali=self.kanal,
                varyant=self.varyant,
                kullanici=self.finance,
                hedef_toplam=Decimal("0"),
            )

    def test_normal_quote_unchanged_without_hedef(self):
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        self.assertNotEqual(pq.fiyat_modeli, "HEDEF_TOPLAM")
        self.assertGreater(pq.toplam_vergisiz, Decimal("0"))
