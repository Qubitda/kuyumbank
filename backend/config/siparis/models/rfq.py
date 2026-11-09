"""RFQ / RFQLine / RFQMessage — F10-020 iskelet (SM servisten)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class RFQ(models.Model):
    class Durum(models.TextChoices):
        TASLAK = "TASLAK", "Taslak"
        GONDERILDI = "GONDERILDI", "Gönderildi"
        KAPANDI = "KAPANDI", "Kapandı"
        IPTAL = "IPTAL", "İptal"

    alici_firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="rfqlar",
    )
    sube = models.ForeignKey(
        "firmalar.OrgBirimi",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="rfqlar",
    )
    baslik = models.CharField(max_length=200)
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.TASLAK
    )
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_rfqlar",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    _allow_status_transition = False

    class Meta:
        verbose_name = "RFQ"
        verbose_name_plural = "RFQlar"
        ordering = ["-olusturma_tarihi", "-pk"]
        permissions = [
            ("manage_rfq", "RFQ oluşturup yönetebilir"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    durum__in=["TASLAK", "GONDERILDI", "KAPANDI", "IPTAL"]
                ),
                name="rfq_durum_gecerli",
            ),
        ]
        indexes = [
            models.Index(fields=["alici_firma", "durum"]),
        ]

    def __str__(self) -> str:
        return f"RFQ#{self.pk or '?'} {self.durum}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            return super().save(*args, **kwargs)
        if self._allow_status_transition:
            return super().save(*args, **kwargs)
        raise ValidationError("RFQ değişmez; geçiş yalnız rfq_servisi (F10-020).")

    def delete(self, *args, **kwargs):
        raise ValidationError("RFQ silinemez.")


class RFQLine(models.Model):
    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="lines")
    aciklama = models.CharField(max_length=255)
    miktar = models.DecimalField(max_digits=18, decimal_places=6)
    birim = models.CharField(max_length=8, default="ADET")
    varyant = models.ForeignKey(
        "urunler.Varyant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rfq_lines",
    )

    class Meta:
        verbose_name = "RFQ satırı"
        verbose_name_plural = "RFQ satırları"
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0),
                name="rfqline_miktar_pozitif",
            ),
        ]

    def __str__(self) -> str:
        return f"RFQL#{self.pk or '?'} RFQ#{self.rfq_id}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("RFQLine değişmez.")
        self.full_clean()
        return super().save(*args, **kwargs)


class RFQMessage(models.Model):
    """Platform aracılı mesaj; alıcı↔tedarikçi kimliği yok (kör)."""

    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name="messages")
    govde = models.TextField(max_length=2000)
    # Yalnız rol etiketi; firma/kimlik sızıntısı yok
    gonderen_rol = models.CharField(max_length=32, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rfq_mesajlari",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "RFQ mesajı"
        verbose_name_plural = "RFQ mesajları"
        ordering = ["pk"]

    def __str__(self) -> str:
        return f"RFQM#{self.pk or '?'} RFQ#{self.rfq_id}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("RFQMessage değişmez.")
        return super().save(*args, **kwargs)
