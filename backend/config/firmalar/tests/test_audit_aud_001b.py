"""AUD-001b — AuditOlay ip_address / changes + sidecar kolon sync."""

from django.db import transaction
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings

from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.audit_servisi import (
    client_ip,
    record_audit,
    record_audit_durable,
)
from firmalar.services.platform_kurulum import ensure_platform_firma
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class Audit001bFieldsTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def test_record_audit_stores_ip_and_changes(self):
        row = record_audit(
            actor=self.buyer,
            action="aud001b.create",
            entity_type="Test",
            entity_id="1",
            ip_address="203.0.113.10",
            changes={"durum": {"old": "TASLAK", "new": "AKTIF"}},
        )
        row.refresh_from_db()
        self.assertEqual(row.ip_address, "203.0.113.10")
        self.assertEqual(row.changes["durum"]["new"], "AKTIF")

    def test_record_audit_defaults_empty_changes(self):
        row = record_audit(
            actor=self.buyer, action="aud001b.empty", entity_type="T", entity_id="2"
        )
        self.assertIsNone(row.ip_address)
        self.assertEqual(row.changes, {})

    @override_settings(TRUSTED_PROXY_COUNT=0)
    def test_client_ip_remote_only(self):
        req = RequestFactory().get("/", REMOTE_ADDR="198.51.100.1")
        req.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.9, 198.51.100.1"
        self.assertEqual(client_ip(req), "198.51.100.1")

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_client_ip_trusted_proxy(self):
        req = RequestFactory().get("/", REMOTE_ADDR="10.0.0.1")
        req.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.9, 10.0.0.1"
        self.assertEqual(client_ip(req), "203.0.113.9")


class Audit001bSidecarTests(TransactionTestCase):
    def setUp(self):
        seed_role_permissions()
        ensure_platform_firma()

    def test_sidecar_persists_ip_and_changes(self):
        marker = "aud001b-sidecar"
        try:
            with transaction.atomic():
                row = record_audit_durable(
                    actor=None,
                    action=marker,
                    success=False,
                    reason="outer",
                    ip_address="192.0.2.55",
                    changes={"field": "x"},
                )
                pk = row.pk
                raise RuntimeError("force rollback")
        except RuntimeError:
            pass

        saved = AuditOlay.objects.get(pk=pk)
        self.assertEqual(saved.ip_address, "192.0.2.55")
        self.assertEqual(saved.changes, {"field": "x"})
        self.assertFalse(saved.success)
