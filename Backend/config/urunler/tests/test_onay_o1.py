"""Faz 2.1 O1 — onay_bekliyor readonly + geri_cek + taslaga_al + kritik kilit."""

from decimal import Decimal

from django.contrib.admin.sites import site
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.utils import timezone

from firmalar.models import AuditOlay
from urunler.admin.urun_admin import UrunAdmin
from urunler.models import Urun, Varyant
from urunler.services import onay_servisi as svc
from urunler.tests._base import KatalogTestTaban


class OnayO1Tests(KatalogTestTaban):
    def setUp(self):
        self.u = self.urun(olusturan_firma=self.tedarikci)
        Varyant.objects.create(urun=self.u, gram=Decimal("2.0"))

    def test_geri_cek_to_taslak(self):
        svc.onaya_gonder(self.u, self.tedarikci_user)
        self.u.refresh_from_db()
        self.assertEqual(self.u.onay_durumu, "onay_bekliyor")
        svc.geri_cek(self.u, self.tedarikci_user)
        self.u.refresh_from_db()
        self.assertEqual(self.u.onay_durumu, "taslak")
        self.assertTrue(
            AuditOlay.objects.filter(action="urun.geri_cek", success=True).exists()
        )

    def test_supplier_cannot_change_onay_bekliyor_admin(self):
        svc.onaya_gonder(self.u, self.tedarikci_user)
        self.u.refresh_from_db()
        ma = UrunAdmin(Urun, site)
        req = RequestFactory().get("/admin/")
        req.user = self.tedarikci_user
        self.assertFalse(ma.has_change_permission(req, self.u))

    def test_kritik_alan_blocked_when_onayli(self):
        svc.onaya_gonder(self.u, self.tedarikci_user)
        svc.onayla(self.u, self.platform)
        self.u.refresh_from_db()
        self.u.ad = "Hack"
        with self.assertRaises(ValidationError):
            svc.assert_onayli_kritik_kilit(self.u)

    def test_taslaga_al_then_edit(self):
        svc.onaya_gonder(self.u, self.tedarikci_user)
        svc.onayla(self.u, self.platform)
        svc.taslaga_al(self.u, self.platform)
        self.u.refresh_from_db()
        self.assertEqual(self.u.onay_durumu, "taslak")
        self.assertEqual(self.u.yayin_durumu, "pasif")
        self.u.ad = "Yeni ad"
        svc.assert_onayli_kritik_kilit(self.u)  # no raise
