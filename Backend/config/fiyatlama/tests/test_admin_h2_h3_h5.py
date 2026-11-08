"""ADR-0009 H2/H3/H5 — teklif admin kilit, maliyet görünürlüğü, versiyon eşleşme sıfır."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.admin.admin import TedarikciTeklifAdmin
from fiyatlama.models import TedarikciTeklif
from fiyatlama.selectors.tenant import (
    teklif_eslestirme_uygun_mu,
    user_may_see_teklif_maliyet,
)
from fiyatlama.services import teklif_servisi
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal
from urunler.models import Kategori, Urun, Varyant

User = get_user_model()


class TeklifAdminH2H3H5Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        platform = ensure_platform_firma()
        cls.ted = Firma.objects.create(ad="H2T", firma_kodu="H2T", tedarikci_mi=True)
        cls.alici_f = Firma.objects.create(ad="H2A", firma_kodu="H2A", alici_mi=True)
        metal = KiymetliMetal.objects.create(kod="AU", ad="Altın", gram_bazli=True)
        ayar = AyarMilyem.objects.create(
            metal=metal, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        grup = FiyatGrubu.objects.create(kod="H2G", ad="H2G")
        kat = Kategori.objects.create(kod="H2K", ad="Yüzük", fiyat_grubu=grup)
        cls.padmin = User(
            username="h2p",
            firma=platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.padmin.set_password("x")
        cls.padmin.save()
        sync_user_role_groups(cls.padmin)

        cls.approver = User(
            username="h2ap",
            firma=platform,
            rol=roles.PLATFORM_CATALOG,
            is_staff=True,
        )
        cls.approver.set_password("x")
        cls.approver.save()
        sync_user_role_groups(cls.approver)

        cls.urun = Urun.objects.create(
            olusturan_firma=cls.ted, ad="H2U", kategori=kat, ayar=ayar
        )
        Urun.objects.filter(pk=cls.urun.pk).update(
            onay_durumu="onayli",
            onaylayan_kullanici=cls.padmin,
            onay_zamani=timezone.now(),
        )
        cls.urun.refresh_from_db()
        cls.varyant = Varyant.objects.create(urun=cls.urun, gram=Decimal("2.0"))

        cls.staff = User(
            username="h2s",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.staff.set_password("x")
        cls.staff.save()
        sync_user_role_groups(cls.staff)

        cls.alici = User(
            username="h2al",
            firma=cls.alici_f,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.alici.set_password("x")
        cls.alici.save()
        sync_user_role_groups(cls.alici)

    def _dates(self):
        bas = timezone.localdate()
        return bas, bas + timedelta(days=30)

    def _teklif(self, **kwargs):
        bas, bit = self._dates()
        defaults = dict(
            varyant=self.varyant,
            tedarikci=self.ted,
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("2.0"),
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
            durum=TedarikciTeklif.Durum.TASLAK,
        )
        defaults.update(kwargs)
        return TedarikciTeklif.objects.create(**defaults)

    def _ma(self):
        return TedarikciTeklifAdmin(TedarikciTeklif, site)

    def _req(self, user):
        req = RequestFactory().get("/admin/")
        req.user = user
        return req

    def test_h3_supplier_sees_own_maliyet(self):
        self.assertTrue(user_may_see_teklif_maliyet(self.staff))
        fields = self._ma().get_fields(self._req(self.staff))
        self.assertIn("birim_fiyat", fields)
        self.assertIn("iscilik_override", fields)

    def test_h3_buyer_hides_maliyet(self):
        self.assertFalse(user_may_see_teklif_maliyet(self.alici))
        fields = self._ma().get_fields(self._req(self.alici))
        self.assertNotIn("birim_fiyat", fields)
        self.assertNotIn("iscilik_override", fields)

    def test_h2_yayinda_commercial_readonly(self):
        t = self._teklif()
        teklif_servisi.onaya_gonder(t, self.staff)
        teklif_servisi.yayina_al(t, self.approver)
        t.refresh_from_db()
        ro = self._ma().get_readonly_fields(self._req(self.staff), t)
        for f in ("gram", "fiyat_modeli", "stok_adet", "oncelik", "gecerlilik_baslangic"):
            self.assertIn(f, ro)

    def test_h2_save_model_blocks_yayinda_gram_change(self):
        t = self._teklif()
        teklif_servisi.onaya_gonder(t, self.staff)
        teklif_servisi.yayina_al(t, self.approver)
        t.refresh_from_db()
        old_gram = t.gram
        t.gram = Decimal("9.9")
        self._ma().save_model(self._req(self.staff), t, form=None, change=True)
        t.refresh_from_db()
        self.assertEqual(t.gram, old_gram)

    def test_h5_yeni_versiyon_clears_eslestirme(self):
        t = self._teklif(
            eslestirme_durumu="onaylandi",
            hedef_urun=self.urun,
            eslestirme_guveni="kesin",
        )
        teklif_servisi.onaya_gonder(t, self.staff)
        teklif_servisi.yayina_al(t, self.approver)
        yeni = teklif_servisi.yeni_versiyon_olustur(t, self.staff, gram=Decimal("2.5"))
        self.assertEqual(yeni.eslestirme_durumu, "")
        self.assertIsNone(yeni.hedef_urun_id)
        self.assertEqual(yeni.eslestirme_kaniti, {})
        self.assertFalse(teklif_eslestirme_uygun_mu(yeni))
