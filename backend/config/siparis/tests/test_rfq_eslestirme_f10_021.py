"""F10-021 — Katalog dışı RFQ eşleştirme motoru."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.models import RFQ, RFQEslestirme
from siparis.services import rfq_eslestirme_servisi, rfq_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from urunler.models import Varyant

User = get_user_model()


class RfqEslestirmeF10021Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)

        cls.catalog = User(
            username="rfq_cat",
            firma=cls.platform,
            rol=roles.PLATFORM_CATALOG,
            is_staff=True,
        )
        cls.catalog.set_password("x")
        cls.catalog.save()
        sync_user_role_groups(cls.catalog)

        # İkinci onaylı ürün — skor ayrımı için
        u2 = type(cls.urun).objects.create(
            olusturan_firma=cls.platform,
            ad="Altın yüzük klasik",
            kategori=cls.urun.kategori,
            ayar=cls.ayar,
        )
        type(cls.urun).objects.filter(pk=u2.pk).update(
            onay_durumu="onayli",
            yayin_durumu="aktif",
            onaylayan_kullanici=cls.finance,
            onay_zamani=timezone.now(),
        )
        u2.refresh_from_db()
        cls.varyant_yuzuk = Varyant.objects.create(
            urun=u2, gram=Decimal("3.000"), ek_bedel=Decimal("0")
        )

    def _katalog_disi_rfq(self):
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="Katalog dışı talep",
            talep_tipi=RFQ.TalepTipi.KATALOG_DISI,
            line_specs=[
                {
                    "aciklama": "Altın yüzük klasik 3 gram",
                    "miktar": Decimal("5"),
                    "birim": "ADET",
                }
            ],
        )
        return rfq, rfq.lines.get()

    def test_aday_bul_skor_and_mask_supplier_sku(self):
        _rfq, line = self._katalog_disi_rfq()
        adaylar = rfq_eslestirme_servisi.adaylari_bul(
            actor=self.catalog, rfq_line=line, limit=10
        )
        self.assertTrue(adaylar)
        top = adaylar[0]
        self.assertEqual(top["varyant_id"], self.varyant_yuzuk.pk)
        self.assertGreater(top["skor"], 0)
        self.assertNotIn("tedarikci_sku", top)
        self.assertIn("sku", top)

    def test_buyer_cannot_oner(self):
        _rfq, line = self._katalog_disi_rfq()
        with self.assertRaises(PermissionDenied):
            rfq_eslestirme_servisi.oner(
                actor=self.buyer,
                rfq_line=line,
                varyant=self.varyant_yuzuk,
            )

    def test_oner_onay_binds_line(self):
        _rfq, line = self._katalog_disi_rfq()
        self.assertTrue(line.katalog_disi)
        row = rfq_eslestirme_servisi.oner(
            actor=self.catalog,
            rfq_line=line,
            varyant=self.varyant_yuzuk,
            kanit={"not": "manuel seçim"},
        )
        self.assertEqual(row.durum, RFQEslestirme.Durum.ONERILDI)
        approved = rfq_eslestirme_servisi.onayla(actor=self.catalog, eslestirme=row)
        self.assertEqual(approved.durum, RFQEslestirme.Durum.ONAYLANDI)
        line.refresh_from_db()
        self.assertEqual(line.varyant_id, self.varyant_yuzuk.pk)
        self.assertFalse(line.katalog_disi)

    def test_onay_rejects_sibling_oneriler(self):
        _rfq, line = self._katalog_disi_rfq()
        a = rfq_eslestirme_servisi.oner(
            actor=self.catalog, rfq_line=line, varyant=self.varyant_yuzuk
        )
        b = rfq_eslestirme_servisi.oner(
            actor=self.catalog, rfq_line=line, varyant=self.varyant
        )
        rfq_eslestirme_servisi.onayla(actor=self.catalog, eslestirme=a)
        b.refresh_from_db()
        self.assertEqual(b.durum, RFQEslestirme.Durum.REDDEDILDI)
        line.refresh_from_db()
        self.assertEqual(line.varyant_id, self.varyant_yuzuk.pk)

    def test_reddet_requires_reason(self):
        _rfq, line = self._katalog_disi_rfq()
        row = rfq_eslestirme_servisi.oner(
            actor=self.catalog, rfq_line=line, varyant=self.varyant_yuzuk
        )
        with self.assertRaises(ValidationError):
            rfq_eslestirme_servisi.reddet(
                actor=self.catalog, eslestirme=row, neden="  "
            )
        rfq_eslestirme_servisi.reddet(
            actor=self.catalog, eslestirme=row, neden="Uymuyor"
        )
        row.refresh_from_db()
        self.assertEqual(row.durum, RFQEslestirme.Durum.REDDEDILDI)
        self.assertEqual(row.kanit.get("red_nedeni"), "Uymuyor")

    def test_cannot_match_already_bound_or_closed(self):
        _rfq, line = self._katalog_disi_rfq()
        row = rfq_eslestirme_servisi.oner(
            actor=self.catalog, rfq_line=line, varyant=self.varyant_yuzuk
        )
        rfq_eslestirme_servisi.onayla(actor=self.catalog, eslestirme=row)
        line.refresh_from_db()
        with self.assertRaises(ValidationError):
            rfq_eslestirme_servisi.oner(
                actor=self.catalog, rfq_line=line, varyant=self.varyant
            )

        rfq2, line2 = self._katalog_disi_rfq()
        rfq2 = rfq_servisi.gonder(actor=self.buyer, rfq=rfq2)
        from firmalar.services.audit_servisi import domain_atomic
        from siparis.services.rfq_servisi import _set

        with domain_atomic():
            locked = RFQ.objects.select_for_update().get(pk=rfq2.pk)
            _set(locked, RFQ.Durum.KAPANDI)
        line2.refresh_from_db()
        with self.assertRaises(ValidationError):
            rfq_eslestirme_servisi.adaylari_bul(actor=self.catalog, rfq_line=line2)

    def test_supplier_denied(self):
        _rfq, line = self._katalog_disi_rfq()
        with self.assertRaises(PermissionDenied):
            rfq_eslestirme_servisi.adaylari_bul(
                actor=self.ted_user, rfq_line=line
            )
