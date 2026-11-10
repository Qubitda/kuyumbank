"""ADR-0018 — Binance anlık metal kur sync (Celery yok; cron)."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from tanimlar.models import KiymetliMetal
from tanimlar.services.feed_adapters import sync_binance_metal


class Command(BaseCommand):
    help = "Binance XAUUSDT×USDTTRY → gram TRY metal kuru (manage_kur actor)."

    def add_arguments(self, parser):
        parser.add_argument("--metal-kod", default="AU", help="KiymetliMetal.kod")
        parser.add_argument("--username", required=True, help="manage_kur kullanıcı")
        parser.add_argument(
            "--xauusdt",
            default=None,
            help="Inject (test); yoksa HTTP",
        )
        parser.add_argument("--usdttry", default=None)
        parser.add_argument("--tcmb-usdtry", default=None)
        parser.add_argument(
            "--skip-capraz",
            action="store_true",
            help="Çapraz sanity atla",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            actor = User.objects.get(username=options["username"])
        except User.DoesNotExist as exc:
            raise CommandError("Kullanıcı yok.") from exc
        try:
            metal = KiymetliMetal.objects.get(kod=options["metal_kod"])
        except KiymetliMetal.DoesNotExist as exc:
            raise CommandError("Metal yok.") from exc
        from decimal import Decimal

        kwargs = {
            "metal": metal,
            "actor": actor,
            "skip_capraz": options["skip_capraz"],
        }
        if options["xauusdt"]:
            kwargs["xauusdt"] = Decimal(options["xauusdt"])
        if options["usdttry"]:
            kwargs["usdttry"] = Decimal(options["usdttry"])
        if options["tcmb_usdtry"]:
            kwargs["tcmb_usdtry"] = Decimal(options["tcmb_usdtry"])
        try:
            obj = sync_binance_metal(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"MetalKuru#{obj.pk} {obj.saf_birim_fiyat} kaynak={obj.kaynak}"
            )
        )
