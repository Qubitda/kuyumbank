"""urunler.0007 O2: kimlik unique reddedildi hariç — ileri/reverse."""

from decimal import Decimal

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class Urun0007O2MigrationTests(TransactionTestCase):
    def tearDown(self):
        call_command("migrate", verbosity=0)

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)

    def _apps(self, *targets):
        executor = MigrationExecutor(connection)
        return executor.loader.project_state(list(targets)).apps

    def _seed_katalog(self, apps, *, suffix: str):
        Firma = apps.get_model("firmalar", "Firma")
        Kategori = apps.get_model("urunler", "Kategori")
        FiyatGrubu = apps.get_model("tanimlar", "FiyatGrubu")
        KiymetliMetal = apps.get_model("tanimlar", "KiymetliMetal")
        AyarMilyem = apps.get_model("tanimlar", "AyarMilyem")
        Kullanici = apps.get_model("firmalar", "Kullanici")

        metal = KiymetliMetal.objects.create(
            kod=f"M{suffix}", ad="Altın", gram_bazli=True
        )
        ayar = AyarMilyem.objects.create(
            metal=metal, ayar_kodu="14K", ayar_degeri=14, milyem=Decimal("0.585")
        )
        grup = FiyatGrubu.objects.create(kod=f"G{suffix}", ad=f"G{suffix}")
        kat = Kategori.objects.create(kod=f"K{suffix}", ad="Yüzük", fiyat_grubu=grup)
        ted = Firma.objects.create(
            ad=f"Ted{suffix}", firma_kodu=f"T{suffix}"[:20], tedarikci_mi=True
        )
        platform = Firma.objects.filter(platform_mu=True).first()
        if platform is None:
            platform = Firma.objects.create(
                ad="Plat", firma_kodu="PLATFORM", platform_mu=True
            )
        padmin = Kullanici.objects.filter(firma_id=platform.pk).first()
        if padmin is None:
            padmin = Kullanici.objects.create(
                username=f"p{suffix}",
                firma=platform,
                rol="platform_catalog",
                is_staff=True,
                password="!",
            )
        return ted, kat, ayar, padmin

    def test_forward_empty_ok(self):
        self._migrate([("urunler", "0006_faz2_index_names")])
        self._migrate([("urunler", "0007_o2_kimlik_uniq_reddedildi_haric")])

    def test_forward_full_allows_reddedildi_duplicate_key(self):
        self._migrate([("urunler", "0006_faz2_index_names")])
        apps = self._apps(("urunler", "0006_faz2_index_names"))
        Urun = apps.get_model("urunler", "Urun")
        ted, kat, ayar, padmin = self._seed_katalog(apps, suffix="F7")

        u1 = Urun.objects.create(
            olusturan_firma=ted,
            ad="U1",
            kategori=kat,
            ayar=ayar,
            kimlik_sinifi="A",
            kimlik_anahtari="MIG-O2",
            platform_kodu="URN-M7-1",
            slug="u1-m7",
        )
        Urun.objects.filter(pk=u1.pk).update(
            onay_durumu="onayli",
            onaylayan_kullanici=padmin,
            onay_zamani=timezone.now(),
        )

        self._migrate([("urunler", "0007_o2_kimlik_uniq_reddedildi_haric")])
        apps7 = self._apps(("urunler", "0007_o2_kimlik_uniq_reddedildi_haric"))
        Urun7 = apps7.get_model("urunler", "Urun")
        u2 = Urun7.objects.create(
            olusturan_firma_id=ted.pk,
            ad="U2",
            kategori_id=kat.pk,
            ayar_id=ayar.pk,
            kimlik_sinifi="C",
            kimlik_anahtari="",
            platform_kodu="URN-M7-2",
            slug="u2-m7",
        )
        Urun7.objects.filter(pk=u2.pk).update(
            kimlik_sinifi="A",
            kimlik_anahtari="MIG-O2",
            onay_durumu="reddedildi",
            red_nedeni="eski",
        )
        self.assertEqual(Urun7.objects.filter(kimlik_anahtari="MIG-O2").count(), 2)

    def test_reverse_ok_without_collision(self):
        self._migrate([("urunler", "0007_o2_kimlik_uniq_reddedildi_haric")])
        self._migrate([("urunler", "0006_faz2_index_names")])

    def test_reverse_raises_on_collision(self):
        self._migrate([("urunler", "0007_o2_kimlik_uniq_reddedildi_haric")])
        apps = self._apps(("urunler", "0007_o2_kimlik_uniq_reddedildi_haric"))
        Urun = apps.get_model("urunler", "Urun")
        ted, kat, ayar, padmin = self._seed_katalog(apps, suffix="R7")

        u1 = Urun.objects.create(
            olusturan_firma=ted,
            ad="A1",
            kategori=kat,
            ayar=ayar,
            kimlik_sinifi="C",
            kimlik_anahtari="",
            platform_kodu="URN-R7-1",
            slug="a1-r7",
        )
        Urun.objects.filter(pk=u1.pk).update(
            kimlik_sinifi="B",
            kimlik_anahtari="REV-COLL",
            onay_durumu="onayli",
            onaylayan_kullanici=padmin,
            onay_zamani=timezone.now(),
        )
        u2 = Urun.objects.create(
            olusturan_firma=ted,
            ad="A2",
            kategori=kat,
            ayar=ayar,
            kimlik_sinifi="C",
            kimlik_anahtari="",
            platform_kodu="URN-R7-2",
            slug="a2-r7",
        )
        Urun.objects.filter(pk=u2.pk).update(
            kimlik_sinifi="B",
            kimlik_anahtari="REV-COLL",
            onay_durumu="reddedildi",
            red_nedeni="x",
        )

        with self.assertRaises(RuntimeError) as ctx:
            self._migrate([("urunler", "0006_faz2_index_names")])
        self.assertIn("Satır silinmedi", str(ctx.exception))
        self.assertNotIn("REV-COLL", str(ctx.exception))
