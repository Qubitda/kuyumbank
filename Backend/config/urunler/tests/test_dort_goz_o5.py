"""Faz 2.1 O5 — onayla/yayina_al dört göz (gönderen ≠ aktör)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.services.rol_servisi import sync_user_role_groups
from urunler.models import UrunKanal, Varyant
from urunler.services import onay_servisi as svc
from urunler.tests._base import KatalogTestTaban

User = get_user_model()


class DortGozO5Tests(KatalogTestTaban):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.psuper = User(
            username="psuper_o5",
            firma=cls.platform.firma,
            rol=roles.PLATFORM_SUPER,
            is_staff=True,
        )
        cls.psuper.set_password("x")
        cls.psuper.save()
        sync_user_role_groups(cls.psuper)

    def setUp(self):
        self.u = self.urun(
            olusturan_firma=self.tedarikci,
            olusturan_kullanici=self.tedarikci_user,
        )
        Varyant.objects.create(urun=self.u, gram=Decimal("2.0"))

    def test_onayla_rejects_same_as_gonderen(self):
        self.u.olusturan_firma = self.psuper.firma
        self.u.save()
        svc.onaya_gonder(self.u, self.psuper)
        with self.assertRaises(PermissionDenied):
            svc.onayla(self.u, self.psuper)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="urun.onayla", success=False, reason="dort_goz"
            ).exists()
        )

    def test_onayla_ok_different_actor(self):
        svc.onaya_gonder(self.u, self.tedarikci_user)
        onayli = svc.onayla(self.u, self.platform)
        self.assertEqual(onayli.onay_durumu, "onayli")

    def test_yayina_al_rejects_gonderen(self):
        self.u.olusturan_firma = self.psuper.firma
        self.u.save()
        svc.onaya_gonder(self.u, self.psuper)
        svc.onayla(self.u, self.platform)
        UrunKanal.objects.create(urun=self.u, kanal=self.kanal, aktif=True)
        with self.assertRaises(PermissionDenied):
            svc.yayina_al(self.u, self.psuper, durum="aktif")
