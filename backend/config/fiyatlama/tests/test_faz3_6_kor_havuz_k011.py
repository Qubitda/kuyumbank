"""Dilim 3.6 — K-011 TeklifTasMaliyeti + kör havuz / B-02 alıcı quote görünürlüğü."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.admin.admin import PriceQuoteAdmin, TeklifTasMaliyetiAdmin
from fiyatlama.models import (
    FiyatSozlesmesi,
    FiyatSozlesmesiKalemi,
    PriceQuote,
    PriceQuoteLine,
    TedarikciTeklif,
    TeklifTasMaliyeti,
)
from fiyatlama.selectors.buyer_quote import (
    BuyerQuoteNotFound,
    assert_buyer_cannot_see_internal,
    get_buyer_quote_view,
    get_quote_for_actor,
    present_buyer_quote,
)
from fiyatlama.selectors.tenant import (
    scope_price_quote_line_queryset,
    scope_price_quote_queryset,
    scope_teklif_tas_maliyeti_queryset,
)
from fiyatlama.services import pricing_service, sozlesme_servisi
from tanimlar.models import (
    AyarMilyem,
    FiyatGrubu,
    KiymetliMetal,
    KurPolitikasi,
    KurSaglayici,
    KurTipi,
    MetalKuru,
    SatisKanali,
)
from urunler.models import Kategori, Urun, UrunTasi as KatalogUrunTasi, Varyant
from urunler.models import TasTipi

User = get_user_model()


class Faz36KorHavuzK011Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.platform = ensure_platform_firma()
        cls.alici_a = Firma.objects.create(
            ad="K6A", firma_kodu="K6A", alici_mi=True
        )
        cls.alici_b = Firma.objects.create(
            ad="K6B", firma_kodu="K6B", alici_mi=True
        )
        cls.ted = Firma.objects.create(
            ad="K6T", firma_kodu="K6T", tedarikci_mi=True
        )

        cls.finance = User(
            username="k6_fin",
            firma=cls.platform,
            rol=roles.PLATFORM_FINANCE,
            is_staff=True,
        )
        cls.finance.set_password("x")
        cls.finance.save()
        sync_user_role_groups(cls.finance)

        cls.buyer_a = User(
            username="k6_ba",
            firma=cls.alici_a,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.buyer_a.set_password("x")
        cls.buyer_a.save()
        sync_user_role_groups(cls.buyer_a)

        cls.buyer_b = User(
            username="k6_bb",
            firma=cls.alici_b,
            rol=roles.ALICI_YONETICI,
            is_staff=True,
        )
        cls.buyer_b.set_password("x")
        cls.buyer_b.save()
        sync_user_role_groups(cls.buyer_b)

        cls.supplier = User(
            username="k6_ted",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.supplier.set_password("x")
        cls.supplier.save()
        sync_user_role_groups(cls.supplier)

        cls.metal = KiymetliMetal.objects.create(
            kod="AUK6", ad="AltınK6", gram_bazli=True
        )
        cls.ayar = AyarMilyem.objects.create(
            metal=cls.metal,
            ayar_kodu="14K6",
            ayar_degeri=14,
            milyem=Decimal("0.585"),
        )
        grup = FiyatGrubu.objects.create(kod="K6G", ad="K6G")
        kat = Kategori.objects.create(kod="K6K", ad="K6", fiyat_grubu=grup)
        cls.kanal = SatisKanali.objects.create(
            kod="K6CH", ad="K6CH", quote_ttl_saniye=30
        )

        KurSaglayici.objects.filter(aktif=True).update(aktif=False)
        cls.saglayici = KurSaglayici.objects.create(
            kod="K6P", ad="K6P", aktif=True, max_gecikme_saniye=60
        )
        KurPolitikasi.objects.get_or_create(
            anahtar="default",
            defaults={
                "alici_kur_tipi": KurTipi.SATIS,
                "tedarikci_kur_tipi": KurTipi.ALIS,
            },
        )
        now = timezone.now()
        MetalKuru.objects.create(
            metal=cls.metal,
            saglayici=cls.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=now,
            alinma_zamani=now,
            saf_birim_fiyat=Decimal("4000.0000"),
            kaynak="api",
        )
        MetalKuru.objects.create(
            metal=cls.metal,
            saglayici=cls.saglayici,
            kur_tipi=KurTipi.ALIS,
            zaman=now,
            alinma_zamani=now,
            saf_birim_fiyat=Decimal("3900.0000"),
            kaynak="api",
        )

        urun = Urun.objects.create(
            olusturan_firma=cls.platform,
            ad="K6 Ürün",
            kategori=kat,
            ayar=cls.ayar,
        )
        Urun.objects.filter(pk=urun.pk).update(
            onay_durumu="onayli",
            yayin_durumu="aktif",
            onaylayan_kullanici=cls.finance,
            onay_zamani=now,
        )
        urun.refresh_from_db()
        cls.urun = urun
        cls.varyant = Varyant.objects.create(
            urun=urun, gram=Decimal("2.500"), ek_bedel=Decimal("10.00")
        )

        # Katalog taşı (urunler.UrunTasi) — vitrin; quote hesabına girmez
        tip = TasTipi.objects.create(kod="K6PIR", ad="Pırlanta", degerli=True)
        KatalogUrunTasi.objects.create(
            urun=urun, tas_tipi=tip, adet=1, karat=Decimal("0.300"), bedel=Decimal("999")
        )

        bas, bit = date.today(), date.today() + timedelta(days=60)
        soz = FiyatSozlesmesi.objects.create(
            firma=cls.alici_a,
            kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
            satis_kanali=cls.kanal,
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
            durum=FiyatSozlesmesi.Durum.TASLAK,
            olusturan_kullanici=cls.finance,
            versiyon=1,
        )
        FiyatSozlesmesiKalemi.objects.create(
            sozlesme=soz,
            metal=cls.metal,
            ayar=cls.ayar,
            marj_tipi=FiyatSozlesmesiKalemi.MarjTipi.TL_PARCA,
            marj_degeri=Decimal("50.00"),
            iscilik=Decimal("100.00"),
        )
        sozlesme_servisi.aktif_yap(soz, cls.finance)

        cls.teklif = TedarikciTeklif.objects.create(
            varyant=cls.varyant,
            tedarikci=cls.ted,
            tedarikci_kodu="K6T1",
            fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
            gram=Decimal("2.500"),
            durum=TedarikciTeklif.Durum.YAYINDA,
            gecerlilik_baslangic=bas,
            gecerlilik_bitis=bit,
            eslestirme_durumu="onaylandi",
            hedef_urun=cls.urun,
            oncelik=10,
            iscilik_override=Decimal("80.00"),
        )
        # Teklif taş maliyeti (K-011)
        cls.tas_maliyet = TeklifTasMaliyeti.objects.create(
            teklif=cls.teklif,
            tas_grubu=TeklifTasMaliyeti.TasGrubu.PIRLANTA,
            adet=1,
            toplam_karat=Decimal("0.2500"),
            bedel=Decimal("200.00"),
            para_birimi="TRY",
        )

        cls.quote = pricing_service.quote(
            alici_firma=cls.alici_a,
            satis_kanali=cls.kanal,
            varyant=cls.varyant,
            kullanici=cls.finance,
        )

    # --- K-011 ---

    def test_k011_two_models_distinct(self):
        self.assertTrue(KatalogUrunTasi.objects.filter(urun=self.urun).exists())
        self.assertTrue(
            TeklifTasMaliyeti.objects.filter(teklif=self.teklif).exists()
        )
        # Katalog bedeli quote toplamına eklenmez (yalnız teklif taş + varyant ek)
        # metal 5850 + isc 80 + marj 50 + tas 200 + ek 10 = 6190
        self.assertEqual(self.quote.toplam_vergisiz, Decimal("6190.00"))
        self.assertNotEqual(
            KatalogUrunTasi.objects.get(urun=self.urun).bedel,
            self.tas_maliyet.bedel,
        )

    def test_k011_no_deprecated_uruntasi_alias(self):
        import fiyatlama.models as fm

        self.assertFalse(hasattr(fm, "UrunTasi"))
        self.assertTrue(hasattr(fm, "TeklifTasMaliyeti"))

    # --- Kör havuz / B-02 ---

    def test_buyer_sees_safe_quote_view(self):
        view = get_buyer_quote_view(self.buyer_a, self.quote.pk)
        assert_buyer_cannot_see_internal(view)
        self.assertEqual(view["toplam_vergisiz"], self.quote.toplam_vergisiz)
        self.assertEqual(view["para_birimi"], "TRY")
        self.assertEqual(view["belge_turu"], PriceQuote.BelgeTuru.PROFORMA)
        self.assertIsNone(view["satirlar"])
        self.assertNotIn("teklif", view)
        self.assertEqual(view["urun"]["ad"], "K6 Ürün")

    def test_buyer_idor_other_firma_404(self):
        with self.assertRaises(BuyerQuoteNotFound):
            get_buyer_quote_view(self.buyer_b, self.quote.pk)
        with self.assertRaises(BuyerQuoteNotFound):
            get_quote_for_actor(self.buyer_b, self.quote.pk)

    def test_supplier_cannot_see_quote(self):
        qs = scope_price_quote_queryset(PriceQuote.objects.all(), self.supplier)
        self.assertFalse(qs.filter(pk=self.quote.pk).exists())
        with self.assertRaises(BuyerQuoteNotFound):
            get_quote_for_actor(self.supplier, self.quote.pk)

    def test_buyer_cannot_see_quote_lines(self):
        lines = scope_price_quote_line_queryset(
            PriceQuoteLine.objects.all(), self.buyer_a
        )
        self.assertFalse(lines.exists())
        self.assertTrue(
            PriceQuoteLine.objects.filter(quote=self.quote).exists()
        )

    def test_platform_sees_quote_and_lines(self):
        qs = scope_price_quote_queryset(PriceQuote.objects.all(), self.finance)
        self.assertTrue(qs.filter(pk=self.quote.pk).exists())
        lines = scope_price_quote_line_queryset(
            PriceQuoteLine.objects.all(), self.finance
        )
        self.assertTrue(lines.filter(quote=self.quote).exists())

    def test_supplier_own_tas_maliyeti_only(self):
        qs = scope_teklif_tas_maliyeti_queryset(
            TeklifTasMaliyeti.objects.all(), self.supplier
        )
        self.assertEqual(list(qs.values_list("pk", flat=True)), [self.tas_maliyet.pk])
        # Alıcı görmez
        qs_b = scope_teklif_tas_maliyeti_queryset(
            TeklifTasMaliyeti.objects.all(), self.buyer_a
        )
        self.assertFalse(qs_b.exists())

    def test_present_buyer_hides_supplier_identity(self):
        payload = present_buyer_quote(self.quote)
        blob = str(payload)
        self.assertNotIn(self.ted.ad, blob)
        self.assertNotIn(self.ted.firma_kodu, blob)
        self.assertNotIn("K6T1", blob)
        assert_buyer_cannot_see_internal(payload)

    def test_admin_buyer_fields_masked(self):
        site = AdminSite()
        ma = PriceQuoteAdmin(PriceQuote, site)
        rf = RequestFactory()
        req = rf.get("/admin/")
        req.user = self.buyer_a
        fields = ma.get_fields(req, self.quote)
        self.assertIn("toplam_vergisiz", fields)
        self.assertNotIn("teklif", fields)
        self.assertNotIn("hesap_girdisi", fields)
        self.assertNotIn("tedarikci_kalem", fields)
        self.assertEqual(ma.get_inline_instances(req, self.quote), [])

    def test_admin_platform_sees_internal(self):
        site = AdminSite()
        ma = PriceQuoteAdmin(PriceQuote, site)
        rf = RequestFactory()
        req = rf.get("/admin/")
        req.user = self.finance
        fields = ma.get_fields(req, self.quote)
        self.assertIn("teklif", fields)
        self.assertIn("hesap_girdisi", fields)
        self.assertTrue(len(ma.get_inline_instances(req, self.quote)) >= 1)

    def test_admin_buyer_no_tas_maliyeti_module(self):
        site = AdminSite()
        ma = TeklifTasMaliyetiAdmin(TeklifTasMaliyeti, site)
        rf = RequestFactory()
        req = rf.get("/admin/")
        req.user = self.buyer_a
        self.assertFalse(ma.has_module_permission(req))
