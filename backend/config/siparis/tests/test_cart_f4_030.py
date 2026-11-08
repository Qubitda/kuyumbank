"""F4-030/031 — Cart tenant izolasyonu + quote satırı (stok düşmez)."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.services import pricing_service
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from siparis.models import CartLine
from siparis.selectors.tenant import CartNotFound, get_cart_for_actor
from siparis.services import cart_servisi
from stok.birim_constants import StokBirimi
from stok.models import StockMovement

User = get_user_model()


class CartServiceTests(PriceQuoteFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.buyer = User(
            username="cart_buyer",
            firma=cls.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)

        cls.other_firma = Firma.objects.create(
            ad="CART2", firma_kodu="CART2", alici_mi=True
        )
        cls.other_buyer = User(
            username="cart_buyer2",
            firma=cls.other_firma,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.other_buyer.set_password("x")
        cls.other_buyer.save()
        sync_user_role_groups(cls.other_buyer)

        cls.ted_user = User(
            username="cart_ted",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.ted_user.set_password("x")
        cls.ted_user.save()
        sync_user_role_groups(cls.ted_user)

    def _quote(self):
        return pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )

    def test_create_cart_for_buyer(self):
        cart = cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        self.assertEqual(cart.alici_firma_id, self.alici.pk)
        again = cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        self.assertEqual(cart.pk, again.pk)

    def test_supplier_cannot_create_cart(self):
        with self.assertRaises(PermissionDenied):
            cart_servisi.al_veya_olustur_sepet(actor=self.ted_user)

    def test_cross_tenant_cart_not_found(self):
        cart = cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        with self.assertRaises(CartNotFound):
            get_cart_for_actor(self.other_buyer, cart_id=cart.pk)

    def test_add_line_quote_gram_no_stock_movement(self):
        quote = self._quote()
        line = cart_servisi.satir_ekle(
            actor=self.buyer, price_quote=quote, miktar=Decimal("2")
        )
        self.assertEqual(line.birim, StokBirimi.GRAM)
        self.assertEqual(line.varyant_id, quote.varyant_id)
        self.assertEqual(line.price_quote_id, quote.pk)
        self.assertFalse(StockMovement.objects.exists())
        dto = cart_servisi.present_cart_line(line)
        self.assertNotIn("teklif", dto)
        self.assertNotIn("tedarikci", dto)
        self.assertEqual(dto["quote_id"], quote.pk)

    def test_add_line_merges_same_varyant(self):
        quote = self._quote()
        cart_servisi.satir_ekle(
            actor=self.buyer, price_quote=quote, miktar=Decimal("1")
        )
        line = cart_servisi.satir_ekle(
            actor=self.buyer, price_quote=quote, miktar=Decimal("3")
        )
        self.assertEqual(CartLine.objects.filter(cart=line.cart).count(), 1)
        self.assertEqual(line.miktar, Decimal("3"))

    def test_expired_quote_rejected(self):
        quote = self._quote()
        after = quote.gecerlilik_sonu + timedelta(seconds=1)
        with self.assertRaises(ValidationError):
            cart_servisi.satir_ekle(
                actor=self.buyer,
                price_quote=quote,
                miktar=Decimal("1"),
                now=after,
            )

    def test_passive_varyant_rejected(self):
        quote = self._quote()
        self.varyant.aktif = False
        self.varyant.save(update_fields=["aktif"])
        with self.assertRaises(ValidationError):
            cart_servisi.satir_ekle(
                actor=self.buyer, price_quote=quote, miktar=Decimal("1")
            )

    def test_other_firma_quote_rejected(self):
        quote = self._quote()
        with self.assertRaises(ValidationError):
            cart_servisi.satir_ekle(
                actor=self.other_buyer, price_quote=quote, miktar=Decimal("1")
            )

    def test_remove_line(self):
        quote = self._quote()
        line = cart_servisi.satir_ekle(
            actor=self.buyer, price_quote=quote, miktar=Decimal("1")
        )
        cart_servisi.satir_sil(actor=self.buyer, line=line)
        self.assertFalse(CartLine.objects.filter(pk=line.pk).exists())

    def test_zero_miktar_rejected(self):
        quote = self._quote()
        with self.assertRaises(ValidationError):
            cart_servisi.satir_ekle(
                actor=self.buyer, price_quote=quote, miktar=Decimal("0")
            )
