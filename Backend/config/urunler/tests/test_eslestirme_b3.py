"""Faz 2.1 B3 — teklif_eslestir_oner hedef/kanıt/durum/oracle."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from firmalar.models import AuditOlay
from fiyatlama.models import TedarikciTeklif
from urunler.models import Varyant
from urunler.services import eslestirme_servisi as svc
from urunler.tests._base import KatalogTestTaban


class EslestirmeB3Tests(KatalogTestTaban):
    def setUp(self):
        self.urun_a = self.urun(
            kimlik_sinifi="A",
            kimlik_anahtari="CERT-B3",
            olusturan_firma=self.tedarikci,
        )
        self.varyant = Varyant.objects.create(urun=self.urun_a, gram=Decimal("3.0"))
        self.teklif = TedarikciTeklif.objects.create(
            varyant=self.varyant,
            tedarikci=self.tedarikci,
            tedarikci_kodu="CERT-B3",
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("3.0"),
        )

    def test_kanit_oracle_ignored_for_kesin(self):
        self.teklif.tedarikci_kodu = "OTHER"
        self.teklif.save(update_fields=["tedarikci_kodu"])
        t = svc.teklif_eslestir_oner(
            self.teklif,
            self.tedarikci_user,
            hedef_urun=self.urun_a,
            kanit={"not": "x"},  # kimlik anahtarı kanıtta yok / yasak anahtar değil
        )
        self.assertEqual(t.eslestirme_guveni, TedarikciTeklif.EslestirmeGuveni.MANUEL)

    def test_forbidden_kanit_key(self):
        with self.assertRaises(ValidationError):
            svc.teklif_eslestir_oner(
                self.teklif,
                self.tedarikci_user,
                kanit={"kimlik_anahtari": "CERT-B3"},
            )
        self.assertTrue(
            AuditOlay.objects.filter(
                action="teklif.eslestir_oner", success=False, reason="kanit_gecersiz"
            ).exists()
        )

    def test_onaylandi_blocks_new_oner(self):
        svc.teklif_eslestir_oner(self.teklif, self.tedarikci_user)
        svc.eslestirmeyi_onayla(self.teklif, self.platform)
        with self.assertRaises(ValidationError):
            svc.teklif_eslestir_oner(self.teklif, self.tedarikci_user)

    def test_foreign_hedef_generic_error(self):
        diger = self.urun(
            olusturan_firma=self.tedarikci_b,
            ad="Gizli",
            kimlik_sinifi="C",
        )
        with self.assertRaises(ValidationError) as ctx:
            svc.teklif_eslestir_oner(
                self.teklif, self.tedarikci_user, hedef_urun=diger
            )
        self.assertNotIn("CERT", str(ctx.exception))
        self.assertNotIn("Gizli", str(ctx.exception))

    def test_supplier_audit_hides_guven(self):
        svc.teklif_eslestir_oner(self.teklif, self.tedarikci_user)
        row = AuditOlay.objects.filter(
            action="teklif.eslestir_oner", success=True
        ).latest("created_at")
        self.assertEqual(row.detail.get("guven"), "gizli")
