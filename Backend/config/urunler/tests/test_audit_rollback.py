"""Faz 1.1 P0 — reddedilen deneme audit'i ürün atomic'inden bağımsız kalır."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.test import TransactionTestCase

from firmalar import roles
from firmalar.models import AuditOlay, Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal
from urunler.models import Kategori, Urun, UrunKanal, Varyant
from urunler.services import onay_servisi as servisler

User = get_user_model()


class OnayAuditRollbackTests(TransactionTestCase):
    """TransactionTestCase: assertRaises ürün atomic'i dışında; audit commit kalır."""

    def setUp(self):
        seed_role_permissions()
        altin = KiymetliMetal.objects.create(kod="ALTIN", ad="Altın", gram_bazli=True)
        self.ayar14 = AyarMilyem.objects.create(
            metal=altin, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        grup = FiyatGrubu.objects.create(kod="YUZUK_ALYANS", ad="Yüzük / Alyans")
        self.kategori = Kategori.objects.create(kod="YUZUK", ad="Yüzük", fiyat_grubu=grup)
        self.tedarikci = Firma.objects.create(
            ad="Ted A", firma_kodu="AUD_A", tedarikci_mi=True
        )
        self.tedarikci_b = Firma.objects.create(
            ad="Ted B", firma_kodu="AUD_B", tedarikci_mi=True
        )
        platform = ensure_platform_firma()

        self.owner = User(
            username="aud_owner",
            firma=self.tedarikci,
            rol=roles.TEDARIKCI_SAHIP,
        )
        self.owner.set_password("x")
        self.owner.save()
        sync_user_role_groups(self.owner)

        self.other = User(
            username="aud_other",
            firma=self.tedarikci_b,
            rol=roles.TEDARIKCI_SAHIP,
        )
        self.other.set_password("x")
        self.other.save()
        sync_user_role_groups(self.other)

        self.depo = User(
            username="aud_depo",
            firma=self.tedarikci,
            rol=roles.TEDARIKCI_DEPO,
        )
        self.depo.set_password("x")
        self.depo.save()
        sync_user_role_groups(self.depo)

        self.platform = User(
            username="aud_plat",
            firma=platform,
            rol=roles.PLATFORM_CATALOG,
            is_staff=True,
        )
        self.platform.set_password("x")
        self.platform.save()
        sync_user_role_groups(self.platform)

        from tanimlar.models import SatisKanali

        self.kanal = SatisKanali.objects.create(kod="AUD_K", ad="Audit kanal")

    def _urun(self, *, olusturan_firma=None, with_varyant=True):
        u = Urun.objects.create(
            olusturan_firma=olusturan_firma or self.tedarikci,
            ad="Audit ürün",
            kategori=self.kategori,
            ayar=self.ayar14,
        )
        if with_varyant:
            Varyant.objects.create(urun=u, gram=Decimal("2.5"))
        return u

    def test_failed_ownership_audit_persists(self):
        u = self._urun()
        before = u.onay_durumu
        with self.assertRaises(PermissionDenied):
            servisler.onaya_gonder(u, self.other)
        u.refresh_from_db()
        self.assertEqual(u.onay_durumu, before)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="urun.onaya_gonder",
                success=False,
                entity_id=str(u.pk),
                reason="sahiplik_uyusmazligi",
            ).exists()
        )

    def test_failed_permission_audit_persists(self):
        u = self._urun()
        with self.assertRaises(PermissionDenied):
            servisler.onaya_gonder(u, self.depo)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="urun.onaya_gonder",
                success=False,
                reason="yetki_yok",
            ).exists()
        )

    def test_failed_validation_audit_persists_product_unchanged(self):
        u = self._urun(with_varyant=False)
        with self.assertRaises(ValidationError):
            servisler.onaya_gonder(u, self.owner)
        u.refresh_from_db()
        self.assertEqual(u.onay_durumu, "taslak")
        self.assertTrue(
            AuditOlay.objects.filter(
                action="urun.onaya_gonder",
                success=False,
                reason="hazir_degil",
            ).exists()
        )

    def test_failed_onayla_audit_persists(self):
        u = self._urun()
        with self.assertRaises(PermissionDenied):
            servisler.onayla(u, self.owner)
        u.refresh_from_db()
        self.assertEqual(u.onay_durumu, "taslak")
        self.assertTrue(
            AuditOlay.objects.filter(action="urun.onayla", success=False).exists()
        )

    def test_failed_reddet_audit_persists(self):
        u = self._urun()
        with self.assertRaises(ValidationError):
            servisler.reddet(u, self.platform, "  ")
        self.assertTrue(
            AuditOlay.objects.filter(
                action="urun.reddet", success=False, reason="neden_yok"
            ).exists()
        )

    def test_failed_yayina_al_audit_persists(self):
        u = self._urun()
        with self.assertRaises(ValidationError):
            servisler.yayina_al(u, self.platform)
        self.assertTrue(
            AuditOlay.objects.filter(action="urun.yayina_al", success=False).exists()
        )

    def test_failed_pasife_al_audit_persists(self):
        u = self._urun()
        with self.assertRaises(PermissionDenied):
            servisler.pasife_al(u, self.owner)
        self.assertTrue(
            AuditOlay.objects.filter(action="urun.pasife_al", success=False).exists()
        )

    def test_success_onaya_gonder_single_audit(self):
        u = self._urun()
        before = AuditOlay.objects.filter(
            action="urun.onaya_gonder", success=True, entity_id=str(u.pk)
        ).count()
        servisler.onaya_gonder(u, self.owner)
        u.refresh_from_db()
        self.assertEqual(u.onay_durumu, "onay_bekliyor")
        after = AuditOlay.objects.filter(
            action="urun.onaya_gonder", success=True, entity_id=str(u.pk)
        ).count()
        self.assertEqual(after, before + 1)

    def test_success_full_transition_audits(self):
        u = self._urun()
        UrunKanal.objects.create(urun=u, kanal=self.kanal)
        servisler.onaya_gonder(u, self.owner)
        servisler.onayla(u, self.platform)
        servisler.yayina_al(u, self.platform)
        servisler.pasife_al(u, self.platform)
        for action in (
            "urun.onaya_gonder",
            "urun.onayla",
            "urun.yayina_al",
            "urun.pasife_al",
        ):
            self.assertEqual(
                AuditOlay.objects.filter(
                    action=action, success=True, entity_id=str(u.pk)
                ).count(),
                1,
            )

    def test_failed_audit_visible_after_nested_product_atomic(self):
        """Red audit, ürün güncelleyen atomic rollback'ten etkilenmez."""
        u = self._urun()
        with transaction.atomic():
            with self.assertRaises(PermissionDenied):
                servisler.onaya_gonder(u, self.other)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="urun.onaya_gonder",
                success=False,
                reason="sahiplik_uyusmazligi",
            ).exists()
        )
        u.refresh_from_db()
        self.assertEqual(u.onay_durumu, "taslak")
