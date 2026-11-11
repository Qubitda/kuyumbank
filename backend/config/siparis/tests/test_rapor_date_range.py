"""Rapor tarih aralığı zorunluluğu / tavan."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from siparis.services.rapor_servisi import resolve_date_range


class RaporDateRangeTests(TestCase):
    def test_default_range_ok(self):
        d_from, d_to = resolve_date_range()
        self.assertLessEqual(d_from, d_to)
        self.assertLessEqual((d_to - d_from).days + 1, 90)

    def test_max_span_rejected(self):
        today = timezone.localdate()
        with self.assertRaises(ValidationError):
            resolve_date_range(
                date_from=today - timedelta(days=400),
                date_to=today,
            )
