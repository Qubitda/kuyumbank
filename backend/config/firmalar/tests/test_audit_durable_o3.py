"""Faz 2.1 O3 — record_audit_durable dış atomic içinde sidecar kalıcılığı."""

from django.db import transaction
from django.test import TransactionTestCase

from firmalar.models import AuditOlay
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.audit_servisi import domain_atomic, record_audit_durable
from firmalar.services.platform_kurulum import ensure_platform_firma


class AuditDurableO3Tests(TransactionTestCase):
    def setUp(self):
        seed_role_permissions()
        ensure_platform_firma()

    def test_survives_outer_atomic_rollback(self):
        marker = "o3-sidecar-survive"
        try:
            with transaction.atomic():
                row = record_audit_durable(
                    actor=None,
                    action=marker,
                    success=False,
                    reason="outer_atomic",
                )
                pk = row.pk
                raise RuntimeError("force rollback")
        except RuntimeError:
            pass

        self.assertTrue(
            AuditOlay.objects.filter(pk=pk, action=marker, success=False).exists()
        )

    def test_domain_atomic_still_raises(self):
        with self.assertRaises(RuntimeError):
            with domain_atomic():
                record_audit_durable(
                    actor=None, action="o3-nested", success=False, reason="x"
                )
