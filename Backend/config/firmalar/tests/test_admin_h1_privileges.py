"""ADR-0009 H1 — tenant admin is_staff / is_superuser düzenleyemez."""

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from firmalar import roles
from firmalar.admin.kullanici_admin import KullaniciAdmin
from firmalar.models import Firma, Kullanici
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups

User = get_user_model()


class AdminH1PrivilegeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.platform = ensure_platform_firma()
        cls.ted = Firma.objects.create(ad="H1T", firma_kodu="H1T", tedarikci_mi=True)
        cls.alici = Firma.objects.create(ad="H1A", firma_kodu="H1A", alici_mi=True)

        cls.padmin = User(
            username="h1p",
            firma=cls.platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.padmin.set_password("x")
        cls.padmin.save()
        sync_user_role_groups(cls.padmin)

        cls.ted_mgr = User(
            username="h1tm",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.ted_mgr.set_password("x")
        cls.ted_mgr.save()
        sync_user_role_groups(cls.ted_mgr)

        cls.alici_mgr = User(
            username="h1am",
            firma=cls.alici,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.alici_mgr.set_password("x")
        cls.alici_mgr.save()
        sync_user_role_groups(cls.alici_mgr)

        cls.target = User(
            username="h1tg",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SATIS,
            is_staff=False,
            is_superuser=False,
        )
        cls.target.set_password("x")
        cls.target.save()
        sync_user_role_groups(cls.target)

    def _ma(self):
        return KullaniciAdmin(Kullanici, site)

    def _req(self, user):
        req = RequestFactory().get("/admin/")
        req.user = user
        return req

    def test_tenant_fieldsets_hide_privileges(self):
        ma = self._ma()
        for user in (self.ted_mgr, self.alici_mgr):
            fields = []
            for _n, opts in ma.get_fieldsets(self._req(user), obj=self.target):
                fields.extend(opts.get("fields", ()))
            self.assertNotIn("is_staff", fields)
            self.assertNotIn("is_superuser", fields)

    def test_platform_fieldsets_show_privileges(self):
        ma = self._ma()
        fields = []
        for _n, opts in ma.get_fieldsets(self._req(self.padmin), obj=self.target):
            fields.extend(opts.get("fields", ()))
        self.assertIn("is_staff", fields)
        self.assertIn("is_superuser", fields)

    def test_tenant_save_cannot_escalate(self):
        ma = self._ma()
        req = self._req(self.ted_mgr)
        self.target.is_superuser = True
        self.target.is_staff = True
        ma.save_model(req, self.target, form=None, change=True)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_superuser)
        self.assertFalse(self.target.is_staff)

    def test_platform_can_set_staff(self):
        ma = self._ma()
        req = self._req(self.padmin)
        self.target.is_staff = True
        ma.save_model(req, self.target, form=None, change=True)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_staff)
