from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from tanimlar.models import AyarMilyem, FiyatGrubu, KiymetliMetal, SatisKanali
from urunler.models import Kategori, OlcuDegeri, Renk, Urun


class KatalogTestTaban(TestCase):
    @classmethod
    def setUpTestData(cls):
        altin = KiymetliMetal.objects.create(kod="ALTIN", ad="Altın", gram_bazli=True)
        celik = KiymetliMetal.objects.create(kod="CELIK", ad="Çelik", gram_bazli=False)
        cls.ayar14 = AyarMilyem.objects.create(
            metal=altin, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        cls.ayarsiz = AyarMilyem.objects.create(
            metal=celik, ayar_kodu="Ayarsız", ayar_degeri=0, milyem=Decimal("0.000")
        )
        grup = FiyatGrubu.objects.create(kod="YUZUK_ALYANS", ad="Yüzük / Alyans")
        cls.kategori = Kategori.objects.create(kod="YUZUK", ad="Yüzük", fiyat_grubu=grup)
        cls.tedarikci = Firma.objects.create(
            ad="Tedarikçi A", firma_kodu="TED_A", tedarikci_mi=True
        )
        cls.tedarikci_b = Firma.objects.create(
            ad="Tedarikçi B", firma_kodu="TED_B", tedarikci_mi=True
        )
        cls.kanal = SatisKanali.objects.create(kod="KUYUMCU_PANEL", ad="Kuyumcu paneli")
        cls.renk_sari = Renk.objects.create(kod="SARI", ad="Sarı")
        cls.renk_beyaz = Renk.objects.create(kod="BEYAZ", ad="Beyaz")
        cls.no14 = OlcuDegeri.objects.create(
            tip="yuzuk_no", deger="14 No", sira=14, sayisal_deger=Decimal("14")
        )
        cls.no16 = OlcuDegeri.objects.create(
            tip="yuzuk_no", deger="16 No", sira=16, sayisal_deger=Decimal("16")
        )
        cls.cm19 = OlcuDegeri.objects.create(
            tip="bilezik_boyu", deger="19 cm", sira=19, sayisal_deger=Decimal("19")
        )

        seed_role_permissions()
        platform_firma = ensure_platform_firma()
        User = get_user_model()

        cls.platform = User(
            username="platform1",
            firma=platform_firma,
            rol=roles.PLATFORM_CATALOG,
            is_staff=True,
        )
        cls.platform.set_password("x")
        cls.platform.save()
        sync_user_role_groups(cls.platform)

        cls.tedarikci_user = User(
            username="ted1",
            firma=cls.tedarikci,
            rol=roles.TEDARIKCI_SAHIP,
        )
        cls.tedarikci_user.set_password("x")
        cls.tedarikci_user.save()
        sync_user_role_groups(cls.tedarikci_user)

        cls.tedarikci_b_user = User(
            username="ted2",
            firma=cls.tedarikci_b,
            rol=roles.TEDARIKCI_SAHIP,
        )
        cls.tedarikci_b_user.set_password("x")
        cls.tedarikci_b_user.save()
        sync_user_role_groups(cls.tedarikci_b_user)

    def urun(self, **kw):
        degerler = dict(
            olusturan_firma=self.tedarikci,
            ad="Tek taş yüzük",
            kategori=self.kategori,
            ayar=self.ayar14,
        )
        degerler.update(kw)
        return Urun.objects.create(**degerler)
