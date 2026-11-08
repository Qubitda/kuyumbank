"""Dilim 3.2 K-008 — AKTIF tarih çakışması, immutability, yetki, fallback."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import FiyatSozlesmesi, FiyatSozlesmesiKalemi
from fiyatlama.models.sozlesme_cozumleme import cozumle
from fiyatlama.services import sozlesme_servisi
from tanimlar.models import AyarMilyem, KiymetliMetal, SatisKanali

User = get_user_model()


class _SozlesmeFixtures:
    @classmethod
    def _seed(cls):
        seed_role_permissions()
        cls.platform = ensure_platform_firma()
        cls.firma = Firma.objects.create(ad="K8F", firma_kodu="K8F", alici_mi=True)
        cls.firma_b = Firma.objects.create(ad="K8G", firma_kodu="K8G", alici_mi=True)
        cls.metal = KiymetliMetal.objects.create(kod="AG", ad="Gümüş", gram_bazli=True)
        cls.ayar = AyarMilyem.objects.create(
            metal=cls.metal, ayar_kodu="925", ayar_degeri=925, milyem=Decimal("0.925")
        )
        cls.kanal_a = SatisKanali.objects.create(kod="K8A", ad="Kanal A")
        cls.kanal_b = SatisKanali.objects.create(kod="K8B", ad="Kanal B")
        cls.finance = User(
            username="k8fin",
            firma=cls.platform,
            rol=roles.PLATFORM_FINANCE,
            is_staff=True,
        )
        cls.finance.set_password("x")
        cls.finance.save()
        sync_user_role_groups(cls.finance)
        cls.no_perm = User(
            username="k8np",
            firma=cls.platform,
            rol=roles.PLATFORM_SUPPORT,
            is_staff=True,
        )
        cls.no_perm.set_password("x")
        cls.no_perm.save()
        sync_user_role_groups(cls.no_perm)

    def _taslak(self, *, firma=None, kanal=None, bas=None, bit=None, versiyon=1, **kw):
        defaults = dict(
            firma=firma or self.firma,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            satis_kanali=kanal,
            gecerlilik_baslangic=bas or date(2026, 1, 1),
            gecerlilik_bitis=bit or date(2026, 6, 30),
            durum=FiyatSozlesmesi.Durum.TASLAK,
            olusturan_kullanici=self.finance,
            versiyon=versiyon,
        )
        defaults.update(kw)
        return FiyatSozlesmesi.objects.create(**defaults)


class K008CakismaTests(_SozlesmeFixtures, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._seed()

    def test_iki_kanalsiz_aktif_cakisma_red(self):
        a = self._taslak()
        sozlesme_servisi.aktif_yap(a, self.finance)
        b = self._taslak(versiyon=2)
        with self.assertRaises(ValidationError):
            sozlesme_servisi.aktif_yap(b, self.finance)

    def test_ayni_kanal_cakisan_tarih_red(self):
        a = self._taslak(kanal=self.kanal_a)
        sozlesme_servisi.aktif_yap(a, self.finance)
        b = self._taslak(
            kanal=self.kanal_a,
            versiyon=2,
            bas=date(2026, 6, 1),
            bit=date(2026, 12, 31),
        )
        with self.assertRaises(ValidationError):
            sozlesme_servisi.aktif_yap(b, self.finance)

    def test_farkli_kanal_izinli(self):
        a = self._taslak(kanal=self.kanal_a)
        sozlesme_servisi.aktif_yap(a, self.finance)
        b = self._taslak(kanal=self.kanal_b, versiyon=1)
        out = sozlesme_servisi.aktif_yap(b, self.finance)
        self.assertEqual(out.durum, FiyatSozlesmesi.Durum.AKTIF)

    def test_kanalsiz_ve_kanalli_birlikte_fallback(self):
        gen = self._taslak(kanal=None)
        FiyatSozlesmesiKalemi.objects.create(
            sozlesme=gen,
            metal=self.metal,
            ayar=self.ayar,
            marj_tipi=FiyatSozlesmesiKalemi.MarjTipi.YUZDE,
            marj_degeri=Decimal("5"),
        )
        ch = self._taslak(kanal=self.kanal_a, versiyon=1)
        k_ch = FiyatSozlesmesiKalemi.objects.create(
            sozlesme=ch,
            metal=self.metal,
            ayar=self.ayar,
            marj_tipi=FiyatSozlesmesiKalemi.MarjTipi.YUZDE,
            marj_degeri=Decimal("9"),
        )
        sozlesme_servisi.aktif_yap(gen, self.finance)
        sozlesme_servisi.aktif_yap(ch, self.finance)
        # Kanal A → kanallı baskın
        out_a = cozumle(
            firma=self.firma,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            tarih=date(2026, 3, 1),
            metal=self.metal,
            ayar=self.ayar,
            satis_kanali=self.kanal_a,
        )
        self.assertEqual(out_a.pk, k_ch.pk)
        # Kanal B → kanalsız fallback
        out_b = cozumle(
            firma=self.firma,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            tarih=date(2026, 3, 1),
            metal=self.metal,
            ayar=self.ayar,
            satis_kanali=self.kanal_b,
        )
        self.assertEqual(out_b.sozlesme_id, gen.pk)

    def test_bitis_baslangic_ayni_gun_cakisir(self):
        a = self._taslak(bas=date(2026, 1, 1), bit=date(2026, 6, 30))
        sozlesme_servisi.aktif_yap(a, self.finance)
        b = self._taslak(
            versiyon=2,
            bas=date(2026, 6, 30),
            bit=date(2026, 12, 31),
        )
        # '[]' inclusive → 30 Haziran çakışır
        with self.assertRaises(ValidationError):
            sozlesme_servisi.aktif_yap(b, self.finance)

    def test_pasif_cakisma_olusturmaz(self):
        a = self._taslak()
        sozlesme_servisi.aktif_yap(a, self.finance)
        sozlesme_servisi.pasifle(a, self.finance)
        b = self._taslak(versiyon=2)
        out = sozlesme_servisi.aktif_yap(b, self.finance)
        self.assertEqual(out.durum, FiyatSozlesmesi.Durum.AKTIF)

    def test_farkli_firma_etkilemez(self):
        a = self._taslak(firma=self.firma)
        sozlesme_servisi.aktif_yap(a, self.finance)
        b = self._taslak(firma=self.firma_b, versiyon=1)
        out = sozlesme_servisi.aktif_yap(b, self.finance)
        self.assertEqual(out.durum, FiyatSozlesmesi.Durum.AKTIF)

    def test_yetkisiz_red(self):
        a = self._taslak()
        with self.assertRaises(PermissionDenied):
            sozlesme_servisi.aktif_yap(a, self.no_perm)

    def test_aktif_kalem_immutable(self):
        a = self._taslak()
        sozlesme_servisi.aktif_yap(a, self.finance)
        a.refresh_from_db()
        self.assertEqual(a.durum, FiyatSozlesmesi.Durum.AKTIF)
        with self.assertRaises(ValidationError):
            FiyatSozlesmesiKalemi.objects.create(
                sozlesme=a,
                metal=self.metal,
                ayar=self.ayar,
                marj_tipi=FiyatSozlesmesiKalemi.MarjTipi.YUZDE,
                marj_degeri=Decimal("1"),
            )

    def test_yeni_versiyon_sonra_aktif_eski_pasif(self):
        a = self._taslak()
        FiyatSozlesmesiKalemi.objects.create(
            sozlesme=a,
            metal=self.metal,
            ayar=self.ayar,
            marj_tipi=FiyatSozlesmesiKalemi.MarjTipi.YUZDE,
            marj_degeri=Decimal("4"),
        )
        sozlesme_servisi.aktif_yap(a, self.finance)
        yeni = sozlesme_servisi.yeni_versiyon_olustur(a, self.finance)
        self.assertEqual(yeni.durum, FiyatSozlesmesi.Durum.TASLAK)
        self.assertEqual(yeni.versiyon, 2)
        self.assertEqual(yeni.kalemler.count(), 1)
        sozlesme_servisi.aktif_yap(yeni, self.finance)
        a.refresh_from_db()
        yeni.refresh_from_db()
        self.assertEqual(a.durum, FiyatSozlesmesi.Durum.PASIF)
        self.assertEqual(yeni.durum, FiyatSozlesmesi.Durum.AKTIF)


class K008ExclusionDbTests(_SozlesmeFixtures, TransactionTestCase):
    def setUp(self):
        self._seed()

    def test_exclusion_constraint_db(self):
        a = self._taslak()
        sozlesme_servisi.aktif_yap(a, self.finance)
        b = FiyatSozlesmesi(
            firma=self.firma,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            satis_kanali=None,
            gecerlilik_baslangic=date(2026, 1, 1),
            gecerlilik_bitis=date(2026, 6, 30),
            durum=FiyatSozlesmesi.Durum.AKTIF,
            olusturan_kullanici=self.finance,
            versiyon=2,
        )
        with self.assertRaises((ValidationError, IntegrityError)):
            with transaction.atomic():
                b.save()
