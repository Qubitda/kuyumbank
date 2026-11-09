"""HarcamaLimiti — firma/org dönem limiti (F10-012)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


class HarcamaLimiti(models.Model):
    class Donem(models.TextChoices):
        AY = "AY", "Aylık"
        YIL = "YIL", "Yıllık"
        SIPARIS = "SIPARIS", "Sipariş başı"

    firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="harcama_limitleri",
    )
    org_birimi = models.ForeignKey(
        "firmalar.OrgBirimi",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="harcama_limitleri",
        help_text="Null = firma geneli.",
    )
    donem = models.CharField(max_length=16, choices=Donem.choices, default=Donem.AY)
    tutar = models.DecimalField(max_digits=18, decimal_places=2)
    para_birimi = models.CharField(max_length=3, default="TRY")
    aktif = models.BooleanField(default=True)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Harcama limiti"
        verbose_name_plural = "Harcama limitleri"
        ordering = ["-pk"]
        permissions = [
            ("manage_spend_limit", "Harcama limiti yönetebilir"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tutar__gt=0),
                name="harcamalimiti_tutar_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(donem__in=["AY", "YIL", "SIPARIS"]),
                name="harcamalimiti_donem_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return f"HL#{self.pk or '?'} {self.tutar} {self.para_birimi}"

    def clean(self):
        super().clean()
        if self.org_birimi_id and self.firma_id:
            if self.org_birimi.firma_id != self.firma_id:
                raise ValidationError(
                    {"org_birimi": "Org birimi firma ile uyumsuz."}
                )
        pb = (self.para_birimi or "").strip().upper()
        if len(pb) != 3:
            raise ValidationError({"para_birimi": "ISO 4217 zorunlu."})
        self.para_birimi = pb

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
