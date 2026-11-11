"""F4-090 — Transactional outbox: rollback siler; process at-least-once."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase

from firmalar.models import OutboxMessage
from firmalar.services import outbox_servisi
from firmalar.services.audit_servisi import domain_atomic
from siparis.models import Order
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class OutboxEnqueueGuardTests(TestCase):
    def test_enqueue_outside_domain_atomic_fails(self):
        with self.assertRaises(ValidationError):
            outbox_servisi.enqueue(event_type="x.y", payload={})


class OutboxRollbackTests(TransactionTestCase):
    def test_rollback_removes_outbox_row(self):
        with self.assertRaises(RuntimeError):
            with domain_atomic():
                outbox_servisi.enqueue(
                    event_type="test.rollback", payload={"n": 1}
                )
                raise RuntimeError("boom")
        self.assertFalse(
            OutboxMessage.objects.filter(event_type="test.rollback").exists()
        )

    def test_commit_keeps_outbox_row(self):
        with domain_atomic():
            outbox_servisi.enqueue(
                event_type="test.commit", payload={"n": 2}
            )
        self.assertEqual(
            OutboxMessage.objects.filter(
                event_type="test.commit", durum=OutboxMessage.Durum.PENDING
            ).count(),
            1,
        )


class OutboxProcessTests(TestCase):
    def test_process_pending_marks_processed_idempotent(self):
        outbox_servisi.register_ack_handler("test.process")
        with domain_atomic():
            msg = outbox_servisi.enqueue(
                event_type="test.process", payload={"a": 1}
            )
        r1 = outbox_servisi.process_pending(limit=10)
        self.assertEqual(r1["processed"], 1)
        msg.refresh_from_db()
        self.assertEqual(msg.durum, OutboxMessage.Durum.PROCESSED)
        self.assertIsNotNone(msg.processed_at)

        r2 = outbox_servisi.process_pending(limit=10)
        self.assertEqual(r2["processed"], 0)
        self.assertEqual(
            OutboxMessage.objects.filter(
                event_type="test.process",
                durum=OutboxMessage.Durum.PROCESSED,
            ).count(),
            1,
        )

    def test_unknown_event_fails_not_processed(self):
        with domain_atomic():
            msg = outbox_servisi.enqueue(
                event_type="test.unknown.no_handler", payload={}
            )
        r = outbox_servisi.process_pending(limit=10)
        self.assertEqual(r["failed"], 1)
        self.assertEqual(r["processed"], 0)
        msg.refresh_from_db()
        self.assertEqual(msg.durum, OutboxMessage.Durum.FAILED)
        self.assertIn("no handler", msg.last_error)


class OutboxOrderIntegrationTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def test_order_create_enqueues_order_created(self):
        self._quote_and_cart(miktar=Decimal("1"))
        co = checkout_servisi.checkout(
            actor=self.buyer, idempotency_key="outbox-ord-1"
        )
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        self.assertEqual(order.durum, Order.Durum.OLUSTURULDU)
        msg = OutboxMessage.objects.get(event_type="order.created")
        self.assertEqual(msg.durum, OutboxMessage.Durum.PENDING)
        self.assertEqual(msg.payload.get("order_id"), order.pk)

        result = outbox_servisi.process_pending(limit=5)
        self.assertGreaterEqual(result["processed"], 1)
        msg.refresh_from_db()
        self.assertEqual(msg.durum, OutboxMessage.Durum.PROCESSED)
