"""F4-040/041 — Checkout lock+rezervasyon + fail durable audit."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import PriceLock
from fiyatlama.services import pricing_service
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from siparis.models import CheckoutAttempt
from siparis.services import cart_servisi, checkout_servisi
from stok.models import StockBalance, StockMovement, StockReservation
from stok.services import ledger_servisi, warehouse_servisi

User = get_user_model()


class CheckoutFixtureMixin(PriceQuoteFixtureMixin):
    @classmethod
    def _build_checkout_world(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.buyer = User(
            username="co_buyer",
            firma=cls.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)

        cls.ted_user = User(
            username="co_ted",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.ted_user.set_password("x")
        cls.ted_user.save()
        sync_user_role_groups(cls.ted_user)

        cls.wh = warehouse_servisi.olustur_warehouse(
            actor=cls.ted_user,
            sahip_firma=cls.ted,
            kod="COWH",
            ad="Checkout depo",
        )
        ledger_servisi.kaydet_hareket(
            actor=cls.ted_user,
            warehouse=cls.wh,
            teklif=cls.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("100"),
        )

    def _quote_and_cart(self, miktar=Decimal("2")):
        quote = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        cart_servisi.satir_ekle(
            actor=self.buyer, price_quote=quote, miktar=miktar
        )
        return quote


class CheckoutServiceTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def test_checkout_creates_lock_and_reservation(self):
        self._quote_and_cart()
        result = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="co-ok-1"
        )
        self.assertEqual(result.attempt.durum, CheckoutAttempt.Durum.BASARILI)
        self.assertEqual(len(result.lines), 1)
        self.assertTrue(PriceLock.objects.filter(pk=result.lines[0].lock_id).exists())
        self.assertTrue(
            StockReservation.objects.filter(
                pk=result.lines[0].reservation_id,
                durum=StockReservation.Durum.AKTIF,
            ).exists()
        )
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.reserved, Decimal("2"))
        self.assertEqual(bal.on_hand, Decimal("100"))

    def test_checkout_idempotent(self):
        self._quote_and_cart()
        a = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="co-idem"
        )
        b = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="co-idem"
        )
        self.assertEqual(a.attempt.pk, b.attempt.pk)
        self.assertEqual(a.lines[0].lock_id, b.lines[0].lock_id)
        self.assertEqual(
            StockReservation.objects.filter(
                durum=StockReservation.Durum.AKTIF
            ).count(),
            1,
        )

    def test_expired_quote_fails(self):
        quote = self._quote_and_cart()
        after = quote.gecerlilik_sonu + timedelta(seconds=1)
        with self.assertRaises(ValidationError):
            checkout_servisi.checkout(
                actor=self.buyer, idempotency_key="co-exp", now=after
            )
        self.assertFalse(
            CheckoutAttempt.objects.filter(
                idempotency_key="co-exp", durum=CheckoutAttempt.Durum.BASARILI
            ).exists()
        )

    def test_empty_cart_fails(self):
        cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        with self.assertRaises(ValidationError):
            checkout_servisi.checkout(
                actor=self.buyer, idempotency_key="co-empty"
            )


class CheckoutFailAuditTests(CheckoutFixtureMixin, TransactionTestCase):
    def setUp(self):
        self._build_checkout_world()

    def test_fail_audit_survives(self):
        cart_servisi.al_veya_olustur_sepet(actor=self.buyer)
        before = AuditOlay.objects.filter(
            action="checkout.fail", success=False
        ).count()
        with self.assertRaises(ValidationError):
            checkout_servisi.checkout(
                actor=self.buyer, idempotency_key="co-fail-aud"
            )
        after = AuditOlay.objects.filter(
            action="checkout.fail", success=False
        ).count()
        self.assertGreater(after, before)
