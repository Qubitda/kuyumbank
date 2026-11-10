"""F11-020 — ATP eşiği → öneri; checkout yok; audit."""

from decimal import Decimal

from django.test import TestCase

from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin
from stok.services import replenishment_servisi


class ReplenishmentF11020Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.ted_user)

    def test_oneri_when_below_threshold(self):
        # on_hand=100 → eşik 200 → öneri 100 (hedef=200)
        rows = replenishment_servisi.oneri_uret(
            actor=self.ted_user,
            esik_atp=Decimal("200"),
            hedef_atp=Decimal("200"),
        )
        self.assertTrue(rows)
        self.assertEqual(Decimal(rows[0]["onerilen_miktar"]), Decimal("100"))
        self.assertFalse(rows[0]["otomatik_checkout"])
        self.assertTrue(
            AuditOlay.objects.filter(
                action="stok.replenishment.oneri", success=True
            ).exists()
        )

    def test_no_oneri_when_above(self):
        rows = replenishment_servisi.oneri_uret(
            actor=self.ted_user,
            esik_atp=Decimal("10"),
            hedef_atp=Decimal("10"),
        )
        self.assertEqual(rows, [])
