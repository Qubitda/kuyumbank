from django.core import mail
from django.test import TestCase, override_settings

from bildirim.models import EmailDelivery
from bildirim.services import manual_servisi, queue_servisi
from firmalar.models import Kullanici
from firmalar.services.platform_kurulum import ensure_platform_firma


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailQueueTests(TestCase):
    def setUp(self):
        self.firma = ensure_platform_firma()
        self.actor = Kullanici.objects.create_superuser(
            username="mailadmin",
            email="mailadmin@example.com",
            password="x",
            firma=self.firma,
        )

    def test_process_sends_pending(self):
        d = manual_servisi.enqueue_manual(
            actor=self.actor,
            to_emails=["buyer@example.com"],
            subject="Merhaba {{firma_adi}}",
            body_html="<p>{{firma_adi}}</p>",
            context={"firma_adi": "Acme"},
        )
        self.assertEqual(d.status, EmailDelivery.Status.PENDING)
        stats = queue_servisi.process_email_queue(limit=10)
        self.assertEqual(stats["sent"], 1)
        d.refresh_from_db()
        self.assertEqual(d.status, EmailDelivery.Status.SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Acme", mail.outbox[0].alternatives[0][0])

    def test_retry_failed(self):
        d = EmailDelivery.objects.create(
            to_emails=["x@y.com"],
            subject="s",
            body_html="<p>b</p>",
            status=EmailDelivery.Status.FAILED,
            attempts=5,
            error="boom",
            idempotency_key="retry-test-1",
            event_type="manual",
        )
        queue_servisi.retry_delivery(d)
        d.refresh_from_db()
        self.assertEqual(d.status, EmailDelivery.Status.PENDING)
        self.assertEqual(d.error, "")
