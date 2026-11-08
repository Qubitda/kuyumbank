"""F4-080 — Quick Reorder: Order → güncel quote → Cart; ATP fail-closed."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from siparis.models import CartLine
from siparis.services import (
    cart_servisi,
    checkout_servisi,
    order_servisi,
    reorder_servisi,
)
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.models import StockBalance, StockMovement
from stok.services import ledger_servisi


class ReorderServiceTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def _create_order(self, key="ro-1", miktar=Decimal("2")):
        self._quote_and_cart(miktar=miktar)
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key=key
        )
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_reorder_fills_cart_with_fresh_quote(self):
        order = self._create_order()
        # Stok tüketildi; iade ile ATP aç
        order_servisi.iptal_siparis(actor=self.buyer, order=order)
        order.refresh_from_db()

        cart = reorder_servisi.sepete_aktar(actor=self.buyer, order=order)
        self.assertEqual(cart.lines.count(), 1)
        line = cart.lines.get()
        self.assertEqual(line.miktar, Decimal("2"))
        self.assertEqual(line.varyant_id, order.lines.get().varyant_id)
        # Eski lock fiyatı değil — yeni quote
        self.assertNotEqual(line.price_quote_id, order.lines.get().price_lock.quote_id)
        self.assertIsNone(getattr(line, "price_lock_id", None))

    def test_reorder_replaces_existing_cart(self):
        order = self._create_order(key="ro-repl")
        order_servisi.iptal_siparis(actor=self.buyer, order=order)
        # Sepete yabancı satır
        q = self._quote_and_cart(miktar=Decimal("1"))
        self.assertTrue(CartLine.objects.filter(price_quote=q).exists())

        cart = reorder_servisi.sepete_aktar(
            actor=self.buyer, order=order, replace_cart=True
        )
        self.assertEqual(cart.lines.count(), 1)
        self.assertEqual(cart.lines.get().miktar, Decimal("2"))

    def test_reorder_atp_fail_closed(self):
        order = self._create_order(key="ro-atp", miktar=Decimal("2"))
        order_servisi.iptal_siparis(actor=self.buyer, order=order)
        # Available'ı 1'e düşür
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        ledger_servisi.kaydet_hareket(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=self.teklif,
            tip=StockMovement.Tip.CIKIS,
            miktar=bal.on_hand - Decimal("1"),
        )
        with self.assertRaises(ValidationError) as ctx:
            reorder_servisi.sepete_aktar(actor=self.buyer, order=order)
        self.assertIn("ATP", str(ctx.exception))
        # Fail-closed: sepet boş kalmalı (replace öncesi hazırlık fail)
        cart = cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        self.assertFalse(CartLine.objects.filter(cart=cart).exists())

    def test_reorder_tenant_idor(self):
        order = self._create_order(key="ro-idor")
        order_servisi.iptal_siparis(actor=self.buyer, order=order)
        with self.assertRaises(PermissionDenied):
            reorder_servisi.sepete_aktar(actor=self.ted_user, order=order)
