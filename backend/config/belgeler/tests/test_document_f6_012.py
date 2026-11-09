"""F6-012 — Document + taş sertifika bağı; tenant izolasyon."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from belgeler.models import Document, TasSertifikaBelgesi
from belgeler.selectors.tenant import DocumentNotFound, get_document_for_actor
from belgeler.services import document_servisi
from firmalar import roles
from firmalar.models import AuditOlay, Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import TeklifTasMaliyeti
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from urunler.models import UrunTasi

User = get_user_model()


class DocumentF6012Tests(PriceQuoteFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.catalog = User(
            username="doc_cat",
            firma=cls.platform,
            rol=roles.PLATFORM_CATALOG,
            is_staff=True,
        )
        cls.catalog.set_password("x")
        cls.catalog.save()
        sync_user_role_groups(cls.catalog)

        cls.ted_user = User(
            username="doc_ted",
            firma=cls.ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        cls.ted_user.set_password("x")
        cls.ted_user.save()
        sync_user_role_groups(cls.ted_user)

        cls.buyer = User(
            username="doc_buyer",
            firma=cls.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)

        # Katalog taş satırı (urun fixture'dan)
        from urunler.models import TasTipi

        tip, _ = TasTipi.objects.get_or_create(
            ad="PırlantaDoc",
            defaults={"degerli": True},
        )
        if not tip.degerli:
            tip.degerli = True
            tip.save(update_fields=["degerli"])
        cls.urun_tasi = UrunTasi.objects.create(
            urun=cls.urun,
            tas_tipi=tip,
            adet=1,
            karat=Decimal("1.000"),
            bedel=Decimal("100.00"),
        )

        cls.teklif_tas = TeklifTasMaliyeti.objects.create(
            teklif=cls.teklif,
            tas_grubu=TeklifTasMaliyeti.TasGrubu.PIRLANTA,
            adet=1,
            toplam_karat=Decimal("1.0000"),
            bedel=Decimal("50.00"),
            sertifika_kurumu="GIA",
            sertifika_no="GIA-OFFER-1",
        )

    def test_katalog_sertifika_platform(self):
        bag = document_servisi.olustur_tas_sertifika(
            actor=self.catalog,
            firma=self.platform,
            baslik="GIA katalog",
            storage_key="certs/katalog/gia-1.pdf",
            urun_tasi=self.urun_tasi,
            content_type="application/pdf",
            byte_size=1024,
        )
        self.assertEqual(bag.document.tip, Document.Tip.TAS_SERTIFIKA)
        self.assertEqual(bag.urun_tasi_id, self.urun_tasi.pk)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="belgeler.tas_sertifika.created",
                entity_id=str(bag.pk),
                success=True,
            ).exists()
        )

    def test_teklif_sertifika_tedarikci(self):
        bag = document_servisi.olustur_tas_sertifika(
            actor=self.ted_user,
            firma=self.ted,
            baslik="GIA teklif",
            storage_key="certs/ted/gia-2.pdf",
            teklif_tas=self.teklif_tas,
        )
        self.assertEqual(bag.teklif_tas_id, self.teklif_tas.pk)
        # Tedarikçi kendi belgesini görür
        doc = get_document_for_actor(self.ted_user, document_id=bag.document_id)
        self.assertEqual(doc.pk, bag.document_id)

    def test_tenant_isolation(self):
        bag = document_servisi.olustur_tas_sertifika(
            actor=self.ted_user,
            firma=self.ted,
            baslik="gizli",
            storage_key="certs/ted/secret.pdf",
            teklif_tas=self.teklif_tas,
        )
        with self.assertRaises(DocumentNotFound):
            get_document_for_actor(self.buyer, document_id=bag.document_id)
        # Başka tedarikçi
        other_ted = Firma.objects.create(
            ad="Other Ted", firma_kodu="OTTED", tedarikci_mi=True
        )
        other_user = User(
            username="other_ted",
            firma=other_ted,
            rol=roles.TEDARIKCI_SAHIP,
            is_staff=True,
        )
        other_user.set_password("x")
        other_user.save()
        sync_user_role_groups(other_user)
        with self.assertRaises(DocumentNotFound):
            get_document_for_actor(other_user, document_id=bag.document_id)

    def test_buyer_denied_create(self):
        with self.assertRaises(PermissionDenied):
            document_servisi.olustur_tas_sertifika(
                actor=self.buyer,
                firma=self.platform,
                baslik="x",
                storage_key="x",
                urun_tasi=self.urun_tasi,
            )

    def test_teklif_firma_mismatch(self):
        with self.assertRaises(ValidationError):
            document_servisi.olustur_tas_sertifika(
                actor=self.catalog,
                firma=self.platform,  # teklif tedarikçisi değil
                baslik="bad",
                storage_key="bad",
                teklif_tas=self.teklif_tas,
            )

    def test_immutable(self):
        bag = document_servisi.olustur_tas_sertifika(
            actor=self.catalog,
            firma=self.platform,
            baslik="imm",
            storage_key="certs/imm.pdf",
            urun_tasi=self.urun_tasi,
        )
        with self.assertRaises(ValidationError):
            bag.document.baslik = "hack"
            bag.document.save()
