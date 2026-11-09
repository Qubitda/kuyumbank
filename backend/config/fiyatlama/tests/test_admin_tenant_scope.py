"""Fiyatlama admin tenant scope — ADR-0003-05 hücreleri."""

from decimal import Decimal

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.admin.admin import (
    FiyatSozlesmesiAdmin,
    FiyatSozlesmesiKalemiAdmin,
    PriceCalculationLogAdmin,
    TedarikciTeklifAdmin,
    TeklifTasMaliyetiAdmin,
)
from fiyatlama.models import (
    FiyatSozlesmesi,
    FiyatSozlesmesiKalemi,
    PriceCalculationLog,
    TedarikciTeklif,
    TeklifTasMaliyeti,
)
from fiyatlama.selectors.tenant import user_may_see_fiyat_maliyet
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal
from urunler.models import Kategori, Urun, Varyant

User = get_user_model()


class FiyatlamaAdminTenantTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        platform = ensure_platform_firma()
        cls.ted_a = Firma.objects.create(
            ad="FTA", firma_kodu="FTA", tedarikci_mi=True
        )
        cls.ted_b = Firma.objects.create(
            ad="FTB", firma_kodu="FTB", tedarikci_mi=True
        )
        cls.alici = Firma.objects.create(
            ad="ALI", firma_kodu="ALI", alici_mi=True
        )

        metal = KiymetliMetal.objects.create(kod="ALTIN", ad="Altın", gram_bazli=True)
        cls.ayar = AyarMilyem.objects.create(
            metal=metal, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        grup = FiyatGrubu.objects.create(kod="FG", ad="FG")
        kat = Kategori.objects.create(kod="K", ad="Yüzük", fiyat_grubu=grup)
        urun_a = Urun.objects.create(
            olusturan_firma=cls.ted_a, ad="UA", kategori=kat, ayar=cls.ayar
        )
        urun_b = Urun.objects.create(
            olusturan_firma=cls.ted_b, ad="UB", kategori=kat, ayar=cls.ayar
        )
        va = Varyant.objects.create(urun=urun_a, gram=Decimal("2"))
        vb = Varyant.objects.create(urun=urun_b, gram=Decimal("3"))

        cls.teklif_a = TedarikciTeklif.objects.create(
            varyant=va,
            tedarikci=cls.ted_a,
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("2"),
            birim_fiyat=Decimal("100"),
        )
        cls.teklif_b = TedarikciTeklif.objects.create(
            varyant=vb,
            tedarikci=cls.ted_b,
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("3"),
            birim_fiyat=Decimal("200"),
        )
        cls.padmin = User(
            username="fp",
            firma=platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.padmin.set_password("x")
        cls.padmin.save()
        sync_user_role_groups(cls.padmin)

        cls.staff_a = User(
            username="fta",
            firma=cls.ted_a,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.staff_a.set_password("x")
        cls.staff_a.save()
        sync_user_role_groups(cls.staff_a)

        cls.alici_user = User(
            username="ali",
            firma=cls.alici,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.alici_user.set_password("x")
        cls.alici_user.save()
        sync_user_role_groups(cls.alici_user)

        cls.tasi_a = TeklifTasMaliyeti.objects.create(
            teklif=cls.teklif_a,
            tas_grubu=TeklifTasMaliyeti.TasGrubu.PIRLANTA,
            adet=1,
            toplam_karat=Decimal("0.5"),
            bedel=Decimal("50"),
        )

        cls.soz_a = FiyatSozlesmesi.objects.create(
            firma=cls.ted_a,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.TEDARIKCI,
            gecerlilik_baslangic="2026-01-01",
            gecerlilik_bitis="2026-12-31",
            durum=FiyatSozlesmesi.Durum.TASLAK,
            olusturan_kullanici=cls.padmin,
        )
        cls.soz_b = FiyatSozlesmesi.objects.create(
            firma=cls.ted_b,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.TEDARIKCI,
            gecerlilik_baslangic="2026-01-01",
            gecerlilik_bitis="2026-12-31",
            durum=FiyatSozlesmesi.Durum.TASLAK,
            olusturan_kullanici=cls.padmin,
        )
        cls.kalem_a = FiyatSozlesmesiKalemi.objects.create(
            sozlesme=cls.soz_a,
            metal=metal,
            marj_tipi=FiyatSozlesmesiKalemi.MarjTipi.YUZDE,
            marj_degeri=Decimal("5"),
            iscilik=Decimal("10"),
        )
        # Fixture: kalem sonrası AKTIF (immutability bypass — yalnız test kurulumu)
        FiyatSozlesmesi.objects.filter(pk__in=[cls.soz_a.pk, cls.soz_b.pk]).update(
            durum=FiyatSozlesmesi.Durum.AKTIF
        )
        cls.soz_a.refresh_from_db()
        cls.soz_b.refresh_from_db()
        cls.log = PriceCalculationLog.objects.create(
            sozlesme=cls.soz_a,
            kalem=cls.kalem_a,
            varyant=va,
            metal_bedeli=Decimal("100"),
            iscilik=Decimal("10"),
            marj=Decimal("5"),
            toplam=Decimal("123"),
        )

        cls.rf = RequestFactory()

    def _req(self, user):
        r = self.rf.get("/admin/")
        r.user = user
        return r

    # Senaryo 1
    def test_s1_teklif_changelist_hides_other(self):
        ma = TedarikciTeklifAdmin(TedarikciTeklif, site)
        qs = ma.get_queryset(self._req(self.staff_a))
        self.assertEqual(list(qs), [self.teklif_a])

    # Senaryo 2
    def test_s2_teklif_get_object_other_none(self):
        ma = TedarikciTeklifAdmin(TedarikciTeklif, site)
        self.assertIsNone(ma.get_object(self._req(self.staff_a), str(self.teklif_b.pk)))

    # Senaryo 3
    def test_s3_sozlesme_queryset_excludes_b(self):
        ma = FiyatSozlesmesiAdmin(FiyatSozlesmesi, site)
        qs = ma.get_queryset(self._req(self.staff_a))
        self.assertTrue(qs.filter(pk=self.soz_a.pk).exists())
        self.assertFalse(qs.filter(pk=self.soz_b.pk).exists())

    # Senaryo 4
    def test_s4_teklif_tas_maliyeti_scoped(self):
        ma = TeklifTasMaliyetiAdmin(TeklifTasMaliyeti, site)
        qs = ma.get_queryset(self._req(self.staff_a))
        self.assertEqual(list(qs), [self.tasi_a])

    def test_s4_kalem_scoped(self):
        ma = FiyatSozlesmesiKalemiAdmin(FiyatSozlesmesiKalemi, site)
        qs = ma.get_queryset(self._req(self.staff_a))
        self.assertEqual(list(qs), [self.kalem_a])

    # Senaryo 6
    def test_s6_platform_sees_all_teklif(self):
        ma = TedarikciTeklifAdmin(TedarikciTeklif, site)
        self.assertEqual(ma.get_queryset(self._req(self.padmin)).count(), 2)

    # Senaryo 7 — maliyet: platform sözleşme/log; teklifte tedarikçi kendi maliyetini görür (ADR-0009 H3)
    def test_s7_supplier_sees_own_teklif_cost_not_platform_maliyet(self):
        from fiyatlama.selectors.tenant import user_may_see_teklif_maliyet

        self.assertFalse(user_may_see_fiyat_maliyet(self.staff_a))
        self.assertTrue(user_may_see_teklif_maliyet(self.staff_a))
        ma = TedarikciTeklifAdmin(TedarikciTeklif, site)
        display = ma.get_list_display(self._req(self.staff_a))
        self.assertIn("birim_fiyat", display)

    def test_s7_alici_price_log_empty(self):
        self.assertFalse(user_may_see_fiyat_maliyet(self.alici_user))
        ma = PriceCalculationLogAdmin(PriceCalculationLog, site)
        self.assertEqual(ma.get_queryset(self._req(self.alici_user)).count(), 0)

    def test_s7_platform_sees_log(self):
        self.assertTrue(user_may_see_fiyat_maliyet(self.padmin))
        ma = PriceCalculationLogAdmin(PriceCalculationLog, site)
        self.assertEqual(ma.get_queryset(self._req(self.padmin)).count(), 1)
