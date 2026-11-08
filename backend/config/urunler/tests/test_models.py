from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from urunler.models import Kategori, TasTipi, UrunTasi, Varyant
from ._base import KatalogTestTaban


class UrunKurallariTest(KatalogTestTaban):
    def test_platform_kodu_otomatik(self):
        u = self.urun()
        self.assertEqual(u.platform_kodu, f"URN-{u.pk:06d}")

    def test_celik_gram_bazli_olamaz(self):
        u = self.urun(ayar=self.ayarsiz, fiyat_tipi="gram")
        with self.assertRaises(ValidationError):
            u.full_clean()

    def test_siparise_ozel_termin_ister(self):
        u = self.urun(temin_tipi="siparis_ozel")
        with self.assertRaises(ValidationError):
            u.full_clean()

    def test_onaysiz_yayin_db_seviyesinde_engellenir(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.urun(yayin_durumu="aktif")

    def test_kategori_dongu_engeli(self):
        alt = Kategori.objects.create(kod="TEK_TAS", ad="Tek taş", ust=self.kategori)
        self.kategori.ust = alt
        with self.assertRaises(ValidationError):
            self.kategori.full_clean()


class VaryantKurallariTest(KatalogTestTaban):
    def test_gram_bazli_varyantta_gram_zorunlu(self):
        v = Varyant(urun=self.urun(), gram=None)
        with self.assertRaises(ValidationError):
            v.full_clean()

    def test_renk_eksenli_urunde_renk_zorunlu(self):
        u = self.urun(renk_ekseni=True)
        with self.assertRaises(ValidationError):
            Varyant(urun=u, gram=Decimal("3")).full_clean()

    def test_renk_eksenli_olmayan_urunde_renk_girilemez(self):
        u = self.urun()
        with self.assertRaises(ValidationError):
            Varyant(urun=u, gram=Decimal("3"), renk=self.renk_sari).full_clean()

    def test_yanlis_olcu_tipi_reddedilir(self):
        u = self.urun(olcu_tipi="yuzuk_no")
        with self.assertRaises(ValidationError):
            Varyant(urun=u, gram=Decimal("3"), beden=self.cm19).full_clean()

    def test_ayni_kombinasyon_iki_kez_girilemez(self):
        u = self.urun(renk_ekseni=True, olcu_tipi="yuzuk_no")
        Varyant.objects.create(urun=u, renk=self.renk_sari, beden=self.no14, gram=Decimal("3.2"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Varyant.objects.create(urun=u, renk=self.renk_sari, beden=self.no14, gram=Decimal("3.3"))

    def test_eksensiz_urunde_tek_varyant(self):
        u = self.urun()
        Varyant.objects.create(urun=u, gram=Decimal("3.2"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Varyant.objects.create(urun=u, gram=Decimal("3.4"))

    def test_ayni_beden_farkli_renk_serbest(self):
        u = self.urun(renk_ekseni=True, olcu_tipi="yuzuk_no")
        Varyant.objects.create(urun=u, renk=self.renk_sari, beden=self.no14, gram=Decimal("3.2"))
        Varyant.objects.create(urun=u, renk=self.renk_beyaz, beden=self.no14, gram=Decimal("3.2"))
        self.assertEqual(u.varyantlar.count(), 2)

    def test_katalog_tas_bedeli(self):
        """katalog_tas_bedeli() urunler.UrunTasi toplamını döner (vitrin verisi)."""
        u = self.urun()
        v = Varyant.objects.create(urun=u, gram=Decimal("3.2"))
        pirlanta = TasTipi.objects.create(kod="PIRLANTA", ad="Pırlanta")
        UrunTasi.objects.create(urun=u, tas_tipi=pirlanta, bedel=Decimal("1000"))
        UrunTasi.objects.create(urun=u, tas_tipi=pirlanta, bedel=Decimal("250.50"))
        self.assertEqual(v.katalog_tas_bedeli(), Decimal("1250.50"))

    def test_teklif_tas_bedeli_none(self):
        """teklif_tas_bedeli(None) sıfır döner."""
        u = self.urun()
        v = Varyant.objects.create(urun=u, gram=Decimal("3.2"))
        self.assertEqual(v.teklif_tas_bedeli(None), Decimal("0"))


