"""F11-010 ticari özet + F11-021 alıcı davranış; tenant + kör."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar.models import AuditOlay, Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.services import pricing_service
from siparis.services import checkout_servisi, order_servisi, rapor_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class RaporF11010F11021Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)
        sync_user_role_groups(cls.finance)
        sync_user_role_groups(cls.ted_user)

    def _order(self, key: str):
        self._quote_and_cart(miktar=Decimal("2"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_f11_010_platform_ticari_ozet(self):
        self._order("rap-ord-1")
        ozet = rapor_servisi.ticari_siparis_ozet(
            actor=self.finance, alici_firma_id=self.alici.pk
        )
        self.assertGreaterEqual(ozet["siparis_adet"], 1)
        self.assertGreater(Decimal(ozet["ciro_vergisiz"]), 0)
        self.assertEqual(ozet["read_model"], "live_orm")
        self.assertNotIn("tedarikci", str(ozet).lower())
        self.assertNotIn("maliyet", str(ozet).lower())

    def test_f11_010_buyer_own_scope(self):
        self._order("rap-ord-2")
        ozet = rapor_servisi.ticari_siparis_ozet(actor=self.buyer)
        self.assertEqual(ozet["alici_firma_id"], self.alici.pk)
        self.assertGreaterEqual(ozet["siparis_adet"], 1)

    def test_f11_010_supplier_denied(self):
        with self.assertRaises(PermissionDenied):
            rapor_servisi.ticari_siparis_ozet(actor=self.ted_user)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="siparis.rapor.denied", success=False
            ).exists()
        )

    def test_f11_010_buyer_ignores_foreign_firma_id(self):
        """Alıcı client alici_firma_id ile çapraz tenant göremez."""
        self._order("rap-ord-x")
        other = Firma.objects.create(
            ad="RAPX", firma_kodu="RAPX", alici_mi=True
        )
        ozet = rapor_servisi.ticari_siparis_ozet(
            actor=self.buyer, alici_firma_id=other.pk
        )
        self.assertEqual(ozet["alici_firma_id"], self.alici.pk)
        self.assertNotEqual(ozet["alici_firma_id"], other.pk)

    def test_f11_021_buyer_behavior(self):
        pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        self._order("rap-ord-3")
        ozet = rapor_servisi.alici_davranis_ozet(
            actor=self.finance, alici_firma_id=self.alici.pk
        )
        self.assertEqual(ozet["alici_firma_id"], self.alici.pk)
        self.assertGreaterEqual(ozet["quote_adet"], 1)
        self.assertGreaterEqual(ozet["siparis_adet"], 1)
        blob = str(ozet).lower()
        self.assertNotIn("tedarikci", blob)
        self.assertNotIn("maliyet", blob)

    def test_f11_021_platform_requires_firma(self):
        with self.assertRaises(ValidationError):
            rapor_servisi.alici_davranis_ozet(actor=self.finance)
