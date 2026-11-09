"""F7-021…024 — ERP/CRM/EDI/connector iskelet testleri."""

from django.test import TestCase, override_settings

from firmalar.models import OutboxMessage
from firmalar.role_permissions import seed_role_permissions
from integrations.crm.fake import FakeCRMAdapter
from integrations.crm.port import CRMSyncRequest
from integrations.edi.punchout import (
    process_inbound_punchout,
    reset_punchout_cache_for_tests,
)
from integrations.erp.fake import FakeERPAdapter
from integrations.erp.port import ERPSyncRequest
from integrations.registry import get_registry, reset_registry_for_tests
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class ConnectorRegistryTests(TestCase):
    def setUp(self):
        reset_registry_for_tests()

    def test_payment_and_carrier_registered(self):
        reg = get_registry()
        self.assertIn("payment", reg.names())
        self.assertIn("carrier", reg.names())
        self.assertIn("erp", reg.names())
        payment = reg.get("payment")
        self.assertIsNotNone(payment)


class FakeERPTests(TestCase):
    def test_roundtrip(self):
        erp = FakeERPAdapter()
        res = erp.push_order(
            ERPSyncRequest(
                entity_type="Order",
                entity_id="42",
                payload={"lines": 1},
            )
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.external_ref, "ERP-Order-42")
        self.assertEqual(len(erp.calls), 1)


class FakeCRMTests(TestCase):
    def test_opt_in_off_skips(self):
        crm = FakeCRMAdapter(enabled=False)
        r = crm.sync(
            CRMSyncRequest(firma_id=1, event="firma.updated", payload={})
        )
        self.assertTrue(r.ok)
        self.assertTrue(r.skipped)

    @override_settings(CRM_SYNC_ENABLED=True)
    def test_opt_in_on(self):
        crm = FakeCRMAdapter(enabled=True)
        r = crm.sync(
            CRMSyncRequest(firma_id=1, event="firma.updated", payload={})
        )
        self.assertTrue(r.ok)
        self.assertFalse(r.skipped)


class PunchoutTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()

    def setUp(self):
        reset_punchout_cache_for_tests()

    def test_inbound_masks_and_idempotent(self):
        r1 = process_inbound_punchout(
            actor=self.buyer,
            firma=self.alici,
            message_id="msg-punch-001",
            payload={
                "item": "ring",
                "tedarikci_id": 999,
                "maliyet": "1",
            },
        )
        self.assertEqual(r1["status"], "accepted")
        self.assertTrue(r1["masked"])
        self.assertTrue(
            OutboxMessage.objects.filter(
                event_type="edi.punchout.inbound"
            ).exists()
        )
        r2 = process_inbound_punchout(
            actor=self.buyer,
            firma=self.alici,
            message_id="msg-punch-001",
            payload={"item": "ring", "tedarikci_id": 1},
        )
        self.assertEqual(r2["status"], "duplicate")
