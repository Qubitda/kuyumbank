"""A2 — Django Admin yüzeyinde tenant scope (doğrulama turu)."""

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from firmalar import roles
from firmalar.admin.firma_admin import FirmaAdresiAdmin, FirmaAdmin
from firmalar.admin.kullanici_admin import KullaniciAdmin
from firmalar.models import Firma, FirmaAdresi, Kullanici
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups

User = get_user_model()


class AdminTenantScopeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.platform = ensure_platform_firma()
        cls.firma_a = Firma.objects.create(
            ad="A Co", firma_kodu="ADM_A", alici_mi=True, tedarikci_mi=True
        )
        cls.firma_b = Firma.objects.create(
            ad="B Co", firma_kodu="ADM_B", alici_mi=True, tedarikci_mi=True
        )
        cls.adres_a = FirmaAdresi.objects.create(
            firma=cls.firma_a, tip="merkez", il="İstanbul", adres="A"
        )
        cls.adres_b = FirmaAdresi.objects.create(
            firma=cls.firma_b, tip="merkez", il="Ankara", adres="B"
        )
        cls.user_a = User(
            username="admin_ua",
            firma=cls.firma_a,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.user_a.set_password("x")
        cls.user_a.save()
        sync_user_role_groups(cls.user_a)

        cls.padmin = User(
            username="admin_p",
            firma=cls.platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.padmin.set_password("x")
        cls.padmin.save()
        sync_user_role_groups(cls.padmin)

        cls.rf = RequestFactory()

    def _req(self, user):
        req = self.rf.get("/admin/")
        req.user = user
        return req

    def test_changelist_firma_adresi_scoped(self):
        ma = FirmaAdresiAdmin(FirmaAdresi, site)
        qs = ma.get_queryset(self._req(self.user_a))
        self.assertEqual(list(qs), [self.adres_a])

    def test_changelist_firma_model_scoped(self):
        ma = FirmaAdmin(Firma, site)
        qs = ma.get_queryset(self._req(self.user_a))
        self.assertEqual(list(qs), [self.firma_a])

    def test_changelist_kullanici_scoped(self):
        ma = KullaniciAdmin(Kullanici, site)
        qs = ma.get_queryset(self._req(self.user_a))
        self.assertTrue(qs.filter(pk=self.user_a.pk).exists())
        self.assertFalse(qs.filter(username="admin_p").exists())

    def test_platform_admin_sees_all_adres(self):
        ma = FirmaAdresiAdmin(FirmaAdresi, site)
        qs = ma.get_queryset(self._req(self.padmin))
        self.assertEqual(qs.count(), 2)
