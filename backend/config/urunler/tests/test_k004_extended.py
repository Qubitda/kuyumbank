"""A5 — K-004 ek senaryolar (yetkisiz rol, audit)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.services.rol_servisi import sync_user_role_groups
from urunler.models import Varyant
from urunler.services import onay_servisi as servisler

from ._base import KatalogTestTaban

User = get_user_model()


class K004ExtendedTests(KatalogTestTaban):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.depo_user = User(
            username="depo1",
            firma=cls.tedarikci,
            rol=roles.TEDARIKCI_DEPO,
        )
        cls.depo_user.set_password("x")
        cls.depo_user.save()
        sync_user_role_groups(cls.depo_user)

    def hazir_urun(self, **kw):
        u = self.urun(**kw)
        Varyant.objects.create(urun=u, gram=Decimal("2.5"))
        return u

    def test_yetkisiz_rol_submit_denied(self):
        u = self.hazir_urun()
        with self.assertRaises(PermissionDenied):
            servisler.onaya_gonder(u, self.depo_user)

    def test_failed_audit_persists_on_ownership_deny(self):
        """Faz 1.1 P0: reddedilen deneme audit'i ürün atomic dışında kalır."""
        u = self.hazir_urun()
        before_status = u.onay_durumu
        before = AuditOlay.objects.filter(
            action="urun.onaya_gonder", success=False
        ).count()
        with self.assertRaises(PermissionDenied):
            servisler.onaya_gonder(u, self.tedarikci_b_user)
        after = AuditOlay.objects.filter(
            action="urun.onaya_gonder", success=False
        ).count()
        self.assertEqual(after, before + 1)
        u.refresh_from_db()
        self.assertEqual(u.onay_durumu, before_status)

    def test_audit_on_success(self):
        u = self.hazir_urun()
        before = AuditOlay.objects.filter(action="urun.onaya_gonder", success=True).count()
        servisler.onaya_gonder(u, self.tedarikci_user)
        after = AuditOlay.objects.filter(action="urun.onaya_gonder", success=True).count()
        self.assertEqual(after, before + 1)

    def test_idor_submit_other_supplier_product(self):
        u = self.hazir_urun(olusturan_firma=self.tedarikci_b)
        with self.assertRaises(PermissionDenied):
            servisler.onaya_gonder(u, self.tedarikci_user)
