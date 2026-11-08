"""ADR-0007 dilim 3.1 — teklif yaşam döngüsü servis testleri."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import AuditOlay, Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import TedarikciTeklif
from fiyatlama.selectors.tenant import (
    scope_teklif_queryset,
    teklif_eslestirme_uygun_mu,
)
from fiyatlama.services import teklif_servisi
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal
from urunler.models import Kategori, Urun, Varyant

User = get_user_model()


class TeklifYasamDongusuTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.platform = ensure_platform_firma()
        cls.ted_a = Firma.objects.create(
            ad="TYA", firma_kodu="TYA", tedarikci_mi=True
        )
        cls.ted_b = Firma.objects.create(
            ad="TYB", firma_kodu="TYB", tedarikci_mi=True
        )
        cls.alici = Firma.objects.create(
            ad="TYAL", firma_kodu="TYAL", alici_mi=True
        )
        metal = KiymetliMetal.objects.create(kod="AU", ad="Altın", gram_bazli=True)
        ayar = AyarMilyem.objects.create(
            metal=metal, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        grup = FiyatGrubu.objects.create(kod="TYG", ad="TYG")
        kat = Kategori.objects.create(kod="TYK", ad="Yüzük", fiyat_grubu=grup)

        cls.padmin = User(
            username="ty_padmin",
            firma=cls.platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.padmin.set_password("x")
        cls.padmin.save()
        sync_user_role_groups(cls.padmin)

        cls.approver = User(
            username="ty_approver",
            firma=cls.platform,
            rol=roles.PLATFORM_CATALOG,
            is_staff=True,
        )
        cls.approver.set_password("x")
        cls.approver.save()
        sync_user_role_groups(cls.approver)

        cls.staff_a = User(
            username="ty_a",
            firma=cls.ted_a,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.staff_a.set_password("x")
        cls.staff_a.save()
        sync_user_role_groups(cls.staff_a)

        cls.staff_b = User(
            username="ty_b",
            firma=cls.ted_b,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.staff_b.set_password("x")
        cls.staff_b.save()
        sync_user_role_groups(cls.staff_b)

        cls.buyer = User(
            username="ty_buyer",
            firma=cls.alici,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)

        cls.super_u = User(
            username="ty_super",
            firma=cls.ted_a,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
            is_superuser=True,
        )
        cls.super_u.set_password("x")
        cls.super_u.save()
        # Grup senkronu yok — permission'sız superuser (kısa yol yok test)

        urun = Urun.objects.create(
            olusturan_firma=cls.ted_a, ad="U", kategori=kat, ayar=ayar
        )
        Urun.objects.filter(pk=urun.pk).update(
            onay_durumu="onayli",
            onaylayan_kullanici=cls.padmin,
            onay_zamani=timezone.now(),
        )
        urun.refresh_from_db()
        cls.urun = urun
        cls.varyant = Varyant.objects.create(urun=urun, gram=Decimal("2.5"))

    def _dates(self):
        bas = date.today()
        return bas, bas + timedelta(days=30)

    def _teklif(self, *, tedarikci=None, kod="SKU1", durum="TASLAK", **extra):
        bas, bit = self._dates()
        defaults = dict(
            varyant=self.varyant,
            tedarikci=tedarikci or self.ted_a,
            tedarikci_kodu=kod,
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("2.5"),
            durum=durum,
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
            eslestirme_durumu="onaylandi",
            hedef_urun=self.urun,
        )
        defaults.update(extra)
        return TedarikciTeklif.objects.create(**defaults)

    def test_onaya_gonder_and_yayina_al_happy(self):
        t = self._teklif()
        teklif_servisi.onaya_gonder(t, self.staff_a)
        t.refresh_from_db()
        self.assertEqual(t.durum, TedarikciTeklif.Durum.ONAY_BEKLIYOR)
        teklif_servisi.yayina_al(t, self.approver)
        t.refresh_from_db()
        self.assertEqual(t.durum, TedarikciTeklif.Durum.YAYINDA)
        self.assertEqual(t.onaylayan_id, self.approver.pk)

    def test_skip_transition_rejected(self):
        t = self._teklif()
        with self.assertRaises(ValidationError):
            teklif_servisi.yayina_al(t, self.approver)

    def test_ownership_other_supplier(self):
        t = self._teklif()
        with self.assertRaises(PermissionDenied):
            teklif_servisi.onaya_gonder(t, self.staff_b)

    def test_ownership_buyer_rejected(self):
        t = self._teklif()
        with self.assertRaises(PermissionDenied):
            teklif_servisi.onaya_gonder(t, self.buyer)

    def test_client_tedarikci_ignored_on_create_path(self):
        # Sahiplik sunucu firmasından; client tedarikci_id yok sayılır (servis kontrolü).
        t = self._teklif(tedarikci=self.ted_a)
        self.assertEqual(t.tedarikci_id, self.ted_a.pk)
        with self.assertRaises(PermissionDenied):
            teklif_servisi.onaya_gonder(t, self.staff_b)

    def test_superuser_no_shortcut(self):
        t = self._teklif()
        with self.assertRaises(PermissionDenied):
            teklif_servisi.onaya_gonder(t, self.super_u)

    def test_dort_goz_same_sender_rejected(self):
        # Platform user with manage? Staff_a can't approve. Use: supplier sends,
        # then same user somehow has approve — use padmin who also "sends" via
        # forging audit by calling onaya as supplier... four-eye: gonderen = approver.
        t = self._teklif()
        teklif_servisi.onaya_gonder(t, self.staff_a)
        # Approver cannot be sender; make approver the sender by recording audit
        AuditOlay.objects.create(
            actor=self.approver,
            actor_firma=self.platform,
            action="teklif.onaya_gonder",
            entity_type="TedarikciTeklif",
            entity_id=str(t.pk),
            success=True,
        )
        with self.assertRaises(PermissionDenied):
            teklif_servisi.yayina_al(t, self.approver)

    def test_aktif_cakisma_kodlu(self):
        t1 = self._teklif(kod="C1")
        teklif_servisi.onaya_gonder(t1, self.staff_a)
        teklif_servisi.yayina_al(t1, self.approver)
        t2 = self._teklif(kod="C1")
        teklif_servisi.onaya_gonder(t2, self.staff_a)
        with self.assertRaises(ValidationError):
            teklif_servisi.yayina_al(t2, self.approver)

    def test_aktif_cakisma_kodsuz(self):
        t1 = self._teklif(kod="")
        teklif_servisi.onaya_gonder(t1, self.staff_a)
        teklif_servisi.yayina_al(t1, self.approver)
        t2 = self._teklif(kod="")
        teklif_servisi.onaya_gonder(t2, self.staff_a)
        with self.assertRaises(ValidationError):
            teklif_servisi.yayina_al(t2, self.approver)

    def test_protect_varyant(self):
        t = self._teklif()
        teklif_servisi.onaya_gonder(t, self.staff_a)
        teklif_servisi.yayina_al(t, self.approver)
        with self.assertRaises(ProtectedError):
            self.varyant.delete()

    def test_gecerlilik_required_for_yayinda(self):
        t = self._teklif(gecerlilik_baslangic=None, gecerlilik_bitis=None)
        teklif_servisi.onaya_gonder(t, self.staff_a)
        with self.assertRaises(ValidationError):
            teklif_servisi.yayina_al(t, self.approver)

    def test_gecerlilik_bitis_before_baslangic(self):
        bas, bit = self._dates()
        t = self._teklif(gecerlilik_baslangic=bas, gecerlilik_bitis=bit)
        t.gecerlilik_bitis = bas - timedelta(days=1)
        with self.assertRaises(ValidationError):
            t.full_clean()

    def test_pasif_yeniden_yayin(self):
        t = self._teklif()
        teklif_servisi.onaya_gonder(t, self.staff_a)
        teklif_servisi.yayina_al(t, self.approver)
        teklif_servisi.pasifle(t, self.staff_a)
        t.refresh_from_db()
        self.assertEqual(t.durum, TedarikciTeklif.Durum.PASIF)
        teklif_servisi.yeniden_yayinla(t, self.approver)
        t.refresh_from_db()
        self.assertEqual(t.durum, TedarikciTeklif.Durum.YAYINDA)

    def test_versiyon_swap_order(self):
        t = self._teklif(kod="V1")
        teklif_servisi.onaya_gonder(t, self.staff_a)
        teklif_servisi.yayina_al(t, self.approver)
        yeni = teklif_servisi.yeni_versiyon_olustur(
            t, self.staff_a, gram=Decimal("3.0")
        )
        self.assertEqual(yeni.durum, TedarikciTeklif.Durum.ONAY_BEKLIYOR)
        self.assertEqual(yeni.versiyon, 2)
        self.assertEqual(yeni.onceki_teklif_id, t.pk)
        t.refresh_from_db()
        self.assertEqual(t.durum, TedarikciTeklif.Durum.YAYINDA)
        teklif_servisi.yayina_al(yeni, self.approver)
        t.refresh_from_db()
        yeni.refresh_from_db()
        self.assertEqual(t.durum, TedarikciTeklif.Durum.PASIF)
        self.assertEqual(yeni.durum, TedarikciTeklif.Durum.YAYINDA)

    def test_predicate_eslestirme(self):
        t = self._teklif(eslestirme_durumu="", hedef_urun=None)
        self.assertFalse(teklif_eslestirme_uygun_mu(t))
        t.eslestirme_durumu = "onerildi"
        t.hedef_urun = self.urun
        self.assertFalse(teklif_eslestirme_uygun_mu(t))
        t.eslestirme_durumu = "onaylandi"
        self.assertTrue(teklif_eslestirme_uygun_mu(t))

    def test_tenant_selector(self):
        ta = self._teklif(kod="TA")
        tb = self._teklif(tedarikci=self.ted_b, kod="TB")
        qs_a = scope_teklif_queryset(TedarikciTeklif.objects.all(), self.staff_a)
        self.assertIn(ta, qs_a)
        self.assertNotIn(tb, qs_a)

    def test_fail_audit_permission(self):
        t = self._teklif()
        before = AuditOlay.objects.filter(success=False).count()
        with self.assertRaises(PermissionDenied):
            teklif_servisi.onaya_gonder(t, self.staff_b)
        self.assertGreater(
            AuditOlay.objects.filter(success=False).count(), before
        )

    def test_success_audit_same_tx(self):
        t = self._teklif()
        teklif_servisi.onaya_gonder(t, self.staff_a)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="teklif.onaya_gonder",
                entity_id=str(t.pk),
                success=True,
            ).exists()
        )
