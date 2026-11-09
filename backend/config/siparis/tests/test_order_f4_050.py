"""F4-050/051/052 — Order + snapshot + rezervasyon tüketimi."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from fiyatlama.models import PriceLock
from siparis.models import CartLine, CheckoutAttempt, Order
from siparis.services import cart_servisi, checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.models import StockBalance, StockMovement, StockReservation


class OrderServiceTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def _checkout(self, key="ord-1", miktar=Decimal("2")):
        self._quote_and_cart(miktar=miktar)
        return checkout_servisi.checkout(
            actor=self.buyer, idempotency_key=key
        )

    def test_create_order_from_checkout(self):
        co = self._checkout()
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        self.assertEqual(order.durum, Order.Durum.OLUSTURULDU)
        self.assertEqual(order.lines.count(), 1)
        line = order.lines.get()
        self.assertEqual(line.miktar, Decimal("2"))
        self.assertEqual(line.price_lock_id, co.lines[0].lock_id)
        lock = PriceLock.objects.select_related("quote").get(pk=line.price_lock_id)
        # GRAM: lock.toplam = quote.gram için; birim = gram başına, satır = × miktar
        birim = (lock.toplam_vergisiz / lock.quote.gram).quantize(Decimal("0.01"))
        self.assertEqual(line.snapshot_birim_fiyat_vergisiz, birim)
        self.assertEqual(line.para_birimi, lock.para_birimi)
        self.assertEqual(
            line.snapshot_satir_tutari_vergisiz,
            (birim * Decimal("2")).quantize(Decimal("0.01")),
        )

    def test_reservation_consumed_and_satis_movement(self):
        co = self._checkout(key="ord-consume")
        order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        res = StockReservation.objects.get(pk=co.lines[0].reservation_id)
        self.assertEqual(res.durum, StockReservation.Durum.TUKETILDI)
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.reserved, Decimal("0"))
        self.assertEqual(bal.on_hand, Decimal("98"))
        self.assertTrue(
            StockMovement.objects.filter(
                tip=StockMovement.Tip.SATIS, miktar=Decimal("-2")
            ).exists()
        )

    def test_idempotent_order_create(self):
        co = self._checkout(key="ord-idem")
        a = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        b = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(
            StockReservation.objects.filter(
                durum=StockReservation.Durum.TUKETILDI
            ).count(),
            1,
        )

    def test_order_line_immutable(self):
        co = self._checkout(key="ord-imm")
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        line = order.lines.get()
        line.snapshot_satir_tutari_vergisiz = Decimal("0.01")
        with self.assertRaises(ValidationError):
            line.save()

    def test_cart_cleared_after_order(self):
        co = self._checkout(key="ord-cart")
        self.assertTrue(CartLine.objects.filter(cart=co.attempt.cart).exists())
        order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        self.assertFalse(CartLine.objects.filter(cart=co.attempt.cart).exists())

    def test_failed_checkout_cannot_order(self):
        cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        with self.assertRaises(ValidationError):
            checkout_servisi.checkout(
                actor=self.buyer, idempotency_key="ord-fail-co"
            )
        attempt = CheckoutAttempt.objects.get(idempotency_key="ord-fail-co")
        self.assertEqual(attempt.durum, CheckoutAttempt.Durum.BASARISIZ)
        with self.assertRaises(ValidationError):
            order_servisi.olustur_from_checkout(
                actor=self.buyer, checkout_attempt=attempt
            )
