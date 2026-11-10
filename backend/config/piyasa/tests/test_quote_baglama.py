"""ADR-0024 — PANO/MANUEL → PriceQuote (PP-9)."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import PriceQuote
from piyasa.models import PiyasaMarjPolitikasi, PiyasaUrun
from piyasa.services import quote_baglama
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from tanimlar.models import KurPolitikasi, KurSaglayici, KurTipi, MetalKuru


class QuoteBaglamaTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

        metal = cls.varyant.urun.ayar.metal
        KurSaglayici.objects.filter(aktif=True).update(aktif=False)
        sag = KurSaglayici.objects.create(
            kod="PP9_FEED",
            ad="PP9",
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
        for tip, fiyat in (
            (KurTipi.SATIS, Decimal("6000.0000")),
            (KurTipi.ALIS, Decimal("5990.0000")),
        ):
            MetalKuru.objects.create(
                metal=metal,
                saglayici=sag,
                kur_tipi=tip,
                zaman=now,
                alinma_zamani=now,
                saf_birim_fiyat=fiyat,
                kaynak="api",
            )
        PiyasaMarjPolitikasi.objects.update_or_create(
            anahtar="default",
            defaults={"marj_modu": PiyasaMarjPolitikasi.MarjModu.YUZDE},
        )
        cls.pano = PiyasaUrun.objects.create(
            kod="pp9has",
            ad="PP9 Has",
            grup=PiyasaUrun.Grup.HAS,
            metal=metal,
            gram=Decimal("1"),
            alis_marj=Decimal("0"),
            satis_marj=Decimal("2"),
            yuvarlama_adimi=Decimal("0"),
            sira=1,
        )

    def test_manuel_quote(self):
        gram = self.varyant.gram or Decimal("1")
        pq = quote_baglama.quote_from_islem_fiyati(
            actor=self.finance,
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kaynak="MANUEL",
            manuel_birim_fiyat=Decimal("7000"),
            agirlik_gr=gram,
        )
        self.assertEqual(pq.fiyat_modeli, "HEDEF_TOPLAM")
        self.assertEqual(pq.toplam_vergisiz, (Decimal("7000") * gram).quantize(Decimal("0.01")))
        self.assertEqual(pq.hesap_girdisi.get("birim_kaynak"), "MANUEL")
        self.assertEqual(pq.hesap_girdisi.get("etkin_birim"), "7000.00")
        self.assertEqual(pq.hesap_girdisi.get("pano_baglama"), "ADR-0024")

    def test_pano_quote(self):
        # Guardrail üstü: yüksek satış marjı (fixture maliyetine göre)
        self.pano.satis_marj = Decimal("80")
        self.pano.save(update_fields=["satis_marj", "guncelleme"])
        gram = Decimal("1")
        pq = quote_baglama.quote_from_islem_fiyati(
            actor=self.finance,
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kaynak="PANO",
            urun_kod="pp9has",
            taraf="SATIS",
            agirlik_gr=gram,
        )
        # 6000 * 1.80 = 10800
        self.assertEqual(pq.toplam_vergisiz, Decimal("10800.00"))
        self.assertEqual(pq.hesap_girdisi.get("birim_kaynak"), "PANO")
        self.assertEqual(pq.hesap_girdisi.get("piyasa_urun_kod"), "pp9has")

    def test_buyer_denied(self):
        with self.assertRaises(PermissionDenied):
            quote_baglama.quote_from_islem_fiyati(
                actor=self.buyer,
                alici_firma=self.alici,
                satis_kanali=self.kanal,
                varyant=self.varyant,
                kaynak="MANUEL",
                manuel_birim_fiyat=Decimal("1000"),
                agirlik_gr=Decimal("1"),
            )

    def test_lock_path(self):
        from fiyatlama.services import pricing_service

        pq = quote_baglama.quote_from_islem_fiyati(
            actor=self.finance,
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kaynak="MANUEL",
            manuel_birim_fiyat=Decimal("50000"),
            agirlik_gr=Decimal("1"),
        )
        # L-11 yolu: alıcı lock (platform finance on_behalf değil)
        lock = pricing_service.lock_quote(quote=pq, kullanici=self.buyer)
        self.assertEqual(lock.quote_id, pq.pk)
        self.assertEqual(PriceQuote.objects.filter(pk=pq.pk).count(), 1)
