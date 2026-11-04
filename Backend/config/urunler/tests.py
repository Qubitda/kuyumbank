from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from firmalar.models import Firma
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal, SatisKanali
from urunler import servisler
from urunler.models import Kategori, OlcuDegeri, Renk, TasTipi, Urun, UrunKanal, UrunTasi, Varyant


class KatalogTestTaban(TestCase):
    @classmethod
    def setUpTestData(cls):
        altin = KiymetliMetal.objects.create(kod="ALTIN", ad="Altın", gram_bazli=True)
        celik = KiymetliMetal.objects.create(kod="CELIK", ad="Çelik", gram_bazli=False)
        cls.ayar14 = AyarMilyem.objects.create(metal=altin, ayar_kodu="14K", milyem=585)
        cls.ayarsiz = AyarMilyem.objects.create(metal=celik, ayar_kodu="Ayarsız", milyem=0)
        grup = FiyatGrubu.objects.create(kod="YUZUK_ALYANS", ad="Yüzük / Alyans")
        cls.kategori = Kategori.objects.create(kod="YUZUK", ad="Yüzük", fiyat_grubu=grup)
        cls.tedarikci = Firma.objects.create(ad="Tedarikçi A", tedarikci_mi=True)
        cls.kanal = SatisKanali.objects.create(kod="KUYUMCU_PANEL", ad="Kuyumcu paneli")
        cls.renk_sari = Renk.objects.create(kod="SARI", ad="Sarı")
        cls.renk_beyaz = Renk.objects.create(kod="BEYAZ", ad="Beyaz")
        cls.no14 = OlcuDegeri.objects.create(tip="yuzuk_no", deger="14", sira=14)
        cls.no16 = OlcuDegeri.objects.create(tip="yuzuk_no", deger="16", sira=16)
        cls.cm19 = OlcuDegeri.objects.create(tip="bilezik_boyu", deger="19 cm", sira=19)
        User = get_user_model()
        cls.platform = User.objects.create_user(username="platform1", password="x", is_superuser=True)
        cls.tedarikci_user = User.objects.create_user(username="ted1", password="x")

    def urun(self, **kw):
        degerler = dict(tedarikci=self.tedarikci, ad="Tek taş yüzük", kategori=self.kategori, ayar=self.ayar14)
        degerler.update(kw)
        return Urun.objects.create(**degerler)


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

    def test_tas_bedeli_toplami(self):
        u = self.urun()
        v = Varyant.objects.create(urun=u, gram=Decimal("3.2"))
        pirlanta = TasTipi.objects.create(kod="PIRLANTA", ad="Pırlanta")
        UrunTasi.objects.create(urun=u, tas_tipi=pirlanta, bedel=Decimal("1000"))
        UrunTasi.objects.create(urun=u, tas_tipi=pirlanta, bedel=Decimal("250.50"))
        self.assertEqual(v.tas_bedeli_toplam(), Decimal("1250.50"))


class OnayAkisiTest(KatalogTestTaban):
    def hazir_urun(self):
        u = self.urun()
        Varyant.objects.create(urun=u, gram=Decimal("3.2"))
        return u

    def test_varyantsiz_urun_onaya_gonderilemez(self):
        with self.assertRaises(ValidationError):
            servisler.onaya_gonder(self.urun(), self.tedarikci_user)

    def test_tam_akis(self):
        u = self.hazir_urun()
        UrunKanal.objects.create(urun=u, kanal=self.kanal)
        servisler.onaya_gonder(u, self.tedarikci_user)
        servisler.onayla(u, self.platform)
        servisler.yayina_al(u, self.platform)
        u.refresh_from_db()
        self.assertEqual((u.onay_durumu, u.yayin_durumu), ("onayli", "aktif"))
        self.assertEqual(u.onaylayan_kullanici, self.platform)

    def test_platform_disi_kullanici_onaylayamaz(self):
        u = self.hazir_urun()
        servisler.onaya_gonder(u, self.tedarikci_user)
        with self.assertRaises(ValidationError):
            servisler.onayla(u, self.tedarikci_user)

    def test_kanalsiz_urun_aktif_yayina_alinamaz(self):
        u = self.hazir_urun()
        servisler.onaya_gonder(u, self.tedarikci_user)
        servisler.onayla(u, self.platform)
        with self.assertRaises(ValidationError):
            servisler.yayina_al(u, self.platform)

    def test_red_nedensiz_olmaz_ve_yeniden_gonderilebilir(self):
        u = self.hazir_urun()
        servisler.onaya_gonder(u, self.tedarikci_user)
        with self.assertRaises(ValidationError):
            servisler.reddet(u, self.platform, "  ")
        servisler.reddet(u, self.platform, "Gram hatalı")
        servisler.onaya_gonder(u, self.tedarikci_user)
        u.refresh_from_db()
        self.assertEqual(u.onay_durumu, "onay_bekliyor")
