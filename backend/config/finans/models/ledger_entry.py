"""LedgerEntry — append-only finansal hareket (ADR-0012 F5-K2/K3)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class LedgerEntryQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError(
            "LedgerEntry değişmez; QuerySet.update yasak (ADR-0012 F5-K2)."
        )

    def delete(self):
        raise ValidationError(
            "LedgerEntry değişmez; QuerySet.delete yasak (ADR-0012 F5-K2)."
        )


class LedgerEntryManager(models.Manager.from_queryset(LedgerEntryQuerySet)):
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError(
            "LedgerEntry değişmez; bulk_update yasak (ADR-0012 F5-K2)."
        )


class LedgerEntry(models.Model):
    class Yon(models.TextChoices):
        BORC = "BORC", "Borç"
        ALACAK = "ALACAK", "Alacak"

    class HareketTipi(models.TextChoices):
        SATIS = "SATIS", "Satış borcu"
        TAHSILAT = "TAHSILAT", "Tahsilat"
        IADE = "IADE", "İade"
        MAHSUP = "MAHSUP", "Mahsup"
        CONTRA = "CONTRA", "Contra / ters"
        DUZELTME = "DUZELTME", "Düzeltme"

    firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="ledger_entries",
        help_text="Hesap sahibi (bakiyesi etkilenen firma).",
    )
    karsi_firma = models.ForeignKey(
        "firmalar.Firma",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="karsi_ledger_entries",
        help_text="Karşı taraf; U-005 netleşene kadar genelde platform (F5-K5).",
    )
    tutar = models.DecimalField(max_digits=18, decimal_places=2)
    para_birimi = models.CharField(max_length=3)
    yon = models.CharField(max_length=8, choices=Yon.choices)
    hareket_tipi = models.CharField(max_length=16, choices=HareketTipi.choices)
    referans_tip = models.CharField(max_length=64, blank=True)
    referans_id = models.CharField(max_length=64, blank=True)
    contra_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="contra_entries",
    )
    idempotency_key = models.CharField(max_length=64)
    aciklama = models.CharField(max_length=255, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_ledger_entries",
    )
    olusturma_tarihi = models.DateTimeField(default=timezone.now)

    objects = LedgerEntryManager()

    class Meta:
        verbose_name = "Ledger hareketi"
        verbose_name_plural = "Ledger hareketleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        permissions = [
            ("post_ledger", "Finans ledger hareketi yazabilir"),
        ]
        indexes = [
            models.Index(fields=["firma", "-olusturma_tarihi"]),
            models.Index(fields=["referans_tip", "referans_id"]),
            models.Index(fields=["hareket_tipi", "-olusturma_tarihi"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tutar__gt=0),
                name="ledgerentry_tutar_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(yon__in=["BORC", "ALACAK"]),
                name="ledgerentry_yon_gecerli",
            ),
            models.UniqueConstraint(
                fields=["firma", "idempotency_key"],
                name="ledgerentry_firma_idempotency_uniq",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"LE#{self.pk or '?'} {self.yon} {self.tutar} {self.para_birimi} "
            f"firma={self.firma_id}"
        )

    def clean(self):
        super().clean()
        if self.tutar is not None and self.tutar <= 0:
            raise ValidationError({"tutar": "Tutar sıfırdan büyük olmalı."})
        pb = (self.para_birimi or "").strip().upper()
        if len(pb) != 3 or not pb.isalpha():
            raise ValidationError(
                {"para_birimi": "ISO 4217 para birimi zorunlu (3 harf)."}
            )
        self.para_birimi = pb
        if self.karsi_firma_id and self.firma_id == self.karsi_firma_id:
            raise ValidationError(
                {"karsi_firma": "firma ve karsi_firma aynı olamaz."}
            )
        if self.hareket_tipi == self.HareketTipi.CONTRA and not self.contra_of_id:
            raise ValidationError(
                {"contra_of": "CONTRA için contra_of zorunlu."}
            )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "LedgerEntry değişmez; UPDATE yasak (ADR-0012 F5-K2)."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "LedgerEntry değişmez; DELETE yasak (ADR-0012 F5-K2)."
        )
