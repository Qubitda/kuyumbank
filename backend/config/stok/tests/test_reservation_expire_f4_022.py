"""F4-022 — Stale reservation expire: lazy sweep, durable order-fail expire, command."""

from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.models import StockBalance, StockMovement, StockReservation
from stok.services import ledger_servisi, reservation_servisi, warehouse_servisi

User = get_user_model()


class LazyExpireOnCreateTests(PriceQuoteFixtureMixin, TestCase):
    """(a) TTL dolmuş AKTIF hold, yeni rezervasyon talebinde süpürülmeli."""

    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.ted_user = User(
            username="exp_ted",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.ted_user.set_password("x")
        cls.ted_user.save()
        sync_user_role_groups(cls.ted_user)
        cls.buyer = User(
            username="exp_buyer",
            firma=cls.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)
        cls.wh = warehouse_servisi.olustur_warehouse(
            actor=cls.ted_user,
            sahip_firma=cls.ted,
            kod="EXPWH",
            ad="Expire depo",
        )
        ledger_servisi.kaydet_hareket(
            actor=cls.ted_user,
            warehouse=cls.wh,
            teklif=cls.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("10"),
        )

    def test_create_sweeps_expired_aktif_and_frees_available(self):
        t0 = timezone.now()
        stale = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("10"),
            alici_firma=self.alici,
            ttl_seconds=60,
            now=t0,
        )
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.reserved, Decimal("10"))
        self.assertEqual(bal.available, Decimal("0"))

        after = stale.gecerlilik_sonu + timedelta(seconds=1)
        # Lazy süpürme: yeni talep, süresi dolmuş hold'u serbest bırakmalı
        fresh = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("4"),
            alici_firma=self.alici,
            ttl_seconds=300,
            now=after,
        )
        stale.refresh_from_db()
        bal.refresh_from_db()
        self.assertEqual(stale.durum, StockReservation.Durum.SURESI_DOLDU)
        self.assertEqual(fresh.durum, StockReservation.Durum.AKTIF)
        self.assertEqual(bal.reserved, Decimal("4"))
        self.assertEqual(bal.available, Decimal("6"))


class OrderExpireDurableTests(CheckoutFixtureMixin, TransactionTestCase):
    """(b) Order create fail'de expire kalıcı olmalı (outer atomic rollback'ten bağımsız)."""

    def setUp(self):
        self._build_checkout_world()

    def test_order_fail_after_ttl_persists_expire(self):
        self._quote_and_cart(miktar=Decimal("2"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="exp-ord-1"
        )
        res = StockReservation.objects.get(pk=co.lines[0].reservation_id)
        after = res.gecerlilik_sonu + timedelta(seconds=1)

        with self.assertRaises(ValidationError):
            order_servisi.olustur_from_checkout(
                actor=self.buyer,
                checkout_attempt=co.attempt,
                now=after,
            )

        res.refresh_from_db()
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(res.durum, StockReservation.Durum.SURESI_DOLDU)
        self.assertEqual(bal.reserved, Decimal("0"))
        self.assertEqual(bal.on_hand, Decimal("100"))
        self.assertFalse(
            StockMovement.objects.filter(tip=StockMovement.Tip.SATIS).exists()
        )


class ExpireCommandTests(PriceQuoteFixtureMixin, TestCase):
    """(c) Management command toplu expire + idempotent + actor=None audit."""

    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.ted_user = User(
            username="exp_cmd_ted",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.ted_user.set_password("x")
        cls.ted_user.save()
        sync_user_role_groups(cls.ted_user)
        cls.buyer = User(
            username="exp_cmd_buyer",
            firma=cls.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)
        cls.wh = warehouse_servisi.olustur_warehouse(
            actor=cls.ted_user,
            sahip_firma=cls.ted,
            kod="EXPCMD",
            ad="Expire cmd depo",
        )
        ledger_servisi.kaydet_hareket(
            actor=cls.ted_user,
            warehouse=cls.wh,
            teklif=cls.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("20"),
        )

    def test_expire_stale_reservations_command(self):
        t0 = timezone.now()
        r1 = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("5"),
            alici_firma=self.alici,
            ttl_seconds=30,
            now=t0,
            idempotency_key="cmd-1",
        )
        r2 = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("3"),
            alici_firma=self.alici,
            ttl_seconds=30,
            now=t0,
            idempotency_key="cmd-2",
        )
        after = r1.gecerlilik_sonu + timedelta(seconds=1)
        before_audits = AuditOlay.objects.filter(
            action="stock_reservation.expire", success=True
        ).count()

        out = StringIO()
        call_command(
            "expire_stale_reservations",
            f"--now={after.isoformat()}",
            stdout=out,
        )
        r1.refresh_from_db()
        r2.refresh_from_db()
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(r1.durum, StockReservation.Durum.SURESI_DOLDU)
        self.assertEqual(r2.durum, StockReservation.Durum.SURESI_DOLDU)
        self.assertEqual(bal.reserved, Decimal("0"))
        after_audits = AuditOlay.objects.filter(
            action="stock_reservation.expire", success=True
        ).count()
        self.assertGreaterEqual(after_audits - before_audits, 2)
        # actor=None audit
        self.assertTrue(
            AuditOlay.objects.filter(
                action="stock_reservation.expire",
                success=True,
                actor__isnull=True,
                entity_id=str(r1.pk),
            ).exists()
        )

        # Idempotent ikinci koşum
        call_command(
            "expire_stale_reservations",
            f"--now={after.isoformat()}",
            stdout=StringIO(),
        )
        after2 = AuditOlay.objects.filter(
            action="stock_reservation.expire", success=True
        ).count()
        self.assertEqual(after2, after_audits)
