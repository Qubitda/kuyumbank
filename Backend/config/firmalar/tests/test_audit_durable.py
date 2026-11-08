"""record_audit_durable: domain_atomic içinde net hata; dışında yazar."""

from django.test import TransactionTestCase

from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.audit_servisi import domain_atomic, record_audit_durable
from firmalar.services.platform_kurulum import ensure_platform_firma


class AuditDurableTests(TransactionTestCase):
    def setUp(self):
        seed_role_permissions()
        ensure_platform_firma()

    def test_writes_outside_domain_atomic(self):
        row = record_audit_durable(
            actor=None, action="test.ok", success=False, reason="x"
        )
        self.assertTrue(AuditOlay.objects.filter(pk=row.pk).exists())

    def test_inside_domain_atomic_raises(self):
        with self.assertRaises(RuntimeError) as ctx:
            with domain_atomic():
                record_audit_durable(
                    actor=None,
                    action="test.nested",
                    success=False,
                    reason="nested",
                )
        self.assertIn("domain_atomic", str(ctx.exception))
