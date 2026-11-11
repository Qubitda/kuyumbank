from django.core.management.base import BaseCommand

from bildirim.services.seed_servisi import seed_templates_and_rules


class Command(BaseCommand):
    help = "Sistem e-posta şablonları + varsayılan NotificationRule seed (idempotent)."

    def handle(self, *args, **options):
        stats = seed_templates_and_rules()
        self.stdout.write(self.style.SUCCESS(str(stats)))
