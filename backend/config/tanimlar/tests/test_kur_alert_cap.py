"""CAP-ALERT — eşik outbox; stale’de yok; checkout bozulmaz; komut."""

from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import OutboxMessage
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.services import pricing_service
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from tanimlar.models import KurAlertKurali, KurTipi, MetalKuru
from tanimlar.services import kur_alert_servisi

User = get_user_model()


class KurAlertCapTests(PriceQuoteFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        seed_role_permissions()
        cls.kur_user = User(
            username="alert_kur",
            firma=cls.platform,
            rol=roles.PLATFORM_FINANCE,
            is_staff=True,
        )
        cls.kur_user.set_password("x")
        cls.kur_user.save()
        sync_user_role_groups(cls.kur_user)

    def test_fresh_threshold_enqueues(self):
        now = timezone.now()
        MetalKuru.objects.filter(metal=self.metal, kur_tipi=KurTipi.SATIS).delete()
        goz = MetalKuru.objects.create(
            metal=self.metal,
            saglayici=self.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=now,
            alinma_zamani=now,
            saf_birim_fiyat=Decimal("5000.0000"),
            kaynak="api",
        )
        kural = kur_alert_servisi.kural_olustur(
            actor=self.kur_user,
            metal=self.metal,
            esik_fiyat=Decimal("4500.0000"),
            yon=KurAlertKurali.Yon.YUKARI,
        )
        rows = kur_alert_servisi.degerlendir(now=now)
        self.assertEqual(len(rows), 1)
        self.assertTrue(
            OutboxMessage.objects.filter(
                event_type="kur.alert", payload__kural_id=kural.pk
            ).exists()
        )
        # Aynı gözlem tekrar tetiklemez
        self.assertEqual(kur_alert_servisi.degerlendir(now=now), [])
        self.assertEqual(goz.saf_birim_fiyat, Decimal("5000.0000"))

    def test_stale_no_alert(self):
        now = timezone.now()
        eski = now - timedelta(seconds=120)
        MetalKuru.objects.filter(metal=self.metal, kur_tipi=KurTipi.SATIS).delete()
        MetalKuru.objects.create(
            metal=self.metal,
            saglayici=self.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=eski,
            alinma_zamani=eski,
            saf_birim_fiyat=Decimal("9000.0000"),
            kaynak="api",
        )
        kur_alert_servisi.kural_olustur(
            actor=self.kur_user,
            metal=self.metal,
            esik_fiyat=Decimal("1000.0000"),
            yon=KurAlertKurali.Yon.YUKARI,
        )
        self.assertEqual(kur_alert_servisi.degerlendir(now=now), [])
        self.assertFalse(OutboxMessage.objects.filter(event_type="kur.alert").exists())

    def test_checkout_path_unaffected(self):
        """Alert servisi quote/checkout’u bozmaz."""
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        self.assertGreater(pq.toplam_vergisiz, 0)

    def test_evaluate_kur_alerts_command(self):
        now = timezone.now()
        MetalKuru.objects.filter(metal=self.metal, kur_tipi=KurTipi.SATIS).delete()
        MetalKuru.objects.create(
            metal=self.metal,
            saglayici=self.saglayici,
            kur_tipi=KurTipi.SATIS,
            zaman=now,
            alinma_zamani=now,
            saf_birim_fiyat=Decimal("5000.0000"),
            kaynak="api",
        )
        kur_alert_servisi.kural_olustur(
            actor=self.kur_user,
            metal=self.metal,
            esik_fiyat=Decimal("4500.0000"),
            yon=KurAlertKurali.Yon.YUKARI,
        )
        out = StringIO()
        call_command(
            "evaluate_kur_alerts",
            f"--now={now.isoformat()}",
            stdout=out,
        )
        self.assertIn("tetik=1", out.getvalue())
        self.assertTrue(
            OutboxMessage.objects.filter(event_type="kur.alert").exists()
        )
        call_command("process_outbox", stdout=StringIO())
        msg = OutboxMessage.objects.get(event_type="kur.alert")
        self.assertEqual(msg.durum, OutboxMessage.Durum.PROCESSED)
