from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from urunler.models import UrunKanal, Varyant
from urunler.services import onay_servisi as servisler
from ._base import KatalogTestTaban


class OnayAkisiTest(KatalogTestTaban):
    def hazir_urun(self):
        u = self.urun()
        Varyant.objects.create(urun=u, gram=Decimal("3.2"))
        return u

    def test_varyantsiz_urun_onaya_gonderilemez(self):
        with self.assertRaises(ValidationError):
            servisler.onaya_gonder(self.urun(), self.tedarikci_user)

    def test_tam_akis(self):
        u = self.hazir_urun()
        UrunKanal.objects.create(urun=u, kanal=self.kanal)
        servisler.onaya_gonder(u, self.tedarikci_user)
        servisler.onayla(u, self.platform)
        servisler.yayina_al(u, self.platform)
        u.refresh_from_db()
        self.assertEqual((u.onay_durumu, u.yayin_durumu), ("onayli", "aktif"))
        self.assertEqual(u.onaylayan_kullanici, self.platform)

    def test_platform_disi_kullanici_onaylayamaz(self):
        u = self.hazir_urun()
        servisler.onaya_gonder(u, self.tedarikci_user)
        with self.assertRaises(PermissionDenied):
            servisler.onayla(u, self.tedarikci_user)

    def test_kanalsiz_urun_aktif_yayina_alinamaz(self):
        u = self.hazir_urun()
        servisler.onaya_gonder(u, self.tedarikci_user)
        servisler.onayla(u, self.platform)
        with self.assertRaises(ValidationError):
            servisler.yayina_al(u, self.platform)

    def test_red_nedensiz_olmaz_ve_yeniden_gonderilebilir(self):
        u = self.hazir_urun()
        servisler.onaya_gonder(u, self.tedarikci_user)
        with self.assertRaises(ValidationError):
            servisler.reddet(u, self.platform, "  ")
        servisler.reddet(u, self.platform, "Gram hatalı")
        servisler.onaya_gonder(u, self.tedarikci_user)
        u.refresh_from_db()
        self.assertEqual(u.onay_durumu, "onay_bekliyor")
