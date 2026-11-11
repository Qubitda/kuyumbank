from django.core.management.base import BaseCommand

from bildirim.services.queue_servisi import process_email_queue


class Command(BaseCommand):
    help = "PENDING EmailDelivery kayıtlarını SMTP ile gönderir (CAP-EMAIL)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        stats = process_email_queue(limit=options["limit"])
        self.stdout.write(self.style.SUCCESS(str(stats)))
