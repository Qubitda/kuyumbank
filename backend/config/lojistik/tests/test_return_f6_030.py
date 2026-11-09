"""F6-030/031 — Return/Dispute SM + stok IADE (ödeme iadesi yok)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from kalite.services import inspection_servisi, olcum_servisi
from lojistik.models import ReturnRequest, Shipment
from lojistik.services import return_servisi, shipment_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.models import StockBalance, StockMovement

User = get_user_model()


class ReturnF6030Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.qc = User(
            username="ret_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)

        cls.log = User(
            username="ret_log",
            firma=cls.platform,
            rol=roles.PLATFORM_LOGISTICS,
            is_staff=True,
        )
        cls.log.set_password("x")
        cls.log.save()
        sync_user_role_groups(cls.log)

    def _order(self, key):
        self._quote_and_cart(miktar=Decimal("2.500"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def _qc_pass(self, order):
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        insp = inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        line = order.lines.get()
        olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=line.miktar,
        )
        return inspection_servisi.pass_et(actor=self.qc, inspection=insp)

    def _delivered(self, key):
        order = self._order(key)
        self._qc_pass(order)
        ship = shipment_servisi.olustur(actor=self.log, order=order)
        ship = shipment_servisi.hazirla(actor=self.log, shipment=ship)
        ship = shipment_servisi.sevk_et(actor=self.log, shipment=ship)
        ship = shipment_servisi.teslim_et(actor=self.log, shipment=ship)
        return order, ship

    def test_happy_path_stock_iade(self):
        order, ship = self._delivered("ret-ok")
        line = order.lines.get()
        bal_before = StockBalance.objects.get(
            warehouse=line.stock_reservation.warehouse,
            teklif=line.stock_reservation.teklif,
            birim=line.birim,
        )
        on_hand_before = bal_before.on_hand

        req = return_servisi.olustur(
            actor=self.log,
            order=order,
            shipment=ship,
            sebep="Hasarlı ürün iadesi",
            line_specs=[{"order_line": line, "miktar": Decimal("1.000")}],
        )
        self.assertEqual(req.durum, ReturnRequest.Durum.TASLAK)
        req = return_servisi.incelemeye_al(actor=self.log, return_request=req)
        req = return_servisi.onayla(actor=self.log, return_request=req)
        self.assertEqual(req.durum, ReturnRequest.Durum.ONAYLANDI)
        self.assertTrue(req.stok_iade_yapildi)
        self.assertFalse(req.finans_mahsup_yapildi)

        bal_after = StockBalance.objects.get(pk=bal_before.pk)
        self.assertEqual(bal_after.on_hand, on_hand_before + Decimal("1.000"))
        self.assertTrue(
            StockMovement.objects.filter(
                tip=StockMovement.Tip.IADE,
                neden__startswith=f"return:{req.pk}:",
            ).exists()
        )
        self.assertTrue(
            AuditOlay.objects.filter(
                action="lojistik.return.onaylandi",
                entity_id=str(req.pk),
                success=True,
            ).exists()
        )

    def test_create_requires_teslim(self):
        order = self._order("ret-not-del")
        self._qc_pass(order)
        ship = shipment_servisi.olustur(actor=self.log, order=order)
        line = order.lines.get()
        with self.assertRaises(ValidationError):
            return_servisi.olustur(
                actor=self.log,
                order=order,
                shipment=ship,
                sebep="Henüz teslim yok",
                line_specs=[{"order_line": line, "miktar": line.miktar}],
            )
        self.assertEqual(ship.durum, Shipment.Durum.TASLAK)

    def test_buyer_denied(self):
        order, ship = self._delivered("ret-deny")
        line = order.lines.get()
        with self.assertRaises(PermissionDenied):
            return_servisi.olustur(
                actor=self.buyer,
                order=order,
                shipment=ship,
                sebep="Alıcı denemesi",
                line_specs=[{"order_line": line, "miktar": Decimal("0.5")}],
            )

    def test_reject_no_stock_move(self):
        order, ship = self._delivered("ret-rej")
        line = order.lines.get()
        req = return_servisi.olustur(
            actor=self.log,
            order=order,
            shipment=ship,
            sebep="Uyuşmazlık incelemesi",
            line_specs=[{"order_line": line, "miktar": Decimal("0.5")}],
        )
        return_servisi.incelemeye_al(actor=self.log, return_request=req)
        req = return_servisi.reddet(
            actor=self.log, return_request=req, reason="Politika dışı"
        )
        self.assertEqual(req.durum, ReturnRequest.Durum.REDDEDILDI)
        self.assertFalse(req.stok_iade_yapildi)
        self.assertFalse(
            StockMovement.objects.filter(neden__startswith=f"return:{req.pk}:").exists()
        )

    def test_illegal_transition(self):
        order, ship = self._delivered("ret-ill")
        line = order.lines.get()
        req = return_servisi.olustur(
            actor=self.log,
            order=order,
            shipment=ship,
            sebep="Geçiş testi için",
            line_specs=[{"order_line": line, "miktar": Decimal("0.1")}],
        )
        with self.assertRaises(ValidationError):
            return_servisi.onayla(actor=self.log, return_request=req)
