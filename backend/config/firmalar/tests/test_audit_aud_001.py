"""AUD-001 — AuditOlay immutability (instance + QuerySet)."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from firmalar.models import AuditOlay
from firmalar.services.audit_servisi import record_audit
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class AuditOlayImmutabilityTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def test_create_ok(self):
        row = record_audit(
            actor=self.buyer,
            action="aud001.create",
            entity_type="Test",
            entity_id="1",
            success=True,
        )
        self.assertTrue(AuditOlay.objects.filter(pk=row.pk).exists())

    def test_instance_update_forbidden(self):
        row = record_audit(
            actor=self.buyer, action="aud001.upd", entity_type="T", entity_id="1"
        )
        row.reason = "mutated"
        with self.assertRaises(ValidationError):
            row.save()

    def test_instance_delete_forbidden(self):
        row = record_audit(
            actor=self.buyer, action="aud001.del", entity_type="T", entity_id="1"
        )
        with self.assertRaises(ValidationError):
            row.delete()
        self.assertTrue(AuditOlay.objects.filter(pk=row.pk).exists())

    def test_queryset_update_forbidden(self):
        record_audit(
            actor=self.buyer, action="aud001.qsu", entity_type="T", entity_id="1"
        )
        with self.assertRaises(ValidationError):
            AuditOlay.objects.filter(action="aud001.qsu").update(reason="x")

    def test_queryset_delete_forbidden(self):
        row = record_audit(
            actor=self.buyer, action="aud001.qsd", entity_type="T", entity_id="1"
        )
        with self.assertRaises(ValidationError):
            AuditOlay.objects.filter(pk=row.pk).delete()
        self.assertTrue(AuditOlay.objects.filter(pk=row.pk).exists())
