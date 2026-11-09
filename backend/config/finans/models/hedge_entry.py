"""HedgeEntry — append-only HAS hedge gram kaydı (ADR-0012 F5-K7)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class HedgeEntryQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError(
            "HedgeEntry değişmez; QuerySet.update yasak (ADR-0012 F5-K7)."
        )

    def delete(self):
        raise ValidationError(
            "HedgeEntry değişmez; QuerySet.delete yasak (ADR-0012 F5-K7)."
        )


class HedgeEntryManager(models.Manager.from_queryset(HedgeEntryQuerySet)):
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError(
            "HedgeEntry değişmez; bulk_update yasak (ADR-0012 F5-K7)."
        )


class HedgeEntry(models.Model):
    """İşaretli gram: + uzun / − kısa hedge; FX open_has'tan düşülür."""

    grams = models.DecimalField(max_digits=18, decimal_places=4)
    metal_kodu = models.CharField(max_length=16, blank=True, default="")
    idempotency_key = models.CharField(max_length=64, unique=True)
    aciklama = models.CharField(max_length=255, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_hedge_entries",
    )
    olusturma_tarihi = models.DateTimeField(default=timezone.now)

    objects = HedgeEntryManager()

    class Meta:
        verbose_name = "Hedge kaydı"
        verbose_name_plural = "Hedge kayıtları"
        ordering = ["-olusturma_tarihi", "-pk"]
        indexes = [
            models.Index(fields=["-olusturma_tarihi"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(grams=0),
                name="hedgeentry_grams_sifir_degil",
            ),
        ]

    def __str__(self) -> str:
        return f"HE#{self.pk or '?'} {self.grams}g"

    def clean(self):
        super().clean()
        if self.grams == 0:
            raise ValidationError({"grams": "grams sıfır olamaz."})

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "HedgeEntry değişmez; UPDATE yasak (ADR-0012 F5-K7)."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "HedgeEntry değişmez; DELETE yasak (ADR-0012 F5-K7)."
        )
