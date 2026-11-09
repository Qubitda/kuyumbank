"""F5-011 — CariHesap projeksiyon + tenant izolasyon."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import CariHesap, LedgerEntry
from finans.selectors import get_cari_for_actor, scope_cari_queryset
from finans.selectors.cari import CariNotFound
from finans.services import cari_servisi, ledger_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class CariHesapTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def test_ledger_updates_cari_bakiye(self):
        ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            karsi_firma=self.platform,
            tutar=Decimal("100.00"),
            para_birimi="TRY",
            yon=LedgerEntry.Yon.BORC,
            hareket_tipi=LedgerEntry.HareketTipi.SATIS,
            idempotency_key="cari-borc-1",
        )
        hesap = CariHesap.objects.get(
            firma=self.alici, karsi_firma=self.platform, para_birimi="TRY"
        )
        self.assertEqual(hesap.bakiye, Decimal("100.00"))

        ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            karsi_firma=self.platform,
            tutar=Decimal("40.00"),
            para_birimi="TRY",
            yon=LedgerEntry.Yon.ALACAK,
            hareket_tipi=LedgerEntry.HareketTipi.TAHSILAT,
            idempotency_key="cari-alacak-1",
        )
        hesap.refresh_from_db()
        self.assertEqual(hesap.bakiye, Decimal("60.00"))

    def test_kredi_limiti_asimi(self):
        hesap = cari_servisi.get_or_create_locked(
            firma=self.alici, para_birimi="TRY", karsi_firma=self.platform
        )
        cari_servisi.set_kredi_limiti(
            actor=self.finance, hesap=hesap, limit=Decimal("50.00")
        )
        with self.assertRaises(ValidationError):
            ledger_servisi.kaydet_hareket(
                actor=self.finance,
                firma=self.alici,
                karsi_firma=self.platform,
                tutar=Decimal("60.00"),
                para_birimi="TRY",
                yon=LedgerEntry.Yon.BORC,
                hareket_tipi=LedgerEntry.HareketTipi.SATIS,
                idempotency_key="cari-limit",
            )

    def test_buyer_sees_own_cari_only(self):
        ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            karsi_firma=self.platform,
            tutar=Decimal("10.00"),
            para_birimi="TRY",
            yon=LedgerEntry.Yon.BORC,
            hareket_tipi=LedgerEntry.HareketTipi.SATIS,
            idempotency_key="cari-vis",
        )
        own = scope_cari_queryset(self.buyer)
        self.assertEqual(own.count(), 1)
        row = own.get()
        cari_servisi.assert_can_view_cari(self.buyer, row)
        get_cari_for_actor(self.buyer, pk=row.pk)

        # Tedarikçi başka firmanın carisini görmez
        self.assertEqual(scope_cari_queryset(self.ted_user).count(), 0)
        with self.assertRaises(CariNotFound):
            get_cari_for_actor(self.ted_user, pk=row.pk)

    def test_direct_cari_update_forbidden(self):
        hesap = cari_servisi.get_or_create_locked(
            firma=self.alici, para_birimi="TRY", karsi_firma=self.platform
        )
        hesap.bakiye = Decimal("999")
        with self.assertRaises(ValidationError):
            hesap.save()
