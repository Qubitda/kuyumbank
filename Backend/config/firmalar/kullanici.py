from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from .firma import Firma


class Kullanici(AbstractUser):
    ROL = [
        ("platform_ops", "Platform: Ops"),
        ("platform_admin", "Platform: Admin"),
        ("platform_super", "Platform: Super"),
        ("alici_yonetici", "Alıcı: Yönetici"),
        ("alici_satinalmaci", "Alıcı: Satın almacı"),
        ("alici_onaylayici", "Alıcı: Sipariş onaylayıcı"),
        ("alici_finans", "Alıcı: Finans"),
        ("alici_denetci", "Alıcı: Salt okunur denetçi"),
        ("tedarikci_sahip", "Tedarikçi: Sahip"),
        ("tedarikci_yonetici", "Tedarikçi: Yönetici"),
        ("tedarikci_satis", "Tedarikçi: Satış temsilcisi"),
        ("tedarikci_depo", "Tedarikçi: Depo/sevkiyat"),
        ("tedarikci_finans", "Tedarikçi: Finans"),
    ]

    PLATFORM_ROLLERI = {"platform_ops", "platform_admin", "platform_super"}
    ALICI_ROLLERI = {
        "alici_yonetici", "alici_satinalmaci", "alici_onaylayici",
        "alici_finans", "alici_denetci",
    }
    TEDARIKCI_ROLLERI = {
        "tedarikci_sahip", "tedarikci_yonetici", "tedarikci_satis",
        "tedarikci_depo", "tedarikci_finans",
    }

    # null=True yalnızca mevcut veriyi güvenli biçimde dönüştürebilmek için
    # veritabanında korunuyor. Yeni kayıt/form tarafında alan zorunludur.
    firma = models.ForeignKey(
        Firma,
        verbose_name="Firma",
        related_name="kullanicilar",
        null=True,
        blank=False,
        on_delete=models.PROTECT,
    )
    rol = models.CharField("Rol", max_length=30, choices=ROL, blank=False)

    class Meta:
        verbose_name = "Kullanıcı"
        verbose_name_plural = "Kullanıcılar"

    def clean(self):
        super().clean()
        errors = {}

        if not self.firma_id:
            errors["firma"] = "Her kullanıcı tam olarak bir firmaya bağlı olmalıdır."

        if not self.rol:
            errors["rol"] = "Her kullanıcıya tek bir iş rolü atanmalıdır."
        elif self.rol not in dict(self.ROL):
            errors["rol"] = "Geçersiz kullanıcı rolü."
        elif self.firma_id:
            if self.rol in self.PLATFORM_ROLLERI and not self.firma.platform_mu:
                errors["rol"] = "Platform rolleri yalnızca platform firmasına atanabilir."
            elif self.rol in self.ALICI_ROLLERI and not self.firma.alici_mi:
                errors["rol"] = "Alıcı rolleri yalnızca alıcı olarak tanımlı firmalara atanabilir."
            elif self.rol in self.TEDARIKCI_ROLLERI and not self.firma.tedarikci_mi:
                errors["rol"] = "Tedarikçi rolleri yalnızca tedarikçi olarak tanımlı firmalara atanabilir."

        if errors:
            raise ValidationError(errors)

    @property
    def is_platform_user(self):
        return self.rol in self.PLATFORM_ROLLERI

    def __str__(self):
        return self.get_full_name() or self.username
