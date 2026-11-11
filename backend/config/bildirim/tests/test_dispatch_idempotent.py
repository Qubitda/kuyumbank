from django.test import TestCase

from bildirim.models import EmailDelivery, RecipientSettings
from bildirim.services import dispatch_servisi, seed_servisi
from firmalar import roles
from firmalar.models import Firma, Kullanici
from firmalar.services import outbox_servisi
from firmalar.services.audit_servisi import domain_atomic
from firmalar.services.outbox_servisi import process_pending


class DispatchIdempotentTests(TestCase):
    def setUp(self):
        seed_servisi.seed_templates_and_rules()
        dispatch_servisi.register_outbox_handlers()
        self.firma = Firma.objects.create(
            ad="Alıcı A",
            firma_kodu="ALCA",
            vergi_no="1111111111",
            alici_mi=True,
            onay_durumu="onayli",
            aktif=True,
        )
        self.user = Kullanici.objects.create_user(
            username="alici1",
            email="alici1@example.com",
            password="x",
            firma=self.firma,
            rol=roles.ALICI_SATINALMACI,
        )
        rs, _ = RecipientSettings.objects.get_or_create(pk=1)
        rs.admin_notify_emails = ["admin@example.com"]
        rs.save()

    def test_outbox_creates_delivery_once(self):
        with domain_atomic():
            outbox_servisi.enqueue(
                event_type="order.created",
                payload={
                    "order_id": 99,
                    "alici_firma_id": self.firma.pk,
                    "line_count": 2,
                },
            )
        stats = process_pending(limit=10)
        self.assertEqual(stats["processed"], 1)
        qs = EmailDelivery.objects.filter(event_type="order.created", order_id=99)
        self.assertGreaterEqual(qs.count(), 1)
        first_count = qs.count()

        # Aynı payload tekrar → yeni outbox; idempotency_key çakışması → ek satır yok
        with domain_atomic():
            outbox_servisi.enqueue(
                event_type="order.created",
                payload={
                    "order_id": 99,
                    "alici_firma_id": self.firma.pk,
                    "line_count": 2,
                },
            )
        process_pending(limit=10)
        self.assertEqual(
            EmailDelivery.objects.filter(event_type="order.created", order_id=99).count(),
            first_count,
        )

    def test_create_deliveries_direct_idempotent(self):
        d1 = dispatch_servisi.create_deliveries_for_event(
            event_type="firma.approved",
            payload={
                "firma_id": self.firma.pk,
                "alici_firma_id": self.firma.pk,
                "firma_adi": self.firma.ad,
                "firma_kodu": self.firma.firma_kodu,
            },
        )
        d2 = dispatch_servisi.create_deliveries_for_event(
            event_type="firma.approved",
            payload={
                "firma_id": self.firma.pk,
                "alici_firma_id": self.firma.pk,
                "firma_adi": self.firma.ad,
                "firma_kodu": self.firma.firma_kodu,
            },
        )
        self.assertGreaterEqual(len(d1), 1)
        self.assertEqual(len(d2), 0)
