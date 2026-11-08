"""Platform firması + firmasız kullanıcı backfill (Faz 1 geçiş)."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from firmalar import roles
from firmalar.models import Firma, Kullanici
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.audit_servisi import record_audit
from firmalar.services.rol_servisi import sync_user_role_groups


class Command(BaseCommand):
    help = (
        "Platform firmasını oluşturur, firmasız kullanıcıları bağlar, "
        "firma_kodu backfill ve rol permission seed çalıştırır."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-role",
            default=roles.PLATFORM_SUPER,
            help="Firmasız superuser/staff için atanacak platform rolü",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        admin_role = options["admin_role"]
        if admin_role not in roles.PLATFORM_ROLLERI:
            raise CommandError("admin-role bir platform rolü olmalıdır.")

        platform = ensure_platform_firma()
        self.stdout.write(f"Platform firma: id={platform.pk} kod={platform.firma_kodu}")

        # firma_kodu boş olanlar
        for firma in Firma.objects.filter(firma_kodu__isnull=True):
            firma.firma_kodu = f"F{firma.pk:05d}"
            firma.save(update_fields=["firma_kodu", "guncelleme_zamani"])
            self.stdout.write(f"firma_kodu atandı: {firma.ad} -> {firma.firma_kodu}")

        for firma in Firma.objects.filter(firma_kodu=""):
            firma.firma_kodu = f"F{firma.pk:05d}"
            firma.save(update_fields=["firma_kodu", "guncelleme_zamani"])

        # Bootstrap chicken-egg: seed önce; assign_user_role actor+perm ister.
        seed_role_permissions()

        null_users = list(Kullanici.objects.filter(firma__isnull=True))
        for user in null_users:
            if not (user.is_superuser or user.is_staff):
                raise CommandError(
                    f"Firmasız iş kullanıcısı otomatik bağlanamaz: {user.username}. "
                    "Manuel firma atayın."
                )
            eski = {"firma_id": user.firma_id, "rol": user.rol}
            user.firma = platform
            user.rol = admin_role
            user.save()
            sync_user_role_groups(user)
            record_audit(
                actor=user,
                action="user.assign_role",
                entity_type="Kullanici",
                entity_id=user.pk,
                success=True,
                detail={
                    "eski": eski,
                    "yeni": {"firma_id": platform.pk, "rol": admin_role},
                    "bootstrap": True,
                },
            )
            self.stdout.write(
                self.style.WARNING(
                    f"Backfill: {user.username} -> platform / {admin_role}"
                )
            )

        # Rolü boş kalanlar
        for user in Kullanici.objects.filter(rol=""):
            if user.firma_id and user.firma.platform_mu:
                eski = {"firma_id": user.firma_id, "rol": user.rol}
                user.rol = admin_role
                user.save(update_fields=["rol"])
                sync_user_role_groups(user)
                record_audit(
                    actor=user,
                    action="user.assign_role",
                    entity_type="Kullanici",
                    entity_id=user.pk,
                    success=True,
                    detail={
                        "eski": eski,
                        "yeni": {"firma_id": user.firma_id, "rol": admin_role},
                        "bootstrap": True,
                    },
                )
            else:
                raise CommandError(f"Boş rollü kullanıcı: {user.username}")

        self.stdout.write(self.style.SUCCESS("bootstrap_platform tamam."))
