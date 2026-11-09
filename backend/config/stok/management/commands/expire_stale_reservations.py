"""F4-022 — TTL dolmuş AKTIF StockReservation toplu expire."""

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from stok.services.reservation_servisi import expire_stale_reservations


class Command(BaseCommand):
    help = (
        "Süresi dolmuş AKTIF stok rezervasyonlarını SURESI_DOLDU yapar "
        "ve reserved serbest bırakır (idempotent)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--now",
            default=None,
            help="ISO-8601 an (test); yoksa timezone.now()",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="En fazla kaç kayıt işlensin",
        )

    def handle(self, *args, **options):
        now = None
        raw = options.get("now")
        if raw:
            now = parse_datetime(raw)
            if now is None:
                self.stderr.write(self.style.ERROR(f"Geçersiz --now: {raw}"))
                return
            if timezone.is_naive(now):
                now = timezone.make_aware(now, timezone.get_current_timezone())
        n = expire_stale_reservations(now=now, limit=options.get("limit"))
        self.stdout.write(
            self.style.SUCCESS(f"Expired {n} stale reservation(s).")
        )
