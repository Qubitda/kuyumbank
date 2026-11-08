from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from urunler.models import Varyant
from urunler.services import onay_servisi as servisler
from ._base import KatalogTestTaban


class K004OwnershipTests(KatalogTestTaban):
    def hazir_urun(self, **kw):
        u = self.urun(**kw)
        Varyant.objects.create(urun=u, gram=Decimal("3.2"))
        return u

    def test_owner_can_submit(self):
        u = self.hazir_urun()
        servisler.onaya_gonder(u, self.tedarikci_user)
        u.refresh_from_db()
        self.assertEqual(u.onay_durumu, "onay_bekliyor")

    def test_other_firma_cannot_submit(self):
        u = self.hazir_urun()
        with self.assertRaises(PermissionDenied):
            servisler.onaya_gonder(u, self.tedarikci_b_user)

    def test_platform_without_submit_on_foreign_product(self):
        """Platform catalog onaylar; başka firmanın ürününü submit etmez (Faz 1 H*)."""
        u = self.hazir_urun()
        with self.assertRaises(PermissionDenied):
            servisler.onaya_gonder(u, self.platform)
