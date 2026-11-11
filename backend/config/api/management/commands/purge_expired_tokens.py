"""Süresi dolmuş DRF authtoken satırlarını sil (AUTH_TOKEN_TTL_SECONDS)."""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "AUTH_TOKEN_TTL_SECONDS geçmiş Token kayıtlarını siler."

    def handle(self, *args, **options):
        ttl = int(getattr(settings, "AUTH_TOKEN_TTL_SECONDS", 0) or 0)
        if ttl <= 0:
            self.stdout.write("AUTH_TOKEN_TTL_SECONDS=0 — purge atlandı.")
            return
        cutoff = timezone.now() - timedelta(seconds=ttl)
        deleted, _ = Token.objects.filter(created__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Purged {deleted} expired token(s)."))
