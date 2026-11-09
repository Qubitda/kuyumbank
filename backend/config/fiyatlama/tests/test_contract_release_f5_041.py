"""F5-041 — ContractReleasePlan / Event; Quote/Lock’a yazmaz."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import AuditOlay, Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import (
    ContractReleasePlan,
    FiyatSozlesmesi,
    PriceLock,
    PriceQuote,
)
from fiyatlama.services import release_servisi, sozlesme_servisi
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal
from urunler.models import Kategori, Urun, Varyant

User = get_user_model()


class ContractReleaseF5041Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.platform = ensure_platform_firma()
        cls.alici = Firma.objects.create(
            ad="CR Alici", firma_kodu="CRA", alici_mi=True
        )
        cls.metal = KiymetliMetal.objects.create(
            kod="CRAU", ad="Altın CR", gram_bazli=True
        )
        cls.ayar = AyarMilyem.objects.create(
            metal=cls.metal,
            ayar_kodu="14",
            ayar_degeri=14,
            milyem=Decimal("0.585"),
        )
        grup = FiyatGrubu.objects.create(kod="CRG", ad="CRG")
        kat = Kategori.objects.create(kod="CRK", ad="Yüzük", fiyat_grubu=grup)

        cls.finance = User(
            username="cr_fin",
            firma=cls.platform,
            rol=roles.PLATFORM_FINANCE,
            is_staff=True,
        )
        cls.finance.set_password("x")
        cls.finance.save()
        sync_user_role_groups(cls.finance)

        cls.no_perm = User(
            username="cr_np",
            firma=cls.platform,
            rol=roles.PLATFORM_SUPPORT,
            is_staff=True,
        )
        cls.no_perm.set_password("x")
        cls.no_perm.save()
        sync_user_role_groups(cls.no_perm)

        urun = Urun.objects.create(
            olusturan_firma=cls.platform,
            ad="CR Ürün",
            kategori=kat,
            ayar=cls.ayar,
        )
        Urun.objects.filter(pk=urun.pk).update(
            onay_durumu="onayli",
            onaylayan_kullanici=cls.finance,
            onay_zamani=timezone.now(),
        )
        urun.refresh_from_db()
        cls.varyant = Varyant.objects.create(urun=urun, gram=Decimal("2.5"))

        bas, bit = date.today(), date.today() + timedelta(days=90)
        cls.soz = FiyatSozlesmesi.objects.create(
            firma=cls.alici,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
            durum=FiyatSozlesmesi.Durum.TASLAK,
            olusturan_kullanici=cls.finance,
            versiyon=1,
        )
        cls.soz = sozlesme_servisi.aktif_yap(cls.soz, cls.finance)

        cls.ted_soz = FiyatSozlesmesi.objects.create(
            firma=cls.alici,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.TEDARIKCI,
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
            durum=FiyatSozlesmesi.Durum.TASLAK,
            olusturan_kullanici=cls.finance,
            versiyon=1,
        )
        cls.ted_soz = sozlesme_servisi.aktif_yap(cls.ted_soz, cls.finance)

    def _aktif_plan(self, *, taahhut="100"):
        plan = release_servisi.olustur_plan(
            actor=self.finance,
            sozlesme=self.soz,
            varyant=self.varyant,
            birim=ContractReleasePlan.Birim.ADET,
            toplam_taahhut=Decimal(taahhut),
        )
        return release_servisi.aktif_et(actor=self.finance, plan=plan)

    def test_happy_path_release_and_audit(self):
        q0 = PriceQuote.objects.count()
        l0 = PriceLock.objects.count()
        plan = self._aktif_plan()
        self.assertEqual(plan.durum, ContractReleasePlan.Durum.AKTIF)

        event = release_servisi.serbest_birak(
            actor=self.finance,
            plan=plan,
            miktar=Decimal("40"),
            donem_baslangic=date.today(),
            donem_bitis=date.today() + timedelta(days=30),
        )
        self.assertEqual(event.miktar, Decimal("40"))
        self.assertEqual(release_servisi.serbest_bakiye(plan), Decimal("60"))
        self.assertEqual(release_servisi.kullanilabilir(plan), Decimal("40"))

        self.assertEqual(PriceQuote.objects.count(), q0)
        self.assertEqual(PriceLock.objects.count(), l0)

        self.assertTrue(
            AuditOlay.objects.filter(
                action="fiyatlama.release.event_created",
                entity_id=str(event.pk),
                success=True,
            ).exists()
        )

    def test_taahhut_asimi_red(self):
        plan = self._aktif_plan(taahhut="10")
        release_servisi.serbest_birak(
            actor=self.finance,
            plan=plan,
            miktar=Decimal("10"),
            donem_baslangic=date.today(),
            donem_bitis=date.today() + timedelta(days=7),
        )
        with self.assertRaises(ValidationError):
            release_servisi.serbest_birak(
                actor=self.finance,
                plan=plan,
                miktar=Decimal("0.001"),
                donem_baslangic=date.today(),
                donem_bitis=date.today() + timedelta(days=7),
            )

    def test_yetki_yok(self):
        with self.assertRaises(PermissionDenied):
            release_servisi.olustur_plan(
                actor=self.no_perm,
                sozlesme=self.soz,
                varyant=self.varyant,
                birim=ContractReleasePlan.Birim.ADET,
                toplam_taahhut=Decimal("5"),
            )
        self.assertTrue(
            AuditOlay.objects.filter(
                action="fiyatlama.release.plan_denied",
                success=False,
                reason="yetki_yok",
            ).exists()
        )

    def test_yalniz_alici_aktif_sozlesme(self):
        with self.assertRaises(ValidationError):
            release_servisi.olustur_plan(
                actor=self.finance,
                sozlesme=self.ted_soz,
                varyant=self.varyant,
                birim=ContractReleasePlan.Birim.ADET,
                toplam_taahhut=Decimal("5"),
            )

    def test_event_immutable(self):
        plan = self._aktif_plan(taahhut="20")
        event = release_servisi.serbest_birak(
            actor=self.finance,
            plan=plan,
            miktar=Decimal("5"),
            donem_baslangic=date.today(),
            donem_bitis=date.today() + timedelta(days=1),
        )
        with self.assertRaises(ValidationError):
            event.miktar = Decimal("6")
            event.save()
        with self.assertRaises(ValidationError):
            event.delete()

    def test_plan_direct_save_blocked(self):
        plan = self._aktif_plan(taahhut="15")
        with self.assertRaises(ValidationError):
            plan.aciklama = "hack"
            plan.save()
