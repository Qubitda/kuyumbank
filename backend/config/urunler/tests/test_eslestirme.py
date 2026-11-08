"""Faz 2.0 — eslestirme_servisi kuralları."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from fiyatlama.models import TedarikciTeklif
from urunler.models import Varyant
from urunler.services import eslestirme_servisi as svc
from urunler.tests._base import KatalogTestTaban


class EslestirmeServisiTests(KatalogTestTaban):
    def setUp(self):
        # Not: seed_role_permissions @atomic burada çağrılmaz (savepoint artığı riski).
        self.urun_a = self.urun(
            kimlik_sinifi="A",
            kimlik_anahtari="CERT-001",
            olusturan_firma=self.tedarikci,
        )
        self.varyant = Varyant.objects.create(urun=self.urun_a, gram=Decimal("3.0"))
        self.teklif = TedarikciTeklif.objects.create(
            varyant=self.varyant,
            tedarikci=self.tedarikci,
            tedarikci_kodu="CERT-001",
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("3.0"),
        )

    def test_kesin_only_when_identity_matches(self):
        t = svc.teklif_eslestir_oner(
            self.teklif, self.tedarikci_user, hedef_urun=self.urun_a
        )
        self.assertEqual(t.eslestirme_guveni, TedarikciTeklif.EslestirmeGuveni.KESIN)
        self.assertEqual(t.hedef_urun_id, self.urun_a.pk)

        self.teklif.tedarikci_kodu = "OTHER"
        self.teklif.save(update_fields=["tedarikci_kodu"])
        t2 = svc.teklif_eslestir_oner(
            self.teklif, self.tedarikci_user, hedef_urun=self.urun_a
        )
        self.assertEqual(t2.eslestirme_guveni, TedarikciTeklif.EslestirmeGuveni.MANUEL)

    def test_hedef_urun_persisted(self):
        hedef = self.urun(
            kimlik_sinifi="C",
            kimlik_anahtari="",
            olusturan_firma=self.tedarikci,
            ad="Hedef C",
        )
        # aynı ayar zorunlu
        t = svc.teklif_eslestir_oner(
            self.teklif, self.tedarikci_user, hedef_urun=hedef
        )
        t.refresh_from_db()
        self.assertEqual(t.hedef_urun_id, hedef.pk)

    def test_onayla_status_after_lock(self):
        svc.teklif_eslestir_oner(self.teklif, self.tedarikci_user)
        t = svc.eslestirmeyi_onayla(self.teklif, self.platform)
        self.assertEqual(t.eslestirme_durumu, TedarikciTeklif.EslestirmeDurumu.ONAYLANDI)

    def test_ayir_only_from_onaylandi(self):
        svc.teklif_eslestir_oner(self.teklif, self.tedarikci_user)
        with self.assertRaises(ValidationError):
            svc.urunu_ayir(self.teklif, self.platform, "erken")
        svc.eslestirmeyi_onayla(self.teklif, self.platform)
        t = svc.urunu_ayir(self.teklif, self.platform, "yanlış birleşti")
        self.assertEqual(t.eslestirme_durumu, TedarikciTeklif.EslestirmeDurumu.AYRILDI)

    def test_approve_eslestirme_perm_required(self):
        svc.teklif_eslestir_oner(self.teklif, self.tedarikci_user)
        with self.assertRaises(PermissionDenied):
            svc.eslestirmeyi_onayla(self.teklif, self.tedarikci_user)
