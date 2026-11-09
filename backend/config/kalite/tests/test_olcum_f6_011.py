"""F6-011 — gram ölçüm + tolerans motoru + otomatik FAIL / override."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import SimpleTestCase, TestCase, override_settings

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from kalite.models import QualityInspection, QualityMeasurement
from kalite.services import inspection_servisi, olcum_servisi, tolerans_motoru
from siparis.birim_constants import SepetBirimi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class ToleransMotoruUnitTests(SimpleTestCase):
    def test_bagil_pct_icin_uygun(self):
        # 10g ±0.5% = 0.05g izin
        s = tolerans_motoru.degerlendir(
            beklenen=Decimal("10"),
            olculen=Decimal("10.04"),
            birim=SepetBirimi.GRAM,
            tolerans_pct=Decimal("0.50"),
            tolerans_abs=Decimal("0"),
        )
        self.assertTrue(s.uygun)
        self.assertEqual(s.izin_verilen, Decimal("0.05"))

    def test_bagil_pct_sapma(self):
        s = tolerans_motoru.degerlendir(
            beklenen=Decimal("10"),
            olculen=Decimal("10.06"),
            birim=SepetBirimi.GRAM,
            tolerans_pct=Decimal("0.50"),
            tolerans_abs=Decimal("0"),
        )
        self.assertFalse(s.uygun)

    def test_abs_taban_max(self):
        # bağıl 0.05; abs 0.10 → izin 0.10
        s = tolerans_motoru.degerlendir(
            beklenen=Decimal("10"),
            olculen=Decimal("10.09"),
            birim=SepetBirimi.GRAM,
            tolerans_pct=Decimal("0.50"),
            tolerans_abs=Decimal("0.10"),
        )
        self.assertTrue(s.uygun)
        self.assertEqual(s.izin_verilen, Decimal("0.10"))

    def test_adet_tam_esitlik(self):
        ok = tolerans_motoru.degerlendir(
            beklenen=Decimal("3"),
            olculen=Decimal("3"),
            birim=SepetBirimi.ADET,
            tolerans_pct=Decimal("5"),
            tolerans_abs=Decimal("1"),
        )
        bad = tolerans_motoru.degerlendir(
            beklenen=Decimal("3"),
            olculen=Decimal("4"),
            birim=SepetBirimi.ADET,
            tolerans_pct=Decimal("5"),
            tolerans_abs=Decimal("1"),
        )
        self.assertTrue(ok.uygun)
        self.assertEqual(ok.izin_verilen, Decimal("0"))
        self.assertFalse(bad.uygun)


@override_settings(
    QC_GRAM_TOLERANCE_PCT=Decimal("0.50"),
    QC_GRAM_TOLERANCE_ABS=Decimal("0"),
)
class OlcumF6011Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.qc = User(
            username="qc_olcum",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)

    def _order(self, key="olcum-ord"):
        self._quote_and_cart(miktar=Decimal("2.500"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def _insp_olcumde(self, key):
        order = self._order(key)
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        insp = inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        return order, insp, order.lines.get()

    def test_uygun_olcum_then_pass(self):
        order, insp, line = self._insp_olcumde("olcum-ok")
        self.assertEqual(line.birim, "GRAM")
        m = olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=line.miktar,
        )
        self.assertEqual(m.sonuc, QualityMeasurement.Sonuc.UYGUN)
        self.assertFalse(m.override_uygulandi)
        self.assertIsNotNone(m.quote_gram)
        insp.refresh_from_db()
        self.assertEqual(insp.durum, QualityInspection.Durum.OLCUMDE)

        insp = inspection_servisi.pass_et(actor=self.qc, inspection=insp)
        self.assertEqual(insp.durum, QualityInspection.Durum.PASS)
        self.assertFalse(inspection_servisi.order_shipment_blocked(order))
        self.assertTrue(
            AuditOlay.objects.filter(
                action="kalite.qc.olcum", entity_id=str(m.pk), success=True
            ).exists()
        )

    def test_sapma_otomatik_fail(self):
        _order, insp, line = self._insp_olcumde("olcum-fail")
        # 2.500 × 0.5% = 0.0125; 2.600 sapma=0.1 → FAIL
        m = olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=Decimal("2.600"),
        )
        self.assertEqual(m.sonuc, QualityMeasurement.Sonuc.SAPMA)
        insp.refresh_from_db()
        self.assertEqual(insp.durum, QualityInspection.Durum.FAIL)
        self.assertTrue(insp.shipment_blok)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="kalite.qc.fail",
                entity_id=str(insp.pk),
                success=True,
            ).exists()
        )

    def test_override_sapma_kalir_olcumde(self):
        _order, insp, line = self._insp_olcumde("olcum-ov")
        m = olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=Decimal("2.600"),
            override_gerekce="Musteri onayi ile kabul edildi",
        )
        self.assertEqual(m.sonuc, QualityMeasurement.Sonuc.SAPMA)
        self.assertTrue(m.override_uygulandi)
        insp.refresh_from_db()
        self.assertEqual(insp.durum, QualityInspection.Durum.OLCUMDE)
        insp = inspection_servisi.pass_et(actor=self.qc, inspection=insp)
        self.assertEqual(insp.durum, QualityInspection.Durum.PASS)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="kalite.qc.olcum_override",
                entity_id=str(m.pk),
                success=True,
            ).exists()
        )

    def test_override_gerekce_kisa_red(self):
        _order, insp, line = self._insp_olcumde("olcum-short")
        with self.assertRaises(ValidationError):
            olcum_servisi.kaydet_olcum(
                actor=self.qc,
                inspection=insp,
                order_line=line,
                olculen=Decimal("2.600"),
                override_gerekce="kisa",
            )
        insp.refresh_from_db()
        self.assertEqual(insp.durum, QualityInspection.Durum.OLCUMDE)
        self.assertEqual(QualityMeasurement.objects.count(), 0)

    def test_pass_olcum_yok_red(self):
        _order, insp, _line = self._insp_olcumde("olcum-nopass")
        with self.assertRaises(ValidationError):
            inspection_servisi.pass_et(actor=self.qc, inspection=insp)

    def test_buyer_olcum_denied(self):
        _order, insp, line = self._insp_olcumde("olcum-deny")
        with self.assertRaises(PermissionDenied):
            olcum_servisi.kaydet_olcum(
                actor=self.buyer,
                inspection=insp,
                order_line=line,
                olculen=line.miktar,
            )
        self.assertTrue(
            AuditOlay.objects.filter(
                action="kalite.qc.olcum_denied",
                success=False,
                reason="yetki_yok",
            ).exists()
        )

    def test_measurement_immutable(self):
        _order, insp, line = self._insp_olcumde("olcum-imm")
        m = olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=line.miktar,
        )
        with self.assertRaises(ValidationError):
            m.olculen = Decimal("9")
            m.save()
