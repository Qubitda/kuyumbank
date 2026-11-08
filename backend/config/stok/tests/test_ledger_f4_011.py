"""F4-011/012/013 — Movement + Balance + düzeltme."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import TedarikciTeklif
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from stok.models import StockBalance, StockMovement
from stok.birim_constants import StokBirimi
from stok.services import ledger_servisi, warehouse_servisi

from django.contrib.auth import get_user_model

User = get_user_model()


class LedgerSliceTests(PriceQuoteFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.admin = User(
            username="led_admin",
            firma=cls.platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.admin.set_password("x")
        cls.admin.save()
        sync_user_role_groups(cls.admin)

        cls.ted_user = User(
            username="led_ted",
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
            kod="LED1",
            ad="Ledger depo",
        )

    def test_giris_creates_balance_in_teklif_birim(self):
        self.assertEqual(self.teklif.fiyat_modeli, TedarikciTeklif.FiyatModeli.METAL_BAZLI)
        mv = ledger_servisi.kaydet_hareket(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=self.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("10.5"),
        )
        self.assertEqual(mv.birim, StokBirimi.GRAM)
        bal = StockBalance.objects.get(
            warehouse=self.wh, teklif=self.teklif, birim=StokBirimi.GRAM
        )
        self.assertEqual(bal.on_hand, Decimal("10.5"))
        self.assertEqual(bal.available, Decimal("10.5"))

    def test_cikis_and_yetersiz_stok(self):
        ledger_servisi.kaydet_hareket(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=self.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("5"),
        )
        ledger_servisi.kaydet_hareket(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=self.teklif,
            tip=StockMovement.Tip.CIKIS,
            miktar=Decimal("2"),
        )
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.on_hand, Decimal("3"))
        with self.assertRaises(ValidationError):
            ledger_servisi.kaydet_hareket(
                actor=self.ted_user,
                warehouse=self.wh,
                teklif=self.teklif,
                tip=StockMovement.Tip.CIKIS,
                miktar=Decimal("9"),
            )

    def test_duzeltme_requires_neden_and_perm(self):
        with self.assertRaises(ValidationError):
            ledger_servisi.duzeltme(
                actor=self.ted_user,
                warehouse=self.wh,
                teklif=self.teklif,
                miktar=Decimal("1"),
                neden="x",
            )
        mv = ledger_servisi.duzeltme(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=self.teklif,
            miktar=Decimal("4"),
            neden="Sayım farkı",
        )
        self.assertEqual(mv.tip, StockMovement.Tip.DUZELTME)
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        self.assertEqual(bal.on_hand, Decimal("4"))

    def test_movement_immutable(self):
        mv = ledger_servisi.kaydet_hareket(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=self.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("1"),
        )
        mv.miktar = Decimal("99")
        with self.assertRaises(ValidationError):
            mv.save()
        with self.assertRaises(ValidationError):
            mv.delete()

    def test_balance_direct_update_blocked(self):
        ledger_servisi.kaydet_hareket(
            actor=self.ted_user,
            warehouse=self.wh,
            teklif=self.teklif,
            tip=StockMovement.Tip.GIRIS,
            miktar=Decimal("1"),
        )
        bal = StockBalance.objects.get(warehouse=self.wh, teklif=self.teklif)
        bal.on_hand = Decimal("100")
        with self.assertRaises(ValidationError):
            bal.save()

    def test_foreign_teklif_on_supplier_warehouse_rejected(self):
        other = Firma.objects.create(
            ad="LEDTED2", firma_kodu="LEDTED2", tedarikci_mi=True
        )
        # teklif belongs to cls.ted; create warehouse for other supplier via admin perms
        other_user = User(
            username="led_ted2",
            firma=other,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        other_user.set_password("x")
        other_user.save()
        sync_user_role_groups(other_user)
        wh2 = warehouse_servisi.olustur_warehouse(
            actor=other_user,
            sahip_firma=other,
            kod="O2",
            ad="Başka depo",
        )
        with self.assertRaises(ValidationError):
            ledger_servisi.kaydet_hareket(
                actor=other_user,
                warehouse=wh2,
                teklif=self.teklif,
                tip=StockMovement.Tip.GIRIS,
                miktar=Decimal("1"),
            )
