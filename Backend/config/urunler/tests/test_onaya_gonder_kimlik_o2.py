"""O2 — onaya_gonder kimlik çakışması (reddedildi→onay_bekliyor); genel hata."""

from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import AuditOlay, Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal
from urunler.models import Kategori, Urun, Varyant
from urunler.services import onay_servisi as svc
from urunler.services.onay_servisi import _KIMLIK_CAKISMA_MSG
from urunler.tests._base import KatalogTestTaban

User = get_user_model()


class OnayaGonderKimlikO2Tests(KatalogTestTaban):
    def _urun_ab(self, *, firma, anahtar, durum="taslak", ad="U"):
        # Önce C/boş anahtar ile oluştur; A+anahtar'ı durumla birlikte update et
        # (aktif kayıt varken taslak INSERT unique'i kırmaz).
        u = self.urun(
            olusturan_firma=firma,
            kimlik_sinifi="C",
            kimlik_anahtari="",
            ad=ad,
        )
        Varyant.objects.create(urun=u, gram=Decimal("2.0"))
        kw = {
            "kimlik_sinifi": "A",
            "kimlik_anahtari": anahtar,
            "onay_durumu": durum,
            "red_nedeni": "x" if durum == "reddedildi" else "",
        }
        if durum == "onayli":
            kw["onaylayan_kullanici"] = self.platform
            kw["onay_zamani"] = timezone.now()
        Urun.objects.filter(pk=u.pk).update(**kw)
        u.refresh_from_db()
        return u

    def test_reddedildi_blocked_when_active_same_key(self):
        aktif = self._urun_ab(
            firma=self.tedarikci_b, anahtar="O2-KEY-1", durum="onayli", ad="Aktif"
        )
        redded = self._urun_ab(
            firma=self.tedarikci, anahtar="O2-KEY-1", durum="reddedildi", ad="Red"
        )
        with self.assertRaises(ValidationError) as ctx:
            svc.onaya_gonder(redded, self.tedarikci_user)
        self.assertEqual(str(ctx.exception.messages[0]), _KIMLIK_CAKISMA_MSG)
        self.assertNotIn(str(aktif.pk), str(ctx.exception))
        self.assertNotIn("Aktif", str(ctx.exception))
        self.assertTrue(
            AuditOlay.objects.filter(
                action="urun.onaya_gonder",
                success=False,
                reason="kimlik_cakisma",
            ).exists()
        )

    def test_reddedildi_ok_when_only_other_reddedildi(self):
        self._urun_ab(
            firma=self.tedarikci_b,
            anahtar="O2-KEY-2",
            durum="reddedildi",
            ad="EskiRed",
        )
        redded = self._urun_ab(
            firma=self.tedarikci, anahtar="O2-KEY-2", durum="reddedildi", ad="Yeniden"
        )
        out = svc.onaya_gonder(redded, self.tedarikci_user)
        self.assertEqual(out.onay_durumu, "onay_bekliyor")


class OnayaGonderKimlikYarisO2Tests(TransactionTestCase):
    def setUp(self):
        seed_role_permissions()
        platform = ensure_platform_firma()
        self.ted = Firma.objects.create(ad="O2Y", firma_kodu="O2Y", tedarikci_mi=True)
        metal = KiymetliMetal.objects.create(kod="O2M", ad="Altın", gram_bazli=True)
        ayar = AyarMilyem.objects.create(
            metal=metal, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        grup = FiyatGrubu.objects.create(kod="O2G", ad="O2G")
        kat = Kategori.objects.create(kod="O2K", ad="Yüzük", fiyat_grubu=grup)
        self.user = User(
            username="o2y",
            firma=self.ted,
            rol=roles.TEDARIKCI_SAHIP,
        )
        self.user.set_password("x")
        self.user.save()
        sync_user_role_groups(self.user)

        padmin = User(
            username="o2yp",
            firma=platform,
            rol=roles.PLATFORM_CATALOG,
            is_staff=True,
        )
        padmin.set_password("x")
        padmin.save()
        sync_user_role_groups(padmin)

        self.u = Urun.objects.create(
            olusturan_firma=self.ted,
            ad="Yaris",
            kategori=kat,
            ayar=ayar,
            kimlik_sinifi="C",
            kimlik_anahtari="",
        )
        Varyant.objects.create(urun=self.u, gram=Decimal("1"))
        Urun.objects.filter(pk=self.u.pk).update(
            kimlik_sinifi="A",
            kimlik_anahtari="O2-YARIS",
            onay_durumu="reddedildi",
            red_nedeni="eski",
        )
        self.u.refresh_from_db()

        rival = Urun.objects.create(
            olusturan_firma=self.ted,
            ad="Rival",
            kategori=kat,
            ayar=ayar,
            kimlik_sinifi="C",
            kimlik_anahtari="",
        )
        Urun.objects.filter(pk=rival.pk).update(
            kimlik_sinifi="A",
            kimlik_anahtari="O2-YARIS",
            onay_durumu="onayli",
            onaylayan_kullanici=padmin,
            onay_zamani=timezone.now(),
        )

    def test_integrity_error_mapped_to_generic(self):
        with mock.patch(
            "urunler.services.onay_servisi._aktif_kimlik_cakisiyor_mu",
            return_value=False,
        ):
            with self.assertRaises(ValidationError) as ctx:
                svc.onaya_gonder(self.u, self.user)
        self.assertEqual(str(ctx.exception.messages[0]), _KIMLIK_CAKISMA_MSG)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="urun.onaya_gonder",
                success=False,
                reason="kimlik_cakisma_yaris",
            ).exists()
        )
