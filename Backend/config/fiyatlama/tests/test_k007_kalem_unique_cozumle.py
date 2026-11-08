"""Dilim 3.2 K-007 — NULL-safe kalem unique + cozumle önceliği."""

from datetime import date
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import FiyatSozlesmesi, FiyatSozlesmesiKalemi
from fiyatlama.models.sozlesme_cozumleme import (
    CokluSozlesmeHatasi,
    cozumle,
)
from tanimlar.models import AyarMilyem, KiymetliMetal, SatisKanali

User = get_user_model()


class K007KalemCozumleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        platform = ensure_platform_firma()
        cls.firma = Firma.objects.create(ad="K7F", firma_kodu="K7F", alici_mi=True)
        cls.metal = KiymetliMetal.objects.create(kod="AU", ad="Altın", gram_bazli=True)
        cls.ayar14 = AyarMilyem.objects.create(
            metal=cls.metal, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        cls.ayar18 = AyarMilyem.objects.create(
            metal=cls.metal, ayar_kodu="18K", ayar_degeri=18, milyem=Decimal("0.750")
        )
        cls.kanal_a = SatisKanali.objects.create(kod="K7A", ad="Kanal A")
        cls.user = User(
            username="k7u",
            firma=platform,
            rol=roles.PLATFORM_FINANCE,
            is_staff=True,
        )
        cls.user.set_password("x")
        cls.user.save()
        sync_user_role_groups(cls.user)

    def setUp(self):
        self._pending_aktif = []

    def _sozlesme(self, *, kanal=None, versiyon=1, aktif=True, **kw):
        """Kalemler TASLAK iken eklenir; istenirse sonra AKTIF yapılır."""
        defaults = dict(
            firma=self.firma,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            satis_kanali=kanal,
            gecerlilik_baslangic=date(2026, 1, 1),
            gecerlilik_bitis=date(2026, 12, 31),
            durum=FiyatSozlesmesi.Durum.TASLAK,
            olusturan_kullanici=self.user,
            versiyon=versiyon,
        )
        defaults.update(kw)
        s = FiyatSozlesmesi.objects.create(**defaults)
        if aktif:
            self._pending_aktif.append(s)
        return s

    def _activate_pending(self):
        from fiyatlama.services import sozlesme_servisi

        for s in getattr(self, "_pending_aktif", []):
            s.refresh_from_db()
            if s.durum != FiyatSozlesmesi.Durum.AKTIF:
                sozlesme_servisi.aktif_yap(s, self.user)
        self._pending_aktif = []

    def _kalem(self, sozlesme, *, ayar=None, marj=Decimal("10"), **kw):
        defaults = dict(
            sozlesme=sozlesme,
            metal=self.metal,
            ayar=ayar,
            marj_tipi=FiyatSozlesmesiKalemi.MarjTipi.YUZDE,
            marj_degeri=marj,
        )
        defaults.update(kw)
        return FiyatSozlesmesiKalemi.objects.create(**defaults)

    def test_genel_ayar_kaydi(self):
        s = self._sozlesme(aktif=False)
        k = self._kalem(s, ayar=None)
        self.assertIsNone(k.ayar_id)

    def test_birden_fazla_farkli_ayar(self):
        s = self._sozlesme(aktif=False)
        self._kalem(s, ayar=None, marj=Decimal("5"))
        self._kalem(s, ayar=self.ayar14, marj=Decimal("8"))
        self._kalem(s, ayar=self.ayar18, marj=Decimal("9"))
        self.assertEqual(s.kalemler.count(), 3)

    def test_ikinci_genel_red(self):
        s = self._sozlesme(aktif=False)
        self._kalem(s, ayar=None)
        with self.assertRaises(ValidationError):
            self._kalem(s, ayar=None, marj=Decimal("11"))

    def test_ikinci_spesifik_red(self):
        s = self._sozlesme(aktif=False)
        self._kalem(s, ayar=self.ayar14)
        with self.assertRaises((ValidationError, IntegrityError)):
            with transaction.atomic():
                self._kalem(s, ayar=self.ayar14, marj=Decimal("12"))

    def test_cozumle_genel_plus_spesifik_prefers_spesifik(self):
        s = self._sozlesme()
        self._kalem(s, ayar=None, marj=Decimal("5"))
        sp = self._kalem(s, ayar=self.ayar14, marj=Decimal("8"))
        self._activate_pending()
        out = cozumle(
            firma=self.firma,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            tarih=date(2026, 6, 1),
            metal=self.metal,
            ayar=self.ayar14,
        )
        self.assertEqual(out.pk, sp.pk)

    def test_cozumle_kanal_onceligi(self):
        s_gen = self._sozlesme(kanal=None, versiyon=1)
        s_ch = self._sozlesme(kanal=self.kanal_a, versiyon=1)
        self._kalem(s_gen, ayar=self.ayar14, marj=Decimal("5"))
        k_ch = self._kalem(s_ch, ayar=self.ayar14, marj=Decimal("7"))
        self._activate_pending()
        out = cozumle(
            firma=self.firma,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            tarih=date(2026, 6, 1),
            metal=self.metal,
            ayar=self.ayar14,
            satis_kanali=self.kanal_a,
        )
        self.assertEqual(out.pk, k_ch.pk)

    def test_cozumle_esit_skor_hata(self):
        """DB tekilliği eşit skor adayını nadiren üretir; skor bağını mock ile doğrula."""
        s = self._sozlesme()
        k1 = self._kalem(s, ayar=self.ayar14, marj=Decimal("1"))
        k2 = self._kalem(s, ayar=self.ayar18, marj=Decimal("2"))
        self._activate_pending()
        k1.refresh_from_db()
        k2.refresh_from_db()

        class _QS:
            def select_related(self, *a, **k):
                return self

            def filter(self, *a, **k):
                return self

            def __iter__(self):
                return iter([k1, k2])

        with mock.patch(
            "fiyatlama.models.sozlesme_cozumleme.FiyatSozlesmesiKalemi.objects.filter",
            return_value=_QS(),
        ):
            with self.assertRaises(CokluSozlesmeHatasi):
                cozumle(
                    firma=self.firma,
                    kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
                    tarih=date(2026, 6, 1),
                    metal=self.metal,
                    ayar=self.ayar14,
                    satis_kanali=None,
                )
