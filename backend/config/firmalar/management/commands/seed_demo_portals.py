"""Demo alıcı + tedarikçi firma/kullanıcı (ADR-0021 AA-8). Yerel inceleme için."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups

User = get_user_model()

DEMO_PASSWORD = "DemoPortal1!"


class Command(BaseCommand):
    help = "DEMO_ALICI / DEMO_TEDARIKCI + portal kullanıcıları (idempotent)."

    def handle(self, *args, **options):
        seed_role_permissions()
        alici, _ = Firma.objects.update_or_create(
            firma_kodu="DEMO_ALICI",
            defaults={
                "ad": "Demo Alıcı Kuyumculuk",
                "alici_mi": True,
                "tedarikci_mi": False,
                "platform_mu": False,
                "onay_durumu": "onayli",
                "aktif": True,
            },
        )
        ted, _ = Firma.objects.update_or_create(
            firma_kodu="DEMO_TEDARIKCI",
            defaults={
                "ad": "Demo Tedarikçi Atölye",
                "alici_mi": False,
                "tedarikci_mi": True,
                "platform_mu": False,
                "onay_durumu": "onayli",
                "aktif": True,
            },
        )

        buyers = self._user("demo_alici", alici, roles.ALICI_SATINALMACI)
        sellers = self._user("demo_tedarikci", ted, roles.TEDARIKCI_SATIS)

        self.stdout.write(self.style.SUCCESS("seed_demo_portals tamam."))
        self.stdout.write(
            f"  Alıcı:     {buyers.username} / {DEMO_PASSWORD}  → /api/v1/ (session)"
        )
        self.stdout.write(
            f"  Tedarikçi: {sellers.username} / {DEMO_PASSWORD}  → /api/v1/supplier/"
        )
        self.stdout.write(
            "  Act-as: Admin aksiyon veya POST /api/v1/act-as/start/"
        )

    def _user(self, username, firma, rol):
        u = User.objects.filter(username=username).first()
        if u is None:
            u = User(username=username, firma=firma, rol=rol, is_staff=False)
            u.set_password(DEMO_PASSWORD)
            u.save()
        else:
            u.firma = firma
            u.rol = rol
            u.is_active = True
            u.set_password(DEMO_PASSWORD)
            u.save()
        sync_user_role_groups(u)
        return u
