"""ReturnRequest — stok-only iade/uyuşmazlık SM (F6-030; U-004)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ReturnRequest(models.Model):
    class Durum(models.TextChoices):
        TASLAK = "TASLAK", "Taslak"
        INCELENIYOR = "INCELENIYOR", "İnceleniyor"
        ONAYLANDI = "ONAYLANDI", "Onaylandı"
        REDDEDILDI = "REDDEDILDI", "Reddedildi"
        IPTAL = "IPTAL", "İptal"

    order = models.ForeignKey(
        "siparis.Order",
        on_delete=models.PROTECT,
        related_name="return_requests",
    )
    shipment = models.ForeignKey(
        "lojistik.Shipment",
        on_delete=models.PROTECT,
        related_name="return_requests",
        help_text="İade için teslim edilmiş sevkiyat (F6-030).",
    )
    durum = models.CharField(
        max_length=16, choices=Durum.choices, default=Durum.TASLAK
    )
    sebep = models.CharField(max_length=255)
    stok_iade_yapildi = models.BooleanField(
        default=False,
        help_text="F6-031: ONAYLANDI sonrası ledger IADE yazıldı mı.",
    )
    finans_mahsup_yapildi = models.BooleanField(
        default=False,
        help_text="F5-023: mahsup ledger yazıldı mı (ödeme iadesi yok).",
    )
    notlar = models.CharField(max_length=255, blank=True)
    # HTTP Idempotency-Key domain yedekleri (crash sonrası replay)
    idempotency_key = models.CharField(max_length=64, blank=True, default="")
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_return_requests",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    _allow_status_transition = False

    class Meta:
        verbose_name = "İade talebi"
        verbose_name_plural = "İade talepleri"
        ordering = ["-olusturma_tarihi", "-pk"]
        permissions = [
            ("manage_return", "İade/uyuşmazlık yönetebilir"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    durum__in=[
                        "TASLAK",
                        "INCELENIYOR",
                        "ONAYLANDI",
                        "REDDEDILDI",
                        "IPTAL",
                    ]
                ),
                name="returnrequest_durum_gecerli",
            ),
            models.UniqueConstraint(
                condition=~models.Q(idempotency_key=""),
                fields=["order", "idempotency_key"],
                name="returnrequest_order_idempotency_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["order", "durum"]),
            models.Index(fields=["durum"]),
        ]

    def __str__(self) -> str:
        return f"RR#{self.pk or '?'} O#{self.order_id} {self.durum}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            return super().save(*args, **kwargs)
        if self._allow_status_transition:
            return super().save(*args, **kwargs)
        raise ValidationError(
            "ReturnRequest değişmez; geçiş yalnız return_servisi (F6-030)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("ReturnRequest silinemez.")
