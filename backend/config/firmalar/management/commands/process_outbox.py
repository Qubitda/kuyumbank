"""F4-090 — PENDING outbox mesajlarını işle (Celery yok)."""

from django.core.management.base import BaseCommand

from firmalar.services import outbox_servisi


class Command(BaseCommand):
    help = "PENDING transactional outbox mesajlarını işler (F4-090, at-least-once)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Bu koşuda en fazla kaç PENDING satır (varsayılan 100).",
        )

    def handle(self, *args, **options):
        result = outbox_servisi.process_pending(limit=options["limit"])
        self.stdout.write(
            self.style.SUCCESS(
                "outbox: seen={seen} processed={processed} "
                "failed={failed} skipped={skipped}".format(**result)
            )
        )
