"""IdempotencyRecord toplu TTL temizliği."""

from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from api.models import IdempotencyRecord
from api.services.idempotency_servisi import purge_expired
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


@override_settings(IDEMPOTENCY_TTL_SECONDS=3600)
class PurgeIdempotencyTests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        ensure_platform_firma()
        cls._build_checkout_world()

    def test_purge_deletes_only_expired(self):
        fresh = IdempotencyRecord.objects.create(
            firma=self.buyer.firma,
            key="fresh-key",
            method="POST",
            path="/api/v1/checkout/",
            request_hash="a" * 64,
            status_code=201,
            response_body={"ok": True},
        )
        stale = IdempotencyRecord.objects.create(
            firma=self.buyer.firma,
            key="stale-key",
            method="POST",
            path="/api/v1/checkout/",
            request_hash="b" * 64,
            status_code=201,
            response_body={"ok": True},
        )
        IdempotencyRecord.objects.filter(pk=stale.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        n = purge_expired()
        self.assertEqual(n, 1)
        self.assertTrue(IdempotencyRecord.objects.filter(pk=fresh.pk).exists())
        self.assertFalse(IdempotencyRecord.objects.filter(pk=stale.pk).exists())
