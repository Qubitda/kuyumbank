"""ProofOfDelivery — teslimat kanıtı (ADR-0013 F6-022; POD opsiyonel)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ProofOfDeliveryQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError(
            "ProofOfDelivery değişmez; QuerySet.update yasak (F6-022)."
        )

    def delete(self):
        raise ValidationError(
            "ProofOfDelivery değişmez; QuerySet.delete yasak (F6-022)."
        )


class ProofOfDeliveryManager(models.Manager.from_queryset(ProofOfDeliveryQuerySet)):
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError(
            "ProofOfDelivery değişmez; bulk_update yasak (F6-022)."
        )


class ProofOfDelivery(models.Model):
    shipment = models.OneToOneField(
        "lojistik.Shipment",
        on_delete=models.PROTECT,
        related_name="pod",
    )
    teslim_alan = models.CharField(max_length=120)
    notlar = models.CharField(max_length=255, blank=True)
    belgeler_ref = models.CharField(
        max_length=255,
        blank=True,
        help_text="Harici belge/storage anahtarı; dosya binary yok (F6-022).",
    )
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_pod",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    objects = ProofOfDeliveryManager()

    class Meta:
        verbose_name = "Teslimat kanıtı (POD)"
        verbose_name_plural = "Teslimat kanıtları"
        ordering = ["-olusturma_tarihi", "-pk"]

    def __str__(self) -> str:
        return f"POD#{self.pk or '?'} SH#{self.shipment_id}"

    def clean(self):
        super().clean()
        if not (self.teslim_alan or "").strip():
            raise ValidationError({"teslim_alan": "Teslim alan zorunlu."})

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "ProofOfDelivery değişmez; UPDATE yasak (F6-022)."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("ProofOfDelivery silinemez.")
