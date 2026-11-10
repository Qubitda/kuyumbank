"""F11-012 — ATP = on_hand − reserved − blocked; tenant scope."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.models import StockBalance
from stok.services import atp_servisi, reservation_servisi

User = get_user_model()


class AtpF11012Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.ted_user)
        sync_user_role_groups(cls.buyer)
        cls.ops = User(
            username="atp_ops",
            firma=cls.platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.ops.set_password("x")
        cls.ops.save()
        sync_user_role_groups(cls.ops)

    def test_formul_and_supplier_scope(self):
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.on_hand, Decimal("100"))
        rows = atp_servisi.atp_satirlari(actor=self.ted_user)
        self.assertTrue(rows)
        r = next(x for x in rows if x["teklif_id"] == self.teklif.pk)
        self.assertEqual(Decimal(r["atp"]), Decimal("100"))
        self.assertEqual(r["formul"], "on_hand - reserved - blocked")
        self.assertIn("warehouse_id", r)

        reservation_servisi.olustur_rezervasyon(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("10"),
            alici_firma=self.alici,
            ttl_seconds=300,
        )
        bal.refresh_from_db()
        rows2 = atp_servisi.atp_satirlari(
            actor=self.ted_user, teklif_id=self.teklif.pk
        )
        self.assertEqual(Decimal(rows2[0]["atp"]), bal.available)
        self.assertEqual(bal.available, Decimal("90"))

    def test_buyer_sees_empty_blind(self):
        rows = atp_servisi.atp_satirlari(actor=self.buyer)
        self.assertEqual(rows, [])

    def test_platform_sees_all(self):
        rows = atp_servisi.atp_satirlari(actor=self.ops)
        self.assertTrue(any(r["teklif_id"] == self.teklif.pk for r in rows))

    def test_toplam_birim_ayri(self):
        t = atp_servisi.atp_toplam_varyant(
            actor=self.ted_user,
            varyant_id=self.varyant.pk,
            birim="ADET",
        )
        self.assertGreaterEqual(t, Decimal("0"))
