"""Faz 2.1 B1 — TedarikciTeklifAdmin readonly + FK scope + sunucu tedarikci."""

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
from fiyatlama.selectors.tenant import scope_teklif_varyant_queryset
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal
from urunler.models import Kategori, Urun, Varyant

User = get_user_model()


class TeklifAdminB1Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        platform = ensure_platform_firma()
        cls.ted_a = Firma.objects.create(ad="B1A", firma_kodu="B1A", tedarikci_mi=True)
        cls.ted_b = Firma.objects.create(ad="B1B", firma_kodu="B1B", tedarikci_mi=True)
        metal = KiymetliMetal.objects.create(kod="AU", ad="Altın", gram_bazli=True)
        ayar = AyarMilyem.objects.create(
            metal=metal, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        grup = FiyatGrubu.objects.create(kod="B1G", ad="B1G")
        kat = Kategori.objects.create(kod="B1K", ad="Yüzük", fiyat_grubu=grup)

        cls.padmin = User(
            username="b1p",
            firma=platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.padmin.set_password("x")
        cls.padmin.save()
        sync_user_role_groups(cls.padmin)

        ua = Urun.objects.create(
            olusturan_firma=cls.ted_a, ad="UA", kategori=kat, ayar=ayar
        )
        ub = Urun.objects.create(
            olusturan_firma=cls.ted_b, ad="UB", kategori=kat, ayar=ayar
        )
        u_cat = Urun.objects.create(
            olusturan_firma=cls.ted_b, ad="CAT", kategori=kat, ayar=ayar
        )
        Urun.objects.filter(pk=u_cat.pk).update(
            onay_durumu="onayli",
            onaylayan_kullanici=cls.padmin,
            onay_zamani=timezone.now(),
        )
        u_cat.refresh_from_db()

        cls.va = Varyant.objects.create(urun=ua, gram=Decimal("2"))
        cls.vb = Varyant.objects.create(urun=ub, gram=Decimal("3"))
        cls.v_cat = Varyant.objects.create(urun=u_cat, gram=Decimal("4"))

        cls.staff_a = User(
            username="b1a",
            firma=cls.ted_a,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.staff_a.set_password("x")
        cls.staff_a.save()
        sync_user_role_groups(cls.staff_a)

    def _ma(self):
        return TedarikciTeklifAdmin(TedarikciTeklif, site)

    def _req(self, user):
        req = RequestFactory().get("/admin/")
        req.user = user
        return req

    def test_supplier_readonly_servis_fields(self):
        ma = self._ma()
        ro = ma.get_readonly_fields(self._req(self.staff_a))
        for f in (
            "durum",
            "onaylayan",
            "onay_zamani",
            "eslestirme_durumu",
            "eslestirme_guveni",
            "hedef_urun",
            "esdegerlik_seviyesi",
            "tedarikci",
        ):
            self.assertIn(f, ro)

    def test_varyant_fk_scoped_for_supplier(self):
        qs = scope_teklif_varyant_queryset(Varyant.objects.all(), self.staff_a)
        ids = set(qs.values_list("pk", flat=True))
        self.assertIn(self.va.pk, ids)
        self.assertNotIn(self.vb.pk, ids)
        self.assertIn(self.v_cat.pk, ids)

    def test_formfield_varyant_uses_selector(self):
        ma = self._ma()
        ff = ma.formfield_for_foreignkey(
            TedarikciTeklif._meta.get_field("varyant"), self._req(self.staff_a)
        )
        ids = set(ff.queryset.values_list("pk", flat=True))
        self.assertIn(self.va.pk, ids)
        self.assertNotIn(self.vb.pk, ids)

    def test_save_model_forces_supplier_firma(self):
        ma = self._ma()
        req = self._req(self.staff_a)
        obj = TedarikciTeklif(
            varyant=self.va,
            tedarikci=self.ted_b,
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("2"),
        )

        class _F:
            cleaned_data = {}

        ma.save_model(req, obj, _F(), change=False)
        self.assertEqual(obj.tedarikci_id, self.ted_a.pk)
