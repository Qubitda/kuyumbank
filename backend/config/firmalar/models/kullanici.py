from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models

from .. import roles


class KullaniciManager(UserManager):
    """Superuser oluştururken platform firma + rol zorunlu (ADR-0003-02)."""

    def _create_user(self, username, email, password, **extra_fields):
        return super()._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        from ..services.platform_kurulum import ensure_platform_firma

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        if not extra_fields.get("firma"):
            extra_fields["firma"] = ensure_platform_firma()
        extra_fields.setdefault("rol", roles.PLATFORM_SUPER)
        user = self._create_user(username, email, password, **extra_fields)
        # Rol grubu + permission matrisi (admin app listesi yetki_servisi ile)
        from ..services.rol_servisi import sync_user_role_groups

        sync_user_role_groups(user)
        return user


class Kullanici(AbstractUser):
    """Sistem kullanıcısı: tek firma + tek iş rolü (ADR-0003)."""

    ROL = roles.ROLE_CHOICES
    PLATFORM_ROLLERI = roles.PLATFORM_ROLLERI
    ALICI_ROLLERI = roles.ALICI_ROLLERI
    TEDARIKCI_ROLLERI = roles.TEDARIKCI_ROLLERI

    objects = KullaniciManager()

    firma = models.ForeignKey(
        "firmalar.Firma",
        verbose_name="Firma",
        related_name="kullanicilar",
        on_delete=models.PROTECT,
    )
    rol = models.CharField("Rol", max_length=30, choices=ROL, blank=False)
    email_verified_at = models.DateTimeField(
        "E-posta doğrulama",
        null=True,
        blank=True,
        help_text="Boş = doğrulanmamış (ADR-0028).",
    )

    class Meta:
        verbose_name = "Kullanıcı"
        verbose_name_plural = "Kullanıcılar"
        permissions = [
            ("manage_users", "Kendi firma kullanıcılarını yönetebilir"),
            ("manage_all_users", "Tüm firma kullanıcılarını yönetebilir"),
            ("act_as_user", "Başka kullanıcı olarak uygulamayı gezebilir (act-as)"),
        ]

    def clean(self):
        super().clean()
        errors = {}

        if not self.firma_id:
            errors["firma"] = "Her kullanıcı tam olarak bir firmaya bağlı olmalıdır."

        if not self.rol:
            errors["rol"] = "Her kullanıcıya tek bir iş rolü atanmalıdır."
        elif self.rol not in roles.ALL_ROLES:
            errors["rol"] = "Geçersiz kullanıcı rolü."
        elif self.firma_id:
            if self.rol in roles.PLATFORM_ROLLERI and not self.firma.platform_mu:
                errors["rol"] = "Platform rolleri yalnızca platform firmasına atanabilir."
            elif self.rol in roles.ALICI_ROLLERI and not self.firma.alici_mi:
                errors["rol"] = "Alıcı rolleri yalnızca alıcı olarak tanımlı firmalara atanabilir."
            elif self.rol in roles.TEDARIKCI_ROLLERI and not self.firma.tedarikci_mi:
                errors["rol"] = "Tedarikçi rolleri yalnızca tedarikçi olarak tanımlı firmalara atanabilir."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Firma/rol zorunluluğu herkes için geçerlidir (superuser dahil)."""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_platform_user(self):
        return self.rol in roles.PLATFORM_ROLLERI and bool(
            self.firma_id and self.firma.platform_mu
        )

    def __str__(self):
        return self.get_full_name() or self.username
