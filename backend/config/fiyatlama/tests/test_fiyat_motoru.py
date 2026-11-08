"""Dilim 3.4 — fiyat_motoru (model + PB dönüşüm)."""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from firmalar.role_permissions import seed_role_permissions
from fiyatlama.services.fiyat_motoru import hesapla_teklif_kalemleri
from tanimlar.models import DovizKuru, KurPolitikasi, KurSaglayici, KurTaraf, KurTipi


class FiyatMotoruTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        KurSaglayici.objects.filter(aktif=True).update(aktif=False)
        cls.sag = KurSaglayici.objects.create(
            kod="M34", ad="M34", aktif=True, max_gecikme_saniye=3600
        )
        KurPolitikasi.objects.get_or_create(
            anahtar="default",
            defaults={
                "alici_kur_tipi": KurTipi.SATIS,
                "tedarikci_kur_tipi": KurTipi.ALIS,
            },
        )
        now = timezone.now()
        DovizKuru.objects.create(
            para_birimi="USD",
            saglayici=cls.sag,
            kur_tipi=KurTipi.SATIS,
            zaman=now,
            alinma_zamani=now,
            kur=Decimal("30.0000"),
            kaynak="api",
        )

    def test_gram_birim_usd_to_try(self):
        sonuc = hesapla_teklif_kalemleri(
            fiyat_modeli="GRAM_BIRIM",
            hedef_para_birimi="TRY",
            gram=Decimal("2"),
            birim_fiyat=Decimal("10"),  # USD/gr
            birim_fiyat_pb="USD",
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("0"),
            taraf=KurTaraf.ALICI,
        )
        # 2 * 10 USD = 20 USD → 600 TRY
        self.assertEqual(sonuc["kalemler"]["gram_birim"], Decimal("600.0000"))
        self.assertEqual(sonuc["para_birimi"], "TRY")
        self.assertIn("pb_donusum", sonuc)

    def test_sabit_parca_ayni_pb(self):
        sonuc = hesapla_teklif_kalemleri(
            fiyat_modeli="SABIT_PARCA",
            hedef_para_birimi="TRY",
            birim_fiyat=Decimal("1500"),
            birim_fiyat_pb="TRY",
            marj_tipi="TL_PARCA",
            marj_degeri=Decimal("100"),
            ek_bedel=Decimal("50"),
        )
        self.assertEqual(sonuc["toplam_vergisiz"], Decimal("1650.00"))
        self.assertNotIn("pb_donusum", sonuc)
