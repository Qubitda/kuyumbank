"""ADR-0005 §8 kabul testleri — Faz 2.1 B4a tamamlayıcı."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from fiyatlama.models import TedarikciTeklif
from urunler.models import Urun, Varyant
from urunler.services import eslestirme_servisi as svc
from urunler.tests._base import KatalogTestTaban


class Adr0005KabulB4aTests(KatalogTestTaban):
    def test_ab_duplicate_kimlik_blocked(self):
        self.urun(
            kimlik_sinifi="A",
            kimlik_anahtari="DUP-1",
            olusturan_firma=self.tedarikci,
        )
        with self.assertRaises(IntegrityError):
            self.urun(
                kimlik_sinifi="A",
                kimlik_anahtari="DUP-1",
                olusturan_firma=self.tedarikci_b,
                ad="Kopya",
            )

    def test_ayar_mismatch_generic(self):
        u14 = self.urun(olusturan_firma=self.tedarikci)
        v = Varyant.objects.create(urun=u14, gram=Decimal("2"))
        t = TedarikciTeklif.objects.create(
            varyant=v,
            tedarikci=self.tedarikci,
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("2"),
        )
        u18 = self.urun(
            olusturan_firma=self.tedarikci,
            ayar=self.ayarsiz,
            ad="Ayarsız hedef",
        )
        with self.assertRaises(ValidationError) as ctx:
            svc.teklif_eslestir_oner(t, self.tedarikci_user, hedef_urun=u18)
        self.assertIn("uygun değil", str(ctx.exception).lower())

    def test_seo_no_hardcoded_sample_brand_in_defaults(self):
        u = self.urun(ad="Özel Model X")
        # save SEO üretimi marka sabitleri içermemeli
        u.save()
        blob = " ".join(
            filter(
                None,
                [u.slug, u.meta_baslik or "", u.meta_aciklama or "", u.gorsel_alt_metni or ""],
            )
        ).lower()
        for brand in ("pandora", "swarovski", "tiffany", "cartier"):
            self.assertNotIn(brand, blob)
