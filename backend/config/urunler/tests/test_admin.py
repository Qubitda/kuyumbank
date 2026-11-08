"""Faz 1.1 P1 — urunler admin tenant scope (ADR-0003-05 senaryo 1–4, 6, 7)."""

from decimal import Decimal

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from firmalar.services.yetki_servisi import can_view_all_tenants
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal, SatisKanali
from urunler.admin.urun_admin import (
    UrunAdmin,
    UrunKanalAdmin,
    VaryantAdmin,
    VaryantInline,
)
from urunler.models import Kategori, Urun, UrunKanal, Varyant
from urunler.selectors.katalog_tenant import (
    scope_urun_queryset,
    user_may_see_tedarikci_identity,
)

User = get_user_model()


class UrunlerAdminTenantScopeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        altin = KiymetliMetal.objects.create(kod="ALTIN", ad="Altın", gram_bazli=True)
        cls.ayar14 = AyarMilyem.objects.create(
            metal=altin, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        grup = FiyatGrubu.objects.create(kod="YUZUK_ALYANS", ad="Yüzük / Alyans")
        cls.kategori = Kategori.objects.create(kod="YUZUK", ad="Yüzük", fiyat_grubu=grup)
        cls.kanal = SatisKanali.objects.create(kod="ADM_K", ad="Admin kanal")

        cls.tedarikci_a = Firma.objects.create(
            ad="Ted A", firma_kodu="UADM_A", tedarikci_mi=True
        )
        cls.tedarikci_b = Firma.objects.create(
            ad="Ted B", firma_kodu="UADM_B", tedarikci_mi=True
        )
        platform = ensure_platform_firma()

        cls.staff_a = User(
            username="uadm_a",
            firma=cls.tedarikci_a,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.staff_a.set_password("x")
        cls.staff_a.save()
        sync_user_role_groups(cls.staff_a)

        cls.staff_b = User(
            username="uadm_b",
            firma=cls.tedarikci_b,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.staff_b.set_password("x")
        cls.staff_b.save()
        sync_user_role_groups(cls.staff_b)

        cls.padmin = User(
            username="uadm_p",
            firma=platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.padmin.set_password("x")
        cls.padmin.save()
        sync_user_role_groups(cls.padmin)

        cls.super_no_view_all = User(
            username="uadm_su",
            firma=platform,
            rol=roles.PLATFORM_SUPPORT,
            is_superuser=True,
            is_staff=True,
        )
        cls.super_no_view_all.set_password("x")
        cls.super_no_view_all.save()
        sync_user_role_groups(cls.super_no_view_all)

        cls.urun_a = Urun.objects.create(
            olusturan_firma=cls.tedarikci_a,
            ad="Ürün A",
            kategori=cls.kategori,
            ayar=cls.ayar14,
        )
        cls.urun_b = Urun.objects.create(
            olusturan_firma=cls.tedarikci_b,
            ad="Ürün B",
            kategori=cls.kategori,
            ayar=cls.ayar14,
        )
        cls.varyant_a = Varyant.objects.create(urun=cls.urun_a, gram=Decimal("1.1"))
        cls.varyant_b = Varyant.objects.create(urun=cls.urun_b, gram=Decimal("2.2"))
        cls.kanal_a = UrunKanal.objects.create(urun=cls.urun_a, kanal=cls.kanal)
        cls.kanal_b = UrunKanal.objects.create(urun=cls.urun_b, kanal=cls.kanal)

        cls.rf = RequestFactory()

    def _req(self, user):
        req = self.rf.get("/admin/")
        req.user = user
        return req

    # --- Senaryo 1: listeleyemez ---
    def test_s1_changelist_urun_hides_other_firma(self):
        ma = UrunAdmin(Urun, site)
        qs = ma.get_queryset(self._req(self.staff_a))
        self.assertEqual(list(qs), [self.urun_a])

    def test_s1_selector_urun_hides_other_firma(self):
        qs = scope_urun_queryset(Urun.objects.all(), self.staff_a)
        self.assertEqual(list(qs), [self.urun_a])

    # --- Senaryo 2: ID ile getiremez ---
    def test_s2_change_get_object_other_firma_none(self):
        ma = UrunAdmin(Urun, site)
        obj = ma.get_object(self._req(self.staff_a), str(self.urun_b.pk))
        self.assertIsNone(obj)

    def test_s2_varyant_get_object_other_firma_none(self):
        ma = VaryantAdmin(Varyant, site)
        obj = ma.get_object(self._req(self.staff_a), str(self.varyant_b.pk))
        self.assertIsNone(obj)

    # --- Senaryo 3: değiştiremez / silemez ---
    def test_s3_other_urun_not_in_change_queryset(self):
        ma = UrunAdmin(Urun, site)
        qs = ma.get_queryset(self._req(self.staff_a))
        self.assertFalse(qs.filter(pk=self.urun_b.pk).exists())

    def test_s3_action_queryset_scoped_excludes_b(self):
        ma = UrunAdmin(Urun, site)
        # Admin action raw queryset genelde tüm ID'leri taşır; _toplu scope uygular
        from urunler.selectors.katalog_tenant import scope_urun_queryset as scope

        scoped = scope(Urun.objects.filter(pk__in=[self.urun_a.pk, self.urun_b.pk]), self.staff_a)
        self.assertEqual(list(scoped), [self.urun_a])

    # --- Senaryo 4: ilişkili nesne ---
    def test_s4_varyant_changelist_scoped(self):
        ma = VaryantAdmin(Varyant, site)
        qs = ma.get_queryset(self._req(self.staff_a))
        self.assertEqual(list(qs), [self.varyant_a])

    def test_s4_urun_kanal_changelist_scoped(self):
        ma = UrunKanalAdmin(UrunKanal, site)
        qs = ma.get_queryset(self._req(self.staff_a))
        self.assertEqual(list(qs), [self.kanal_a])

    def test_s4_inline_queryset_scoped(self):
        # view/change_varyant rol matrisinden (seed_role_permissions); user_permissions yok
        parent = UrunAdmin(Urun, site)
        inline = VaryantInline(Urun, parent.admin_site)
        qs = inline.get_queryset(self._req(self.staff_a))
        self.assertTrue(qs.filter(pk=self.varyant_a.pk).exists())
        self.assertFalse(qs.filter(pk=self.varyant_b.pk).exists())

    def test_s4_formfield_urun_fk_scoped(self):
        ma = VaryantAdmin(Varyant, site)
        ff = ma.formfield_for_foreignkey(
            Varyant._meta.get_field("urun"), self._req(self.staff_a)
        )
        self.assertEqual(list(ff.queryset), [self.urun_a])

    def test_s4_tedarikci_identity_hidden_from_supplier_staff(self):
        self.assertFalse(user_may_see_tedarikci_identity(self.staff_a))
        ma = UrunAdmin(Urun, site)
        display = ma.get_list_display(self._req(self.staff_a))
        self.assertNotIn("olusturan_firma", display)
        autocomplete = ma.get_autocomplete_fields(self._req(self.staff_a))
        self.assertNotIn("olusturan_firma", autocomplete)

    # --- Senaryo 6: platform yalnız tanımlı perm ---
    def test_s6_platform_admin_sees_all_urun(self):
        self.assertTrue(can_view_all_tenants(self.padmin))
        ma = UrunAdmin(Urun, site)
        qs = ma.get_queryset(self._req(self.padmin))
        self.assertEqual(qs.count(), 2)
        self.assertTrue(user_may_see_tedarikci_identity(self.padmin))

    # --- Senaryo 7: superuser sessiz aşamaz ---
    def test_s7_superuser_without_view_all_no_urun_bypass(self):
        self.assertTrue(self.super_no_view_all.is_superuser)
        self.assertFalse(can_view_all_tenants(self.super_no_view_all))
        ma = UrunAdmin(Urun, site)
        qs = ma.get_queryset(self._req(self.super_no_view_all))
        self.assertEqual(qs.count(), 0)
