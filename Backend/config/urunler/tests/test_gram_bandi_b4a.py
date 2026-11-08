"""Faz 2.1 B4a — gram bandı hesabı + eşleştirme reddi + onay yeniden doğrulama."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from firmalar.models import AuditOlay
from fiyatlama.models import TedarikciTeklif
from urunler.models import Varyant
from urunler.services import eslestirme_servisi as svc
from urunler.services.gram_bandi import varyant_gram_bandi
from urunler.tests._base import KatalogTestTaban


class GramBandiB4aTests(KatalogTestTaban):
    def setUp(self):
        self.urun_a = self.urun(olusturan_firma=self.tedarikci)
        self.varyant = Varyant.objects.create(urun=self.urun_a, gram=Decimal("10.000"))
        self.teklif = TedarikciTeklif.objects.create(
            varyant=self.varyant,
            tedarikci=self.tedarikci,
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("10.000"),
        )

    @override_settings(VARYANT_GRAM_BANDI_ORAN=Decimal("0.05"))
    def test_band_from_oran(self):
        lo, hi = varyant_gram_bandi(self.varyant)
        self.assertEqual(lo, Decimal("9.500"))
        self.assertEqual(hi, Decimal("10.500"))

    def test_band_override_fields(self):
        self.varyant.gram_bandi_min = Decimal("8")
        self.varyant.gram_bandi_max = Decimal("9")
        self.varyant.save(update_fields=["gram_bandi_min", "gram_bandi_max"])
        lo, hi = varyant_gram_bandi(self.varyant)
        self.assertEqual(lo, Decimal("8"))
        self.assertEqual(hi, Decimal("9"))

    @override_settings(VARYANT_GRAM_BANDI_ORAN=Decimal("0.05"))
    def test_oner_rejects_out_of_band(self):
        self.teklif.gram = Decimal("12.000")
        self.teklif.save(update_fields=["gram"])
        with self.assertRaises(ValidationError):
            svc.teklif_eslestir_oner(self.teklif, self.tedarikci_user)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="teklif.eslestir_oner", success=False, reason="gram_bandi_disi"
            ).exists()
        )

    @override_settings(VARYANT_GRAM_BANDI_ORAN=Decimal("0.05"))
    def test_onayla_rechecks_band(self):
        svc.teklif_eslestir_oner(self.teklif, self.tedarikci_user)
        # Bandı daralt; öneri zaten var
        self.varyant.gram_bandi_min = Decimal("1")
        self.varyant.gram_bandi_max = Decimal("2")
        self.varyant.save(update_fields=["gram_bandi_min", "gram_bandi_max"])
        with self.assertRaises(ValidationError):
            svc.eslestirmeyi_onayla(self.teklif, self.platform)
