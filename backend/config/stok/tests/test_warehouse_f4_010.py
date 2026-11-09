"""Faz 4 dilim 1 — Warehouse + birim + dual-stock envanter (F4-002 / F4-010)."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from firmalar import roles
from firmalar.models import AuditOlay, Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import TedarikciTeklif
from stok.models import Warehouse
from stok.selectors.tenant import scope_warehouse_queryset
from stok.services import birim, warehouse_servisi

User = get_user_model()


class WarehouseSliceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.platform = ensure_platform_firma()
        cls.ted = Firma.objects.create(
            ad="STTED", firma_kodu="STTED", tedarikci_mi=True
        )
        cls.ted2 = Firma.objects.create(
            ad="STTED2", firma_kodu="STTED2", tedarikci_mi=True
        )
        cls.alici = Firma.objects.create(
            ad="STAL", firma_kodu="STAL", alici_mi=True
        )

        cls.admin = User(
            username="st_padmin",
            firma=cls.platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.admin.set_password("x")
        cls.admin.save()
        sync_user_role_groups(cls.admin)

        cls.ted_sahip = User(
            username="st_ted",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.ted_sahip.set_password("x")
        cls.ted_sahip.save()
        sync_user_role_groups(cls.ted_sahip)

        cls.ted2_user = User(
            username="st_ted2",
            firma=cls.ted2,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.ted2_user.set_password("x")
        cls.ted2_user.save()
        sync_user_role_groups(cls.ted2_user)

        cls.buyer = User(
            username="st_buyer",
            firma=cls.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)

    def test_platform_creates_platform_warehouse(self):
        wh = warehouse_servisi.olustur_warehouse(
            actor=self.admin,
            sahip_firma=self.platform,
            kod="PL-MAIN",
            ad="Platform ana depo",
        )
        self.assertEqual(wh.sahip_tipi, Warehouse.SahipTipi.PLATFORM)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="warehouse.create",
                entity_id=str(wh.pk),
                success=True,
                actor=self.admin,
            ).exists()
        )

    def test_supplier_creates_own_warehouse(self):
        wh = warehouse_servisi.olustur_warehouse(
            actor=self.ted_sahip,
            sahip_firma=self.ted,
            kod="T1",
            ad="Tedarikçi depo",
        )
        self.assertEqual(wh.sahip_tipi, Warehouse.SahipTipi.TEDARIKCI)
        self.assertEqual(wh.sahip_firma_id, self.ted.pk)

    def test_supplier_cannot_create_for_other_firma(self):
        with self.assertRaises(PermissionDenied):
            warehouse_servisi.olustur_warehouse(
                actor=self.ted_sahip,
                sahip_firma=self.ted2,
                kod="X",
                ad="Yabancı",
            )
        self.assertTrue(
            AuditOlay.objects.filter(
                action="warehouse.create",
                success=False,
                actor=self.ted_sahip,
            ).exists()
        )

    def test_buyer_firma_rejected_as_owner(self):
        with self.assertRaises(ValidationError):
            warehouse_servisi.olustur_warehouse(
                actor=self.admin,
                sahip_firma=self.alici,
                kod="B1",
                ad="Alıcı depo olamaz",
            )

    def test_tenant_selector_isolation(self):
        mine = warehouse_servisi.olustur_warehouse(
            actor=self.ted_sahip,
            sahip_firma=self.ted,
            kod="MINE",
            ad="Benim",
        )
        warehouse_servisi.olustur_warehouse(
            actor=self.ted2_user,
            sahip_firma=self.ted2,
            kod="OTHER",
            ad="Diğer",
        )
        qs_ted = scope_warehouse_queryset(Warehouse.objects.all(), self.ted_sahip)
        qs_buyer = scope_warehouse_queryset(Warehouse.objects.all(), self.buyer)
        qs_admin = scope_warehouse_queryset(Warehouse.objects.all(), self.admin)
        self.assertEqual(list(qs_ted), [mine])
        self.assertEqual(list(qs_buyer), [])
        self.assertEqual(qs_admin.count(), 2)

    def test_birim_from_fiyat_modeli_mapping(self):
        self.assertEqual(
            birim.birim_from_fiyat_modeli(
                TedarikciTeklif.FiyatModeli.SABIT_PARCA
            ),
            birim.StokBirimi.ADET,
        )
        self.assertEqual(
            birim.birim_from_fiyat_modeli(
                TedarikciTeklif.FiyatModeli.GRAM_BIRIM
            ),
            birim.StokBirimi.GRAM,
        )
        self.assertEqual(
            birim.birim_from_fiyat_modeli(
                TedarikciTeklif.FiyatModeli.METAL_BAZLI
            ),
            birim.StokBirimi.GRAM,
        )

    def test_birim_unknown_model_fails(self):
        with self.assertRaises(ValidationError):
            birim.birim_from_fiyat_modeli("BILINMEYEN")

    def test_farkli_birim_karistirilamaz(self):
        with self.assertRaises(ValidationError):
            birim.assert_ayni_birim(
                birim.StokBirimi.ADET,
                birim.StokBirimi.GRAM,
                context="aynı depo",
            )

    def test_legacy_stock_columns_removed(self):
        from fiyatlama.models import TedarikciTeklif
        from urunler.models import Varyant

        varyant_fields = {f.name for f in Varyant._meta.get_fields()}
        teklif_fields = {f.name for f in TedarikciTeklif._meta.get_fields()}
        self.assertNotIn("stok", varyant_fields)
        self.assertNotIn("stok_adet", teklif_fields)
