"""StockMovement — immutable stok ledger satırı (ADR-0011 F4-A3)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from stok.birim_constants import StokBirimi


class StockMovementQuerySet(models.QuerySet):
    """ADR-0011 F4-A3 — bulk UPDATE/DELETE yasak (trigger yok; ORM koruması)."""

    def update(self, **kwargs):
        raise ValidationError(
            "StockMovement değişmez; QuerySet.update yasak (ADR-0011 F4-A3)."
        )

    def delete(self):
        raise ValidationError(
            "StockMovement değişmez; QuerySet.delete yasak (ADR-0011 F4-A3)."
        )


class StockMovementManager(models.Manager.from_queryset(StockMovementQuerySet)):
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError(
            "StockMovement değişmez; bulk_update yasak (ADR-0011 F4-A3)."
        )


class StockMovement(models.Model):
    class Tip(models.TextChoices):
        GIRIS = "GIRIS", "Giriş"
        CIKIS = "CIKIS", "Çıkış"
        DUZELTME = "DUZELTME", "Düzeltme"
        # Rezervasyon/satış tipleri sonraki dilimlerde kullanılır
        REZERVASYON = "REZERVASYON", "Rezervasyon"
        REZERVASYON_IPTAL = "REZERVASYON_IPTAL", "Rezervasyon iptal"
        SATIS = "SATIS", "Satış"
        IADE = "IADE", "İade"

    warehouse = models.ForeignKey(
        "stok.Warehouse",
        on_delete=models.PROTECT,
        related_name="movements",
    )
    teklif = models.ForeignKey(
        "fiyatlama.TedarikciTeklif",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    varyant = models.ForeignKey(
        "urunler.Varyant",
        on_delete=models.PROTECT,
        related_name="stock_movements",
        help_text="Denormalize: teklif.varyant ile eşit olmalı.",
    )
    birim = models.CharField(max_length=8, choices=StokBirimi.CHOICES)
    # İşaretli miktar: giriş +, çıkış − (DUZELTME her iki yön)
    miktar = models.DecimalField(max_digits=18, decimal_places=6)
    tip = models.CharField(max_length=24, choices=Tip.choices)
    neden = models.CharField(max_length=255, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_stock_movements",
    )
    olusturma_tarihi = models.DateTimeField(default=timezone.now)

    objects = StockMovementManager()

    class Meta:
        verbose_name = "Stok hareketi"
        verbose_name_plural = "Stok hareketleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        indexes = [
            models.Index(fields=["warehouse", "teklif", "-olusturma_tarihi"]),
            models.Index(fields=["teklif", "-olusturma_tarihi"]),
            models.Index(fields=["tip", "-olusturma_tarihi"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(miktar=0),
                name="stockmovement_miktar_sifir_degil",
            ),
            models.CheckConstraint(
                condition=models.Q(birim__in=["ADET", "GRAM", "KARAT"]),
                name="stockmovement_birim_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    tip__in=[
                        "GIRIS",
                        "CIKIS",
                        "DUZELTME",
                        "REZERVASYON",
                        "REZERVASYON_IPTAL",
                        "SATIS",
                        "IADE",
                    ]
                ),
                name="stockmovement_tip_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return f"SM#{self.pk or '?'} {self.tip} {self.miktar} {self.birim}"

    def clean(self):
        super().clean()
        if self.teklif_id and self.varyant_id:
            if self.teklif.varyant_id != self.varyant_id:
                raise ValidationError(
                    {"varyant": "varyant, teklif.varyant ile eşit olmalı."}
                )
        if self.miktar == 0:
            raise ValidationError({"miktar": "Miktar sıfır olamaz."})

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "StockMovement değişmez; UPDATE yasak (ADR-0011 F4-A3)."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "StockMovement değişmez; DELETE yasak (ADR-0011 F4-A3)."
        )
