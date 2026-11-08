"""urunler.0005: tedarikci verisi teklif taslağına taşınır; boş/dolu ileri-geri."""

from decimal import Decimal

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class Urun0005MigrationTests(TransactionTestCase):
    def tearDown(self):
        call_command("migrate", verbosity=0)

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)

    def _apps(self, *targets):
        executor = MigrationExecutor(connection)
        return executor.loader.project_state(list(targets)).apps

    def test_forward_empty_db_ok(self):
        """Boş katalog: 0004 → 0005 hatasız."""
        self._migrate([("urunler", "0004_faz1_kimlik_rbac")])
        self._migrate([("urunler", "0005_faz2_katalog_ownership")])
        apps = self._apps(("urunler", "0005_faz2_katalog_ownership"))
        Urun = apps.get_model("urunler", "Urun")
        Teklif = apps.get_model("fiyatlama", "TedarikciTeklif")
        self.assertEqual(Urun.objects.count(), 0)
        self.assertEqual(Teklif.objects.count(), 0)

    def test_forward_full_copies_to_teklif_and_reverse_restores(self):
        # firmalar güncel kalsın (firma_kodu); yalnız urunler geri alınır
        self._migrate(
            [
                ("firmalar", "0004_faz1_firma_not_null"),
                ("fiyatlama", "0003_faz2_eslestirme_alanlari"),
                ("urunler", "0004_faz1_kimlik_rbac"),
            ]
        )
        apps = self._apps(
            ("firmalar", "0004_faz1_firma_not_null"),
            ("urunler", "0004_faz1_kimlik_rbac"),
            ("fiyatlama", "0003_faz2_eslestirme_alanlari"),
            ("tanimlar", "0001_initial"),
        )
        Firma = apps.get_model("firmalar", "Firma")
        Kategori = apps.get_model("urunler", "Kategori")
        Urun = apps.get_model("urunler", "Urun")
        Varyant = apps.get_model("urunler", "Varyant")
        FiyatGrubu = apps.get_model("tanimlar", "FiyatGrubu")
        KiymetliMetal = apps.get_model("tanimlar", "KiymetliMetal")
        AyarMilyem = apps.get_model("tanimlar", "AyarMilyem")

        metal = KiymetliMetal.objects.create(kod="ALTIN_M5", ad="Altın", gram_bazli=True)
        ayar = AyarMilyem.objects.create(
            metal=metal, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        grup = FiyatGrubu.objects.create(kod="M5_G", ad="M5")
        kat = Kategori.objects.create(kod="M5_K", ad="Yüzük", fiyat_grubu=grup)
        ted = Firma.objects.create(ad="Ted M5", firma_kodu="M5TED", tedarikci_mi=True)
        urun = Urun.objects.create(
            tedarikci=ted,
            tedarikci_urun_kodu="TED-SKU-99",
            ad="M5 Ürün",
            kategori=kat,
            ayar=ayar,
        )
        Varyant.objects.create(urun=urun, gram=Decimal("2.500"))

        self._migrate([("urunler", "0005_faz2_katalog_ownership")])
        apps5 = self._apps(("urunler", "0005_faz2_katalog_ownership"))
        Urun5 = apps5.get_model("urunler", "Urun")
        Teklif = apps5.get_model("fiyatlama", "TedarikciTeklif")
        u5 = Urun5.objects.get(pk=urun.pk)
        self.assertEqual(u5.olusturan_firma_id, ted.pk)
        self.assertFalse(any(f.name == "tedarikci" for f in Urun5._meta.fields))
        t = Teklif.objects.get(tedarikci_id=ted.pk)
        self.assertEqual(t.tedarikci_kodu, "TED-SKU-99")
        self.assertEqual(t.durum, "TASLAK")

        self._migrate([("urunler", "0004_faz1_kimlik_rbac")])
        apps4 = self._apps(
            ("firmalar", "0004_faz1_firma_not_null"),
            ("urunler", "0004_faz1_kimlik_rbac"),
        )
        Urun4 = apps4.get_model("urunler", "Urun")
        u4 = Urun4.objects.get(pk=urun.pk)
        self.assertEqual(u4.tedarikci_id, ted.pk)
        self.assertEqual(u4.tedarikci_urun_kodu, "TED-SKU-99")

    def test_forward_blocks_when_no_varyant(self):
        self._migrate(
            [
                ("firmalar", "0004_faz1_firma_not_null"),
                ("fiyatlama", "0003_faz2_eslestirme_alanlari"),
                ("urunler", "0004_faz1_kimlik_rbac"),
            ]
        )
        apps = self._apps(
            ("firmalar", "0004_faz1_firma_not_null"),
            ("urunler", "0004_faz1_kimlik_rbac"),
            ("tanimlar", "0001_initial"),
        )
        Firma = apps.get_model("firmalar", "Firma")
        Kategori = apps.get_model("urunler", "Kategori")
        Urun = apps.get_model("urunler", "Urun")
        FiyatGrubu = apps.get_model("tanimlar", "FiyatGrubu")
        KiymetliMetal = apps.get_model("tanimlar", "KiymetliMetal")
        AyarMilyem = apps.get_model("tanimlar", "AyarMilyem")

        metal = KiymetliMetal.objects.create(kod="ALTIN_M5b", ad="Altın", gram_bazli=True)
        ayar = AyarMilyem.objects.create(
            metal=metal, ayar_kodu="18K", ayar_degeri=18, milyem=Decimal("0.750")
        )
        grup = FiyatGrubu.objects.create(kod="M5b_G", ad="M5b")
        kat = Kategori.objects.create(kod="M5b_K", ad="Kolye", fiyat_grubu=grup)
        ted = Firma.objects.create(ad="Ted M5b", firma_kodu="M5bTED", tedarikci_mi=True)
        Urun.objects.create(
            tedarikci=ted,
            tedarikci_urun_kodu="NO-VAR",
            ad="Varyantsız",
            kategori=kat,
            ayar=ayar,
        )

        try:
            with self.assertRaises(RuntimeError) as ctx:
                self._migrate([("urunler", "0005_faz2_katalog_ownership")])
            self.assertIn("taşınamayan", str(ctx.exception))
        finally:
            # tearDown migrate 0005'i yeniden dener; engel satırı sil
            Urun.objects.all().delete()
