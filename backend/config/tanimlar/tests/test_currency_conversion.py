"""Dilim 3.4 — CurrencyConversion (K-012) + kur politikası entegrasyonu."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from firmalar.role_permissions import seed_role_permissions
from tanimlar.models import (
    DovizKuru,
    KurPolitikasi,
    KurSaglayici,
    KurTaraf,
    KurTipi,
)
from tanimlar.services import kur_servisi
from tanimlar.services.currency_conversion import (
    CurrencyConversionError,
    convert,
    to_try,
)


class CurrencyConversionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        KurSaglayici.objects.filter(aktif=True).update(aktif=False)
        cls.saglayici = KurSaglayici.objects.create(
            kod="FX34",
            ad="FX34",
            aktif=True,
            max_gecikme_saniye=3600,
        )
        KurPolitikasi.objects.get_or_create(
            anahtar="default",
            defaults={
                "alici_kur_tipi": KurTipi.SATIS,
                "tedarikci_kur_tipi": KurTipi.ALIS,
            },
        )
        now = timezone.now()
        cls.usd_satis = DovizKuru.objects.create(
            para_birimi="USD",
            saglayici=cls.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=now,
            alinma_zamani=now,
            kur=Decimal("34.5000"),
            kaynak="api",
        )
        cls.usd_alis = DovizKuru.objects.create(
            para_birimi="USD",
            saglayici=cls.saglayici,
            kur_tipi=KurTipi.ALIS,
            zaman=now,
            alinma_zamani=now,
            kur=Decimal("34.0000"),
            kaynak="api",
        )
        cls.eur_satis = DovizKuru.objects.create(
            para_birimi="EUR",
            saglayici=cls.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=now,
            alinma_zamani=now,
            kur=Decimal("37.0000"),
            kaynak="api",
        )

    def test_ayni_pb_kimlik(self):
        r = convert(
            Decimal("10.555"),
            kaynak_pb="TRY",
            hedef_pb="TRY",
            taraf=KurTaraf.ALICI,
        )
        self.assertEqual(r.efektif_carpan, Decimal("1"))
        self.assertEqual(r.gozlem_idler, ())
        self.assertEqual(r.tutar_yuvarlanmis, Decimal("10.56"))

    def test_usd_to_try_alici_satis(self):
        r = to_try(
            Decimal("100"),
            kaynak_pb="USD",
            taraf=KurTaraf.ALICI,
        )
        self.assertEqual(r.tutar, Decimal("3450.0000"))
        self.assertEqual(r.tutar_yuvarlanmis, Decimal("3450.00"))
        self.assertEqual(r.gozlem_idler, (self.usd_satis.pk,))

    def test_try_to_usd(self):
        r = convert(
            Decimal("3450"),
            kaynak_pb="TRY",
            hedef_pb="USD",
            taraf=KurTaraf.ALICI,
        )
        self.assertEqual(r.tutar_yuvarlanmis, Decimal("100.00"))

    def test_tedarikci_alis_tipi_ayri(self):
        r = to_try(
            Decimal("100"),
            kaynak_pb="USD",
            taraf=KurTaraf.TEDARIKCI,
        )
        self.assertEqual(r.tutar, Decimal("3400.0000"))
        self.assertEqual(r.gozlem_idler, (self.usd_alis.pk,))

    def test_fx_to_fx_pivot(self):
        # 100 USD → TRY 3450 → /37 EUR
        r = convert(
            Decimal("100"),
            kaynak_pb="USD",
            hedef_pb="EUR",
            taraf=KurTaraf.ALICI,
        )
        expected = (Decimal("100") * Decimal("34.5")) / Decimal("37")
        self.assertEqual(r.tutar, expected)
        self.assertEqual(len(r.gozlem_idler), 2)

    def test_sabit_gozlem_sessiz_yenileme_yok(self):
        """Verilen gözlem kullanılır; daha yeni resolve edilmez."""
        eski = timezone.now() - timedelta(seconds=10)
        gozlem = DovizKuru.objects.create(
            para_birimi="USD",
            saglayici=self.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=eski,
            alinma_zamani=eski,
            kur=Decimal("30.0000"),
            kaynak="api",
        )
        r = to_try(
            Decimal("10"),
            kaynak_pb="USD",
            taraf=KurTaraf.ALICI,
            gozlem=gozlem,
        )
        self.assertEqual(r.tutar, Decimal("300.0000"))
        self.assertEqual(r.gozlem_idler, (gozlem.pk,))

    def test_stale_gozlem_red(self):
        eski = timezone.now() - timedelta(seconds=7200)
        gozlem = DovizKuru.objects.create(
            para_birimi="GBP",
            saglayici=self.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=eski,
            alinma_zamani=eski,
            kur=Decimal("40.0000"),
            kaynak="api",
        )
        with self.assertRaises(kur_servisi.KurStaleError):
            to_try(
                Decimal("1"),
                kaynak_pb="GBP",
                taraf=KurTaraf.ALICI,
                gozlem=gozlem,
            )

    def test_eksik_gozlem_red(self):
        with self.assertRaises(kur_servisi.KurYokError):
            to_try(Decimal("1"), kaynak_pb="GBP", taraf=KurTaraf.ALICI)

    def test_desteklenmeyen_pb(self):
        with self.assertRaises(CurrencyConversionError):
            convert(
                Decimal("1"),
                kaynak_pb="JPY",
                hedef_pb="TRY",
                taraf=KurTaraf.ALICI,
            )

    def test_gozlem_pb_uyusmazligi(self):
        with self.assertRaises(CurrencyConversionError):
            to_try(
                Decimal("1"),
                kaynak_pb="USD",
                taraf=KurTaraf.ALICI,
                gozlem=self.eur_satis,
            )
