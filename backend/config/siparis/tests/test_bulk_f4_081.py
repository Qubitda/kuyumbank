"""F4-081 — Bulk Order / CSV: kısmi hata + idempotent Order."""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from django.utils import timezone

from fiyatlama.models import TedarikciTeklif
from siparis.models import Order
from siparis.services import bulk_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.models import StockMovement
from stok.services import ledger_servisi
from urunler.models import Urun, Varyant


class BulkOrderServiceTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        cls.varyant.refresh_from_db()
        # İkinci ürün/varyant (eksensiz unique urun başına)
        now = timezone.now()
        urun2 = Urun.objects.create(
            olusturan_firma=cls.platform,
            ad="Bulk Urun 2",
            kategori=cls.urun.kategori,
            ayar=cls.urun.ayar,
        )
        Urun.objects.filter(pk=urun2.pk).update(
            onay_durumu="onayli",
            yayin_durumu="aktif",
            onaylayan_kullanici=cls.finance,
            onay_zamani=now,
        )
        urun2.refresh_from_db()
        cls.varyant2 = Varyant.objects.create(
            urun=urun2, gram=Decimal("1.000"), ek_bedel=Decimal("5.00")
        )
        cls.varyant2.refresh_from_db()
        bas, bit = date.today(), date.today() + timedelta(days=60)
        cls.teklif2 = TedarikciTeklif.objects.create(
            varyant=cls.varyant2,
            tedarikci=cls.ted,
            tedarikci_kodu="PQ2",
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("1.000"),
            durum=TedarikciTeklif.Durum.YAYINDA,
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
            eslestirme_durumu="onaylandi",
            hedef_urun=urun2,
            oncelik=10,
            iscilik_override=Decimal("80.00"),
        )
        ledger_servisi.kaydet_hareket(
            actor=cls.ted_user,
            warehouse=cls.wh,
            teklif=cls.teklif2,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("50"),
        )

    def test_csv_happy_creates_order(self):
        csv_text = (
            "sku,miktar,birim\n"
            f"{self.varyant.sku},2,GRAM\n"
            f"{self.varyant2.sku},1,GRAM\n"
        )
        result = bulk_servisi.toplu_siparis(
            actor=self.buyer,
            satis_kanali=self.kanal,
            idempotency_key="bulk-ok-1",
            csv_text=csv_text,
        )
        self.assertFalse(result.replayed)
        self.assertIsNotNone(result.order)
        self.assertEqual(result.order.durum, Order.Durum.OLUSTURULDU)
        self.assertEqual(result.order.lines.count(), 2)
        self.assertEqual(len(result.accepted), 2)
        self.assertEqual(result.errors, [])

    def test_partial_errors_still_orders_good_rows(self):
        csv_text = (
            "sku,miktar\n"
            f"{self.varyant.sku},1\n"
            "SKU-NO-SUCH,3\n"
        )
        result = bulk_servisi.toplu_siparis(
            actor=self.buyer,
            satis_kanali=self.kanal,
            idempotency_key="bulk-partial-1",
            csv_text=csv_text,
        )
        self.assertIsNotNone(result.order)
        self.assertEqual(result.order.lines.count(), 1)
        self.assertEqual(len(result.accepted), 1)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Varyant", result.errors[0].hata)

    def test_replay_same_key_no_second_order(self):
        csv_text = f"sku,miktar\n{self.varyant.sku},1\n"
        first = bulk_servisi.toplu_siparis(
            actor=self.buyer,
            satis_kanali=self.kanal,
            idempotency_key="bulk-idem-1",
            csv_text=csv_text,
        )
        second = bulk_servisi.toplu_siparis(
            actor=self.buyer,
            satis_kanali=self.kanal,
            idempotency_key="bulk-idem-1",
            csv_text=csv_text,
        )
        self.assertTrue(second.replayed)
        self.assertEqual(second.order.pk, first.order.pk)
        self.assertEqual(
            Order.objects.filter(
                alici_firma=self.buyer.firma, idempotency_key="bulk-idem-1"
            ).count(),
            1,
        )

    def test_wrong_birim_no_conversion(self):
        csv_text = f"sku,miktar,birim\n{self.varyant.sku},1,ADET\n"
        result = bulk_servisi.toplu_siparis(
            actor=self.buyer,
            satis_kanali=self.kanal,
            idempotency_key="bulk-birim-1",
            csv_text=csv_text,
        )
        self.assertIsNone(result.order)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Birim uyumsuz", result.errors[0].hata)
        self.assertIn("dönüşüm yok", result.errors[0].hata)
