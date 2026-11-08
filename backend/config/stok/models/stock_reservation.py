"""StockReservation — checkout hold + TTL (ADR-0011 F4-A5/A6)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from stok.birim_constants import StokBirimi


class StockReservation(models.Model):
    class Durum(models.TextChoices):
        AKTIF = "AKTIF", "Aktif"
        SURESI_DOLDU = "SURESI_DOLDU", "Süresi doldu"
        TUKETILDI = "TUKETILDI", "Tüketildi"
        IPTAL = "IPTAL", "İptal"

    warehouse = models.ForeignKey(
        "stok.Warehouse",
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    teklif = models.ForeignKey(
        "fiyatlama.TedarikciTeklif",
        on_delete=models.PROTECT,
        related_name="stock_reservations",
    )
    varyant = models.ForeignKey(
        "urunler.Varyant",
        on_delete=models.PROTECT,
        related_name="stock_reservations",
    )
    birim = models.CharField(max_length=8, choices=StokBirimi.CHOICES)
    miktar = models.DecimalField(max_digits=18, decimal_places=6)
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.AKTIF
    )
    gecerlilik_sonu = models.DateTimeField()
    alici_firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="stock_reservations",
        help_text="Rezervasyonu yapan alıcı firma (tenant).",
    )
    idempotency_key = models.CharField(max_length=64, null=True, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_stock_reservations",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    kapanma_tarihi = models.DateTimeField(null=True, blank=True)

    # Servis: yalnız AKTIF → SURESI_DOLDU / TUKETILDI / IPTAL
    _allow_status_transition = False

    class Meta:
        verbose_name = "Stok rezervasyonu"
        verbose_name_plural = "Stok rezervasyonları"
        ordering = ["-olusturma_tarihi", "-pk"]
        indexes = [
            models.Index(fields=["warehouse", "teklif", "durum"]),
            models.Index(fields=["durum", "gecerlilik_sonu"]),
            models.Index(fields=["alici_firma", "-olusturma_tarihi"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0),
                name="stockreservation_miktar_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(birim__in=["ADET", "GRAM", "KARAT"]),
                name="stockreservation_birim_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    durum__in=["AKTIF", "SURESI_DOLDU", "TUKETILDI", "IPTAL"]
                ),
                name="stockreservation_durum_gecerli",
            ),
            models.UniqueConstraint(
                fields=["warehouse", "idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False)
                & ~models.Q(idempotency_key=""),
                name="stockreservation_wh_idempotency_uniq",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"SR#{self.pk or '?'} {self.durum} "
            f"{self.miktar} {self.birim}"
        )

    def is_gecerli(self, *, now=None) -> bool:
        now = now or timezone.now()
        return self.durum == self.Durum.AKTIF and now < self.gecerlilik_sonu

    def clean(self):
        super().clean()
        if self.teklif_id and self.varyant_id:
            if self.teklif.varyant_id != self.varyant_id:
                raise ValidationError(
                    {"varyant": "varyant, teklif.varyant ile eşit olmalı."}
                )
        if self.miktar is not None and self.miktar <= 0:
            raise ValidationError({"miktar": "Miktar pozitif olmalı."})

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean()
            return super().save(*args, **kwargs)

        if self._allow_status_transition:
            update_fields = kwargs.get("update_fields")
            allowed = {"durum", "kapanma_tarihi"}
            if update_fields is not None and set(update_fields) <= allowed:
                return super().save(*args, **kwargs)
            raise ValidationError(
                "Rezervasyon geçişi yalnız durum/kapanma alanlarıyla yapılır."
            )

        raise ValidationError(
            "StockReservation değişmez; yalnız servis durum geçişleri."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("StockReservation silinemez; iptal/expire kullanın.")
