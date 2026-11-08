from django.core.management.base import BaseCommand

from firmalar.role_permissions import seed_role_permissions


class Command(BaseCommand):
    help = "Rol → permission matrisini idempotent şekilde Group'lara işler."

    def handle(self, *args, **options):
        stats = seed_role_permissions()
        self.stdout.write(
            self.style.SUCCESS(
                f"Rol grupları senkron: {stats['synced']} / {stats['groups']}"
            )
        )
