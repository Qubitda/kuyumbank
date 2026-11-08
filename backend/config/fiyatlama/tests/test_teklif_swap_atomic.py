"""Versiyon swap atomikliği + fail audit durable (TransactionTestCase)."""

from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TransactionTestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import AuditOlay, Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import TedarikciTeklif
from fiyatlama.services import teklif_servisi
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal
from urunler.models import Kategori, Urun, Varyant

User = get_user_model()


class TeklifSwapAtomicTests(TransactionTestCase):
    def setUp(self):
        seed_role_permissions()
        self.platform = ensure_platform_firma()
        self.ted = Firma.objects.create(
            ad="SWA", firma_kodu="SWA", tedarikci_mi=True
        )
        metal = KiymetliMetal.objects.create(kod="AUS", ad="Altın", gram_bazli=True)
        ayar = AyarMilyem.objects.create(
            metal=metal, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        grup = FiyatGrubu.objects.create(kod="SWG", ad="SWG")
        kat = Kategori.objects.create(kod="SWK", ad="Yüzük", fiyat_grubu=grup)

        self.approver = User(
            username="sw_appr",
            firma=self.platform,
            rol=roles.PLATFORM_CATALOG,
            is_staff=True,
        )
        self.approver.set_password("x")
        self.approver.save()
        sync_user_role_groups(self.approver)

        self.staff = User(
            username="sw_ted",
            firma=self.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        self.staff.set_password("x")
        self.staff.save()
        sync_user_role_groups(self.staff)

        urun = Urun.objects.create(
            olusturan_firma=self.ted, ad="U", kategori=kat, ayar=ayar
        )
        Urun.objects.filter(pk=urun.pk).update(
            onay_durumu="onayli",
            onaylayan_kullanici=self.approver,
            onay_zamani=timezone.now(),
        )
        urun.refresh_from_db()
        self.varyant = Varyant.objects.create(urun=urun, gram=Decimal("2"))
        bas = date.today()
        bit = bas + timedelta(days=10)
        self.t1 = TedarikciTeklif.objects.create(
            varyant=self.varyant,
            tedarikci=self.ted,
            tedarikci_kodu="SW1",
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("2"),
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
            eslestirme_durumu="onaylandi",
            hedef_urun=urun,
        )
        teklif_servisi.onaya_gonder(self.t1, self.staff)
        teklif_servisi.yayina_al(self.t1, self.approver)

    def test_swap_rollback_keeps_eski_yayinda(self):
        yeni = teklif_servisi.yeni_versiyon_olustur(
            self.t1, self.staff, gram=Decimal("2.1")
        )
        real_save = TedarikciTeklif.save

        def boom(self, *args, **kwargs):
            if (
                self.pk == yeni.pk
                and self.durum == TedarikciTeklif.Durum.YAYINDA
            ):
                raise IntegrityError("forced-swap-fail")
            return real_save(self, *args, **kwargs)

        with mock.patch.object(TedarikciTeklif, "save", boom):
            with self.assertRaises(ValidationError):
                teklif_servisi.yayina_al(yeni, self.approver)

        self.t1.refresh_from_db()
        yeni.refresh_from_db()
        self.assertEqual(self.t1.durum, TedarikciTeklif.Durum.YAYINDA)
        self.assertEqual(yeni.durum, TedarikciTeklif.Durum.ONAY_BEKLIYOR)

    def test_fail_audit_durable_outside_atomic(self):
        other = Firma.objects.create(
            ad="SWB", firma_kodu="SWB", tedarikci_mi=True
        )
        staff_b = User(
            username="sw_b",
            firma=other,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        staff_b.set_password("x")
        staff_b.save()
        sync_user_role_groups(staff_b)

        before = AuditOlay.objects.filter(
            action="teklif.onaya_gonder", success=False
        ).count()
        with self.assertRaises(Exception):
            teklif_servisi.onaya_gonder(self.t1, staff_b)
        self.assertGreater(
            AuditOlay.objects.filter(
                action="teklif.onaya_gonder", success=False
            ).count(),
            before,
        )
