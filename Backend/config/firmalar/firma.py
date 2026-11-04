from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class Firma(models.Model):
    ONAY = [("bekliyor", "Bekliyor"), ("onayli", "Onaylı"), ("reddedildi", "Reddedildi")]

    ad = models.CharField("Firma adı", max_length=150)
    unvan = models.CharField("Ticari unvan", max_length=200, blank=True)
    vergi_no = models.CharField(
        "Vergi no", max_length=11, unique=True, null=True, blank=True,
        validators=[RegexValidator(r"^\d{10,11}$", "10 veya 11 haneli rakam girin")],
    )
    vergi_dairesi = models.CharField("Vergi dairesi", max_length=80, blank=True)
    telefon = models.CharField("Telefon", max_length=20, blank=True)
    eposta = models.EmailField("E-posta", blank=True)

    alici_mi = models.BooleanField("Alıcı (müşteri)", default=False)
    tedarikci_mi = models.BooleanField("Tedarikçi", default=False)
    platform_mu = models.BooleanField("Platform (biz)", default=False)

    onay_durumu = models.CharField("Onay durumu", max_length=10, choices=ONAY, default="bekliyor")
    aktif = models.BooleanField("Aktif", default=True)
    olusturma_zamani = models.DateTimeField(auto_now_add=True)
    guncelleme_zamani = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Firma"
        verbose_name_plural = "Firmalar"
        ordering = ["ad"]
        constraints = [
            models.UniqueConstraint(
                fields=["platform_mu"],
                condition=models.Q(platform_mu=True),
                name="tek_platform_firmasi",
            ),
        ]

    def clean(self):
        super().clean()
        if not self.pk:
            return

        # Firma tipi değişikliği, mevcut kullanıcı rollerini geçersiz kılamaz.
        from .kullanici import Kullanici

        assigned_roles = set(self.kullanicilar.exclude(rol="").values_list("rol", flat=True))
        errors = {}
        if assigned_roles.intersection(Kullanici.PLATFORM_ROLLERI) and not self.platform_mu:
            errors["platform_mu"] = "Bu firmaya atanmış platform rolleri var; önce kullanıcı rollerini taşıyın."
        if assigned_roles.intersection(Kullanici.ALICI_ROLLERI) and not self.alici_mi:
            errors["alici_mi"] = "Bu firmaya atanmış alıcı rolleri var; önce kullanıcı rollerini değiştirin."
        if assigned_roles.intersection(Kullanici.TEDARIKCI_ROLLERI) and not self.tedarikci_mi:
            errors["tedarikci_mi"] = "Bu firmaya atanmış tedarikçi rolleri var; önce kullanıcı rollerini değiştirin."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.ad
