"""F5-022 — Tedarikçi hak ediş iskeleti (QC PASS tetik)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import TedarikciHakEdis
from finans.services import fx_servisi, hak_edis_servisi
from kalite.services import inspection_servisi, olcum_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class HakEdisF5022Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.qc = User(
            username="he_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)
        sync_user_role_groups(cls.finance)

    def _order(self, key, miktar=Decimal("2.500")):
        self._quote_and_cart(miktar=miktar)
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def _pass_qc(self, order):
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

    def test_qc_pass_creates_hakedildi_vade_0(self):
        order = self._order("he-ok")
        insp = self._pass_qc(order)
        rows = list(TedarikciHakEdis.objects.filter(quality_inspection=insp))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.durum, TedarikciHakEdis.Durum.HAKEDILDI)
        self.assertEqual(row.gram, Decimal("2.5000"))
        self.assertIsNone(row.tutar)
        self.assertIsNotNone(row.hak_edis_tarihi)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="finans.hak_edis.created",
                entity_id=str(row.pk),
                success=True,
            ).exists()
        )

    def test_idempotent_on_repeat_call(self):
        order = self._order("he-idem")
        insp = self._pass_qc(order)
        again = hak_edis_servisi.kaydet_qc_pass(actor=self.qc, inspection=insp)
        self.assertEqual(TedarikciHakEdis.objects.filter(order=order).count(), 1)
        self.assertEqual(again[0].pk, TedarikciHakEdis.objects.get(order=order).pk)

    @override_settings(SUPPLIER_ACCRUAL_VADE_GUN=3)
    def test_vade_bekliyor_then_convert(self):
        order = self._order("he-vade")
        insp = self._pass_qc(order)
        row = TedarikciHakEdis.objects.get(quality_inspection=insp)
        self.assertEqual(row.durum, TedarikciHakEdis.Durum.BEKLEMEDE)
        self.assertIsNone(row.hak_edis_tarihi)
        converted = hak_edis_servisi.hakedise_cevir(
            actor=self.finance, hak_edis=row
        )
        self.assertEqual(converted.durum, TedarikciHakEdis.Durum.HAKEDILDI)

    def test_unpaid_supplier_has_updates_fx(self):
        before = fx_servisi.unpaid_supplier_has()
        order = self._order("he-fx", miktar=Decimal("1.250"))
        self._pass_qc(order)
        after = fx_servisi.unpaid_supplier_has()
        self.assertEqual(after, before + Decimal("1.2500"))

    def test_reject_non_pass_inspection(self):
        order = self._order("he-nopass")
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        with self.assertRaises(ValidationError):
            hak_edis_servisi.kaydet_qc_pass(actor=self.qc, inspection=insp)
