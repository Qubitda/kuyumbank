"""Dilim 3.3 — kur politikası (B-04/B-05, stale, manuel dört göz)."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from tanimlar.models import (
    KiymetliMetal,
    KurPolitikasi,
    KurSaglayici,
    KurTaraf,
    KurTipi,
    MetalKuru,
    SatisKanali,
)
from tanimlar.services import kur_servisi

User = get_user_model()


class KurPolitikasiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        platform = ensure_platform_firma()
        cls.giren = User(
            username="kur_giren",
            firma=platform,
            rol=roles.PLATFORM_FINANCE,
            is_staff=True,
        )
        cls.giren.set_password("x")
        cls.giren.save()
        sync_user_role_groups(cls.giren)

        cls.onaylayan = User(
            username="kur_onay",
            firma=platform,
            rol=roles.PLATFORM_FINANCE,
            is_staff=True,
        )
        cls.onaylayan.set_password("x")
        cls.onaylayan.save()
        sync_user_role_groups(cls.onaylayan)

        cls.yetkisiz = User(
            username="kur_yetkisiz",
            firma=platform,
            rol=roles.PLATFORM_SUPPORT,
            is_staff=True,
        )
        cls.yetkisiz.set_password("x")
        cls.yetkisiz.save()
        sync_user_role_groups(cls.yetkisiz)

        cls.metal = KiymetliMetal.objects.create(kod="AU33", ad="Altın33", gram_bazli=True)
        # 0002 seed MANUEL aktif olabilir; tek aktif kuralına uy
        KurSaglayici.objects.filter(aktif=True).update(aktif=False)
        cls.saglayici = KurSaglayici.objects.create(
            kod="P33",
            ad="Provider 33",
            aktif=True,
            max_gecikme_saniye=60,
        )
        KurPolitikasi.objects.get_or_create(
            anahtar="default",
            defaults={
                "alici_kur_tipi": KurTipi.SATIS,
                "tedarikci_kur_tipi": KurTipi.ALIS,
            },
        )

    def test_tek_aktif_saglayici_db(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                KurSaglayici.objects.create(
                    kod="P33B",
                    ad="İkinci aktif",
                    aktif=True,
                    max_gecikme_saniye=30,
                )

    def test_aktif_saglayici_ayarla_tek(self):
        diger = KurSaglayici.objects.create(
            kod="P33C", ad="Pasif", aktif=False, max_gecikme_saniye=30
        )
        kur_servisi.aktif_saglayici_ayarla(self.giren, diger.pk)
        self.saglayici.refresh_from_db()
        diger.refresh_from_db()
        self.assertFalse(self.saglayici.aktif)
        self.assertTrue(diger.aktif)
        # geri al — diğer testler için
        kur_servisi.aktif_saglayici_ayarla(self.giren, self.saglayici.pk)

    def test_manuel_dort_goz_ve_audit(self):
        now = timezone.now()
        obj = kur_servisi.manuel_metal_kuru_gir(
            self.giren,
            self.onaylayan,
            metal=self.metal,
            saf_birim_fiyat=Decimal("6500.0000"),
            kur_tipi=KurTipi.SATIS,
            zaman=now,
            neden="Feed kesildi",
        )
        self.assertEqual(obj.kaynak, "manuel")
        self.assertEqual(obj.onaylayan_kullanici_id, self.onaylayan.pk)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="kur.manuel_metal", entity_id=str(obj.pk), success=True
            ).exists()
        )

    def test_manuel_ayni_kisi_dort_goz_red(self):
        with self.assertRaises(PermissionDenied):
            kur_servisi.manuel_metal_kuru_gir(
                self.giren,
                self.giren,
                metal=self.metal,
                saf_birim_fiyat=Decimal("1.0000"),
                kur_tipi=KurTipi.SATIS,
                neden="x",
            )
        self.assertTrue(
            AuditOlay.objects.filter(
                action="kur.manuel_metal", success=False, reason="dort_goz"
            ).exists()
        )

    def test_manuel_yetki_yok(self):
        with self.assertRaises(PermissionDenied):
            kur_servisi.manuel_metal_kuru_gir(
                self.yetkisiz,
                self.onaylayan,
                metal=self.metal,
                saf_birim_fiyat=Decimal("1.0000"),
                kur_tipi=KurTipi.SATIS,
                neden="x",
            )

    def test_resolve_alici_satis_tipi(self):
        now = timezone.now()
        kur_servisi.feed_metal_kuru_kaydet(
            saglayici=self.saglayici,
            metal=self.metal,
            saf_birim_fiyat=Decimal("7000.0000"),
            kur_tipi=KurTipi.SATIS,
            zaman=now,
            alinma_zamani=now,
        )
        kur_servisi.feed_metal_kuru_kaydet(
            saglayici=self.saglayici,
            metal=self.metal,
            saf_birim_fiyat=Decimal("6900.0000"),
            kur_tipi=KurTipi.ALIS,
            zaman=now,
            alinma_zamani=now,
        )
        alici = kur_servisi.resolve_metal_kuru(
            self.metal, taraf=KurTaraf.ALICI, now=now
        )
        ted = kur_servisi.resolve_metal_kuru(
            self.metal, taraf=KurTaraf.TEDARIKCI, now=now
        )
        self.assertEqual(alici.kur_tipi, KurTipi.SATIS)
        self.assertEqual(alici.saf_birim_fiyat, Decimal("7000.0000"))
        self.assertEqual(ted.kur_tipi, KurTipi.ALIS)
        self.assertEqual(ted.saf_birim_fiyat, Decimal("6900.0000"))

    def test_stale_resolve_hata(self):
        eski = timezone.now() - timedelta(seconds=120)
        MetalKuru.objects.create(
            metal=self.metal,
            saglayici=self.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=eski,
            alinma_zamani=eski,
            saf_birim_fiyat=Decimal("1.0000"),
            kaynak="api",
        )
        with self.assertRaises(kur_servisi.KurStaleError):
            kur_servisi.resolve_metal_kuru(
                self.metal, taraf=KurTaraf.ALICI, now=timezone.now()
            )

    def test_pasif_saglayici_resolve_yok_fallback(self):
        """Aktif olmayan sağlayıcının kuru kullanılmaz (B-04)."""
        pasif = KurSaglayici.objects.create(
            kod="P33PASIF", ad="Pasif", aktif=False, max_gecikme_saniye=60
        )
        now = timezone.now()
        MetalKuru.objects.create(
            metal=self.metal,
            saglayici=pasif,
            kur_tipi=KurTipi.SATIS,
            zaman=now,
            alinma_zamani=now,
            saf_birim_fiyat=Decimal("9999.0000"),
            kaynak="api",
        )
        # Aktif sağlayıcıda gözlem yok → KurYokError (pasife düşmez)
        with self.assertRaises(kur_servisi.KurYokError):
            kur_servisi.resolve_metal_kuru(
                self.metal, taraf=KurTaraf.ALICI, now=now
            )

    def test_feed_pasif_saglayici_red(self):
        pasif = KurSaglayici.objects.create(
            kod="P33F", ad="F", aktif=False, max_gecikme_saniye=60
        )
        with self.assertRaises(ValidationError):
            kur_servisi.feed_metal_kuru_kaydet(
                saglayici=pasif,
                metal=self.metal,
                saf_birim_fiyat=Decimal("1"),
                kur_tipi=KurTipi.SATIS,
                zaman=timezone.now(),
            )

    def test_kanal_ttl_yoksa_hata(self):
        kanal = SatisKanali.objects.create(kod="K33", ad="K33", aktif=True)
        with self.assertRaises(ValidationError):
            kur_servisi.kanal_quote_ttl_saniye(kanal)
        kanal.quote_ttl_saniye = 120
        kanal.save()
        self.assertEqual(kur_servisi.kanal_quote_ttl_saniye(kanal), 120)
