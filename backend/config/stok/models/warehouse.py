"""Warehouse — sahipli depo kaydı (ADR-0011 F4-A2; konsinye yok)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


class Warehouse(models.Model):
    class SahipTipi(models.TextChoices):
        PLATFORM = "PLATFORM", "Platform"
        TEDARIKCI = "TEDARIKCI", "Tedarikçi"

    kod = models.CharField(max_length=32)
    ad = models.CharField(max_length=120)
    sahip_firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="warehouses",
        help_text="Platform veya tedarikçi firma; alıcı-only ve konsinye yok.",
    )
    sahip_tipi = models.CharField(max_length=16, choices=SahipTipi.choices)
    aktif = models.BooleanField(default=True)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Depo"
        verbose_name_plural = "Depolar"
        ordering = ["sahip_firma_id", "kod"]
        constraints = [
            models.UniqueConstraint(
                fields=["sahip_firma", "kod"],
                name="warehouse_firma_kod_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(sahip_tipi__in=["PLATFORM", "TEDARIKCI"]),
                name="warehouse_sahip_tipi_gecerli",
            ),
        ]
        indexes = [
            models.Index(fields=["sahip_firma", "aktif"]),
            models.Index(fields=["sahip_tipi", "aktif"]),
        ]
        permissions = [
            ("manage_warehouse", "Platform depolarını yönetebilir"),
            ("manage_own_warehouse", "Kendi firma depolarını yönetebilir"),
        ]

    def __str__(self) -> str:
        return f"{self.kod} — {self.ad}"

    def clean(self):
        super().clean()
        firma = self.sahip_firma
        if firma is None and self.sahip_firma_id:
            from firmalar.models import Firma

            firma = Firma.objects.filter(pk=self.sahip_firma_id).first()
        if firma is None:
            raise ValidationError({"sahip_firma": "Sahip firma zorunlu."})

        if getattr(firma, "platform_mu", False):
            expected = self.SahipTipi.PLATFORM
        elif getattr(firma, "tedarikci_mi", False):
            expected = self.SahipTipi.TEDARIKCI
        else:
            raise ValidationError(
                {
                    "sahip_firma": (
                        "Depo yalnız platform veya tedarikçi firmaya bağlanır "
                        "(konsinye/alıcı deposu yok — ADR-0011 F4-A13)."
                    )
                }
            )

        if self.sahip_tipi and self.sahip_tipi != expected:
            raise ValidationError(
                {
                    "sahip_tipi": (
                        f"Firma tipiyle uyumsuz; beklenen {expected}."
                    )
                }
            )
        self.sahip_tipi = expected

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
