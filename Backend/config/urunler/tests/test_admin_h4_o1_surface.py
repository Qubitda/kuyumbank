"""ADR-0009 H4 — O1 kilidi bağımsız VaryantAdmin yüzeyinde."""

from decimal import Decimal

from django.contrib.admin.sites import site
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from urunler.admin.urun_admin import VaryantAdmin
from urunler.models import Varyant
from urunler.services import onay_servisi as svc
from urunler.tests._base import KatalogTestTaban


class AdminH4O1SurfaceTests(KatalogTestTaban):
    def setUp(self):
        self.u = self.urun(olusturan_firma=self.tedarikci)
        self.v = Varyant.objects.create(urun=self.u, gram=Decimal("2.0"))

    def _req(self, user):
        req = RequestFactory().get("/admin/")
        req.user = user
        return req

    def test_varyant_admin_no_change_when_onay_bekliyor(self):
        svc.onaya_gonder(self.u, self.tedarikci_user)
        self.u.refresh_from_db()
        ma = VaryantAdmin(Varyant, site)
        self.assertFalse(ma.has_change_permission(self._req(self.tedarikci_user), self.v))

    def test_varyant_save_model_denied_onay_bekliyor(self):
        svc.onaya_gonder(self.u, self.tedarikci_user)
        self.v.refresh_from_db()
        ma = VaryantAdmin(Varyant, site)
        self.v.gram = Decimal("9.0")
        with self.assertRaises(PermissionDenied):
            ma.save_model(self._req(self.tedarikci_user), self.v, form=None, change=True)

    def test_supplier_changelist_no_list_editable(self):
        ma = VaryantAdmin(Varyant, site)
        req = self._req(self.tedarikci_user)
        cl = ma.get_changelist_instance(req)
        self.assertEqual(cl.list_editable, ())
        self.assertEqual(ma.list_editable, ("gram", "sabit_fiyat", "ek_bedel", "stok", "aktif"))
