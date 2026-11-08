"""F4-020/021 — StockReservation TTL + oversell."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from stok.birim_constants import StokBirimi
from stok.models import StockBalance, StockMovement, StockReservation
from stok.services import ledger_servisi, reservation_servisi, warehouse_servisi

User = get_user_model()


class ReservationServiceTests(PriceQuoteFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.ted_user = User(
            username="res_ted",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.ted_user.set_password("x")
        cls.ted_user.save()
        sync_user_role_groups(cls.ted_user)

        cls.buyer = User(
            username="res_buyer",
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
            kod="RES1",
            ad="Rezerv depo",
        )
        ledger_servisi.kaydet_hareket(
            actor=cls.ted_user,
            warehouse=cls.wh,
            teklif=cls.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("10"),
        )

    def test_create_reduces_available_not_on_hand(self):
        res = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("3"),
            alici_firma=self.alici,
        )
        self.assertEqual(res.durum, StockReservation.Durum.AKTIF)
        self.assertEqual(res.birim, StokBirimi.GRAM)
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.on_hand, Decimal("10"))
        self.assertEqual(bal.reserved, Decimal("3"))
        self.assertEqual(bal.available, Decimal("7"))
        self.assertFalse(
            StockMovement.objects.filter(
                tip=StockMovement.Tip.REZERVASYON
            ).exists()
        )

    def test_oversell_rejected(self):
        reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("8"),
            alici_firma=self.alici,
        )
        with self.assertRaises(ValidationError):
            reservation_servisi.olustur_rezervasyon(
                actor=self.buyer,
                warehouse=self.wh,
                teklif=self.teklif,
                miktar=Decimal("3"),
                alici_firma=self.alici,
            )

    def test_idempotent_create(self):
        a = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("2"),
            alici_firma=self.alici,
            idempotency_key="idem-r1",
        )
        b = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("2"),
            alici_firma=self.alici,
            idempotency_key="idem-r1",
        )
        self.assertEqual(a.pk, b.pk)
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.reserved, Decimal("2"))

    def test_cancel_releases_reserved(self):
        res = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("4"),
            alici_firma=self.alici,
        )
        reservation_servisi.iptal_rezervasyon(res, actor=self.buyer)
        res.refresh_from_db()
        self.assertEqual(res.durum, StockReservation.Durum.IPTAL)
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.reserved, Decimal("0"))
        self.assertEqual(bal.on_hand, Decimal("10"))

    def test_expire_releases_reserved(self):
        now = timezone.now()
        res = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("5"),
            alici_firma=self.alici,
            ttl_seconds=60,
            now=now,
        )
        after = res.gecerlilik_sonu + timedelta(seconds=1)
        reservation_servisi.sync_reservation_expiration(res, now=after)
        res.refresh_from_db()
        self.assertEqual(res.durum, StockReservation.Durum.SURESI_DOLDU)
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.reserved, Decimal("0"))
        self.assertEqual(bal.available, Decimal("10"))

    def test_consume_writes_satis_and_drops_on_hand(self):
        res = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("4"),
            alici_firma=self.alici,
        )
        reservation_servisi.tuket_rezervasyon(res, actor=self.buyer)
        res.refresh_from_db()
        self.assertEqual(res.durum, StockReservation.Durum.TUKETILDI)
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.on_hand, Decimal("6"))
        self.assertEqual(bal.reserved, Decimal("0"))
        self.assertTrue(
            StockMovement.objects.filter(
                tip=StockMovement.Tip.SATIS, miktar=Decimal("-4")
            ).exists()
        )

    def test_expired_cannot_consume(self):
        now = timezone.now()
        res = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("2"),
            alici_firma=self.alici,
            ttl_seconds=30,
            now=now,
        )
        after = res.gecerlilik_sonu + timedelta(seconds=1)
        with self.assertRaises(ValidationError):
            reservation_servisi.tuket_rezervasyon(res, actor=self.buyer, now=after)
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.reserved, Decimal("0"))

    def test_adet_gram_not_mixed_via_birim(self):
        # Aynı teklif GRAM; ADET balance yaratılmaz
        res = reservation_servisi.olustur_rezervasyon(
            actor=self.buyer,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("1"),
            alici_firma=self.alici,
        )
        self.assertEqual(res.birim, StokBirimi.GRAM)
        self.assertFalse(
            StockBalance.objects.filter(
                warehouse=self.wh, birim=StokBirimi.ADET
            ).exists()
        )


class ReservationConcurrencyTests(PriceQuoteFixtureMixin, TransactionTestCase):
    def setUp(self):
        self._build_quote_world()
        seed_role_permissions()
        self.ted_user = User(
            username="resc_ted",
            firma=self.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        self.ted_user.set_password("x")
        self.ted_user.save()
        sync_user_role_groups(self.ted_user)
        self.buyer = User(
            username="resc_buyer",
            firma=self.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        self.buyer.set_password("x")
        self.buyer.save()
        sync_user_role_groups(self.buyer)
        self.wh = warehouse_servisi.olustur_warehouse(
            actor=self.ted_user,
            sahip_firma=self.ted,
            kod="RESC",
            ad="Conc depo",
        )
        ledger_servisi.kaydet_hareket(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=self.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("10"),
        )

    def test_concurrent_reserve_no_oversell(self):
        wh_id = self.wh.pk
        teklif_id = self.teklif.pk
        buyer_id = self.buyer.pk
        alici_id = self.alici.pk

        def worker():
            from fiyatlama.models import TedarikciTeklif as TT
            from firmalar.models import Firma as F
            from stok.models import Warehouse as W

            wh = W.objects.get(pk=wh_id)
            teklif = TT.objects.get(pk=teklif_id)
            buyer = User.objects.get(pk=buyer_id)
            alici = F.objects.get(pk=alici_id)
            try:
                reservation_servisi.olustur_rezervasyon(
                    actor=buyer,
                    warehouse=wh,
                    teklif=teklif,
                    miktar=Decimal("6"),
                    alici_firma=alici,
                )
                return "ok"
            except ValidationError:
                return "fail"

        results = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futs = [pool.submit(worker) for _ in range(4)]
            for f in as_completed(futs):
                results.append(f.result())

        self.assertEqual(results.count("ok"), 1)
        self.assertEqual(results.count("fail"), 3)
        bal = StockBalance.objects.get(warehouse_id=wh_id, teklif_id=teklif_id)
        self.assertEqual(bal.reserved, Decimal("6"))
        self.assertEqual(bal.available, Decimal("4"))
        self.assertEqual(
            StockReservation.objects.filter(
                warehouse_id=wh_id, durum=StockReservation.Durum.AKTIF
            ).count(),
            1,
        )
