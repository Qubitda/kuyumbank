"""F11-011 — platform quote/lock özeti; maliyet sızıntısı yok."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.services import fiyat_analitik_servisi, pricing_service
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin

User = get_user_model()


class FiyatAnalitikF11011Tests(PriceQuoteFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)
        cls.buyer = User(
            username="fa_buyer",
            firma=cls.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)

    def test_platform_quote_ozet(self):
        pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        ozet = fiyat_analitik_servisi.quote_ozet(
            actor=self.finance, alici_firma_id=self.alici.pk
        )
        self.assertGreaterEqual(ozet["adet"], 1)
        self.assertNotIn("maliyet", ozet)
        self.assertNotIn("tedarikci", str(ozet).lower())

    def test_buyer_denied(self):
        with self.assertRaises(PermissionDenied):
            fiyat_analitik_servisi.quote_ozet(actor=self.buyer)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="fiyatlama.analitik.denied", success=False
            ).exists()
        )

    def test_lock_ozet(self):
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        pricing_service.lock_quote(pq, kullanici=self.buyer)
        ozet = fiyat_analitik_servisi.lock_ozet(
            actor=self.finance, alici_firma_id=self.alici.pk
        )
        self.assertGreaterEqual(ozet["adet"], 1)
