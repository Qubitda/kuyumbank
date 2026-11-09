"""F5-010 — LedgerEntry append-only + contra + yetki."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.test import TestCase, TransactionTestCase

from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from finans.models import LedgerEntry
from finans.services import ledger_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class LedgerEntryImmutabilityTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def _post(self, *, key="le-1", yon=LedgerEntry.Yon.BORC):
        return ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            karsi_firma=self.platform,
            tutar=Decimal("100.00"),
            para_birimi="try",
            yon=yon,
            hareket_tipi=LedgerEntry.HareketTipi.SATIS,
            idempotency_key=key,
            referans_tip="Order",
            referans_id="1",
        )

    def test_post_ok_and_audit(self):
        entry = self._post()
        self.assertEqual(entry.tutar, Decimal("100.00"))
        self.assertEqual(entry.para_birimi, "TRY")
        self.assertTrue(
            AuditOlay.objects.filter(
                action="finans.ledger.post", entity_id=str(entry.pk), success=True
            ).exists()
        )

    def test_idempotent(self):
        a = self._post(key="idem-le")
        b = self._post(key="idem-le")
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(LedgerEntry.objects.filter(idempotency_key="idem-le").count(), 1)

    def test_buyer_denied(self):
        with self.assertRaises(PermissionDenied):
            ledger_servisi.kaydet_hareket(
                actor=self.buyer,
                firma=self.alici,
                tutar=Decimal("10.00"),
                para_birimi="TRY",
                yon=LedgerEntry.Yon.BORC,
                hareket_tipi=LedgerEntry.HareketTipi.SATIS,
                idempotency_key="buyer-deny",
            )

    def test_instance_update_forbidden(self):
        entry = self._post(key="upd")
        entry.aciklama = "mutated"
        with self.assertRaises(ValidationError):
            entry.save()

    def test_instance_delete_forbidden(self):
        entry = self._post(key="del")
        with self.assertRaises(ValidationError):
            entry.delete()
        self.assertTrue(LedgerEntry.objects.filter(pk=entry.pk).exists())

    def test_queryset_update_delete_forbidden(self):
        entry = self._post(key="qs")
        with self.assertRaises(ValidationError):
            LedgerEntry.objects.filter(pk=entry.pk).update(aciklama="x")
        with self.assertRaises(ValidationError):
            LedgerEntry.objects.filter(pk=entry.pk).delete()

    def test_contra_flips_yon(self):
        entry = self._post(key="c-src", yon=LedgerEntry.Yon.BORC)
        contra = ledger_servisi.contra_hareket(
            actor=self.finance, entry=entry, idempotency_key="c-dst"
        )
        self.assertEqual(contra.hareket_tipi, LedgerEntry.HareketTipi.CONTRA)
        self.assertEqual(contra.yon, LedgerEntry.Yon.ALACAK)
        self.assertEqual(contra.contra_of_id, entry.pk)
        again = ledger_servisi.contra_hareket(
            actor=self.finance, entry=entry, idempotency_key="c-dst-2"
        )
        self.assertEqual(again.pk, contra.pk)

    def test_zero_tutar_rejected(self):
        with self.assertRaises(ValidationError):
            ledger_servisi.kaydet_hareket(
                actor=self.finance,
                firma=self.alici,
                tutar=Decimal("0"),
                para_birimi="TRY",
                yon=LedgerEntry.Yon.BORC,
                hareket_tipi=LedgerEntry.HareketTipi.DUZELTME,
                idempotency_key="zero",
            )


class LedgerEntryDbGuardTests(CheckoutFixtureMixin, TransactionTestCase):
    """PG trigger — UPDATE/DELETE reddi."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)

    def test_db_update_blocked(self):
        entry = ledger_servisi.kaydet_hareket(
            actor=self.finance,
            firma=self.alici,
            tutar=Decimal("50.00"),
            para_birimi="TRY",
            yon=LedgerEntry.Yon.BORC,
            hareket_tipi=LedgerEntry.HareketTipi.SATIS,
            idempotency_key="db-upd",
        )
        with self.assertRaises(Exception):
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE finans_ledgerentry SET aciklama=%s WHERE id=%s",
                    ["hack", entry.pk],
                )
                transaction.commit()
