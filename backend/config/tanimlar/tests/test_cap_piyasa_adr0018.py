"""ADR-0018 CAP-PIYASA — kaynak, LKG, çapraz, feed, batch, guardrail."""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import FiyatBatchIslek, FiyatBatchSatir
from fiyatlama.services import fiyat_batch_servisi, guardrail_servisi, pricing_service
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from tanimlar.fiyat_kaynagi import FeedHealth, FiyatKaynagi
from tanimlar.models import KurTipi, MetalKuru
from tanimlar.services import kur_servisi
from tanimlar.services.capraz_sanity import capraz_makas_kontrol
from tanimlar.services.feed_adapters import sync_binance_metal, troy_oz_to_gram_try
from tanimlar.services.kaynak_resolve import etkin_kaynak
from urunler.models import Urun

User = get_user_model()


class CapPiyasaAdr0018Tests(PriceQuoteFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        sync_user_role_groups(cls.finance)
        cls.kur_user = User(
            username="cap_kur",
            firma=cls.platform,
            rol=roles.PLATFORM_FINANCE,
            is_staff=True,
        )
        cls.kur_user.set_password("x")
        cls.kur_user.save()
        sync_user_role_groups(cls.kur_user)

    def test_etkin_kaynak_precedence(self):
        self.assertEqual(etkin_kaynak(urun=self.urun), FiyatKaynagi.CANLI_PIYASA)
        Urun.objects.filter(pk=self.urun.pk).update(
            fiyat_kaynagi=FiyatKaynagi.MANUEL_GIRIS
        )
        self.urun.refresh_from_db()
        self.assertEqual(etkin_kaynak(urun=self.urun), FiyatKaynagi.MANUEL_GIRIS)

    def test_stale_lkg_banner(self):
        now = timezone.now()
        MetalKuru.objects.filter(metal=self.metal).delete()
        stale = MetalKuru.objects.create(
            metal=self.metal,
            saglayici=self.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=now - timedelta(seconds=120),
            alinma_zamani=now - timedelta(seconds=120),
            saf_birim_fiyat=Decimal("4100.0000"),
            kaynak="api",
        )
        from tanimlar.models import KurTaraf

        detay = kur_servisi.resolve_metal_kuru_detay(
            self.metal, taraf=KurTaraf.ALICI, now=now
        )
        self.assertTrue(detay.is_lkg)
        self.assertEqual(detay.feed_health, FeedHealth.FEED_STALE_LKG)
        self.assertEqual(detay.gozlem.pk, stale.pk)
        self.assertIn("LKG", detay.banner)
        pol = kur_servisi.get_or_create_politikasi()
        self.assertEqual(pol.feed_health, FeedHealth.FEED_STALE_LKG)

    def test_capraz_sanity_red(self):
        r = capraz_makas_kontrol(
            xauusdt=Decimal("2000"),
            usdttry=Decimal("40"),
            tcmb_usdtry=Decimal("30"),
            esik_yuzde=Decimal("2"),
        )
        self.assertFalse(r.ok)

    def test_troy_quantize(self):
        g = troy_oz_to_gram_try(oz_try=Decimal("3110.35"))
        self.assertEqual(g, Decimal("100.000000"))

    def test_sync_binance_inject(self):
        MetalKuru.objects.filter(metal=self.metal, kaynak="api").delete()
        now_before = timezone.now()
        obj = sync_binance_metal(
            metal=self.metal,
            actor=self.kur_user,
            xauusdt=Decimal("2000"),
            usdttry=Decimal("34"),
            skip_capraz=True,
        )
        self.assertEqual(obj.kaynak, "api")
        self.assertGreater(obj.saf_birim_fiyat, 0)
        self.assertGreaterEqual(obj.zaman, now_before)

    def test_guardrail_blocks_under_cost(self):
        r = guardrail_servisi.assert_marj_guardrail(
            toplam_vergisiz=Decimal("100.00"),
            maliyet_referans=Decimal("150.00"),
        )
        self.assertFalse(r.ok)

    def test_batch_dry_run_and_publish_freeze(self):
        v = self.varyant
        hedef = {v.pk: Decimal("1500.00")}
        islek = fiyat_batch_servisi.dry_run_manuel_freeze(
            actor=self.kur_user,
            filtre={"varyant_ids": [v.pk]},
            hedef_fiyatlar=hedef,
        )
        self.assertEqual(islek.durum, FiyatBatchIslek.Durum.DRY_RUN)
        self.assertEqual(islek.tip, FiyatBatchIslek.Tip.MANUEL_FREEZE)
        satir = islek.satirlar.get()
        self.assertEqual(satir.sonuc, FiyatBatchSatir.Sonuc.ADAY)
        published = fiyat_batch_servisi.publish(actor=self.kur_user, islek=islek)
        self.assertEqual(published.durum, FiyatBatchIslek.Durum.YAYINLANDI)
        v.refresh_from_db()
        self.assertEqual(v.sabit_fiyat, Decimal("1500.00"))
        self.urun.refresh_from_db()
        self.assertEqual(self.urun.fiyat_tipi, "sabit")
        self.assertEqual(self.urun.fiyat_kaynagi, FiyatKaynagi.MANUEL_GIRIS)

    def test_quote_includes_feed_meta(self):
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        self.assertIn("etkin_fiyat_kaynagi", pq.hesap_girdisi)
        self.assertIn("feed_health", pq.hesap_girdisi)
