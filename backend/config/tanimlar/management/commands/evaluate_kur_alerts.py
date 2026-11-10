"""CAP-ALERT — aktif kur eşik kurallarını değerlendir."""

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from tanimlar.services.kur_alert_servisi import degerlendir


class Command(BaseCommand):
    help = "Kur alert kurallarını tara; stale’de tetik yok."

    def add_arguments(self, parser):
        parser.add_argument(
            "--now",
            dest="now",
            default=None,
            help="ISO datetime (test/cron simülasyonu); yoksa timezone.now()",
        )

    def handle(self, *args, **options):
        now = None
        raw = options.get("now")
        if raw:
            now = parse_datetime(raw)
            if now is None:
                raise CommandError(f"Geçersiz --now: {raw}")
            if timezone.is_naive(now):
                now = timezone.make_aware(now, timezone.get_current_timezone())
        rows = degerlendir(now=now)
        self.stdout.write(self.style.SUCCESS(f"tetik={len(rows)} {rows}"))
