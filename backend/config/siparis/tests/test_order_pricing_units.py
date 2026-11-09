"""Sipariş satır tutarı — ADET vs GRAM (quote toplamı × stok miktarı).

toplam_vergisiz: teklif.gram (veya parça) için quote toplamı.
Stok GRAM iken cart miktarı gramdır → orantılı ölçek gerekir.
"""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import TedarikciTeklif
from fiyatlama.services import pricing_service
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from siparis.services import cart_servisi, checkout_servisi, order_servisi
from stok.models import StockMovement
from stok.services import ledger_servisi, warehouse_servisi

User = get_user_model()
_CENT = Decimal("0.01")


def _q2(v: Decimal) -> Decimal:
    return Decimal(v).quantize(_CENT, rounding=ROUND_HALF_UP)


class OrderPricingUnitTests(PriceQuoteFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.buyer = User(
            username="prc_buyer",
            firma=cls.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)
        cls.ted_user = User(
            username="prc_ted",
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
            kod="PRCWH",
            ad="Fiyat depo",
        )
        ledger_servisi.kaydet_hareket(
            actor=cls.ted_user,
            warehouse=cls.wh,
            teklif=cls.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("100"),
        )

    def test_gram_order_line_scales_by_quote_gram(self):
        """METAL_BAZLI: quote 2.5g=5990; stok 2.0g → 5990*(2/2.5)=4792."""
        quote = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        self.assertEqual(quote.gram, Decimal("2.5000"))
        self.assertEqual(quote.toplam_vergisiz, Decimal("5990.00"))
        miktar = Decimal("2.000")
        expected = _q2(
            quote.toplam_vergisiz * (miktar / quote.gram)
        )
        self.assertEqual(expected, Decimal("4792.00"))

        cart_servisi.satir_ekle(
            actor=self.buyer, price_quote=quote, miktar=miktar
        )
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="prc-gram-1"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        line = order.lines.get()
        self.assertEqual(line.birim, "GRAM")
        self.assertEqual(line.miktar, miktar)
        self.assertEqual(line.snapshot_satir_tutari_vergisiz, expected)
        self.assertEqual(
            line.snapshot_birim_fiyat_vergisiz,
            _q2(quote.toplam_vergisiz / quote.gram),
        )

    def test_adet_order_line_multiplies_piece_total(self):
        """SABIT_PARCA: toplam = parça fiyatı; miktar ADET ile çarpılır."""
        bas, bit = date.today(), date.today() + timedelta(days=60)
        TedarikciTeklif.objects.filter(pk=self.teklif.pk).update(
            durum=TedarikciTeklif.Durum.PASIF
        )
        t = TedarikciTeklif.objects.create(
            varyant=self.varyant,
            tedarikci=self.ted,
            tedarikci_kodu="PRCAD",
            fiyat_modeli=TedarikciTeklif.FiyatModeli.SABIT_PARCA,
            birim_fiyat=Decimal("1500.0000"),
            para_birimi="TRY",
            durum=TedarikciTeklif.Durum.YAYINDA,
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
            eslestirme_durumu="onaylandi",
            hedef_urun=self.urun,
            oncelik=1,
        )
        ledger_servisi.kaydet_hareket(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=t,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("50"),
        )
        quote = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            teklif_id=t.pk,
            kullanici=self.finance,
        )
        # sabit 1500 + marj 50 + ek 10 = 1560 (fixture kalem)
        self.assertEqual(quote.toplam_vergisiz, Decimal("1560.00"))
        miktar = Decimal("3")
        expected = _q2(quote.toplam_vergisiz * miktar)

        cart_servisi.satir_ekle(
            actor=self.buyer, price_quote=quote, miktar=miktar
        )
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="prc-adet-1"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        line = order.lines.get()
        self.assertEqual(line.birim, "ADET")
        self.assertEqual(line.snapshot_satir_tutari_vergisiz, expected)
        self.assertEqual(
            line.snapshot_birim_fiyat_vergisiz, quote.toplam_vergisiz
        )
