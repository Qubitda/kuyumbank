"""StockBalance ATP check + get_or_create_balance_locked yarış dayanıklılığı."""

from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from stok.birim_constants import StokBirimi
from stok.models import StockBalance
from stok.services import warehouse_servisi
from stok.services.ledger_servisi import (
    get_or_create_balance_locked,
    save_balance_fields,
)

from django.contrib.auth import get_user_model

User = get_user_model()


class _BalanceWorld(PriceQuoteFixtureMixin):
    @classmethod
    def _build_balance_world(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.ted_user = User(
            username="bal_ted",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.ted_user.set_password("x")
        cls.ted_user.save()
        sync_user_role_groups(cls.ted_user)
        cls.wh = warehouse_servisi.olustur_warehouse(
            actor=cls.ted_user,
            sahip_firma=cls.ted,
            kod="BAL1",
            ad="Balance depo",
        )


class StockBalanceAtpConstraintTests(_BalanceWorld, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_balance_world()

    def test_reserved_plus_blocked_cannot_exceed_on_hand(self):
        bal = get_or_create_balance_locked(
            warehouse=self.wh, teklif=self.teklif, birim=StokBirimi.GRAM
        )
        bal.on_hand = Decimal("10")
        bal.reserved = Decimal("8")
        bal.blocked = Decimal("3")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                save_balance_fields(
                    bal, update_fields=["on_hand", "reserved", "blocked"]
                )


class GetOrCreateBalanceRaceTests(_BalanceWorld, TransactionTestCase):
    def setUp(self):
        self._build_balance_world()

    def test_integrity_error_branch_reselects_locked_row(self):
        """İlk insert UniqueConstraint yarışında IntegrityError → yeniden kilitle."""
        with transaction.atomic():
            first = get_or_create_balance_locked(
                warehouse=self.wh, teklif=self.teklif, birim=StokBirimi.GRAM
            )

        class _QS:
            def __init__(self, row, *, empty_first=False):
                self._row = row
                self._empty_first = empty_first
                self._n = 0

            def filter(self, **kwargs):
                self._n += 1
                return self

            def first(self):
                if self._empty_first and self._n == 1:
                    return None
                return self._row

            def get(self, **kwargs):
                if "pk" in kwargs:
                    return StockBalance.objects.get(pk=kwargs["pk"])
                return self._row

        calls = {"n": 0}

        def _sfu(*args, **kwargs):
            calls["n"] += 1
            # 1) boş first → create dene; 2) IntegrityError sonrası get
            return _QS(first, empty_first=(calls["n"] == 1))

        with transaction.atomic():
            with patch(
                "stok.services.ledger_servisi.StockBalance.objects.select_for_update",
                side_effect=_sfu,
            ):
                with patch.object(
                    StockBalance, "save", side_effect=IntegrityError("dup")
                ):
                    again = get_or_create_balance_locked(
                        warehouse=self.wh,
                        teklif=self.teklif,
                        birim=StokBirimi.GRAM,
                    )
        self.assertEqual(again.pk, first.pk)
