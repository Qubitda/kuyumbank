"""Süresi dolmuş IdempotencyRecord temizliği (API-B1 TTL)."""

from django.core.management.base import BaseCommand

from api.services.idempotency_servisi import purge_expired, ttl_seconds


class Command(BaseCommand):
    help = (
        "IDEMPOTENCY_TTL_SECONDS geçmiş IdempotencyRecord satırlarını siler "
        "(cron/ops; lazy lookup tek başına tabloyu küçültmez)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="En fazla kaç kayıt silinsin",
        )

    def handle(self, *args, **options):
        n = purge_expired(limit=options.get("limit"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Purged {n} idempotency record(s) (ttl={ttl_seconds()}s)."
            )
        )
