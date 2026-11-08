from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.test import TestCase

from firmalar import roles
from firmalar.models import Firma, FirmaAdresi
from firmalar.role_permissions import seed_role_permissions
from firmalar.selectors.tenant import assert_same_firma, scope_queryset
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import assign_user_role, sync_user_role_groups
from firmalar.services.yetki_servisi import can_view_all_tenants, has_perm


User = get_user_model()


class TenantIsolationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.platform_firma = ensure_platform_firma()
        cls.firma_a = Firma.objects.create(
            ad="Firma A", firma_kodu="FA", alici_mi=True, tedarikci_mi=True
        )
        cls.firma_b = Firma.objects.create(
            ad="Firma B", firma_kodu="FB", alici_mi=True, tedarikci_mi=True
        )
        cls.adres_a = FirmaAdresi.objects.create(
            firma=cls.firma_a, tip="merkez", il="İstanbul", ilce="Kadıköy", adres="A"
        )
        cls.adres_b = FirmaAdresi.objects.create(
            firma=cls.firma_b, tip="merkez", il="Ankara", ilce="Çankaya", adres="B"
        )

        cls.user_a = User(username="ua", firma=cls.firma_a, rol=roles.ALICI_YONETICI)
        cls.user_a.set_password("x")
        cls.user_a.save()
        sync_user_role_groups(cls.user_a)

        cls.user_b = User(username="ub", firma=cls.firma_b, rol=roles.ALICI_YONETICI)
        cls.user_b.set_password("x")
        cls.user_b.save()
        sync_user_role_groups(cls.user_b)

        cls.platform_admin = User(
            username="padmin",
            firma=cls.platform_firma,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.platform_admin.set_password("x")
        cls.platform_admin.save()
        sync_user_role_groups(cls.platform_admin)

        cls.super_no_bypass = User(
            username="su",
            firma=cls.platform_firma,
            rol=roles.PLATFORM_SUPPORT,
            is_superuser=True,
            is_staff=True,
        )
        cls.super_no_bypass.set_password("x")
        cls.super_no_bypass.save()
        sync_user_role_groups(cls.super_no_bypass)

    def test_list_other_firma_adres_hidden(self):
        qs = scope_queryset(FirmaAdresi.objects.all(), self.user_a, firma_field="firma_id")
        self.assertEqual(list(qs), [self.adres_a])

    def test_get_other_firma_raises_404(self):
        with self.assertRaises(Http404):
            assert_same_firma(self.user_a, self.adres_b)

    def test_firm_admin_cannot_use_platform_perm(self):
        self.assertFalse(has_perm(self.user_a, "firmalar.view_all_tenants"))
        self.assertFalse(has_perm(self.user_a, "urunler.approve_urun"))
        self.assertFalse(can_view_all_tenants(self.user_a))

    def test_platform_admin_has_view_all(self):
        self.assertTrue(can_view_all_tenants(self.platform_admin))
        qs = scope_queryset(
            FirmaAdresi.objects.all(), self.platform_admin, firma_field="firma_id"
        )
        self.assertEqual(qs.count(), 2)

    def test_superuser_without_view_all_perm_no_tenant_bypass(self):
        """is_superuser + support rolü view_all yoksa çapraz tenant yok."""
        self.assertTrue(self.super_no_bypass.is_superuser)
        self.assertFalse(can_view_all_tenants(self.super_no_bypass))
        qs = scope_queryset(
            FirmaAdresi.objects.all(), self.super_no_bypass, firma_field="firma_id"
        )
        self.assertEqual(qs.count(), 0)  # platform firmasının adresi yok

    def test_user_requires_firma(self):
        u = User(username="nofirma", rol=roles.ALICI_YONETICI)
        u.set_password("x")
        with self.assertRaises(ValidationError):
            u.save()

    def test_second_platform_firma_rejected(self):
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Firma.objects.create(
                ad="Sahte Platform",
                firma_kodu="PLATFORM2",
                platform_mu=True,
            )

    def test_assign_user_role_syncs_group(self):
        assign_user_role(
            actor=self.user_a,
            user=self.user_a,
            firma=self.firma_a,
            rol=roles.ALICI_DENETCI,
        )
        self.user_a.refresh_from_db()
        self.assertEqual(self.user_a.rol, roles.ALICI_DENETCI)
        self.assertTrue(
            self.user_a.groups.filter(name=f"rol:{roles.ALICI_DENETCI}").exists()
        )

    def test_seed_idempotent(self):
        seed_role_permissions()
        seed_role_permissions()
        from django.contrib.auth.models import Group

        self.assertEqual(
            Group.objects.filter(name=f"rol:{roles.PLATFORM_SUPER}").count(), 1
        )
