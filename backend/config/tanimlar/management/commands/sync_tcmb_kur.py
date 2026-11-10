"""ADR-0018 — TCMB EOD döviz sync."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from tanimlar.services.feed_adapters import sync_tcmb_doviz


class Command(BaseCommand):
    help = "TCMB EOD döviz gözlemi (kaynak=tcmb)."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--pb", default="USD")
        parser.add_argument("--kur", required=True, help="TRY per 1 PB")

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            actor = User.objects.get(username=options["username"])
        except User.DoesNotExist as exc:
            raise CommandError("Kullanıcı yok.") from exc
        try:
            obj = sync_tcmb_doviz(
                actor=actor,
                para_birimi=options["pb"],
                kur=Decimal(options["kur"]),
            )
        except Exception as exc:  # noqa: BLE001
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"DovizKuru#{obj.pk} {obj.para_birimi}={obj.kur} kaynak={obj.kaynak}"
            )
        )
