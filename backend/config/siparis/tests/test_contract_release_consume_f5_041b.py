"""F5-041b — Contract release sipariş tüketimi / iptal iadesi."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import ContractReleaseConsumption, ContractReleasePlan, FiyatSozlesmesi
from fiyatlama.services import release_servisi, sozlesme_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class ContractReleaseConsumeF5041bTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        # manage_sozlesme: finance kullanıcısı quote dünyasında var
        cls.finance.rol = roles.PLATFORM_FINANCE
        cls.finance.save(update_fields=["rol"])
        sync_user_role_groups(cls.finance)

        bas, bit = date.today(), date.today() + timedelta(days=90)
        soz = FiyatSozlesmesi.objects.create(
            firma=cls.alici,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
            durum=FiyatSozlesmesi.Durum.TASLAK,
            olusturan_kullanici=cls.finance,
            versiyon=1,
        )
        cls.soz = sozlesme_servisi.aktif_yap(soz, cls.finance)

    def _aktif_plan(self, *, taahhut="50", release="20"):
        # Checkout fixture METAL_BAZLI → stok/sepet birimi GRAM
        plan = release_servisi.olustur_plan(
            actor=self.finance,
            sozlesme=self.soz,
            varyant=self.varyant,
            birim=ContractReleasePlan.Birim.GRAM,
            toplam_taahhut=Decimal(taahhut),
        )
        plan = release_servisi.aktif_et(actor=self.finance, plan=plan)
        release_servisi.serbest_birak(
            actor=self.finance,
            plan=plan,
            miktar=Decimal(release),
            donem_baslangic=date.today(),
            donem_bitis=date.today() + timedelta(days=30),
        )
        return plan

    def _order(self, *, key: str, miktar: Decimal):
        self._quote_and_cart(miktar=miktar)
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        return order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )

    def test_order_consumes_release(self):
        plan = self._aktif_plan(release="10")
        self.assertEqual(release_servisi.kullanilabilir(plan), Decimal("10"))

        order = self._order(key="cr-consume-ok", miktar=Decimal("2"))
        line = order.lines.get()
        plan.refresh_from_db()

        self.assertEqual(release_servisi.tuketilen(plan), Decimal("2"))
        self.assertEqual(release_servisi.kullanilabilir(plan), Decimal("8"))
        self.assertTrue(
            ContractReleaseConsumption.objects.filter(
                plan=plan,
                order_line=line,
                yon=ContractReleaseConsumption.Yon.TUKETIM,
                miktar=Decimal("2"),
            ).exists()
        )
        self.assertTrue(
            AuditOlay.objects.filter(
                action="fiyatlama.release.consumed",
                success=True,
            ).exists()
        )

    def test_insufficient_release_blocks_order(self):
        self._aktif_plan(release="1")
        self._quote_and_cart(miktar=Decimal("2"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="cr-consume-fail"
        )
        with self.assertRaises(ValidationError):
            order_servisi.olustur_from_checkout(
                actor=self.buyer, checkout_attempt=co.attempt
            )

    def test_cancel_reverses_consumption(self):
        plan = self._aktif_plan(release="10")
        order = self._order(key="cr-consume-cancel", miktar=Decimal("3"))
        self.assertEqual(release_servisi.kullanilabilir(plan), Decimal("7"))

        order_servisi.iptal_siparis(actor=self.buyer, order=order)
        plan.refresh_from_db()
        self.assertEqual(release_servisi.tuketilen(plan), Decimal("0"))
        self.assertEqual(release_servisi.kullanilabilir(plan), Decimal("10"))
        self.assertTrue(
            ContractReleaseConsumption.objects.filter(
                plan=plan,
                yon=ContractReleaseConsumption.Yon.IADE,
                miktar=Decimal("3"),
            ).exists()
        )

    def test_no_plan_order_ok(self):
        """AKTIF plan yoksa tüketim kapısı yok."""
        order = self._order(key="cr-no-plan", miktar=Decimal("2"))
        self.assertEqual(order.lines.count(), 1)
        self.assertFalse(
            ContractReleaseConsumption.objects.filter(
                order_line__order=order
            ).exists()
        )
