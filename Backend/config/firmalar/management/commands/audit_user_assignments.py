from django.core.management.base import BaseCommand

from firmalar import roles
from firmalar.models.kullanici import Kullanici


class Command(BaseCommand):
    help = "Kullanıcıların firma/rol atamalarını salt okunur biçimde denetler."

    def handle(self, *args, **options):
        users = Kullanici.objects.select_related("firma").order_by("username")
        problems = 0
        for user in users:
            reasons = []
            if not user.firma_id:
                reasons.append("firma atanmamış")
            if not user.rol:
                reasons.append("rol atanmamış")
            elif user.rol not in roles.ALL_ROLES:
                reasons.append("geçersiz rol kodu")
            elif user.firma_id:
                if user.rol in roles.PLATFORM_ROLLERI and not user.firma.platform_mu:
                    reasons.append("platform rolü platform olmayan firmada")
                elif user.rol in roles.ALICI_ROLLERI and not user.firma.alici_mi:
                    reasons.append("alıcı rolü alıcı olmayan firmada")
                elif user.rol in roles.TEDARIKCI_ROLLERI and not user.firma.tedarikci_mi:
                    reasons.append("tedarikçi rolü tedarikçi olmayan firmada")
            if reasons:
                problems += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"{user.username} (id={user.pk}): {', '.join(reasons)}"
                    )
                )

        if problems:
            self.stdout.write(self.style.ERROR(f"Sorunlu kullanıcı: {problems}"))
            self.stdout.write("Bu kayıtlar düzeltilmeden firma FK null=False yapılmamalıdır.")
        else:
            self.stdout.write(self.style.SUCCESS("Tüm kullanıcıların firma/rol ataması tutarlı."))
