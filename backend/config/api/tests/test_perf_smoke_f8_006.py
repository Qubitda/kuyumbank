"""F8-006 — quote/lock/cart+checkout soft süre smoke + baseline çıktı."""

import json

from django.test import TestCase

from api.services.perf_smoke import (
    DEFAULT_SOFT_LIMIT_S,
    run_quote_lock_checkout_smoke,
    samples_to_rows,
)
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class PerfSmokeF8006Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()

    def test_critical_paths_under_soft_limit(self):
        samples = run_quote_lock_checkout_smoke(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            quote_actor=self.finance,
            buyer=self.buyer,
            soft_limit_s=DEFAULT_SOFT_LIMIT_S,
        )
        rows = samples_to_rows(samples)
        # Baseline raporu (test stdout)
        print("F8-006 baseline:", json.dumps(rows, ensure_ascii=False))
        self.assertEqual(len(samples), 3)
        self.assertEqual({s.name for s in samples}, {"quote", "lock_quote", "cart_checkout"})
        for s in samples:
            self.assertTrue(
                s.ok,
                msg=f"{s.name} failed: {s.detail or s.elapsed_ms}ms",
            )
            self.assertGreater(s.elapsed_ms, 0.0)
