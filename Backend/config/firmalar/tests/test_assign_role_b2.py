"""Faz 2.1 B2 — assign_user_role actor/perm/tenant + KullaniciAdmin FK scope."""

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from firmalar import roles
from firmalar.admin.kullanici_admin import KullaniciAdmin
from firmalar.models import AuditOlay, Firma, Kullanici
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import assign_user_role, sync_user_role_groups

User = get_user_model()


class AssignRoleB2Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.platform = ensure_platform_firma()
        cls.firma_a = Firma.objects.create(
            ad="RA", firma_kodu="RA", alici_mi=True, tedarikci_mi=True
        )
        cls.firma_b = Firma.objects.create(
            ad="RB", firma_kodu="RB", alici_mi=True, tedarikci_mi=True
        )
        cls.padmin = User(
            username="b2p",
            firma=cls.platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.padmin.set_password("x")
        cls.padmin.save()
        sync_user_role_groups(cls.padmin)

        cls.mgr_a = User(
            username="b2ma",
            firma=cls.firma_a,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.mgr_a.set_password("x")
        cls.mgr_a.save()
        sync_user_role_groups(cls.mgr_a)

        cls.target_a = User(
            username="b2ta",
            firma=cls.firma_a,
            rol=roles.ALICI_DENETCI,
        )
        cls.target_a.set_password("x")
        cls.target_a.save()
        sync_user_role_groups(cls.target_a)

        cls.target_b = User(
            username="b2tb",
            firma=cls.firma_b,
            rol=roles.ALICI_DENETCI,
        )
        cls.target_b.set_password("x")
        cls.target_b.save()
        sync_user_role_groups(cls.target_b)

    def test_audit_actor_is_changer(self):
        assign_user_role(
            actor=self.mgr_a,
            user=self.target_a,
            firma=self.firma_a,
            rol=roles.ALICI_SATINALMACI,
        )
        row = AuditOlay.objects.filter(action="user.assign_role", success=True).latest(
            "created_at"
        )
        self.assertEqual(row.actor_id, self.mgr_a.pk)
        self.assertEqual(row.detail.get("hedef_user_id"), self.target_a.pk)

    def test_cross_tenant_denied(self):
        with self.assertRaises(PermissionDenied):
            assign_user_role(
                actor=self.mgr_a,
                user=self.target_b,
                firma=self.firma_a,
                rol=roles.ALICI_DENETCI,
            )
        self.assertTrue(
            AuditOlay.objects.filter(
                action="user.assign_role", success=False, reason="tenant_hedef"
            ).exists()
        )

    def test_firma_change_only_platform(self):
        with self.assertRaises(PermissionDenied):
            assign_user_role(
                actor=self.mgr_a,
                user=self.target_a,
                firma=self.firma_b,
                rol=roles.ALICI_DENETCI,
            )
        assign_user_role(
            actor=self.padmin,
            user=self.target_a,
            firma=self.firma_b,
            rol=roles.ALICI_DENETCI,
        )
        self.target_a.refresh_from_db()
        self.assertEqual(self.target_a.firma_id, self.firma_b.pk)

    def test_admin_firma_fk_scoped(self):
        ma = KullaniciAdmin(Kullanici, site)
        req = RequestFactory().get("/admin/")
        req.user = self.mgr_a
        ff = ma.formfield_for_foreignkey(Kullanici._meta.get_field("firma"), req)
        ids = set(ff.queryset.values_list("pk", flat=True))
        self.assertEqual(ids, {self.firma_a.pk})
