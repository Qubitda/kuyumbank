"""F5-023 — İade mahsup; ödeme iadesi yasak (U-004)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import LedgerEntry
from finans.services import mahsup_servisi
from kalite.services import inspection_servisi, olcum_servisi
from lojistik.services import return_servisi, shipment_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class MahsupF5023Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.qc = User(
            username="mah_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)

        cls.log = User(
            username="mah_log",
            firma=cls.platform,
            rol=roles.PLATFORM_LOGISTICS,
            is_staff=True,
        )
        cls.log.set_password("x")
        cls.log.save()
        sync_user_role_groups(cls.log)
        sync_user_role_groups(cls.finance)

    def _delivered(self, key):
        self._quote_and_cart(miktar=Decimal("2.000"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        insp = inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        line = order.lines.get()
        olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=line.miktar,
        )
        inspection_servisi.pass_et(actor=self.qc, inspection=insp)
        ship = shipment_servisi.olustur(actor=self.log, order=order)
        ship = shipment_servisi.hazirla(actor=self.log, shipment=ship)
        ship = shipment_servisi.sevk_et(actor=self.log, shipment=ship)
        ship = shipment_servisi.teslim_et(actor=self.log, shipment=ship)
        return order, ship, line

    def test_odeme_iadesi_blocked(self):
        order, ship, line = self._delivered("mah-ref")
        req = return_servisi.olustur(
            actor=self.log,
            order=order,
            shipment=ship,
            sebep="İade talebi mahsup",
            line_specs=[{"order_line": line, "miktar": Decimal("1.000")}],
        )
        with self.assertRaises(ValidationError):
            mahsup_servisi.odeme_iadesi_yap(actor=self.finance, return_request=req)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="finans.refund.denied",
                success=False,
                reason="odeme_iadesi_yok_u004",
            ).exists()
        )

    def test_onay_then_mahsup_posts_ledger(self):
        order, ship, line = self._delivered("mah-ok")
        req = return_servisi.olustur(
            actor=self.log,
            order=order,
            shipment=ship,
            sebep="Kısmi iade mahsup",
            line_specs=[{"order_line": line, "miktar": Decimal("1.000")}],
        )
        return_servisi.incelemeye_al(actor=self.log, return_request=req)
        req = return_servisi.onayla(actor=self.log, return_request=req)
        self.assertTrue(req.stok_iade_yapildi)
        self.assertFalse(req.finans_mahsup_yapildi)
        entry = mahsup_servisi.iade_mahsup(
            actor=self.finance, return_request=req
        )
        req.refresh_from_db()
        self.assertTrue(req.finans_mahsup_yapildi)
        self.assertEqual(entry.yon, LedgerEntry.Yon.ALACAK)
        self.assertEqual(entry.firma_id, order.alici_firma_id)
        expected = (line.snapshot_satir_tutari_vergisiz * Decimal("0.5")).quantize(
            Decimal("0.01")
        )
        self.assertEqual(entry.tutar, expected)

    def test_mahsup_idempotent(self):
        order, ship, line = self._delivered("mah-idem")
        req = return_servisi.olustur(
            actor=self.log,
            order=order,
            shipment=ship,
            sebep="Mahsup idempotent",
            line_specs=[{"order_line": line, "miktar": line.miktar}],
        )
        return_servisi.incelemeye_al(actor=self.log, return_request=req)
        req = return_servisi.onayla(actor=self.log, return_request=req)
        first = mahsup_servisi.iade_mahsup(actor=self.finance, return_request=req)
        again = mahsup_servisi.iade_mahsup(actor=self.finance, return_request=req)
        self.assertEqual(
            LedgerEntry.objects.filter(
                referans_tip="ReturnRequest", referans_id=str(req.pk)
            ).count(),
            1,
        )
        self.assertEqual(again.pk, first.pk)
